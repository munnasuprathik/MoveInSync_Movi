# MCP Server Architecture

## Overview

This module implements a Model Context Protocol (MCP) server for the Movi transport management system. The architecture provides:

1. **Reusable Supabase Orchestration Layer** - Centralized database operations
2. **MCP Tools** - Separate tools for Route Management and Bus Dashboard
3. **Streamable HTTP Server** - SSE-based streaming for real-time responses
4. **LangGraph MCP Client** - Async streamable HTTP client using LangGraph
5. **State Management** - Two-layer filtering (prompt + tool parameter validation)

## Architecture

```
Frontend
    ↓
FastAPI (/api/mcp/chat?state=route_management)
    ↓
LangGraph MCP Client
    ↓ (with state filtering)
MCP Server
    ↓
Supabase Orchestration Layer
    ↓
Database (Supabase)
```

## Components

### 1. Supabase Orchestration Layer (`orchestration.py`)

Reusable layer that provides unified database operations for all MCP tools:
- Stops, Paths, Routes operations
- Vehicles, Drivers, Trips, Deployments operations
- Consistent error handling and audit trail support

### 2. MCP Tools

#### Route Management Tools (`tools/route_management_tools.py`)
- **State**: `route_management`
- **Tools**: 
  - Stops: list, get, create, update, delete
  - Paths: list, get, create, update, delete
  - Routes: list, get, create, update, delete

#### Bus Dashboard Tools (`tools/bus_dashboard_tools.py`)
- **State**: `bus_dashboard`
- **Tools**:
  - Vehicles: list, get, create, update, delete
  - Drivers: list, get, create, update, delete
  - Trips: list, get, create, update, delete
  - Deployments: list, get, get_by_trip, create, update, delete

### 3. MCP Server (`server.py`)

- Registers all tools
- Provides tool execution with state validation
- Supports streaming responses via SSE

### 4. LangGraph MCP Client (`langgraph_client.py`)

- Integrates MCP tools with LangGraph agent
- Uses Groq LLM (llama-3.1-8b-instant)
- Implements two-layer state filtering:
  - **Layer 5.1**: Prompt-level filtering (tells LLM which tools to use)
  - **Layer 5.2**: Tool parameter validation (validates tool matches state)

### 5. FastAPI Routes (`routes/mcp_agent.py`)

- `POST /api/mcp/chat?state={state}` - Non-streaming chat
- `POST /api/mcp/chat/stream?state={state}` - Streaming chat (SSE)
- `GET /api/mcp/tools?state={state}` - List available tools

## State Management

### Valid States

- `route_management` - Route Management page tools only
- `bus_dashboard` - Bus Dashboard page tools only

### Two-Layer Filtering

#### Layer 5.1: Prompt-Level Filtering
The system prompt explicitly tells the LLM which tools are available based on state:
- Route Management: Only stops, paths, routes tools
- Bus Dashboard: Only vehicles, drivers, trips, deployments tools

#### Layer 5.2: Tool Parameter Validation
Each tool execution validates that the tool matches the current state:
```python
if state != ROUTE_MANAGEMENT_STATE:
    return error_message
```

## Usage

### Frontend Integration

```javascript
// Route Management page
const response = await fetch('/api/mcp/chat?state=route_management', {
  method: 'POST',
  body: JSON.stringify({
    messages: [{ role: 'user', content: 'List all stops' }]
  })
});

// Bus Dashboard page
const response = await fetch('/api/mcp/chat?state=bus_dashboard', {
  method: 'POST',
  body: JSON.stringify({
    messages: [{ role: 'user', content: 'List all vehicles' }]
  })
});
```

### Streaming

```javascript
const eventSource = new EventSource('/api/mcp/chat/stream?state=route_management');
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

## Environment Variables

Required in `.env`:
```
GROQ_API_KEY=your_groq_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

## File Structure

```
backend/mcp/
├── __init__.py
├── types.py                    # MCP type definitions
├── orchestration.py            # Reusable Supabase layer
├── server.py                   # MCP server implementation
├── langgraph_client.py         # LangGraph MCP client
├── tools/
│   ├── __init__.py
│   ├── route_management_tools.py
│   └── bus_dashboard_tools.py
└── README.md                   # This file
```

## Notes

- All database operations go through the orchestration layer for consistency
- State is validated at both prompt and tool execution levels
- Streaming is supported via Server-Sent Events (SSE)
- Tool execution results are returned as text content

