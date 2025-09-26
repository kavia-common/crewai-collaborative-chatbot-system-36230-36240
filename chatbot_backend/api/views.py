from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, action
from rest_framework.response import Response

from .models import ChatSession, Message, ChatAgentAssignment
from .serializers import (
    ChatSessionSerializer,
    MessageSerializer,
)
from .services import run_two_agent_collaboration


# PUBLIC_INTERFACE
@api_view(["GET"])
def health(request):
    """
    Health check endpoint.

    Returns:
        200 OK with a simple message confirming server health.
    Note:
        Keep the response minimal to satisfy automated tests that check for exact equality.
        API clients can assume "Ocean Professional" theme globally from README/style guide.
    """
    return Response({"message": "Server is up!"})


class ChatSessionViewSet(viewsets.ModelViewSet):
    """
    Manages chat sessions lifecycle.

    Ocean Professional UI Hints:
    - Primary actions (Create Session) use #2563EB
    - Secondary actions (Archive/Delete) use #F59E0B highlights
    """
    queryset = ChatSession.objects.all().order_by("-created_at")
    serializer_class = ChatSessionSerializer
    lookup_field = "session_id"

    @swagger_auto_schema(
        operation_summary="Create a new chat session",
        operation_description="Creates a new collaborative chat session. The session_id must be unique.",
        responses={201: ChatSessionSerializer()},
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    # PUBLIC_INTERFACE
    @action(detail=True, methods=["get"])
    def history(self, request, session_id=None):
        """
        Return the chronological message history for a session.

        Returns:
            200 OK with a list of messages.
        """
        session = get_object_or_404(ChatSession, session_id=session_id)
        msgs = Message.objects.filter(session=session).order_by("created_at", "id")
        ser = MessageSerializer(msgs, many=True)
        return Response(ser.data, status=status.HTTP_200_OK)

    # PUBLIC_INTERFACE
    @action(detail=True, methods=["get"])
    def state(self, request, session_id=None):
        """
        Return the current state snapshot of a session:
        - session info
        - assignments (agent order)
        - message count
        """
        session = get_object_or_404(ChatSession, session_id=session_id)
        assignments = ChatAgentAssignment.objects.filter(session=session).order_by("order", "id")
        assignment_data = [
            {
                "order": a.order,
                "agent": a.agent.name,
                "role": a.agent.role,
                "prompt_override": bool(a.prompt_override),
            }
            for a in assignments
        ]
        data = {
            "session_id": session.session_id,
            "title": session.title,
            "user_id": session.user_id,
            "message_count": Message.objects.filter(session=session).count(),
            "assignments": assignment_data,
            "theme_hint": "Ocean Professional",
        }
        return Response(data, status=status.HTTP_200_OK)

    # PUBLIC_INTERFACE
    @action(detail=True, methods=["post"])
    @swagger_auto_schema(
        operation_summary="Send a user message and run 2-agent collaboration",
        operation_description="Appends a user message to the session, then orchestrates a two-agent turn sequence. "
                              "WebSocket updates broadcast to ws/chat/<session_id>/",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["content"],
            properties={
                "content": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="User's message to send into the collaborative flow.",
                )
            },
        ),
        responses={200: MessageSerializer(many=True)},
    )
    def send(self, request, session_id=None):
        content = request.data.get("content", "")
        if not content:
            return Response({"detail": "content is required"}, status=status.HTTP_400_BAD_REQUEST)

        session = get_object_or_404(ChatSession, session_id=session_id)
        messages = run_two_agent_collaboration(session, content)
        return Response(MessageSerializer(messages, many=True).data, status=status.HTTP_200_OK)


class MessageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only viewset for messages. Use ChatSessionViewSet.send to add new messages.
    """
    queryset = Message.objects.all().order_by("created_at", "id")
    serializer_class = MessageSerializer
