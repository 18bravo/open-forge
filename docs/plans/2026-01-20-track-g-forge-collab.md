# Track G: Forge Collaboration Platform Design

**Date:** 2026-01-20
**Status:** Draft
**Track:** G - Collaboration
**Dependencies:** api, ontology, ui

---

## Executive Summary

Track G implements collaboration capabilities for Open Forge, providing fine-grained sharing permissions, curated collections, real-time alerts, and comprehensive audit logging. This track addresses ~10+ collaboration features that enable enterprise teamwork.

### Key Packages

| Package | Purpose |
|---------|---------|
| `forge-sharing` | Permissions & access control |
| `forge-collections` | Curated asset collections |
| `forge-alerts` | Notifications & subscriptions |
| `forge-audit` | Audit logging & compliance |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       FORGE COLLABORATION PLATFORM                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         ACCESS LAYER                                   │  │
│  │  ┌───────────────────────────────────────────────────────────────┐    │  │
│  │  │                    FORGE SHARING                               │    │  │
│  │  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  │    │  │
│  │  │  │   Users   │  │   Groups  │  │   Roles   │  │  Policies │  │    │  │
│  │  │  │           │  │           │  │           │  │           │  │    │  │
│  │  │  └───────────┘  └───────────┘  └───────────┘  └───────────┘  │    │  │
│  │  └───────────────────────────────────────────────────────────────┘    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                      │                                       │
│                                      ▼                                       │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐  │
│  │  FORGE COLLECTIONS  │  │    FORGE ALERTS     │  │    FORGE AUDIT      │  │
│  ├─────────────────────┤  ├─────────────────────┤  ├─────────────────────┤  │
│  │  Workspaces         │  │  Subscriptions      │  │  Event Capture      │  │
│  │  Folders            │  │  Delivery Channels  │  │  Query Interface    │  │
│  │  Bookmarks          │  │  Alert Rules        │  │  Retention Policy   │  │
│  │  Tags               │  │  Digest Scheduling  │  │  Export/Report      │  │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Package 1: Forge Sharing

### Purpose

Fine-grained access control with users, groups, roles, and attribute-based policies.

### Module Structure

```
packages/forge-sharing/
├── src/
│   └── forge_sharing/
│       ├── __init__.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── user.py            # User model
│       │   ├── group.py           # Group model
│       │   ├── role.py            # Role model
│       │   ├── permission.py      # Permission grants
│       │   └── policy.py          # ABAC policies
│       ├── engine/
│       │   ├── __init__.py
│       │   ├── evaluator.py       # Permission evaluator
│       │   ├── resolver.py        # Inheritance resolver
│       │   └── cache.py           # Permission cache
│       ├── providers/
│       │   ├── __init__.py
│       │   ├── local.py           # Local auth
│       │   ├── oidc.py            # OIDC provider
│       │   ├── saml.py            # SAML provider
│       │   └── ldap.py            # LDAP/AD
│       └── api/
│           ├── __init__.py
│           └── routes.py
├── tests/
└── pyproject.toml
```

### Core Classes

```python
# models/permission.py
from enum import Enum
from pydantic import BaseModel
from datetime import datetime

class PermissionLevel(str, Enum):
    NONE = "none"
    VIEW = "view"
    EDIT = "edit"
    MANAGE = "manage"
    OWNER = "owner"

class ResourceType(str, Enum):
    DATASET = "dataset"
    ONTOLOGY = "ontology"
    PIPELINE = "pipeline"
    APP = "app"
    COLLECTION = "collection"
    WORKSPACE = "workspace"

class PermissionGrant(BaseModel):
    id: str
    resource_type: ResourceType
    resource_id: str
    principal_type: Literal["user", "group", "role"]
    principal_id: str
    level: PermissionLevel
    inherited_from: str | None = None  # Parent resource ID
    created_at: datetime
    created_by: str
    expires_at: datetime | None = None
    conditions: dict | None = None  # ABAC conditions

class EffectivePermission(BaseModel):
    resource_type: ResourceType
    resource_id: str
    user_id: str
    level: PermissionLevel
    sources: list[str]  # Grant IDs that contribute
    cached_at: datetime
```

```python
# models/role.py
class Permission(BaseModel):
    action: str  # e.g., "datasets:read", "pipelines:execute"
    resource_pattern: str  # e.g., "*", "datasets/*", "datasets/prod-*"

class Role(BaseModel):
    id: str
    name: str
    description: str | None = None
    permissions: list[Permission]
    is_system: bool = False  # Built-in roles
    created_at: datetime
    updated_at: datetime

# Built-in roles
BUILTIN_ROLES = {
    "viewer": Role(
        id="viewer",
        name="Viewer",
        permissions=[
            Permission(action="*:read", resource_pattern="*"),
        ],
        is_system=True
    ),
    "editor": Role(
        id="editor",
        name="Editor",
        permissions=[
            Permission(action="*:read", resource_pattern="*"),
            Permission(action="*:write", resource_pattern="*"),
        ],
        is_system=True
    ),
    "admin": Role(
        id="admin",
        name="Administrator",
        permissions=[
            Permission(action="*", resource_pattern="*"),
        ],
        is_system=True
    ),
}
```

```python
# models/policy.py
class PolicyCondition(BaseModel):
    attribute: str
    operator: Literal["eq", "ne", "in", "not_in", "contains", "gt", "lt", "regex"]
    value: Any

class Policy(BaseModel):
    id: str
    name: str
    description: str | None = None
    effect: Literal["allow", "deny"]
    priority: int = 0  # Higher = evaluated first
    conditions: list[PolicyCondition]
    actions: list[str]  # Actions this policy applies to
    resources: list[str]  # Resource patterns
    principals: list[str]  # Principal patterns
    enabled: bool = True

    def matches(
        self,
        action: str,
        resource: str,
        principal: str,
        context: dict
    ) -> bool:
        """Check if policy applies to this request."""
        if not self._matches_pattern(action, self.actions):
            return False
        if not self._matches_pattern(resource, self.resources):
            return False
        if not self._matches_pattern(principal, self.principals):
            return False

        # Evaluate conditions
        for condition in self.conditions:
            if not self._evaluate_condition(condition, context):
                return False

        return True

    def _evaluate_condition(self, condition: PolicyCondition, context: dict) -> bool:
        value = self._get_nested_value(context, condition.attribute)

        if condition.operator == "eq":
            return value == condition.value
        elif condition.operator == "ne":
            return value != condition.value
        elif condition.operator == "in":
            return value in condition.value
        elif condition.operator == "not_in":
            return value not in condition.value
        elif condition.operator == "contains":
            return condition.value in value
        elif condition.operator == "gt":
            return value > condition.value
        elif condition.operator == "lt":
            return value < condition.value
        elif condition.operator == "regex":
            import re
            return bool(re.match(condition.value, str(value)))

        return False
```

```python
# engine/evaluator.py
class PermissionEvaluator:
    """Evaluate permissions for access control."""

    def __init__(
        self,
        grant_store: "GrantStore",
        policy_store: "PolicyStore",
        cache: "PermissionCache"
    ):
        self.grants = grant_store
        self.policies = policy_store
        self.cache = cache

    async def check(
        self,
        user_id: str,
        action: str,
        resource_type: ResourceType,
        resource_id: str,
        context: dict | None = None
    ) -> bool:
        """Check if user has permission for action on resource."""
        context = context or {}

        # Check cache first
        cache_key = f"{user_id}:{action}:{resource_type}:{resource_id}"
        cached = await self.cache.get(cache_key)
        if cached is not None:
            return cached

        # Get effective permission
        effective = await self.get_effective_permission(
            user_id, resource_type, resource_id
        )

        # Check if permission level allows action
        allowed = self._level_allows_action(effective.level, action)

        # Apply ABAC policies
        if allowed:
            allowed = await self._evaluate_policies(
                user_id, action, f"{resource_type}:{resource_id}", context
            )

        # Cache result
        await self.cache.set(cache_key, allowed, ttl=300)

        return allowed

    async def get_effective_permission(
        self,
        user_id: str,
        resource_type: ResourceType,
        resource_id: str
    ) -> EffectivePermission:
        """Calculate effective permission for user on resource."""
        # Get user's groups
        user_groups = await self._get_user_groups(user_id)

        # Get user's roles
        user_roles = await self._get_user_roles(user_id)

        # Get all applicable grants
        grants = []

        # Direct user grants
        grants.extend(await self.grants.get_grants(
            resource_type=resource_type,
            resource_id=resource_id,
            principal_type="user",
            principal_id=user_id
        ))

        # Group grants
        for group_id in user_groups:
            grants.extend(await self.grants.get_grants(
                resource_type=resource_type,
                resource_id=resource_id,
                principal_type="group",
                principal_id=group_id
            ))

        # Role grants
        for role_id in user_roles:
            grants.extend(await self.grants.get_grants(
                resource_type=resource_type,
                resource_id=resource_id,
                principal_type="role",
                principal_id=role_id
            ))

        # Inherited grants from parent resources
        parent_grants = await self._get_inherited_grants(
            user_id, user_groups, user_roles, resource_type, resource_id
        )
        grants.extend(parent_grants)

        # Calculate highest permission level
        highest_level = PermissionLevel.NONE
        sources = []

        for grant in grants:
            # Check expiration
            if grant.expires_at and grant.expires_at < datetime.utcnow():
                continue

            if self._level_rank(grant.level) > self._level_rank(highest_level):
                highest_level = grant.level

            sources.append(grant.id)

        return EffectivePermission(
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user_id,
            level=highest_level,
            sources=sources,
            cached_at=datetime.utcnow()
        )

    async def _evaluate_policies(
        self,
        user_id: str,
        action: str,
        resource: str,
        context: dict
    ) -> bool:
        """Evaluate ABAC policies."""
        policies = await self.policies.get_active_policies()

        # Sort by priority (higher first)
        policies.sort(key=lambda p: p.priority, reverse=True)

        # Enrich context
        context["user"] = await self._get_user_attributes(user_id)
        context["time"] = datetime.utcnow()

        for policy in policies:
            if policy.matches(action, resource, user_id, context):
                return policy.effect == "allow"

        # Default allow if no policy matched
        return True
```

### API Routes

```python
# api/routes.py
router = APIRouter(prefix="/api/v1/sharing", tags=["sharing"])

@router.post("/grants")
async def create_grant(
    resource_type: ResourceType,
    resource_id: str,
    principal_type: Literal["user", "group", "role"],
    principal_id: str,
    level: PermissionLevel,
    expires_at: datetime | None = None
) -> PermissionGrant:
    """Grant permission to a principal."""
    pass

@router.delete("/grants/{grant_id}")
async def revoke_grant(grant_id: str) -> dict:
    """Revoke a permission grant."""
    pass

@router.get("/grants")
async def list_grants(
    resource_type: ResourceType | None = None,
    resource_id: str | None = None,
    principal_id: str | None = None
) -> list[PermissionGrant]:
    """List permission grants."""
    pass

@router.get("/resources/{resource_type}/{resource_id}/effective")
async def get_effective_permissions(
    resource_type: ResourceType,
    resource_id: str,
    user_id: str | None = None
) -> EffectivePermission:
    """Get effective permissions for resource."""
    pass

@router.post("/check")
async def check_permission(
    user_id: str,
    action: str,
    resource_type: ResourceType,
    resource_id: str
) -> dict:
    """Check if user has permission."""
    pass

@router.get("/groups")
async def list_groups() -> list[Group]:
    """List all groups."""
    pass

@router.post("/groups")
async def create_group(name: str, description: str | None = None) -> Group:
    """Create a group."""
    pass

@router.post("/groups/{group_id}/members")
async def add_group_member(group_id: str, user_id: str) -> dict:
    """Add user to group."""
    pass

@router.get("/roles")
async def list_roles() -> list[Role]:
    """List all roles."""
    pass
```

---

## Package 2: Forge Collections

### Purpose

Organize assets into workspaces, folders, and curated collections with bookmarks and tags.

### Module Structure

```
packages/forge-collections/
├── src/
│   └── forge_collections/
│       ├── __init__.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── workspace.py       # Workspace model
│       │   ├── folder.py          # Folder model
│       │   ├── bookmark.py        # Bookmarks
│       │   └── tag.py             # Tags
│       ├── services/
│       │   ├── __init__.py
│       │   ├── workspace.py       # Workspace service
│       │   ├── folder.py          # Folder service
│       │   └── search.py          # Collection search
│       └── api/
│           ├── __init__.py
│           └── routes.py
├── tests/
└── pyproject.toml
```

### Core Classes

```python
# models/workspace.py
class Workspace(BaseModel):
    id: str
    name: str
    description: str | None = None
    icon: str | None = None
    color: str | None = None
    owner_id: str
    visibility: Literal["private", "team", "public"] = "team"
    settings: dict = {}
    created_at: datetime
    updated_at: datetime

    # Stats
    member_count: int = 0
    item_count: int = 0

class WorkspaceMember(BaseModel):
    workspace_id: str
    user_id: str
    role: Literal["viewer", "editor", "admin", "owner"]
    joined_at: datetime
    invited_by: str | None = None
```

```python
# models/folder.py
class Folder(BaseModel):
    id: str
    name: str
    description: str | None = None
    workspace_id: str
    parent_id: str | None = None
    path: str  # /workspace_id/folder1/folder2
    icon: str | None = None
    color: str | None = None
    created_by: str
    created_at: datetime
    updated_at: datetime

    # Contents
    item_count: int = 0

class FolderItem(BaseModel):
    id: str
    folder_id: str
    resource_type: str
    resource_id: str
    position: int  # For ordering
    added_by: str
    added_at: datetime
    notes: str | None = None
```

```python
# models/bookmark.py
class Bookmark(BaseModel):
    id: str
    user_id: str
    resource_type: str
    resource_id: str
    name: str | None = None  # Custom display name
    notes: str | None = None
    tags: list[str] = []
    created_at: datetime

class RecentItem(BaseModel):
    user_id: str
    resource_type: str
    resource_id: str
    last_accessed: datetime
    access_count: int = 1
```

```python
# services/workspace.py
class WorkspaceService:
    """Manage workspaces and their contents."""

    def __init__(self, db: AsyncSession, sharing: PermissionEvaluator):
        self.db = db
        self.sharing = sharing

    async def create_workspace(
        self,
        name: str,
        owner_id: str,
        description: str | None = None,
        visibility: str = "team"
    ) -> Workspace:
        """Create a new workspace."""
        workspace = Workspace(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            owner_id=owner_id,
            visibility=visibility,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Create workspace record
        self.db.add(WorkspaceModel(**workspace.dict()))

        # Create owner membership
        self.db.add(WorkspaceMemberModel(
            workspace_id=workspace.id,
            user_id=owner_id,
            role="owner",
            joined_at=datetime.utcnow()
        ))

        # Grant owner permissions
        await self.sharing.grants.create_grant(
            resource_type=ResourceType.WORKSPACE,
            resource_id=workspace.id,
            principal_type="user",
            principal_id=owner_id,
            level=PermissionLevel.OWNER
        )

        await self.db.commit()
        return workspace

    async def get_user_workspaces(
        self,
        user_id: str,
        include_shared: bool = True
    ) -> list[Workspace]:
        """Get workspaces accessible to user."""
        # Get owned workspaces
        query = select(WorkspaceModel).where(WorkspaceModel.owner_id == user_id)
        result = await self.db.execute(query)
        workspaces = [Workspace.from_orm(w) for w in result.scalars()]

        if include_shared:
            # Get workspaces user is member of
            member_query = (
                select(WorkspaceModel)
                .join(WorkspaceMemberModel)
                .where(WorkspaceMemberModel.user_id == user_id)
                .where(WorkspaceModel.owner_id != user_id)
            )
            result = await self.db.execute(member_query)
            workspaces.extend([Workspace.from_orm(w) for w in result.scalars()])

        return workspaces
```

### API Routes

```python
# api/routes.py
router = APIRouter(prefix="/api/v1/collections", tags=["collections"])

@router.get("/workspaces")
async def list_workspaces(
    include_shared: bool = True
) -> list[Workspace]:
    """List user's workspaces."""
    pass

@router.post("/workspaces")
async def create_workspace(
    name: str,
    description: str | None = None,
    visibility: Literal["private", "team", "public"] = "team"
) -> Workspace:
    """Create a workspace."""
    pass

@router.get("/workspaces/{workspace_id}")
async def get_workspace(workspace_id: str) -> Workspace:
    """Get workspace details."""
    pass

@router.post("/workspaces/{workspace_id}/members")
async def add_workspace_member(
    workspace_id: str,
    user_id: str,
    role: str = "viewer"
) -> WorkspaceMember:
    """Add member to workspace."""
    pass

@router.get("/workspaces/{workspace_id}/folders")
async def list_folders(
    workspace_id: str,
    parent_id: str | None = None
) -> list[Folder]:
    """List folders in workspace."""
    pass

@router.post("/workspaces/{workspace_id}/folders")
async def create_folder(
    workspace_id: str,
    name: str,
    parent_id: str | None = None
) -> Folder:
    """Create a folder."""
    pass

@router.post("/folders/{folder_id}/items")
async def add_folder_item(
    folder_id: str,
    resource_type: str,
    resource_id: str
) -> FolderItem:
    """Add item to folder."""
    pass

@router.get("/bookmarks")
async def list_bookmarks(
    tags: list[str] | None = None
) -> list[Bookmark]:
    """List user's bookmarks."""
    pass

@router.post("/bookmarks")
async def create_bookmark(
    resource_type: str,
    resource_id: str,
    name: str | None = None,
    tags: list[str] | None = None
) -> Bookmark:
    """Create a bookmark."""
    pass

@router.get("/recent")
async def list_recent(
    limit: int = 20
) -> list[RecentItem]:
    """List recently accessed items."""
    pass
```

---

## Package 3: Forge Alerts

### Purpose

Real-time notifications, subscription management, and alert delivery across multiple channels.

### Module Structure

```
packages/forge-alerts/
├── src/
│   └── forge_alerts/
│       ├── __init__.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── subscription.py    # Subscriptions
│       │   ├── alert.py           # Alert definitions
│       │   ├── notification.py    # Notifications
│       │   └── channel.py         # Delivery channels
│       ├── engine/
│       │   ├── __init__.py
│       │   ├── evaluator.py       # Alert evaluation
│       │   ├── dispatcher.py      # Notification dispatch
│       │   └── digest.py          # Digest generation
│       ├── channels/
│       │   ├── __init__.py
│       │   ├── email.py           # Email channel
│       │   ├── slack.py           # Slack channel
│       │   ├── webhook.py         # Webhook channel
│       │   └── in_app.py          # In-app notifications
│       └── api/
│           ├── __init__.py
│           └── routes.py
├── tests/
└── pyproject.toml
```

### Core Classes

```python
# models/subscription.py
class Subscription(BaseModel):
    id: str
    user_id: str
    resource_type: str
    resource_id: str
    events: list[str]  # ["updated", "deleted", "quality_failed"]
    channels: list[str]  # ["email", "slack", "in_app"]
    digest_frequency: Literal["instant", "hourly", "daily", "weekly"] | None = "instant"
    enabled: bool = True
    created_at: datetime

class AlertRule(BaseModel):
    id: str
    name: str
    description: str | None = None
    resource_type: str
    resource_pattern: str  # Glob pattern, e.g., "datasets/prod-*"
    condition: "AlertCondition"
    actions: list["AlertAction"]
    severity: Literal["info", "warning", "error", "critical"]
    enabled: bool = True
    created_by: str
    created_at: datetime

class AlertCondition(BaseModel):
    type: str  # "threshold", "change", "pattern", "schedule"
    parameters: dict
    # Examples:
    # threshold: {"metric": "row_count", "operator": "lt", "value": 1000}
    # change: {"field": "schema", "change_type": "any"}
    # pattern: {"field": "status", "regex": "FAILED|ERROR"}
    # schedule: {"expected_by": "08:00", "timezone": "UTC"}
```

```python
# models/notification.py
class Notification(BaseModel):
    id: str
    user_id: str
    title: str
    message: str
    resource_type: str | None = None
    resource_id: str | None = None
    severity: Literal["info", "warning", "error", "critical"] = "info"
    read: bool = False
    read_at: datetime | None = None
    created_at: datetime
    metadata: dict = {}

class NotificationDigest(BaseModel):
    id: str
    user_id: str
    period_start: datetime
    period_end: datetime
    notification_count: int
    notifications: list[Notification]
    sent_at: datetime | None = None
    channel: str
```

```python
# engine/evaluator.py
class AlertEvaluator:
    """Evaluate alert conditions."""

    def __init__(self, rule_store: "RuleStore"):
        self.rules = rule_store

    async def evaluate_event(
        self,
        event_type: str,
        resource_type: str,
        resource_id: str,
        event_data: dict
    ) -> list[AlertRule]:
        """Find rules that match an event."""
        matching_rules = []

        rules = await self.rules.get_rules_for_resource(resource_type, resource_id)

        for rule in rules:
            if event_type not in self._get_rule_events(rule):
                continue

            if await self._evaluate_condition(rule.condition, event_data):
                matching_rules.append(rule)

        return matching_rules

    async def _evaluate_condition(
        self,
        condition: AlertCondition,
        event_data: dict
    ) -> bool:
        """Evaluate a single condition."""
        if condition.type == "threshold":
            metric = event_data.get(condition.parameters["metric"])
            operator = condition.parameters["operator"]
            value = condition.parameters["value"]

            if operator == "lt":
                return metric < value
            elif operator == "gt":
                return metric > value
            elif operator == "eq":
                return metric == value
            elif operator == "ne":
                return metric != value

        elif condition.type == "change":
            field = condition.parameters["field"]
            change_type = condition.parameters.get("change_type", "any")

            old_value = event_data.get(f"old_{field}")
            new_value = event_data.get(f"new_{field}")

            if change_type == "any":
                return old_value != new_value
            elif change_type == "increase":
                return new_value > old_value
            elif change_type == "decrease":
                return new_value < old_value

        elif condition.type == "pattern":
            import re
            field = condition.parameters["field"]
            pattern = condition.parameters["regex"]
            value = event_data.get(field, "")
            return bool(re.match(pattern, str(value)))

        return False
```

```python
# engine/dispatcher.py
class NotificationDispatcher:
    """Dispatch notifications to channels."""

    def __init__(self, channels: dict[str, "NotificationChannel"]):
        self.channels = channels

    async def dispatch(
        self,
        notification: Notification,
        channel_names: list[str]
    ):
        """Send notification to specified channels."""
        for channel_name in channel_names:
            channel = self.channels.get(channel_name)
            if channel:
                try:
                    await channel.send(notification)
                except Exception as e:
                    logger.error(f"Failed to send to {channel_name}: {e}")

    async def dispatch_to_subscribers(
        self,
        event_type: str,
        resource_type: str,
        resource_id: str,
        notification_data: dict,
        subscription_store: "SubscriptionStore"
    ):
        """Find subscribers and dispatch notifications."""
        subscriptions = await subscription_store.get_subscriptions(
            resource_type=resource_type,
            resource_id=resource_id,
            event=event_type
        )

        for sub in subscriptions:
            if not sub.enabled:
                continue

            notification = Notification(
                id=str(uuid.uuid4()),
                user_id=sub.user_id,
                title=notification_data["title"],
                message=notification_data["message"],
                resource_type=resource_type,
                resource_id=resource_id,
                severity=notification_data.get("severity", "info"),
                created_at=datetime.utcnow(),
                metadata=notification_data.get("metadata", {})
            )

            # Store notification
            await self._store_notification(notification)

            # Dispatch based on frequency
            if sub.digest_frequency == "instant":
                await self.dispatch(notification, sub.channels)
            # Else: will be included in digest
```

```python
# channels/slack.py
class SlackChannel:
    """Slack notification channel."""

    def __init__(self, webhook_url: str | None = None):
        self.webhook_url = webhook_url

    async def send(self, notification: Notification):
        """Send notification to Slack."""
        import httpx

        # Get user's Slack webhook (or use default)
        webhook = await self._get_user_webhook(notification.user_id) or self.webhook_url

        if not webhook:
            raise ValueError("No Slack webhook configured")

        color = {
            "info": "#36a64f",
            "warning": "#ffcc00",
            "error": "#ff6600",
            "critical": "#ff0000"
        }.get(notification.severity, "#36a64f")

        payload = {
            "attachments": [{
                "color": color,
                "title": notification.title,
                "text": notification.message,
                "fields": [
                    {
                        "title": "Resource",
                        "value": f"{notification.resource_type}/{notification.resource_id}",
                        "short": True
                    },
                    {
                        "title": "Severity",
                        "value": notification.severity.upper(),
                        "short": True
                    }
                ],
                "ts": int(notification.created_at.timestamp())
            }]
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(webhook, json=payload)
            response.raise_for_status()
```

### API Routes

```python
# api/routes.py
router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])

@router.get("/notifications")
async def list_notifications(
    unread_only: bool = False,
    limit: int = 50
) -> list[Notification]:
    """List user's notifications."""
    pass

@router.post("/notifications/{notification_id}/read")
async def mark_read(notification_id: str) -> Notification:
    """Mark notification as read."""
    pass

@router.post("/notifications/read-all")
async def mark_all_read() -> dict:
    """Mark all notifications as read."""
    pass

@router.get("/subscriptions")
async def list_subscriptions() -> list[Subscription]:
    """List user's subscriptions."""
    pass

@router.post("/subscriptions")
async def create_subscription(
    resource_type: str,
    resource_id: str,
    events: list[str],
    channels: list[str] = ["in_app"],
    digest_frequency: str = "instant"
) -> Subscription:
    """Create a subscription."""
    pass

@router.delete("/subscriptions/{subscription_id}")
async def delete_subscription(subscription_id: str) -> dict:
    """Delete a subscription."""
    pass

@router.get("/rules")
async def list_alert_rules() -> list[AlertRule]:
    """List alert rules."""
    pass

@router.post("/rules")
async def create_alert_rule(
    name: str,
    resource_type: str,
    resource_pattern: str,
    condition: AlertCondition,
    actions: list[AlertAction],
    severity: str = "warning"
) -> AlertRule:
    """Create an alert rule."""
    pass

@router.get("/channels")
async def list_channels() -> list[dict]:
    """List available notification channels."""
    pass

@router.post("/channels/test")
async def test_channel(
    channel: str,
    config: dict
) -> dict:
    """Test a notification channel."""
    pass
```

---

## Package 4: Forge Audit

### Purpose

Comprehensive audit logging for compliance, security analysis, and operational visibility.

### Module Structure

```
packages/forge-audit/
├── src/
│   └── forge_audit/
│       ├── __init__.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── event.py           # Audit event
│       │   └── query.py           # Query models
│       ├── capture/
│       │   ├── __init__.py
│       │   ├── middleware.py      # FastAPI middleware
│       │   ├── decorators.py      # Function decorators
│       │   └── hooks.py           # Event hooks
│       ├── storage/
│       │   ├── __init__.py
│       │   ├── postgres.py        # PostgreSQL storage
│       │   ├── elasticsearch.py   # Elasticsearch storage
│       │   └── s3.py              # S3 archival
│       ├── query/
│       │   ├── __init__.py
│       │   ├── search.py          # Audit search
│       │   └── aggregations.py    # Analytics
│       └── api/
│           ├── __init__.py
│           └── routes.py
├── tests/
└── pyproject.toml
```

### Core Classes

```python
# models/event.py
class AuditEvent(BaseModel):
    id: str
    timestamp: datetime
    event_type: str  # "resource.created", "resource.updated", "user.login"
    action: str  # "create", "read", "update", "delete", "execute"
    actor_id: str
    actor_type: Literal["user", "service", "system"]
    resource_type: str | None = None
    resource_id: str | None = None
    resource_name: str | None = None

    # Request context
    ip_address: str | None = None
    user_agent: str | None = None
    request_id: str | None = None
    session_id: str | None = None

    # Change details
    changes: dict | None = None  # {"field": {"old": x, "new": y}}
    metadata: dict = {}

    # Outcome
    success: bool = True
    error_message: str | None = None

    # Security
    sensitive: bool = False  # If true, restrict access to audit
    retention_days: int | None = None  # Override default retention
```

```python
# capture/middleware.py
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time

class AuditMiddleware(BaseHTTPMiddleware):
    """Capture audit events from HTTP requests."""

    def __init__(self, app, audit_logger: "AuditLogger", config: dict = None):
        super().__init__(app)
        self.audit = audit_logger
        self.config = config or {}

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        request_id = str(uuid.uuid4())

        # Extract user info
        user_id = await self._get_user_id(request)

        # Process request
        response = await call_next(request)

        # Log audit event for write operations
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            await self._log_request(
                request=request,
                response=response,
                user_id=user_id,
                request_id=request_id,
                duration_ms=int((time.time() - start_time) * 1000)
            )

        return response

    async def _log_request(
        self,
        request: Request,
        response: Response,
        user_id: str,
        request_id: str,
        duration_ms: int
    ):
        """Log audit event for request."""
        # Parse resource from path
        resource_type, resource_id = self._parse_resource(request.url.path)

        # Determine action from method
        action_map = {
            "POST": "create",
            "PUT": "update",
            "PATCH": "update",
            "DELETE": "delete"
        }

        event = AuditEvent(
            id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            event_type=f"{resource_type}.{action_map[request.method]}",
            action=action_map[request.method],
            actor_id=user_id,
            actor_type="user",
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            request_id=request_id,
            success=200 <= response.status_code < 300,
            metadata={
                "method": request.method,
                "path": str(request.url.path),
                "status_code": response.status_code,
                "duration_ms": duration_ms
            }
        )

        await self.audit.log(event)
```

```python
# query/search.py
class AuditSearch:
    """Search and query audit events."""

    def __init__(self, storage: "AuditStorage"):
        self.storage = storage

    async def search(
        self,
        event_types: list[str] | None = None,
        actions: list[str] | None = None,
        actor_id: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        success: bool | None = None,
        query: str | None = None,  # Full-text search
        limit: int = 100,
        offset: int = 0
    ) -> "AuditSearchResult":
        """Search audit events with filters."""
        filters = []

        if event_types:
            filters.append({"event_type": {"$in": event_types}})
        if actions:
            filters.append({"action": {"$in": actions}})
        if actor_id:
            filters.append({"actor_id": actor_id})
        if resource_type:
            filters.append({"resource_type": resource_type})
        if resource_id:
            filters.append({"resource_id": resource_id})
        if start_time:
            filters.append({"timestamp": {"$gte": start_time}})
        if end_time:
            filters.append({"timestamp": {"$lte": end_time}})
        if success is not None:
            filters.append({"success": success})

        return await self.storage.search(
            filters=filters,
            query=query,
            limit=limit,
            offset=offset
        )

    async def get_activity_timeline(
        self,
        resource_type: str,
        resource_id: str,
        limit: int = 50
    ) -> list[AuditEvent]:
        """Get activity timeline for a resource."""
        return await self.search(
            resource_type=resource_type,
            resource_id=resource_id,
            limit=limit
        )

    async def get_user_activity(
        self,
        user_id: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None
    ) -> list[AuditEvent]:
        """Get activity for a user."""
        return await self.search(
            actor_id=user_id,
            start_time=start_time,
            end_time=end_time
        )
```

```python
# query/aggregations.py
class AuditAggregations:
    """Aggregate audit data for analytics."""

    def __init__(self, storage: "AuditStorage"):
        self.storage = storage

    async def activity_by_user(
        self,
        start_time: datetime,
        end_time: datetime,
        limit: int = 20
    ) -> list[dict]:
        """Get activity counts by user."""
        return await self.storage.aggregate(
            group_by="actor_id",
            metric="count",
            filters=[
                {"timestamp": {"$gte": start_time}},
                {"timestamp": {"$lte": end_time}}
            ],
            limit=limit
        )

    async def activity_by_resource_type(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> list[dict]:
        """Get activity counts by resource type."""
        return await self.storage.aggregate(
            group_by="resource_type",
            metric="count",
            filters=[
                {"timestamp": {"$gte": start_time}},
                {"timestamp": {"$lte": end_time}}
            ]
        )

    async def activity_over_time(
        self,
        start_time: datetime,
        end_time: datetime,
        interval: str = "hour"  # hour, day, week
    ) -> list[dict]:
        """Get activity over time."""
        return await self.storage.time_series(
            date_field="timestamp",
            interval=interval,
            start_time=start_time,
            end_time=end_time
        )

    async def failed_actions(
        self,
        start_time: datetime,
        end_time: datetime,
        limit: int = 100
    ) -> list[AuditEvent]:
        """Get failed actions for security analysis."""
        return await self.storage.search(
            filters=[
                {"success": False},
                {"timestamp": {"$gte": start_time}},
                {"timestamp": {"$lte": end_time}}
            ],
            limit=limit
        )
```

### API Routes

```python
# api/routes.py
router = APIRouter(prefix="/api/v1/audit", tags=["audit"])

@router.get("/events")
async def search_events(
    event_types: list[str] | None = None,
    actions: list[str] | None = None,
    actor_id: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    success: bool | None = None,
    query: str | None = None,
    limit: int = 100,
    offset: int = 0
) -> AuditSearchResult:
    """Search audit events."""
    pass

@router.get("/events/{event_id}")
async def get_event(event_id: str) -> AuditEvent:
    """Get audit event details."""
    pass

@router.get("/resources/{resource_type}/{resource_id}/timeline")
async def get_resource_timeline(
    resource_type: str,
    resource_id: str,
    limit: int = 50
) -> list[AuditEvent]:
    """Get activity timeline for resource."""
    pass

@router.get("/users/{user_id}/activity")
async def get_user_activity(
    user_id: str,
    start_time: datetime | None = None,
    end_time: datetime | None = None,
    limit: int = 100
) -> list[AuditEvent]:
    """Get user activity."""
    pass

@router.get("/analytics/by-user")
async def activity_by_user(
    start_time: datetime,
    end_time: datetime,
    limit: int = 20
) -> list[dict]:
    """Get activity aggregated by user."""
    pass

@router.get("/analytics/by-resource")
async def activity_by_resource(
    start_time: datetime,
    end_time: datetime
) -> list[dict]:
    """Get activity aggregated by resource type."""
    pass

@router.get("/analytics/timeline")
async def activity_timeline(
    start_time: datetime,
    end_time: datetime,
    interval: str = "hour"
) -> list[dict]:
    """Get activity over time."""
    pass

@router.post("/export")
async def export_audit_logs(
    start_time: datetime,
    end_time: datetime,
    format: Literal["json", "csv"] = "json"
) -> StreamingResponse:
    """Export audit logs."""
    pass
```

---

## Implementation Roadmap

### Phase G1: Sharing + Collections (Weeks 1-3)

**Deliverables:**
1. forge-sharing with RBAC
2. forge-collections with workspaces/folders
3. Permission evaluation engine
4. Workspace UI

### Phase G2: Alerts + Audit (Weeks 4-5)

**Deliverables:**
1. forge-alerts with notification dispatch
2. forge-audit with event capture
3. Slack and email channels
4. Audit log UI

### Phase G3: Scribe + Hub (Week 6)

**Deliverables:**
1. Rich text reporting (Forge Scribe)
2. Workspace management UI (Forge Hub)
