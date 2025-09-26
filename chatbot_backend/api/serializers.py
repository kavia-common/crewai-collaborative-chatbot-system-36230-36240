from rest_framework import serializers
from .models import AgentProfile, ToolDefinition, ChatSession, ChatAgentAssignment, Message, RunLog


class ToolDefinitionSerializer(serializers.ModelSerializer):
    """Serializer for ToolDefinition model."""

    class Meta:
        model = ToolDefinition
        fields = [
            "id",
            "name",
            "description",
            "schema",
            "is_active",
            "created_at",
            "updated_at",
        ]


class AgentProfileSerializer(serializers.ModelSerializer):
    """Serializer for AgentProfile model."""

    class Meta:
        model = AgentProfile
        fields = [
            "id",
            "name",
            "role",
            "description",
            "model_hint",
            "is_active",
            "created_at",
            "updated_at",
        ]


class ChatAgentAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for ChatAgentAssignment. Exposes related agent and tools."""
    agent = AgentProfileSerializer(read_only=True)
    agent_id = serializers.PrimaryKeyRelatedField(
        queryset=AgentProfile.objects.all(), source="agent", write_only=True
    )
    tools = ToolDefinitionSerializer(many=True, read_only=True)
    tool_ids = serializers.PrimaryKeyRelatedField(
        queryset=ToolDefinition.objects.all(), many=True, write_only=True, required=False
    )

    class Meta:
        model = ChatAgentAssignment
        fields = [
            "id",
            "session",
            "agent",
            "agent_id",
            "order",
            "prompt_override",
            "tools",
            "tool_ids",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["session", "tools", "created_at", "updated_at"]

    def create(self, validated_data):
        tool_ids = validated_data.pop("tool_ids", [])
        assignment = super().create(validated_data)
        if tool_ids:
            assignment.tools.set(tool_ids)
        return assignment

    def update(self, instance, validated_data):
        tool_ids = validated_data.pop("tool_ids", None)
        instance = super().update(instance, validated_data)
        if tool_ids is not None:
            instance.tools.set(tool_ids)
        return instance


class ChatSessionSerializer(serializers.ModelSerializer):
    """Serializer for ChatSession with nested agent assignments."""
    assignments = ChatAgentAssignmentSerializer(many=True, read_only=True)

    class Meta:
        model = ChatSession
        fields = [
            "id",
            "session_id",
            "title",
            "user_id",
            "metadata",
            "assignments",
            "created_at",
            "updated_at",
        ]


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for Message model."""
    agent = AgentProfileSerializer(read_only=True)
    agent_id = serializers.PrimaryKeyRelatedField(
        queryset=AgentProfile.objects.all(), source="agent", allow_null=True, required=False, write_only=True
    )

    class Meta:
        model = Message
        fields = [
            "id",
            "session",
            "role",
            "agent",
            "agent_id",
            "content",
            "tool_name",
            "tool_input",
            "tool_output",
            "tokens_prompt",
            "tokens_completion",
            "latency_ms",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class RunLogSerializer(serializers.ModelSerializer):
    """Serializer for RunLog model."""
    agent = AgentProfileSerializer(read_only=True)
    agent_id = serializers.PrimaryKeyRelatedField(
        queryset=AgentProfile.objects.all(), source="agent", allow_null=True, required=False, write_only=True
    )

    class Meta:
        model = RunLog
        fields = [
            "id",
            "session",
            "agent",
            "agent_id",
            "status",
            "details",
            "extra",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]
