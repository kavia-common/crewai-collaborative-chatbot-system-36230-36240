import time
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction

from .models import (
    AgentProfile,
    ChatAgentAssignment,
    ChatSession,
    Message,
    RunLog,
)


def _ws_group_name(session_id: str) -> str:
    """Derive Channels group name for a chat session."""
    return f"chat_{session_id}"


def broadcast_event(session_id: str, event: str, payload: Dict[str, Any]) -> None:
    """Broadcast an event to the session's WebSocket group."""
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    async_to_sync(channel_layer.group_send)(
        _ws_group_name(session_id),
        {
            "type": "chat.message",
            "event": event,
            "payload": payload,
        },
    )


@dataclass
class AgentTurnResult:
    agent: Optional[AgentProfile]
    content: str
    meta: Dict[str, Any]


class SimpleAgentRuntime:
    """
    A lightweight, mock "agent runtime" that simulates an LLM response.
    Replace this with actual CrewAI agent calls if available in the environment.
    """

    def __init__(self, agent: AgentProfile, prompt_override: str = ""):
        self.agent = agent
        self.prompt_override = prompt_override or ""

    def run(self, session: ChatSession, conversation: List[Message]) -> AgentTurnResult:
        """
        Simulate generating a response based on the last user/agent message.
        """
        last_text = ""
        if conversation:
            last_text = conversation[-1].content

        # Simulated latency and token accounting
        start = time.time()
        time.sleep(0.05)
        response = f"{self.agent.name} ({self.agent.role}) responding to: {last_text[:200]}"
        latency_ms = int((time.time() - start) * 1000)

        return AgentTurnResult(
            agent=self.agent,
            content=response,
            meta={
                "tokens_prompt": min(len(last_text) // 4, 2000),
                "tokens_completion": min(len(response) // 4, 2000),
                "latency_ms": latency_ms,
                "model": self.agent.model_hint or "mock-model",
                "prompt_override_used": bool(self.prompt_override),
            },
        )


# PUBLIC_INTERFACE
def run_two_agent_collaboration(session: ChatSession, user_text: str) -> List[Message]:
    """
    Orchestrate a simple 2-agent collaboration:
    - Save user message
    - Iterate through agents in assignment order, each producing a turn
    - Persist outputs and emit websocket events
    """
    # Register run start
    run_log = RunLog.objects.create(
        session=session, status=RunLog.STATUS_RUNNING, details="Two-agent run started"
    )
    broadcast_event(session.session_id, "run_started", {"session_id": session.session_id, "run_id": run_log.id})

    created_messages: List[Message] = []
    try:
        with transaction.atomic():
            # Save user message
            user_msg = Message.objects.create(
                session=session,
                role=Message.ROLE_USER,
                content=user_text,
                metadata={"ui_theme_hint": "Ocean Professional"},
            )
            created_messages.append(user_msg)
            broadcast_event(session.session_id, "message_created", {"message_id": user_msg.id})

            # Fetch agent order
            assignments = list(
                ChatAgentAssignment.objects.select_related("agent")
                .filter(session=session)
                .order_by("order", "id")
            )

            # A minimal conversation context
            conversation = list(Message.objects.filter(session=session).order_by("created_at", "id"))

            # Each agent takes a turn in order
            for a in assignments:
                agent = a.agent
                runtime = SimpleAgentRuntime(agent=agent, prompt_override=a.prompt_override)
                result = runtime.run(session, conversation)

                agent_msg = Message.objects.create(
                    session=session,
                    role=Message.ROLE_AGENT,
                    agent=agent,
                    content=result.content,
                    tokens_prompt=result.meta.get("tokens_prompt"),
                    tokens_completion=result.meta.get("tokens_completion"),
                    latency_ms=result.meta.get("latency_ms"),
                    metadata={
                        "model": result.meta.get("model"),
                        "prompt_override_used": result.meta.get("prompt_override_used", False),
                    },
                )
                created_messages.append(agent_msg)
                conversation.append(agent_msg)

                # Emit event for each agent turn
                broadcast_event(
                    session.session_id,
                    "agent_turn",
                    {
                        "agent": agent.name,
                        "role": agent.role,
                        "message_id": agent_msg.id,
                        "content": agent_msg.content,
                    },
                )

        # Mark success
        run_log.status = RunLog.STATUS_SUCCESS
        run_log.details = "Two-agent run completed"
        run_log.extra = {"messages_created": [m.id for m in created_messages]}
        run_log.save(update_fields=["status", "details", "extra", "updated_at"])
        broadcast_event(session.session_id, "run_completed", {"run_id": run_log.id})
    except Exception as ex:
        run_log.status = RunLog.STATUS_ERROR
        run_log.details = f"Run failed: {ex}"
        run_log.save(update_fields=["status", "details", "updated_at"])
        broadcast_event(session.session_id, "run_error", {"run_id": run_log.id, "error": str(ex)})
        raise

    return created_messages
