<div align="center">
  <img src="static/icon.png" width="128" height="128" alt="Bus Kar! Logo" style="border-radius: 24px;" />
  <h1>Bus Kar! 🚌🇮🇳</h1>
  <p><strong>Agent-First Transit API & Model Context Protocol (MCP) Plugin for Indian City Buses</strong></p>
  <p>
    <a href="https://bus-kar-api.vercel.app"><img src="https://img.shields.io/badge/Vercel-Live_Deployment-black?style=flat&logo=vercel" alt="Vercel" /></a>
    <a href="https://bus-kar-api.vercel.app/docs"><img src="https://img.shields.io/badge/Swagger-API_Docs-emerald?style=flat&logo=fastapi" alt="API Docs" /></a>
    <a href="https://github.com/Mdsam464/bus-kar-api"><img src="https://img.shields.io/badge/GitHub-Repository-blue?style=flat&logo=github" alt="GitHub" /></a>
  </p>
</div>

**Bus Kar!** connects real-time Indian city bus telemetry (GTFS / GTFS-RT) with AI Agents (ChatGPT, Claude, Gemini, WhatsApp bots, and voice assistants).

It features a **Crowdsourced Public Colloquial Station Tagging Engine** so commuters can query and register natural vernacular names for bus stops (e.g., *"Purana Adda"*, *"Near Metro Gate 2"*, *"Majestic"*).

---

## 📂 Project Architecture

```
transit-agent-api/
├── app/
│   ├── main.py              # FastAPI entrypoint with auto-seeding & lifecycle
│   ├── config.py            # Pydantic environment configuration
│   ├── database.py          # Async SQLAlchemy engine (SQLite dev / Postgres prod)
│   ├── mcp_server.py        # Model Context Protocol (MCP) server for AI agents
│   ├── models/
│   │   ├── gtfs.py          # GTFS stops & routes models
│   │   └── stop_tag.py      # Public crowdsourced colloquial tags model
│   ├── schemas/
│   │   ├── transit.py       # Pydantic schemas for ETA, trips, and fares
│   │   └── tags.py          # Schemas for tag suggestions and upvotes
│   ├── services/
│   │   ├── delhi_otd.py     # Delhi Open Transit Data (OTD) connector & seed
│   │   ├── eta_service.py   # Real-time ETA, routing, and fare calculation
│   │   └── tag_service.py   # Colloquial resolution, upvoting, & normalization
│   └── routers/
│       ├── transit.py       # REST API: /api/v1/transit/...
│       └── tags.py          # REST API: /api/v1/tags/...
├── requirements.txt         # Python dependencies
├── .env.example             # Configuration variables
├── SPECS.md                 # Full technical system specifications
└── MONETIZATION_PLAN.md     # 4-pillar revenue and business strategy
```

---

## 🚀 Quickstart Guide

### 1. Setup Virtual Environment
```bash
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the FastAPI REST Server
```bash
uvicorn app.main:app --reload --port 8000
```
- Interactive Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Alternative ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🤖 Running as an MCP Plugin (for Claude, Cursor, Antigravity)

This project provides an out-of-the-box **Model Context Protocol (MCP)** server in [`app/mcp_server.py`](app/mcp_server.py).

### Add to Claude Desktop / Cursor / Antigravity MCP Config:
```json
{
  "mcpServers": {
    "bus-kar": {
      "command": "python",
      "args": ["-m", "app.mcp_server"],
      "cwd": "C:/Users/salma/.gemini/antigravity/scratch/transit-agent-api"
    }
  }
}
```

### Exposed MCP Tools:
1. `resolve_stop(query, city, limit)`: Resolves colloquial nicknames (e.g. *"Purana adda"*, *"AIIMS gate 2"*) to canonical GTFS stops.
2. `get_live_bus_eta(stop_id, city, route_number)`: Returns live vehicle arrivals, occupancy, and dynamic tracking map link.
3. `plan_transit_trip(origin, destination, city, preference)`: Calculates routes, travel time, and first/last-mile ride options.
4. `get_fare_and_ticketing_info(...)`: DTC fare calculator with Pink Scheme free pass logic and digital ticketing links.
5. `suggest_colloquial_tag(stop_id, tag, city, language, category)`: Registers a public user-suggested nickname.
6. `vote_stop_tag(tag_id, vote_type)`: Upvotes or downvotes community tags.
7. `list_stop_tags(stop_id, city)`: Lists all active community aliases for a stop.

---

## 📚 Key Reference Documents
- [System Specifications (`SPECS.md`)](SPECS.md)
- [Monetization & Business Plan (`MONETIZATION_PLAN.md`)](MONETIZATION_PLAN.md)
