# Movi – Multimodal Transport Platform

Movi combines a Supabase/PostgreSQL data layer, a FastAPI backend with an MCP-powered LangGraph agent, and a Vite/React frontend. This single README replaces the previous per-package documents and covers setup, architecture, and key workflows end to end.

---

## Architecture at a Glance

```
Movi V1/
├── app.py                 # Unified FastAPI entrypoint (CRUD + MCP agent)
├── run_server.py          # Dev helper (uvicorn wrapper)
├── backend/               # Legacy route/service modules reused by app.py
├── database/              # Supabase schema, repositories, and seed scripts
├── frontend/              # Vite/React SPA with chatbot widget
├── data/                  # Assignment documents
├── requirements.txt       # Python dependencies
└── README.md              # You are here
```

- **Database**: Supabase project backed by PostgreSQL. All entities (stops → paths → routes → trips → deployments) implement soft delete + audit columns.
- **Backend**: FastAPI app exposes REST CRUD endpoints under `/api/*` and ensures the LangGraph/MCP agent is reachable via `/agent`, `/api/chat`, and `/api/upload-image`.
- **Frontend**: Vite + React SPA with Bus Dashboard and Manage Route pages, plus a floating chatbot driven by the MCP backend.
- **AI Assistant**: Claude Sonnet 4.5 orchestrated through LangGraph. MCP tools hosted by Supabase handle SQL queries and business workflows.

---

## Getting Started

### 1. Prerequisites
- Python 3.10+ and a virtual environment
- Node.js 16+ and npm
- Supabase project (URL, anon key, service-role key)
- Anthropic API key

### 2. Install Python Dependencies
```bash
python -m venv .venv
.venv\Scripts\activate      # Windows PowerShell
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create `.env` at the project root:
```
# Supabase REST + repositories
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key

# MCP / LangGraph agent
SUPABASE_PROJECT_REF=your_supabase_project_ref   # e.g., abcd1234
SUPABASE_ACCESS_TOKEN=your_supabase_service_role_token
ANTHROPIC_API_KEY=your_anthropic_api_key
```

> Tip: All Supabase values live under **Project Settings → API**. Keep `.env` out of version control.

### 4. Prepare the Database
1. Run `database/schema.sql` in the Supabase SQL editor.
2. (Optional) seed realistic data:
   ```bash
   python database/init_database.py
   ```
   The script creates 45+ stops, 20 paths, 80 routes, 23 vehicles, 30 drivers, and 560+ trips with Bengaluru-centric metadata.

### 5. Run the Backend
```bash
python run_server.py   # Serves CRUD API + LangGraph agent on http://localhost:5005
```
Endpoints of note:
- REST: `http://localhost:5005/api/...`
- Docs: `http://localhost:5005/docs`
- Agent (chatbot): `POST /agent`, `/api/chat`, `/api/upload-image`

### 6. Run the Frontend
```bash
cd frontend
npm install
npm run dev            # http://localhost:5000
```
React Router exposes `/bus-dashboard` and `/manage-route`, and `src/components/Chatbot.jsx` targets the agent endpoints above.

---

## Database Layer Highlights
- **Repositories & utils** (`database/repositories.py`, `database/utils.py`) wrap Supabase Python client calls for Stops, Paths, Routes, Trips, Vehicles, Drivers, and Deployments.
- **Soft delete helpers** (`soft_delete_*`, `get_active_*`) prevent hard deletes while preserving audit trails.
- **Schema**: `schema.sql` defines the Stop → Path → Route → Trip → Deployment pipeline plus supporting tables (`users`, `vehicles`, `drivers`).
- **Seed script**: `init_database.py` can purge and re-populate Supabase via service-role credentials.

---

## Backend & MCP Agent

### REST API
Reusing the route/service modules under `backend/routes` and `backend/services`, FastAPI exposes CRUD endpoints such as:
- `GET /api/stops`, `POST /api/stops`
- `GET /api/paths/{id}/stops`
- `GET /api/vehicles/unassigned`
- `GET /api/trips/by-name/{display_name}`
- `POST /api/deployments`, etc.

### LangGraph / MCP Agent
- Defined entirely in `app.py` via `MoviAgent`. Handles session state, consequence checks, multi-turn forms, and multimodal uploads.
- `langchain_mcp_adapters` loads hosted Supabase MCP tools; `_call_model_with_tools` now handles Anthropic’s tool-use loop so SQL results flow back to users.
- Chat endpoints:
  - `POST /agent` – raw API for orchestrating the graph
  - `POST /api/chat` – frontend text chatbot
  - `POST /api/upload-image` – multimodal entrypoint (screenshots + instructions)

---

## Frontend (Vite + React)
- Entry point: `frontend/src/main.jsx`
- Pages:
  - `BusDashboard.jsx` – live trips, deployments, booking status
  - `ManageRoute.jsx` – stop/path/route management
- Shared layout/components: `src/components/Layout.jsx`, `Chatbot.jsx`
- Styles live alongside components/pages (`*.css` files).
- REST calls centralized in `src/services/api.js`; chatbot-specific calls target `/api/chat` and `/api/upload-image`.

---

## Operational Notes
- **Soft Deletes**: Every table carries `deleted_at/ deleted_by`. REST endpoints and repositories filter them by default; use `database/soft_delete_utils.py` to archive or restore records.
- **Audit Columns**: `created_by`, `updated_by`, `deleted_by`, plus timestamp triggers, allow complete traceability.
- **Views**: Supabase views (`active_stops`, `active_routes`, etc.) simplify “only active records” queries.
- **MCP Tooling**: The backend does not ship local tool definitions; instead it talks to Supabase’s MCP host. Ensure the service-role token has access to the SQL tools described in the assignment.

---

## Need to Explore More?
- `PARTS_3_4_IMPLEMENTATION.md`, `PENDING_ITEMS.md`, and `SUPABASE_CONNECTION_FLOW.md` capture assignment requirements, tribal knowledge, and integration details.
- `requirements.txt` lists Python dependencies (FastAPI, LangGraph, MCP adapters, Anthropic SDK, etc.).
- `frontend/package.json` defines the minimal React toolchain.

With this unified README you no longer need separate backend/database/frontend documents—the sections above consolidate everything required to install, run, and extend Movi. Happy shipping!

