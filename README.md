# MoveInSync_Movi – MCP LangGraph Transport Assistant

Movi V1 is a transport-operations assistant with a Vite/React UI and a FastAPI backend. It combines legacy CRUD APIs with a LangGraph-based agent that uses Supabase MCP tools, confirmation guards, and Claude multimodal vision to manage routes, vehicles, and trips safely.

It also serves as a reference implementation of a transport-operations copilot. The Vite/React frontend lets operations teams manage static assets (stops, routes, vehicles) and live trips, while the FastAPI backend hosts both the classic CRUD APIs and a LangGraph-powered agent that speaks to Supabase via MCP tools, consults “tribal knowledge”, and even reads dashboard screenshots with Claude vision.

## Repository Layout

- `frontend/` – Vite + React UI (`BusDashboard`, `ManageRoute`, chat/vision uploader, REST client in `src/services/api.js`)
- `backend/` – FastAPI routers (`backend/routes`), service layer, MCP helpers (`backend/mcp`)
- `database/` – Supabase/Postgres schema, repositories, utilities, Bengaluru seed script
- `app.py` – FastAPI entrypoint, LangGraph agent wiring, vision upload endpoint
- `.env.example` (create this yourself) – holds Supabase + Anthropic secrets

Git: this directory is a standard Git repository (`git init`, `git add .`, `git commit -m "..."`). Push it anywhere you like (`git remote add origin <url>` + `git push -u origin main`).

## Architecture & LangGraph Graph Explanation

### LangGraph Design

Although the code leverages `langgraph.prebuilt.create_react_agent`, we wrap it with custom state handling in `app.py`. The effective `agent_state` we pass around contains:

- `messages`: rolling dialogue history sourced from `session_memories[session_id]["messages"]`
- `current_page`: which UI surface the user is on (`busDashboard`, `manageRoute`, etc.)
- `allowed_tables` / `table_schemas`: tribal knowledge about which Supabase tables may be touched per page (`PAGE_TABLE_ACCESS`, `TABLE_SCHEMAS`)
- `pending_confirmation`: destructive-action guard rails queued by `analyze_trip_removal_request`
- `vision_context`: when `/api/upload-image` calls `process_dashboard_image`, we stash `{trip_name, detected_action, confidence}` to enrich the user prompt



#### Core Nodes

1. **Input Router (FastAPI)** – Accepts `/agent`, `/api/chat`, `/api/upload-image`, normalizes sessions, runs `_ensure_memory`.
2. **Tribal Knowledge Guard** – Builds `context_payload` (page, allowed tables, schemas). If a request targets forbidden data, the system prompt forces the LLM to ask the user to switch pages.
3. **Consequence Guard (`backend/mcp/consequence_checker.py`)** – Parses “remove vehicle” intents, fetches `daily_trips` + `deployments`, emits `ConsequenceWarning`, and queues confirmation in memory.
4. **Vision Extractor (`backend/mcp/vision.py`)** – Optional multimodal node that produces `VisionExtraction` (trip/action/confidence) and augments the query.
5. **LangGraph ReAct Planner** – `create_react_agent` with Claude Sonnet 4.5 plus MCP tools from `load_mcp_tools(session)`. Handles reasoning/tool selection.
6. **MCP Tool Executor** – Executes Supabase data actions (select/insert/update/delete) safely through MCP’s streaming HTTP transport.
7. **Confirmation Loop** – `_handle_confirmation` inspects the next user utterance: `yes` → `_perform_post_confirmation_action`, `no` → abort, null → reprompt.
8. **Legacy REST Routers** – Remain mounted so the React UI can coexist with the agent while migration occurs.

#### Conditional Edges & Tribal Knowledge

- **Destructive Intent Edge**: After loading session history, we run `analyze_trip_removal_request`. If it returns a warning, we divert to the Confirmation Loop and never call LangGraph until the user replies with an explicit “yes/no”.
- **Vision Edge**: `/api/upload-image` calls `process_dashboard_image`. If `trip_name` is detected, we splice that context into the prompt (`_build_augmented_query`) and preface the final answer with `[Vision] ...`. If no vision data is returned, we skip this branch.
- **Page Enforcement Edge**: When `current_page` is absent or mismatched, we overwrite the session and limit `allowed_tables`. The system prompt instructs Claude to refuse cross-page mutations, effectively encoding tribal knowledge about which dataset belongs to which UI.
- **Post-Confirmation Edge**: If a confirmation payload includes a `deployment_id`, `_perform_post_confirmation_action` directly soft-deletes via `DeploymentsRepository` before handing control back to LangGraph.

These guard nodes keep “tribal knowledge” (page-scoped table access, destructive action policies) close to the edge of the graph so the generative core only receives curated, safe context. Multimodal inputs merely enrich the agent_state; they never bypass the confirmation edge.

## Database Deep Dive

The project uses Supabase (hosted Postgres) with the schema defined in `database/schema.sql` and seed data in `database/init_database.py`.

- **Entities**
  - `users`: audit principals referenced by every “who” column (`created_by`, `updated_by`, `deleted_by`)
  - Static assets: `stops`, `paths`, `routes` (each with soft-delete columns, audit timestamps, and FK relationships)
  - Operational tables: `vehicles`, `drivers`, `daily_trips`, `deployments`
  - `deployments` joins trips, vehicles, drivers and enforces uniqueness (`UNIQUE(trip_id, vehicle_id)`)
- **Audit & Soft Delete**
  - Every table has `deleted_at`, `deleted_by`, plus triggers (`update_*_updated_at`) wired to `update_updated_at_column()` ensuring `updated_at` auto-refreshes.
  - Utility views (`active_*`) expose only non-deleted records to simplify reporting.
- **Indexes**
  - FK indexes (e.g., `idx_daily_trips_route_id`)
  - Soft-delete-friendly partial indexes (`WHERE deleted_at IS NULL`) for each table to keep “active” lookups fast.
  - Domain-specific indexes: license plates, trip dates/status, etc., to accelerate dashboard queries.
- **Repository Layer (`database/repositories.py`)**
  - Table-specific classes wrap Supabase queries, applying soft-delete filters and column-correct `eq()` clauses (e.g., `stop_id` vs generic `id`), plus helper methods for `soft_delete`.
- **Utilities & Seeds**
  - `database/utils.py` exposes soft-delete/restore helpers shared across routes.
  - `database/init_database.py` can optionally clear existing data and repopulate Bengaluru-specific stops, paths, routes, vehicles, drivers, trips, and deployments with realistic metadata (shift-based route codes, booking stats, etc.).

Together, this database layer is the “tribal knowledge base” the agent reasons over. Mapping tables to UI pages (`PAGE_TABLE_ACCESS`) ensures the LLM never touches irrelevant entities.

## Setup Instructions

### Prerequisites

- Python 3.11+
- Node.js 18+ (Vite dev server)
- Git
- Supabase project with Database + Service Role key
- Anthropic API key (Claude Sonnet 4.5 + vision)

### Environment Variables

Create `.env` at the repo root (never commit secrets):

```
SUPABASE_URL=...
SUPABASE_KEY=...                 # service role key for client SDK
SUPABASE_PROJECT_REF=...         # used by MCP HTTP transport
SUPABASE_ACCESS_TOKEN=...        # Supabase personal access token for MCP
SYSTEM_USER_ID=1                 # user id for automated deletions
ANTHROPIC_API_KEY=...
ANTHROPIC_VISION_MODEL=claude-3-5-sonnet-latest   # optional override
```

### Backend (FastAPI + LangGraph)

```powershell
cd "C:\Users\username\folder\Movi V1"
python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 5005 --reload
```

Or run `python run_server.py` which invokes uvicorn with the same settings.

### Database Bootstrap

1. In Supabase SQL Editor, paste `database/schema.sql` and run it once.
2. Back in your terminal:
   ```powershell
   .venv\Scripts\activate
   python database/init_database.py
   ```
   This script soft-deletes existing rows, inserts the Bengaluru fixtures, and ensures the default `admin` user exists.

### Frontend (Vite + React)

```powershell
cd frontend
npm install
npm run dev
```

The Vite dev server defaults to `http://localhost:5173` and talks to the backend at `http://localhost:5005/api` unless you override the origin by creating `frontend/.env` with `VITE_API_BASE_URL=<backend origin>`.

### Agent + Vision Flows

- REST chat: `POST http://localhost:5005/api/chat` with `{message, current_page, session_id}`.
- LangGraph endpoint: `POST http://localhost:5005/agent`.
- Vision: `POST http://localhost:5005/api/upload-image` (multipart form with `file`, `message`, `current_page`, `session_id`). Requires `ANTHROPIC_API_KEY`.

### Verification Checklist

- `curl http://localhost:5005/api/stops/` → returns seeded stops
- `curl -X POST http://localhost:5005/agent -H "Content-Type: application/json" -d "{\"query\":\"List active trips\",\"current_page\":\"busDashboard\"}"` → agent response referencing only dashboard tables
- `npm run dev` and open the React UI; ensure chat widget hits `/api/chat`

## Deploying on Render.com

1. **Blueprint deploy** – Click “New + → Blueprint” in Render and point it to this repo. The included `render.yaml` defines:
   - `movi-backend` (Python FastAPI web service) that installs from `requirements.txt` and runs `uvicorn app:app --host 0.0.0.0 --port $PORT`.
   - `movi-frontend` (static Vite build) that runs `npm install && npm run build` inside `frontend/` and publishes `frontend/dist`.

2. **Environment variables** – Supply all secrets in Render’s dashboard (the blueprint marks them as `sync: false`):
   - `SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_PROJECT_REF`, `SUPABASE_ACCESS_TOKEN`
   - `SYSTEM_USER_ID` (defaults to `1`), `ANTHROPIC_API_KEY`, optionally `ANTHROPIC_VISION_MODEL`

3. **Frontend API target** – The blueprint wires `VITE_API_BASE_URL` to the backend’s `RENDER_EXTERNAL_URL`. The frontend automatically appends `/api`, so no rewrites or proxies are required.

4. **Supabase bootstrap** – Run `database/schema.sql` + `python database/init_database.py` locally once so Supabase is populated before pointing Render at it.

5. **Post-deploy checks** – After both services are live:
   - Hit `https://<backend>.onrender.com/api/stops/` (or `/api/health` if you add it) to confirm FastAPI is reachable.
   - Open the static site’s URL and verify CRUD pages and the chat widget can talk to the backend.

## MCP Tooling

When `app.py` calls `load_mcp_tools(session)`, it pulls the Supabase MCP server’s tool inventory for the connected project. In practice we see the standard database toolkit:

- `supabase_sql` – run ad-hoc SQL when structured tools are insufficient (schema changes, complex joins).
- `supabase_select` – read rows from a table with filters, ordering, and pagination constraints.
- `supabase_insert` – insert JSON payloads into any allowed table.
- `supabase_update` – patch rows that match a filter.
- `supabase_delete` – delete or soft-delete rows (we wrap this with our confirmation guard).
- `supabase_storage_upload` / `supabase_storage_download` – interact with Supabase Storage buckets for screenshots or attachments.

Because MCP tools are discovered dynamically, you can confirm the list locally by logging each `tool.name` right after `load_mcp_tools(session)` or tailing the FastAPI startup logs (`Loaded N tools` line).

## Contributing & Next Steps

- Linting/tests are not yet wired; consider adding Ruff or Pytest, plus frontend eslint.
- Extend the LangGraph guardrails with structured state objects if you move beyond `create_react_agent`.
- For production, swap the Supabase service-role key for a Vault secret and rotate the MCP access token regularly.

Happy shipping!
