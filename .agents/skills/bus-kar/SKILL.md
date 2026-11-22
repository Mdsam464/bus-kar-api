---
name: bus-kar
description: Real-time Indian city bus tracker, live GPS ETAs, trip routing, DTC fare calculator with Pink Scheme free rules for women, and crowdsourced colloquial station tags. Use whenever the user asks for bus arrivals, routes, fares, or Indian transit navigation.
---

# Bus Kar! Transit Skill for Gemini & Antigravity

Use this skill whenever the user asks about:
- Bus timings, arrivals, or real-time GPS locations in Indian metro cities (Delhi, Bengaluru, Mumbai).
- Journey planning between two points (e.g. "Kashmere Gate to Nehru Place").
- Bus fares, ticket prices, and concession rules (e.g. Free travel for women under Delhi Pink Slip scheme or Karnataka Shakti scheme).
- Suggesting or looking up colloquial bus stop nicknames (e.g. "Purana Adda", "Silk Board", "AIIMS Gate 2").

## Local API Endpoints (Live on http://127.0.0.1:8000)

The backend provides fast, zero-dependency REST endpoints:

1. **Resolve Colloquial Name**:
   `GET http://127.0.0.1:8000/api/v1/transit/stops/resolve?query=<nickname>&city=delhi`
2. **Live Bus ETA**:
   `GET http://127.0.0.1:8000/api/v1/transit/stops/<stop_id>/eta?route_number=<optional>`
3. **Plan Journey**:
   `GET http://127.0.0.1:8000/api/v1/transit/trip/plan?origin=<from>&destination=<to>&preference=fastest`
4. **Calculate Fare & Pink Ticket**:
   `GET http://127.0.0.1:8000/api/v1/transit/fare?from_stop=<from>&to_stop=<to>&passenger_category=woman`
5. **Suggest Crowdsourced Tag**:
   `POST http://127.0.0.1:8000/api/v1/tags/suggest` with JSON `{"stop_id": "...", "tag": "...", "city": "delhi"}`

## Python SDK Tool Calling
You can also invoke tools programmatically using the Python helper:
`from integrations.gemini.gemini_tools import execute_gemini_tool_call`
