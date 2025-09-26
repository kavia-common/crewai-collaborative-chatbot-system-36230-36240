-- Reference SQL DDL for the collaborative chatbot schema (SQLite dialect approximation)

CREATE TABLE "api_agentprofile" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "created_at" datetime NOT NULL,
    "updated_at" datetime NOT NULL,
    "name" varchar(64) NOT NULL UNIQUE,
    "role" varchar(128) NOT NULL DEFAULT '',
    "description" text NOT NULL DEFAULT '',
    "model_hint" varchar(128) NOT NULL DEFAULT '',
    "is_active" bool NOT NULL DEFAULT 1
);

CREATE TABLE "api_tooldefinition" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "created_at" datetime NOT NULL,
    "updated_at" datetime NOT NULL,
    "name" varchar(128) NOT NULL UNIQUE,
    "description" text NOT NULL DEFAULT '',
    "schema" json NULL,
    "is_active" bool NOT NULL DEFAULT 1
);

CREATE TABLE "api_chatsession" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "created_at" datetime NOT NULL,
    "updated_at" datetime NOT NULL,
    "session_id" varchar(64) NOT NULL UNIQUE,
    "title" varchar(200) NOT NULL DEFAULT '',
    "user_id" varchar(128) NOT NULL DEFAULT '',
    "metadata" json NULL
);

CREATE TABLE "api_chatagentassignment" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "created_at" datetime NOT NULL,
    "updated_at" datetime NOT NULL,
    "order" integer NOT NULL DEFAULT 0,
    "prompt_override" text NOT NULL DEFAULT '',
    "session_id" integer NOT NULL REFERENCES "api_chatsession" ("id") ON DELETE CASCADE,
    "agent_id" integer NOT NULL REFERENCES "api_agentprofile" ("id") ON DELETE RESTRICT
);

CREATE UNIQUE INDEX "api_chatagentassignment_unique_session_agent" ON "api_chatagentassignment" ("session_id", "agent_id");

CREATE TABLE "api_chatagentassignment_tools" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "chatagentassignment_id" integer NOT NULL REFERENCES "api_chatagentassignment" ("id") ON DELETE CASCADE,
    "tooldefinition_id" integer NOT NULL REFERENCES "api_tooldefinition" ("id") ON DELETE CASCADE,
    UNIQUE ("chatagentassignment_id", "tooldefinition_id")
);

CREATE TABLE "api_message" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "created_at" datetime NOT NULL,
    "updated_at" datetime NOT NULL,
    "role" varchar(16) NOT NULL,
    "content" text NOT NULL,
    "tool_name" varchar(128) NOT NULL DEFAULT '',
    "tool_input" json NULL,
    "tool_output" json NULL,
    "tokens_prompt" integer NULL,
    "tokens_completion" integer NULL,
    "latency_ms" integer NULL,
    "metadata" json NULL,
    "session_id" integer NOT NULL REFERENCES "api_chatsession" ("id") ON DELETE CASCADE,
    "agent_id" integer NULL REFERENCES "api_agentprofile" ("id") ON DELETE SET NULL
);

CREATE INDEX "api_message_session_created_idx" ON "api_message" ("session_id", "created_at");
CREATE INDEX "api_message_role_idx" ON "api_message" ("role");

CREATE TABLE "api_runlog" (
    "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
    "created_at" datetime NOT NULL,
    "updated_at" datetime NOT NULL,
    "status" varchar(16) NOT NULL DEFAULT 'running',
    "details" text NOT NULL DEFAULT '',
    "extra" json NULL,
    "session_id" integer NOT NULL REFERENCES "api_chatsession" ("id") ON DELETE CASCADE,
    "agent_id" integer NULL REFERENCES "api_agentprofile" ("id") ON DELETE SET NULL
);

CREATE INDEX "api_runlog_session_status_idx" ON "api_runlog" ("session_id", "status");
