import sys
import os

# Ensure project root is in sys.path regardless of where Claude Code launches this script
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import asyncio
import json
from typing import Any, Dict, List, Optional
try:
    from mcp.server import MCPServer as FastMCP
except ImportError:
    from mcp.server.fastmcp import FastMCP
from app.database import AsyncSessionLocal
from app.services.tag_service import TagService
from app.services.eta_service import ETAService

# Create FastMCP Server instance
mcp = FastMCP("bus-kar", dependencies=["httpx", "sqlalchemy"])

@mcp.tool()
async def resolve_stop(query: str, city: str = "delhi", limit: int = 3) -> str:
    """
    Resolves colloquial landmarks, local street names, or metro gates into official transit stop IDs.
    Example: 'Silk Board near bridge', 'Purana adda', 'Kashmere gate ISBT', 'AIIMS gate 2'.
    """
    async with AsyncSessionLocal() as session:
        candidates = await TagService.resolve_stop_by_query(session, city, query, limit)
        return json.dumps([c.model_dump() for c in candidates], indent=2)

@mcp.tool()
async def get_live_bus_eta(stop_id: str, city: str = "delhi", route_number: Optional[str] = None) -> str:
    """
    Fetches real-time bus arrivals and live GPS telemetry at a stop, including ETA in minutes,
    crowd occupancy, and an interactive micro-map link.
    """
    async with AsyncSessionLocal() as session:
        res = await ETAService.get_stop_eta(session, city, stop_id, route_number)
        return json.dumps(res.model_dump(), indent=2)

@mcp.tool()
async def plan_transit_trip(
    origin: str, 
    destination: str, 
    city: str = "delhi", 
    preference: str = "fastest"
) -> str:
    """
    Plans an optimal bus journey between two stops or landmarks, calculating travel time, transfers,
    and first/last-mile suggestions.
    Preference can be: 'fastest', 'ac_only', or 'cheapest'.
    """
    async with AsyncSessionLocal() as session:
        res = await ETAService.plan_trip(session, city, origin, destination, preference)
        return json.dumps(res.model_dump(), indent=2)

@mcp.tool()
async def get_fare_and_ticketing_info(
    from_stop: str,
    to_stop: str,
    route_number: str = "534",
    city: str = "delhi",
    passenger_category: str = "general"
) -> str:
    """
    Calculates official bus fares, checks concession eligibility (e.g., Delhi Pink Ticket free for women),
    and gives deep links for digital WhatsApp/QR ticketing.
    passenger_category can be: 'general', 'woman', 'senior_citizen', 'student'.
    """
    res = ETAService.get_fare_details(city, route_number, from_stop, to_stop, passenger_category)
    return json.dumps(res.model_dump(), indent=2)

@mcp.tool()
async def suggest_colloquial_tag(
    stop_id: str,
    tag: str,
    city: str = "delhi",
    language: str = "en",
    category: str = "landmark"
) -> str:
    """
    Suggests a new public colloquial tag or landmark nickname for a bus stop.
    Instantly published and available for all commuters and agents to search.
    """
    async with AsyncSessionLocal() as session:
        tag_obj = await TagService.suggest_tag(session, city, stop_id, tag, language, category)
        return json.dumps({
            "status": "success",
            "tag_id": tag_obj.id,
            "stop_id": tag_obj.stop_id,
            "tag": tag_obj.tag,
            "upvotes": tag_obj.upvotes,
            "message": "Tag registered publicly."
        }, indent=2)

@mcp.tool()
async def vote_stop_tag(tag_id: str, vote_type: str = "upvote") -> str:
    """
    Upvotes or downvotes an existing crowdsourced colloquial stop tag to boost good aliases and suppress spam.
    vote_type can be 'upvote' or 'downvote'.
    """
    async with AsyncSessionLocal() as session:
        tag_obj = await TagService.vote_tag(session, tag_id, vote_type)
        if not tag_obj:
            return json.dumps({"error": f"Tag ID '{tag_id}' not found."}, indent=2)
        return json.dumps({
            "status": "success",
            "tag_id": tag_obj.id,
            "new_upvotes": tag_obj.upvotes,
            "new_downvotes": tag_obj.downvotes,
            "tag_status": tag_obj.status
        }, indent=2)

@mcp.tool()
async def list_stop_tags(stop_id: str, city: str = "delhi") -> str:
    """
    Lists all public colloquial aliases and community tags associated with a specific stop.
    """
    async with AsyncSessionLocal() as session:
        tags = await TagService.get_tags_for_stop(session, stop_id)
        return json.dumps([
            {
                "id": t.id,
                "tag": t.tag,
                "category": t.category,
                "upvotes": t.upvotes,
                "downvotes": t.downvotes,
                "language": t.language
            }
            for t in tags
        ], indent=2)

if __name__ == "__main__":
    # Runs the stdio MCP server for agent clients (Claude Desktop, Cursor, Antigravity)
    mcp.run()
