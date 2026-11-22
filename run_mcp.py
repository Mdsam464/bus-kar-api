import json
import sys
import httpx

API_BASE = "http://127.0.0.1:8000"

TOOLS = [
    {
        "name": "resolve_stop",
        "description": "Resolves colloquial Indian bus stop nicknames or landmarks (e.g. 'Purana Adda', 'Silk Board', 'AIIMS gate 2') into official GTFS stop IDs.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Colloquial nickname or landmark"},
                "city": {"type": "string", "default": "delhi", "description": "Transit city"},
                "limit": {"type": "integer", "default": 3}
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_live_bus_eta",
        "description": "Retrieves real-time bus arrivals and live GPS telemetry at a stop, including countdown, crowd occupancy, and live map link.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "stop_id": {"type": "string", "description": "Canonical GTFS stop ID"},
                "city": {"type": "string", "default": "delhi"},
                "route_number": {"type": "string", "description": "Optional route filter"}
            },
            "required": ["stop_id"]
        }
    },
    {
        "name": "plan_transit_trip",
        "description": "Plans a point-to-point transit journey calculating routes, travel time, fare estimate, and first/last-mile ride suggestions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "origin": {"type": "string"},
                "destination": {"type": "string"},
                "city": {"type": "string", "default": "delhi"},
                "preference": {"type": "string", "default": "fastest"}
            },
            "required": ["origin", "destination"]
        }
    },
    {
        "name": "get_fare_and_ticketing_info",
        "description": "Calculates official bus fares, checks concession eligibility (e.g. Delhi Pink Pass 100% free for women), and returns ticketing links.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "from_stop": {"type": "string"},
                "to_stop": {"type": "string"},
                "route_number": {"type": "string", "default": "534"},
                "city": {"type": "string", "default": "delhi"},
                "passenger_category": {"type": "string", "default": "general"}
            },
            "required": ["from_stop", "to_stop"]
        }
    },
    {
        "name": "suggest_colloquial_tag",
        "description": "Registers a new public colloquial nickname for a bus stop. Available immediately to all commuters.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "stop_id": {"type": "string"},
                "tag": {"type": "string"},
                "city": {"type": "string", "default": "delhi"},
                "category": {"type": "string", "default": "landmark"}
            },
            "required": ["stop_id", "tag"]
        }
    },
    {
        "name": "vote_stop_tag",
        "description": "Upvotes or downvotes an existing crowdsourced colloquial stop tag.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tag_id": {"type": "string"},
                "vote_type": {"type": "string", "enum": ["upvote", "downvote"], "default": "upvote"}
            },
            "required": ["tag_id"]
        }
    },
    {
        "name": "list_stop_tags",
        "description": "Lists all active public colloquial aliases for a stop.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "stop_id": {"type": "string"},
                "city": {"type": "string", "default": "delhi"}
            },
            "required": ["stop_id"]
        }
    }
]

def execute_tool_http(name: str, args: dict) -> str:
    with httpx.Client(base_url=API_BASE, timeout=5.0) as client:
        if name == "resolve_stop":
            resp = client.get("/api/v1/transit/stops/resolve", params=args)
            return resp.text

        elif name == "get_live_bus_eta":
            stop_id = args.pop("stop_id")
            resp = client.get(f"/api/v1/transit/stops/{stop_id}/eta", params=args)
            return resp.text

        elif name == "plan_transit_trip":
            resp = client.get("/api/v1/transit/trip/plan", params=args)
            return resp.text

        elif name == "get_fare_and_ticketing_info":
            resp = client.get("/api/v1/transit/fare", params=args)
            return resp.text

        elif name == "suggest_colloquial_tag":
            resp = client.post("/api/v1/tags/suggest", json=args)
            return resp.text

        elif name == "vote_stop_tag":
            tag_id = args["tag_id"]
            resp = client.post(f"/api/v1/tags/{tag_id}/vote", json=args)
            return resp.text

        elif name == "list_stop_tags":
            stop_id = args["stop_id"]
            resp = client.get(f"/api/v1/tags/stops/{stop_id}", params=args)
            return resp.text

        return json.dumps({"error": f"Unknown tool: {name}"})

def send_response(resp: dict):
    sys.stdout.write(json.dumps(resp) + "\n")
    sys.stdout.flush()

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            req = json.loads(line)
        except Exception:
            continue

        req_id = req.get("id")
        method = req.get("method")

        if method == "initialize":
            send_response({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "bus-kar", "version": "1.0.0"}
                }
            })

        elif method == "notifications/initialized":
            pass

        elif method == "ping":
            send_response({"jsonrpc": "2.0", "id": req_id, "result": {}})

        elif method == "tools/list":
            send_response({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": TOOLS}
            })

        elif method == "tools/call":
            params = req.get("params", {})
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            try:
                result_text = execute_tool_http(tool_name, tool_args)
                send_response({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": result_text}]
                    }
                })
            except Exception as e:
                send_response({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                        "isError": True
                    }
                })

if __name__ == "__main__":
    main()
