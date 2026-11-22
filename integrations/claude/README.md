# Anthropic Claude Integration & Distribution Guide for Bus Kar! 🚌

Bus Kar! provides native support for Anthropic Claude via the **Model Context Protocol (MCP)** and **Claude Desktop Plugins**.

Production API Endpoint: `https://bus-kar-api.vercel.app`

---

## 🌍 How to Share Bus Kar with Other Claude Users

### Method 1: Claude Desktop Plugin (.zip Upload) — Recommended for Teams
You can share the pre-packaged plugin zip:
👉 [`integrations/claude-plugin/bus-kar-claude-plugin.zip`](../claude-plugin/bus-kar-claude-plugin.zip)

1. Open **Claude Desktop** (or Claude for Work / Team).
2. Go to **Settings → Extensions / Plugins → Upload Plugin**.
3. Select `bus-kar-claude-plugin.zip`.
4. Claude will immediately register all 7 Bus Kar transit tools!

*For Claude Team/Enterprise admins: Upload to your **Organization Catalog** to automatically enable it for every team member in your company.*

---

### Method 2: 1-Click Install via Smithery.ai
This repository is pre-configured with `smithery.yaml`.
Once published on [Smithery.ai](https://smithery.ai):
- **Claude Desktop:** Users can install with a single click.
- **Claude Code CLI:** Users can install with one command:
  ```bash
  npx -y @smithery/cli install bus-kar --client claude
  ```

---

### Method 3: Direct Claude Desktop Config (Any Computer)
Other users can clone or download `run_mcp.py` and point their Claude Desktop config to:
```json
{
  "mcpServers": {
    "bus-kar": {
      "command": "python",
      "args": ["-u", "run_mcp.py"],
      "env": {
        "BUS_KAR_API_URL": "https://bus-kar-api.vercel.app"
      }
    }
  }
}
```
*Note: Because `run_mcp.py` connects to `https://bus-kar-api.vercel.app`, users do not need to run a local backend or database on their computer.*

---

### Method 4: Claude Code CLI
```bash
claude mcp add bus-kar -- python -u run_mcp.py
```

---

## 🛠️ Available Transit Tools in Claude

1. `resolve_stop`: Resolves colloquial Indian bus stop nicknames or landmarks (e.g. *Purana Adda*, *Silk Board*, *AIIMS gate 2*) into official GTFS stop IDs.
2. `get_live_bus_eta`: Real-time bus arrivals and live GPS telemetry, including countdown, crowd occupancy, and live map link.
3. `plan_transit_trip`: Point-to-point transit journey calculation, travel time, and first/last-mile ride suggestions.
4. `get_fare_and_ticketing_info`: DTC official fares & 100% free Pink Ticket concessions for women.
5. `suggest_colloquial_tag`: Registers a new public colloquial nickname for a bus stop.
6. `vote_stop_tag`: Upvotes or downvotes an existing crowdsourced colloquial stop tag.
7. `list_stop_tags`: Lists all active public colloquial aliases for a stop.
