# crewai-collaborative-chatbot-system-36230-36240

This backend includes Django models to persist a 2-agent CrewAI collaborative chatbot:

- AgentProfile: defines agents (name, role, description, model hint, active).
- ToolDefinition: optional registry of tools agents can use.
- ChatSession: one conversation session; stores external session_id, title, user_id, metadata.
- ChatAgentAssignment: per-session agent configuration and ordering; links to tools.
- Message: all messages (user, agent, system, tool) with rich metadata and token/latency fields.
- RunLog: high-level run lifecycle and outcome, useful for analytics/debugging.

Migrations
- To apply: 
  - cd chatbot_backend
  - python manage.py makemigrations (if needed)
  - python manage.py migrate

Admin
- The above models are registered in Django admin for quick inspection and manual data entry.

Notes
- Database defaults to SQLite (config/settings.py). For production use, configure DATABASES via environment variables.
- For raw SQL reference, see api/sql_schema_reference.sql.
