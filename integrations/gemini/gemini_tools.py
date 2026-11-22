"""
Bus Kar! Google Gemini SDK Integration (Official google-genai SDK)
Compatible with Gemini 2.5 Flash, Gemini 2.5 Pro, and Gemini 3.x models.
"""

import httpx
from typing import Any, Dict, List, Optional

BUS_KAR_API_BASE = "http://localhost:8000"  # Or your public https://bus-kar.onrender.com

# 1. Gemini Function Declarations (Schema definition)
resolve_stop_declaration = {
    "name": "resolve_stop",
    "description": "Resolves colloquial Indian bus stop nicknames or landmarks (e.g. 'Purana Adda', 'Silk Board', 'AIIMS gate 2') into official GTFS stop IDs.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "query": {
                "type": "STRING",
                "description": "Colloquial nickname or landmark description"
            },
            "city": {
                "type": "STRING",
                "description": "Transit city (default: delhi)"
            },
            "limit": {
                "type": "INTEGER",
                "description": "Number of candidate stops to return"
            }
        },
        "required": ["query"]
    }
}

get_live_bus_eta_declaration = {
    "name": "get_live_bus_eta",
    "description": "Retrieves real-time bus arrivals and live GPS telemetry at a stop, including ETA countdown, crowd level, and live tracking map link.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "stop_id": {
                "type": "STRING",
                "description": "Canonical GTFS stop ID (e.g. DTC_KG_01)"
            },
            "city": {
                "type": "STRING",
                "description": "Transit city (default: delhi)"
            },
            "route_number": {
                "type": "STRING",
                "description": "Optional filter for specific bus route (e.g. 534)"
            }
        },
        "required": ["stop_id"]
    }
}

plan_transit_trip_declaration = {
    "name": "plan_transit_trip",
    "description": "Plans a point-to-point bus journey between two stops or landmarks, calculating travel duration, fare estimate, and first/last-mile ride suggestions.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "origin": {
                "type": "STRING",
                "description": "Starting stop name or landmark"
            },
            "destination": {
                "type": "STRING",
                "description": "Destination stop name or landmark"
            },
            "city": {
                "type": "STRING",
                "description": "Transit city (default: delhi)"
            },
            "preference": {
                "type": "STRING",
                "description": "fastest, ac_only, or cheapest"
            }
        },
        "required": ["origin", "destination"]
    }
}

get_fare_and_ticketing_declaration = {
    "name": "get_fare_and_ticketing",
    "description": "Calculates official bus fares, checks concession eligibility (e.g. free travel for women under Delhi Pink Pass), and returns digital booking links.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "from_stop": { "type": "STRING" },
            "to_stop": { "type": "STRING" },
            "route_number": { "type": "STRING" },
            "passenger_category": {
                "type": "STRING",
                "description": "general, woman, senior_citizen, student"
            }
        },
        "required": ["from_stop", "to_stop"]
    }
}

suggest_colloquial_tag_declaration = {
    "name": "suggest_colloquial_tag",
    "description": "Registers a new public colloquial nickname for a bus stop. Available immediately to all commuters.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "stop_id": { "type": "STRING" },
            "tag": { "type": "STRING" },
            "city": { "type": "STRING" },
            "category": { "type": "STRING" }
        },
        "required": ["stop_id", "tag"]
    }
}

# The complete list of tool declarations ready to pass to Gemini
bus_kar_gemini_tools = [{
    "function_declarations": [
        resolve_stop_declaration,
        get_live_bus_eta_declaration,
        plan_transit_trip_declaration,
        get_fare_and_ticketing_declaration,
        suggest_colloquial_tag_declaration
    ]
}]


# 2. Tool Execution Dispatcher
def execute_gemini_tool_call(function_name: str, args: Dict[str, Any], base_url: str = BUS_KAR_API_BASE) -> Dict[str, Any]:
    """
    Executes the function called by the Gemini model against the Bus Kar! API backend.
    """
    with httpx.Client(base_url=base_url, timeout=10.0) as client:
        if function_name == "resolve_stop":
            resp = client.get("/api/v1/transit/stops/resolve", params=args)
            return resp.json()

        elif function_name == "get_live_bus_eta":
            stop_id = args.pop("stop_id")
            resp = client.get(f"/api/v1/transit/stops/{stop_id}/eta", params=args)
            return resp.json()

        elif function_name == "plan_transit_trip":
            resp = client.get("/api/v1/transit/trip/plan", params=args)
            return resp.json()

        elif function_name == "get_fare_and_ticketing":
            resp = client.get("/api/v1/transit/fare", params=args)
            return resp.json()

        elif function_name == "suggest_colloquial_tag":
            resp = client.post("/api/v1/tags/suggest", json=args)
            return resp.json()

        else:
            return {"error": f"Unknown tool: {function_name}"}


# 3. Example End-to-End Chat Loop with Gemini SDK
def chat_with_gemini_example(user_prompt: str, api_key: str):
    """
    Example demonstrating function calling with google-genai SDK.
    Install: pip install google-genai
    """
    from google import genai

    client = genai.Client(api_key=api_key)
    
    # Send user query with Bus Kar tools attached
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=user_prompt,
        config={"tools": bus_kar_gemini_tools}
    )

    # Check for function calls
    if response.function_calls:
        for call in response.function_calls:
            print(f"Gemini requested tool call: {call.name} with args: {call.args}")
            tool_result = execute_gemini_tool_call(call.name, dict(call.args))
            print("Tool Execution Result:", tool_result)
            return tool_result

    print("Gemini direct response:", response.text)
    return response.text
