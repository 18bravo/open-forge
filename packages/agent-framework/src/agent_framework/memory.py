"""
Agent memory and persistence for Open Forge.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
import json

from langchain_core.messages import BaseMessage, messages_from_dict, messages_to_dict
from langgraph.checkpoint.memory import MemorySaver
from redis.asyncio import Redis

from core.config import get_settings


class RedisMemorySaver(MemorySaver):
    """
    Redis-backed memory saver for LangGraph checkpoints.

    Provides persistent storage for agent state across sessions.
    """

    def __init__(self, redis_client: Optional[Redis] = None, prefix: str = "openforge:checkpoint"):
        super().__init__()
        self._redis = redis_client
        self.prefix = prefix

    async def _get_redis(self) -> Redis:
        if self._redis is None:
            settings = get_settings()
            self._redis = Redis.from_url(settings.redis.url)
        return self._redis

    def _make_key(self, thread_id: str, checkpoint_id: Optional[str] = None) -> str:
        if checkpoint_id:
            return f"{self.prefix}:{thread_id}:{checkpoint_id}"
        return f"{self.prefix}:{thread_id}:latest"

    async def aget(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get checkpoint from Redis."""
        redis = await self._get_redis()
        thread_id = config.get("configurable", {}).get("thread_id")
        checkpoint_id = config.get("configurable", {}).get("checkpoint_id")

        if not thread_id:
            return None

        key = self._make_key(thread_id, checkpoint_id)
        data = await redis.get(key)

        if data:
            return json.loads(data)
        return None

    async def aput(self, config: Dict[str, Any], checkpoint: Dict[str, Any]) -> None:
        """Save checkpoint to Redis."""
        redis = await self._get_redis()
        thread_id = config.get("configurable", {}).get("thread_id")

        if not thread_id:
            return

        checkpoint_id = checkpoint.get("id", datetime.utcnow().isoformat())
        checkpoint["id"] = checkpoint_id
        checkpoint["saved_at"] = datetime.utcnow().isoformat()

        # Save with specific checkpoint ID
        specific_key = self._make_key(thread_id, checkpoint_id)
        await redis.set(specific_key, json.dumps(checkpoint))

        # Also save as latest
        latest_key = self._make_key(thread_id, None)
        await redis.set(latest_key, json.dumps(checkpoint))

        # Add to checkpoint list for thread
        list_key = f"{self.prefix}:{thread_id}:list"
        await redis.lpush(list_key, checkpoint_id)

    async def alist(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """List all checkpoints for a thread."""
        redis = await self._get_redis()
        thread_id = config.get("configurable", {}).get("thread_id")

        if not thread_id:
            return []

        list_key = f"{self.prefix}:{thread_id}:list"
        checkpoint_ids = await redis.lrange(list_key, 0, -1)

        checkpoints = []
        for cid in checkpoint_ids:
            key = self._make_key(thread_id, cid.decode() if isinstance(cid, bytes) else cid)
            data = await redis.get(key)
            if data:
                checkpoints.append(json.loads(data))

        return checkpoints


class ConversationMemory:
    """
    Manages conversation history for agents.

    Provides:
    - Message storage and retrieval
    - Context window management
    - Summary generation for long conversations
    """

    def __init__(
        self,
        max_messages: int = 100,
        summarize_after: int = 50,
        redis_client: Optional[Redis] = None
    ):
        self.max_messages = max_messages
        self.summarize_after = summarize_after
        self._redis = redis_client
        self._local_cache: Dict[str, List[Dict[str, Any]]] = {}

    async def _get_redis(self) -> Optional[Redis]:
        if self._redis is None:
            try:
                settings = get_settings()
                self._redis = Redis.from_url(settings.redis.url)
            except Exception:
                return None
        return self._redis

    def _thread_key(self, thread_id: str) -> str:
        return f"openforge:memory:{thread_id}"

    async def add_message(
        self,
        thread_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a message to the conversation."""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }

        redis = await self._get_redis()
        if redis:
            key = self._thread_key(thread_id)
            await redis.rpush(key, json.dumps(message))
            # Trim to max size
            await redis.ltrim(key, -self.max_messages, -1)
        else:
            if thread_id not in self._local_cache:
                self._local_cache[thread_id] = []
            self._local_cache[thread_id].append(message)
            self._local_cache[thread_id] = self._local_cache[thread_id][-self.max_messages:]

    async def get_messages(
        self,
        thread_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get conversation messages."""
        redis = await self._get_redis()

        if redis:
            key = self._thread_key(thread_id)
            if limit:
                messages = await redis.lrange(key, -limit, -1)
            else:
                messages = await redis.lrange(key, 0, -1)
            return [json.loads(m) for m in messages]
        else:
            messages = self._local_cache.get(thread_id, [])
            if limit:
                return messages[-limit:]
            return messages

    async def clear(self, thread_id: str) -> None:
        """Clear conversation history."""
        redis = await self._get_redis()
        if redis:
            await redis.delete(self._thread_key(thread_id))
        else:
            self._local_cache.pop(thread_id, None)


class EngagementContext:
    """
    Manages engagement-level context that persists across agent interactions.
    """

    def __init__(self, engagement_id: str, redis_client: Optional[Redis] = None):
        self.engagement_id = engagement_id
        self._redis = redis_client

    async def _get_redis(self) -> Optional[Redis]:
        if self._redis is None:
            try:
                settings = get_settings()
                self._redis = Redis.from_url(settings.redis.url)
            except Exception:
                return None
        return self._redis

    def _context_key(self) -> str:
        return f"openforge:engagement:{self.engagement_id}:context"

    async def set(self, key: str, value: Any) -> None:
        """Set a context value."""
        redis = await self._get_redis()
        if redis:
            ctx_key = self._context_key()
            await redis.hset(ctx_key, key, json.dumps(value))

    async def get(self, key: str, default: Any = None) -> Any:
        """Get a context value."""
        redis = await self._get_redis()
        if redis:
            ctx_key = self._context_key()
            value = await redis.hget(ctx_key, key)
            if value:
                return json.loads(value)
        return default

    async def get_all(self) -> Dict[str, Any]:
        """Get all context values."""
        redis = await self._get_redis()
        if redis:
            ctx_key = self._context_key()
            data = await redis.hgetall(ctx_key)
            return {k.decode(): json.loads(v) for k, v in data.items()}
        return {}

    async def delete(self, key: str) -> None:
        """Delete a context value."""
        redis = await self._get_redis()
        if redis:
            ctx_key = self._context_key()
            await redis.hdel(ctx_key, key)
