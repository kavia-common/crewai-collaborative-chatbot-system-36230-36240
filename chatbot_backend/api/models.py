from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    """Abstract base model with created/updated timestamps."""
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        abstract = True


class AgentProfile(TimeStampedModel):
    """
    Stores metadata about an agent participating in a chat session.
    Example agents: 'researcher', 'writer', 'coordinator' etc.
    """
    # PUBLIC_INTERFACE
    name = models.CharField(max_length=64, unique=True, help_text="Logical name of the agent (e.g., researcher, writer)")
    # PUBLIC_INTERFACE
    role = models.CharField(max_length=128, blank=True, default="", help_text="High-level role or responsibility")
    # PUBLIC_INTERFACE
    description = models.TextField(blank=True, default="", help_text="Detailed description or system prompt summary")
    # PUBLIC_INTERFACE
    model_hint = models.CharField(max_length=128, blank=True, default="", help_text="Optional LLM/model hint used by CrewAI")
    # PUBLIC_INTERFACE
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f"{self.name} ({'active' if self.is_active else 'inactive'})"

    class Meta:
        verbose_name = "Agent Profile"
        verbose_name_plural = "Agent Profiles"


class ToolDefinition(TimeStampedModel):
    """
    Optional metadata to record tools available to agents in CrewAI.
    """
    # PUBLIC_INTERFACE
    name = models.CharField(max_length=128, unique=True)
    # PUBLIC_INTERFACE
    description = models.TextField(blank=True, default="")
    # PUBLIC_INTERFACE
    schema = models.JSONField(blank=True, null=True, help_text="Optional tool schema/specification")
    # PUBLIC_INTERFACE
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = "Tool Definition"
        verbose_name_plural = "Tool Definitions"


class ChatSession(TimeStampedModel):
    """
    Represents a chat conversation session. Pairs with CrewAI run context.
    """
    # PUBLIC_INTERFACE
    session_id = models.CharField(max_length=64, unique=True, db_index=True, help_text="External identifier for the session")
    # PUBLIC_INTERFACE
    title = models.CharField(max_length=200, blank=True, default="", help_text="Optional user-friendly title")
    # PUBLIC_INTERFACE
    user_id = models.CharField(max_length=128, blank=True, default="", help_text="Optional external user identifier")
    # PUBLIC_INTERFACE
    metadata = models.JSONField(blank=True, null=True, help_text="Arbitrary metadata (e.g., settings, model prefs)")

    def __str__(self) -> str:
        return self.title or self.session_id

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Chat Session"
        verbose_name_plural = "Chat Sessions"


class ChatAgentAssignment(TimeStampedModel):
    """
    Links AgentProfile to a ChatSession and allows per-session configuration.
    """
    # PUBLIC_INTERFACE
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="assignments")
    # PUBLIC_INTERFACE
    agent = models.ForeignKey(AgentProfile, on_delete=models.PROTECT, related_name="session_assignments")
    # PUBLIC_INTERFACE
    order = models.PositiveIntegerField(default=0, help_text="Order in the collaboration sequence")
    # PUBLIC_INTERFACE
    prompt_override = models.TextField(blank=True, default="", help_text="Optional per-session prompt/system message")
    # PUBLIC_INTERFACE
    tools = models.ManyToManyField(ToolDefinition, blank=True, related_name="agent_assignments")

    class Meta:
        unique_together = ("session", "agent")
        ordering = ["order", "id"]
        verbose_name = "Chat Agent Assignment"
        verbose_name_plural = "Chat Agent Assignments"

    def __str__(self) -> str:
        return f"{self.session.session_id} -> {self.agent.name} (#{self.order})"


class Message(TimeStampedModel):
    """
    Stores messages exchanged in a chat session. Includes agent/user/source and tool outputs.
    """
    ROLE_USER = "user"
    ROLE_AGENT = "agent"
    ROLE_SYSTEM = "system"
    ROLE_TOOL = "tool"

    ROLE_CHOICES = (
        (ROLE_USER, "User"),
        (ROLE_AGENT, "Agent"),
        (ROLE_SYSTEM, "System"),
        (ROLE_TOOL, "Tool"),
    )

    # PUBLIC_INTERFACE
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
    # PUBLIC_INTERFACE
    role = models.CharField(max_length=16, choices=ROLE_CHOICES, db_index=True)
    # PUBLIC_INTERFACE
    agent = models.ForeignKey(AgentProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name="messages",
                              help_text="Agent emitting the message (if role=agent/tool)")
    # PUBLIC_INTERFACE
    content = models.TextField(help_text="Message content (markdown/text)")
    # PUBLIC_INTERFACE
    tool_name = models.CharField(max_length=128, blank=True, default="", help_text="Tool that produced this message (if any)")
    # PUBLIC_INTERFACE
    tool_input = models.JSONField(blank=True, null=True, help_text="Structured tool input")
    # PUBLIC_INTERFACE
    tool_output = models.JSONField(blank=True, null=True, help_text="Structured tool output")
    # PUBLIC_INTERFACE
    tokens_prompt = models.IntegerField(null=True, blank=True)
    # PUBLIC_INTERFACE
    tokens_completion = models.IntegerField(null=True, blank=True)
    # PUBLIC_INTERFACE
    latency_ms = models.IntegerField(null=True, blank=True, help_text="Latency for the LLM/tool call")
    # PUBLIC_INTERFACE
    metadata = models.JSONField(blank=True, null=True, help_text="Arbitrary metadata for the message")

    class Meta:
        ordering = ["created_at", "id"]
        indexes = [
            models.Index(fields=["session", "created_at"]),
            models.Index(fields=["role"]),
        ]
        verbose_name = "Message"
        verbose_name_plural = "Messages"

    def __str__(self) -> str:
        who = self.agent.name if self.agent else self.role
        return f"{self.session.session_id} [{who}]: {self.content[:30]}..."


class RunLog(TimeStampedModel):
    """
    Tracks high-level CrewAI run lifecycle and outcome for a session or segment.
    Useful for analytics and debugging collaborative flows.
    """
    STATUS_RUNNING = "running"
    STATUS_SUCCESS = "success"
    STATUS_ERROR = "error"
    STATUS_CHOICES = (
        (STATUS_RUNNING, "Running"),
        (STATUS_SUCCESS, "Success"),
        (STATUS_ERROR, "Error"),
    )

    # PUBLIC_INTERFACE
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="run_logs")
    # PUBLIC_INTERFACE
    agent = models.ForeignKey(AgentProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name="run_logs")
    # PUBLIC_INTERFACE
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_RUNNING, db_index=True)
    # PUBLIC_INTERFACE
    details = models.TextField(blank=True, default="", help_text="Human-readable details, stack traces, etc.")
    # PUBLIC_INTERFACE
    extra = models.JSONField(blank=True, null=True, help_text="Structured metadata and metrics")

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["session", "status"]),
        ]
        verbose_name = "Run Log"
        verbose_name_plural = "Run Logs"

    def __str__(self) -> str:
        return f"{self.session.session_id} [{self.get_status_display()}]"
