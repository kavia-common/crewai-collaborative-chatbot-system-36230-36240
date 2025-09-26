# crewai-collaborative-chatbot-system-36230-36240

Django backend for a 2-agent collaborative chatbot with REST and WebSocket (Channels).

Key models:
- AgentProfile: defines agents (name, role, description, model hint, active)
- ToolDefinition: optional registry of tools agents can use
- ChatSession: one conversation session; stores external session_id, title, user_id, metadata
- ChatAgentAssignment: per-session agent configuration and ordering; links to tools
- Message: all messages (user, agent, system, tool) with rich metadata and token/latency fields
- RunLog: high-level run lifecycle and outcome, useful for analytics/debugging

APIs (DRF):
- Preferred base path: /api/
  - GET /api/health/
  - POST /api/sessions/  body: {"session_id": "abc123", "title": "...", "user_id": "..."}
  - GET /api/sessions/{session_id}/
  - GET /api/sessions/{session_id}/history/
  - GET /api/sessions/{session_id}/state/
  - POST /api/sessions/{session_id}/send/  body: {"content":"Hello"}
- Convenience root mirror (to avoid 404s if frontend omits /api):
  - GET /health/
  - POST /sessions/
  - GET /sessions/{session_id}/
  - GET /sessions/{session_id}/history/
  - GET /sessions/{session_id}/state/
  - POST /sessions/{session_id}/send/  body: {"content":"Hello"}

Frontend integration notes:
- Use the backend base URL with the /api prefix. For this environment:
  REACT_APP_API_BASE_URL=https://vscode-internal-28521-beta.beta01.cloud.kavia.ai:3001/api
  (If your frontend variable name differs, map it accordingly.)
- If your frontend or dev proxy strips the /api prefix, the root mirror allows /sessions/ etc. to still work at the root.
- Ensure CORS is enabled (this backend sets CORS_ALLOW_ALL_ORIGINS=True for development).
- Double-check protocol/host/port in the frontend to match the running backend. Mismatches (e.g., http vs https, wrong port) commonly cause “Failed to fetch”.

WebSocket (Channels):
- ws://<host>/ws/chat/<session_id>/
  - Receives events: connected, message_created, agent_turn, run_started, run_completed, run_error

Ocean Professional UI hints:
- REST responses include theme_hint where relevant; primary color #2563EB, secondary #F59E0B.

Setup
1) cd chatbot_backend
2) pip install -r requirements.txt
3) python manage.py migrate
4) python manage.py createsuperuser  (optional)
5) run ASGI server (e.g., daphne or uvicorn):
   - uvicorn config.asgi:application --host 0.0.0.0 --port 8000

Admin
- /admin/ to manage agents/tools/sessions

Notes
- Database defaults to SQLite (config/settings.py). For production use, set DB_* env vars.
- Channels layer defaults to in-memory. For production, set CHANNEL_BACKEND to channels_redis.core.RedisChannelLayer and configure REDIS_URL.
- For raw SQL reference, see api/sql_schema_reference.sql.
