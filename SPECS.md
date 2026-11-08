# System Architecture & API Specifications: AI Agent Bus Tracker & Info Provider (India)

**Document Version:** 1.0.0  
**Target Ecosystem:** Model Context Protocol (MCP) & OpenAPI 3.1 (ChatGPT Actions, Claude, Gemini, WhatsApp/Telegram Bots)  
**Primary Region:** Indian Metro Transit Networks (DTC/DIMTS Delhi, BMTC Bengaluru, BEST Mumbai, etc.)

---

## 1. Executive Summary & Vision

The **Transit AI Agent API & Plugin** is an intelligent, developer- and agent-friendly middleware that connects real-time public bus feeds (GTFS & GTFS-RT) with Large Language Models. 

Unlike consumer transit apps cluttered with banner ads and rigid form inputs, this system exposes semantic tools that allow conversational agents to answer complex multi-step commuter queries, provide live vehicle ETAs with lightweight map deep-links, and harness a **public, crowdsourced colloquial station tagging system** tailored to the linguistic diversity of Indian commuters.

---

## 2. Core Architecture Overview

```
                      ┌─────────────────────────────────────────┐
                      │             AI Agents & Clients         │
                      │  (WhatsApp/Telegram Bot, Claude,        │
                      │   ChatGPT Action, Voice Assistant)      │
                      └────────────────────┬────────────────────┘
                                           │
                        ┌──────────────────┴──────────────────┐
                        │   Protocol Layer                    │
                        │   - MCP Server (JSON-RPC over SSE)  │
                        │   - REST API (OpenAPI 3.1 JSON)     │
                        └──────────────────┬──────────────────┘
                                           │
    ┌──────────────────────────────────────┴──────────────────────────────────────┐
    │                         Transit Agent Core Engine                           │
    ├─────────────────────────────┬───────────────────────────┬───────────────────┤
    │  Public Tagging & Alias     │   Routing & Fare Matrix   │  Real-time ETA &  │
    │  Vector Resolution Engine   │   Calculation Engine      │  Tracking Engine  │
    └──────────────┬──────────────┴─────────────┬─────────────┴─────────┬─────────┘
                   │                            │                       │
    ┌──────────────┴──────────────┐             │          ┌────────────┴────────────┐
    │ PostgreSQL + PostGIS + pgvector           │          │ Redis In-Memory Store   │
    │ - GTFS Static (Stops, Routes, Shapes)     │          │ - Live VehiclePositions │
    │ - Public Crowdsourced Tags & Upvotes      │          │ - Cached Stop ETAs (15s)│
    │ - Stop Semantic Embeddings                │          │ - Route Congestion Index│
    └───────────────────────────────────────────┘          └────────────┬────────────┘
                                                                        │
                                            ┌───────────────────────────┴────────────┐
                                            │ Data Ingestion Worker                  │
                                            │ - Delhi OTD / BMTC / BEST Feeds        │
                                            │ - GTFS-RT Protobuf Parser (every 15s)  │
                                            │ - TripUpdate & VehiclePositions        │
                                            └────────────────────────────────────────┘
```

---

## 3. Public Crowdsourced Colloquial Station Tags System

### 3.1. Problem Statement
Official transit stop names in GTFS feeds rarely match what commuters speak. For example:
- Official: `Kempegowda Bus Station (Bay 12)` $\rightarrow$ Commuters say: *Majestic*, *KBS*, or *City Railway Station back gate*.
- Official: `Maharana Pratap Inter State Bus Terminus` $\rightarrow$ Commuters say: *Kashmere Gate ISBT*, *Purana adda*.
- Official: `Bandra Station (W) Lucky Restaurant` $\rightarrow$ Commuters say: *Lucky junction*, *Bandra station west*.

### 3.2. Crowdsourced Public Tags Model
Any user or agent interaction can view, suggest, or upvote colloquial tags for bus stops. These tags are instantly indexed publicly to improve stop-resolution accuracy across the entire network.

#### Data Schema (`stop_tags`)
```sql
CREATE TABLE stop_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stop_id VARCHAR(100) NOT NULL REFERENCES gtfs_stops(stop_id) ON DELETE CASCADE,
    city VARCHAR(50) NOT NULL,
    tag VARCHAR(150) NOT NULL,              -- e.g. "Majestic", "Silk Board Bridge Neeche"
    tag_normalized VARCHAR(150) NOT NULL,   -- lowercase, stripped punctuation, normalized
    language VARCHAR(10) DEFAULT 'en',      -- 'en', 'hi', 'kn', 'mr', 'ta', etc.
    embedding vector(384),                  -- MiniLM-L6 semantic embedding for fuzzy search
    category VARCHAR(50) DEFAULT 'landmark',-- 'landmark', 'metro_gate', 'slang', 'junction'
    upvotes INT DEFAULT 1,
    downvotes INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'public',    -- 'public', 'flagged', 'verified'
    submitted_by VARCHAR(100),              -- anonymous user hash or client agent ID
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_stop_tags_stop_id ON stop_tags(stop_id);
CREATE INDEX idx_stop_tags_tag_norm ON stop_tags(tag_normalized);
CREATE INDEX idx_stop_tags_city ON stop_tags(city);
CREATE INDEX idx_stop_tags_vector ON stop_tags USING ivfflat (embedding vector_cosine_ops);
```

### 3.3. Tag Resolution & Scoring Pipeline
When a user asks: *"Bus from Silk Board to Majestic"*:
1. **Search Order**: Exact Tag Match $\rightarrow$ Vector / Phonetic Search on Community Tags $\rightarrow$ GTFS Official Stop Name Match.
2. **Confidence Score Calculation**:
   $$\text{Score} = (\text{CosineSimilarity} \times 0.6) + \left(\min\left(1.0, \frac{\text{upvotes} - \text{downvotes}}{10}\right) \times 0.4\right)$$
3. **Spam Mitigation**:
   - Automated toxicity / obscenity filter on tag creation.
   - If $\text{downvotes} > 3 \times \text{upvotes}$, the tag is auto-flagged and excluded from default agent resolution.

---

## 4. Agent Tools & API Specifications

The system exposes two standard interfaces:
1. **MCP (Model Context Protocol)** tools for AI agents.
2. **RESTful HTTP (OpenAPI 3.1)** for webhooks, custom backends, and frontend clients.

---

### Tool 1: `resolve_stop`
Resolves a colloquial landmark, metro gate, or street name to one or more candidate transit stops using the GTFS directory and crowdsourced community tags.

- **Parameters:**
  ```json
  {
    "city": { "type": "string", "description": "e.g., 'delhi', 'bengaluru', 'mumbai'" },
    "query": { "type": "string", "description": "Colloquial query, e.g. 'Silk Board near police booth', 'IIT Delhi Gate 1'" },
    "limit": { "type": "integer", "default": 3, "description": "Number of best candidate stops to return" }
  }
  ```
- **Returns:**
  ```json
  {
    "candidates": [
      {
        "stop_id": "DTC_4102",
        "official_name": "Central Silk Board (Towards BTM)",
        "matched_tag": "Silk Board junction",
        "tag_upvotes": 42,
        "latitude": 12.9176,
        "longitude": 77.6233,
        "confidence": 0.94
      }
    ]
  }
  ```

---

### Tool 2: `get_live_bus_eta`
Retrieves real-time vehicle positions, upcoming bus arrivals at a specific stop, crowd level, and a dynamic 1-tap live tracking micro-map URL.

- **Parameters:**
  ```json
  {
    "city": { "type": "string" },
    "stop_id": { "type": "string" },
    "route_number": { "type": "string", "description": "Optional filter, e.g., '534', '500-D', 'AC-4' " }
  }
  ```
- **Returns:**
  ```json
  {
    "stop_id": "DTC_4102",
    "stop_name": "Central Silk Board",
    "timestamp": "2026-11-07T15:35:00+05:30",
    "arrivals": [
      {
        "route_number": "500-D",
        "vehicle_id": "DL-1PC-8912",
        "vehicle_type": "AC_Electric",
        "eta_minutes": 4,
        "distance_meters": 1200,
        "last_ping_seconds_ago": 12,
        "occupancy_status": "MANY_SEATS_AVAILABLE",
        "live_map_url": "https://live.bustracker.local/v/DL1PC8912?stop=DTC_4102"
      }
    ]
  }
  ```

---

### Tool 3: `plan_transit_trip`
Computes an optimal point-to-point transit itinerary taking into account bus sub-types (AC vs Ordinary), transfers, and current live traffic speeds.

- **Parameters:**
  ```json
  {
    "city": { "type": "string" },
    "origin_query": { "type": "string", "description": "Stop ID or colloquial landmark" },
    "destination_query": { "type": "string", "description": "Stop ID or colloquial landmark" },
    "preference": { 
      "type": "string", 
      "enum": ["fastest", "ac_only", "cheapest", "least_transfers"],
      "default": "fastest"
    }
  }
  ```
- **Returns:**
  ```json
  {
    "routes": [
      {
        "option_id": 1,
        "total_travel_time_minutes": 38,
        "fare_estimate": { "currency": "INR", "amount": 25, "fare_type": "AC" },
        "legs": [
          {
            "route_number": "534",
            "from_stop": "Nehru Place",
            "to_stop": "Mayur Vihar Phase 1",
            "stops_count": 9,
            "next_bus_eta_minutes": 3,
            "bus_type": "AC_LowFloor"
          }
        ],
        "transfers": 0
      }
    ]
  }
  ```

---

### Tool 4: `get_fare_and_ticketing_info`
Provides official fare slabs, concession eligibility (e.g., Delhi Pink Pass for women, BMTC Shakti Scheme, Daily/Monthly passes), and ticketing deep-links (Chartr WhatsApp QR or Chalo).

- **Parameters:**
  ```json
  {
    "city": { "type": "string" },
    "route_number": { "type": "string" },
    "from_stop_id": { "type": "string" },
    "to_stop_id": { "type": "string" },
    "passenger_category": { 
      "type": "string", 
      "enum": ["general", "woman", "senior_citizen", "student"],
      "default": "general"
    }
  }
  ```
- **Returns:**
  ```json
  {
    "city": "delhi",
    "route_number": "534",
    "fare_inr": 15,
    "bus_type": "Non-AC",
    "concessions_applicable": [
      {
        "scheme": "Delhi Pink Ticket Scheme",
        "eligible": true,
        "final_fare": 0,
        "note": "Free travel with Pink Slip issued by conductor on-board"
      }
    ],
    "digital_ticketing": {
      "provider": "Chartr",
      "method": "WhatsApp_or_QR",
      "booking_link": "https://wa.me/919999999999?text=Ticket+534+NehruPlace"
    }
  }
  ```

---

### Tool 5: `suggest_colloquial_tag` *(New Crowdsourced Feature)*
Allows conversational users and agents to register new colloquial station names, aliases, or local landmark references.

- **Parameters:**
  ```json
  {
    "city": { "type": "string" },
    "stop_id": { "type": "string" },
    "tag": { "type": "string", "description": "e.g. 'Near Gate 4 Metro Exit', 'Opposite McDonald's'" },
    "language": { "type": "string", "default": "en", "description": "ISO language code: en, hi, kn, mr, etc." },
    "category": { "type": "string", "enum": ["landmark", "metro_gate", "slang", "junction"], "default": "landmark" }
  }
  ```
- **Returns:**
  ```json
  {
    "status": "success",
    "tag_id": "8b9a12c4-...",
    "stop_id": "DTC_4102",
    "tag": "Opposite McDonald's",
    "upvotes": 1,
    "message": "Public colloquial tag registered. It is now instantly active and searchable for all AI agents."
  }
  ```

---

### Tool 6: `vote_stop_tag` *(New Crowdsourced Feature)*
Allows users to upvote or downvote existing colloquial tags to elevate accurate aliases and suppress spam.

- **Parameters:**
  ```json
  {
    "tag_id": { "type": "string" },
    "vote_type": { "type": "string", "enum": ["upvote", "downvote"] }
  }
  ```
- **Returns:**
  ```json
  {
    "status": "success",
    "tag_id": "8b9a12c4-...",
    "new_score": 15,
    "current_status": "public"
  }
  ```

---

### Tool 7: `list_stop_tags`
Returns all public colloquial tags registered for a given stop.

- **Parameters:**
  ```json
  {
    "stop_id": { "type": "string" },
    "city": { "type": "string" }
  }
  ```
- **Returns:**
  ```json
  {
    "stop_id": "DTC_4102",
    "official_name": "Central Silk Board",
    "tags": [
      { "tag_id": "t1", "tag": "Silk Board", "upvotes": 112, "downvotes": 2 },
      { "tag_id": "t2", "tag": "Silk Board Flyover Bottom", "upvotes": 45, "downvotes": 1 },
      { "tag_id": "t3", "tag": "Silk Board Metro Gate 2", "upvotes": 28, "downvotes": 0 }
    ]
  }
  ```

---

## 5. Technical Implementation Stack

| Layer | Recommended Technology | Justification |
| :--- | :--- | :--- |
| **Language & Framework** | **Python (FastAPI)** or **Go** | High performance for decoding Google Protobuf (`gtfs-realtime.proto`), async concurrency. |
| **Real-time Spatial Store** | **Redis (with Redis-Geospatial)** | Sub-millisecond read/write for live vehicle GPS lat/long updates every 15s. |
| **Relational & Vector DB** | **PostgreSQL + PostGIS + pgvector** | Stores GTFS static timetable schedules, route linestrings, and vector embeddings for community tags. |
| **Embedding Model** | `all-MiniLM-L6-v2` (Sentence-Transformers) | Fast, lightweight 384-dim embeddings run locally with negligible inference overhead. |
| **Protocol Support** | **MCP (Model Context Protocol) + OpenAPI 3.1** | Out-of-the-box compatibility with Anthropic Claude, OpenAI, Antigravity, and LangChain/LlamaIndex. |
| **Micro-Map Visualizer** | **Lightweight Leaflet / MapLibre PWA** | Zero-dependency micro-HTML/JS page that loads instantly via `live_map_url` when user taps from chat. |

---

## 6. Resilience & Edge Cases in Indian Transit

1. **Ghost Buses & Telemetry Loss**:
   - If a bus does not ping for $> 180$ seconds, it is flagged as `STALE_TELEMETRY`. The agent transparently informs: *"Last seen 4 mins ago near Stop X. May experience delay."*
2. **Hindi & Vernacular Transliteration**:
   - Commuters often type Hindi in Latin characters (*Hinglish*), e.g., *"ISBT ke paas wala bus stop"*.
   - The query pre-processor normalizes Hinglish particles (`ke paas`, `se`, `tak`, `wala`) before vector matching.
3. **Crowdsource Tag Poisoning**:
   - Strict rate-limiting per IP/Client ID (maximum 5 tag suggestions per 10 minutes).
   - Regex-based moderation check for phone numbers, URLs, and abusive language.

---

## 7. Immediate Next Steps & Milestones

1. **Milestone 1 (Data Sandbox)**: Set up Delhi Open Transit Data (OTD) API credentials and download the GTFS static bundle + GTFS-RT Protobuf streams.
2. **Milestone 2 (Database & Ingestion Engine)**: Run schema migration for `gtfs_stops`, `gtfs_routes`, and `stop_tags`. Spin up the 15-second polling worker.
3. **Milestone 3 (MCP & REST Server)**: Implement the 7 tools in FastAPI and package as an MCP server.
4. **Milestone 4 (Interactive Bot / UI Test)**: Connect to a WhatsApp sandbox (Twilio or Meta Cloud API) or test inside Claude/Antigravity to verify natural conversation flows.
