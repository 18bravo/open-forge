"""
Prompt management system for agents.
"""
from typing import Dict, Optional
from pathlib import Path
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import yaml

class PromptManager:
    """Manages prompts for agents."""
    
    def __init__(self, prompts_dir: Optional[Path] = None):
        self.prompts_dir = prompts_dir or Path(__file__).parent / "prompt_templates"
        self._cache: Dict[str, ChatPromptTemplate] = {}
    
    def get_prompt(self, agent_name: str, prompt_name: str) -> ChatPromptTemplate:
        """Get a prompt template."""
        cache_key = f"{agent_name}:{prompt_name}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Load from file
        prompt_path = self.prompts_dir / agent_name / f"{prompt_name}.yaml"
        
        if prompt_path.exists():
            with open(prompt_path) as f:
                config = yaml.safe_load(f)
            prompt = self._build_prompt_from_config(config)
        else:
            # Return a default prompt
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a helpful assistant."),
                ("human", "{input}")
            ])
        
        self._cache[cache_key] = prompt
        return prompt
    
    def _build_prompt_from_config(self, config: Dict) -> ChatPromptTemplate:
        """Build a ChatPromptTemplate from configuration."""
        messages = []
        
        for msg in config.get("messages", []):
            role = msg.get("role", "human")
            content = msg.get("content", "")
            
            if role == "placeholder":
                messages.append(MessagesPlaceholder(variable_name=content))
            else:
                messages.append((role, content))
        
        return ChatPromptTemplate.from_messages(messages)
    
    def register_prompt(
        self,
        agent_name: str,
        prompt_name: str,
        prompt: ChatPromptTemplate
    ) -> None:
        """Register a prompt programmatically."""
        cache_key = f"{agent_name}:{prompt_name}"
        self._cache[cache_key] = prompt