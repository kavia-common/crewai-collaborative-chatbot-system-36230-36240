from django.contrib import admin
from .models import AgentProfile, ToolDefinition, ChatSession, ChatAgentAssignment, Message, RunLog


@admin.register(AgentProfile)
class AgentProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "role", "is_active", "updated_at")
    search_fields = ("name", "role", "description")
    list_filter = ("is_active",)


@admin.register(ToolDefinition)
class ToolDefinitionAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "updated_at")
    search_fields = ("name", "description")
    list_filter = ("is_active",)


class ChatAgentAssignmentInline(admin.TabularInline):
    model = ChatAgentAssignment
    extra = 0
    filter_horizontal = ("tools",)


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ("session_id", "title", "user_id", "created_at", "updated_at")
    search_fields = ("session_id", "title", "user_id")
    inlines = [ChatAgentAssignmentInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("session", "role", "agent", "created_at")
    search_fields = ("content", "tool_name")
    list_filter = ("role",)
    autocomplete_fields = ("session", "agent")


@admin.register(RunLog)
class RunLogAdmin(admin.ModelAdmin):
    list_display = ("session", "agent", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("details",)
    autocomplete_fields = ("session", "agent")
