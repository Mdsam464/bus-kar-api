# Anthropic Claude Integration Guide for Bus Kar! 🚌

Bus Kar! provides native support for Anthropic Claude via the **Model Context Protocol (MCP)**.

---

## 🖥️ Option 1: Claude Desktop App (Windows)

Depending on how you installed Claude Desktop on Windows:

### For Microsoft Store Version (Packaged):
Copy the configuration into:  
`C:\Users\salma\AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json`

### For Standard Installer:
Copy the configuration into:  
`%APPDATA%\Claude\claude_desktop_config.json`

### Config Content:
```json
{
  "mcpServers": {
    "bus-kar": {
      "command": "C:/Python314/python.exe",
      "args": [
        "C:/Users/salma/.gemini/antigravity/scratch/transit-agent-api/run_mcp.py"
      ]
    }
  }
}
```
*(Or use the remote SSE endpoint: `"url": "https://bus-kar.onrender.com/mcp/sse"`)*

1. Completely quit Claude Desktop (close from system tray).
2. Reopen Claude Desktop.
3. The Hammer icon (🔨) in the chat window will show 7 active Bus Kar tools!

---

## 💻 Option 2: Claude Code (CLI)

In PowerShell, inside the project folder:
```powershell
claude.cmd mcp add bus-kar -- C:\Python314\python.exe C:\Users\salma\.gemini\antigravity\scratch\transit-agent-api\run_mcp.py
```

Or copy [`claude_code_config.json`](claude_code_config.json) to `.mcp.json` in your project root, then launch:
```powershell
claude.cmd
```

---

## 🛠️ Exposed MCP Tools in Claude:
1. `resolve_stop(query, city, limit)`
2. `get_live_bus_eta(stop_id, city, route_number)`
3. `plan_transit_trip(origin, destination, city, preference)`
4. `get_fare_and_ticketing_info(from_stop, to_stop, route_number, city, passenger_category)`
5. `suggest_colloquial_tag(stop_id, tag, city, language, category)`
6. `vote_stop_tag(tag_id, vote_type)`
7. `list_stop_tags(stop_id, city)`
