# Bus Kar! Universal AI Integration Hub 🚌🤖

Bus Kar! is an open, model-agnostic transit plugin and API. It provides native, turnkey integrations for the top three AI platforms:

```
                                  ┌───────────────────────────────┐
                                  │           BUS KAR!            │
                                  │   Real-Time Transit Engine    │
                                  └───────────────┬───────────────┘
                                                  │
                 ┌────────────────────────────────┼────────────────────────────────┐
                 ▼                                ▼                                ▼
    ┌─────────────────────────┐      ┌─────────────────────────┐      ┌─────────────────────────┐
    │     OpenAI ChatGPT      │      │    Anthropic Claude     │      │      Google Gemini      │
    │   Custom GPT Actions    │      │  Model Context Protocol │      │  Official GenAI SDK &   │
    │      (OpenAPI 3.1)      │      │       (MCP 2.x)         │      │     AI Studio Tools     │
    ├─────────────────────────┤      ├─────────────────────────┤      ├─────────────────────────┤
    │ 📁 integrations/chatgpt │      │ 📁 integrations/claude  │      │ 📁 integrations/gemini  │
    └─────────────────────────┘      └─────────────────────────┘      └─────────────────────────┘
```

---

## 📁 Integration Quick Links

| Platform | Protocol | Configuration Folder | Setup Time |
| :--- | :--- | :--- | :--- |
| **OpenAI ChatGPT** | Custom GPT Action (OpenAPI 3.1) | [`integrations/chatgpt/`](integrations/chatgpt/README.md) | ~3 mins |
| **Anthropic Claude** | Model Context Protocol (MCP) | [`integrations/claude/`](integrations/claude/README.md) | ~1 min |
| **Google Gemini** | GenAI SDK Function Calling & Extensions | [`integrations/gemini/`](integrations/gemini/README.md) | ~2 mins |

---

## 🛠️ The 7 Universal Transit Tools

Regardless of which AI model you connect, all three platforms share the exact same underlying capabilities:

1. **`resolve_stop`**: Translates vernacular landmarks (*"Purana Adda"*, *"Silk Board bridge neeche"*, *"AIIMS gate 2"*) into official GTFS stop IDs.
2. **`get_live_bus_eta`**: Real-time vehicle arrivals, countdown in minutes, distance in meters, crowd occupancy, and 1-tap live map tracking URL.
3. **`plan_transit_trip`**: Optimal route itinerary, transfer stops, travel duration, and first/last-mile ride suggestions (Rapido/Uber/Auto).
4. **`get_fare_and_ticketing`**: Calculates official fare slabs, verifies **100% FREE travel for women** under the Delhi Government Pink Slip scheme, and provides digital QR ticketing links.
5. **`suggest_colloquial_tag`**: Crowdsourced station nickname submission, instantly indexed and public to all commuters.
6. **`vote_stop_tag`**: Upvotes/downvotes community tags to boost high-quality aliases and suppress spam.
7. **`list_stop_tags`**: Lists all active community nicknames for any bus stop.
