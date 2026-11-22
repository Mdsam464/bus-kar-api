import sys
import os

# Ensure project root is in sys.path regardless of where Claude Code launches this script
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import asyncio
import json
from typing import Any, Dict, List, Optional, Annotated
from pydantic import Field

try:
    from mcp.server import MCPServer as FastMCP
except ImportError:
    from mcp.server.fastmcp import FastMCP

from mcp.types import ToolAnnotations
from app.database import AsyncSessionLocal
from app.services.tag_service import TagService
from app.services.eta_service import ETAService

# Create FastMCP / MCPServer instance
mcp = FastMCP("bus-kar", dependencies=["httpx", "sqlalchemy"])

@mcp.tool(
    name="resolve_stop",
    title="Resolve Colloquial Transit Stop",
    description="Resolves colloquial landmarks, local street names, or metro gates into official GTFS transit stop IDs.",
    annotations=ToolAnnotations(
        title="Resolve Colloquial Transit Stop",
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False
    )
)
async def resolve_stop(
    query: Annotated[str, Field(description="Colloquial landmark, local street nickname, or metro gate (e.g. 'Purana Adda', 'AIIMS Gate 2', 'Silk Board').")],
    city: Annotated[str, Field(description="City identifier (default: 'delhi').")] = "delhi",
    limit: Annotated[int, Field(description="Maximum number of candidate stop recommendations to return.")] = 3
) -> str:
    """
    Resolves colloquial landmarks, local street names, or metro gates into official transit stop IDs.
    Example: 'Silk Board near bridge', 'Purana adda', 'Kashmere gate ISBT', 'AIIMS gate 2'.
    """
    async with AsyncSessionLocal() as session:
        candidates = await TagService.resolve_stop_by_query(session, city, query, limit)
        return json.dumps([c.model_dump() for c in candidates], indent=2)

@mcp.tool(
    name="get_live_bus_eta",
    title="Get Live Bus Telemetry & ETA",
    description="Fetches real-time bus arrivals and live GPS telemetry at a stop, including countdown ETA in minutes, crowd occupancy, and an interactive tracking map link.",
    annotations=ToolAnnotations(
        title="Get Live Bus Telemetry & ETA",
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=False,
        open_world_hint=False
    )
)
async def get_live_bus_eta(
    stop_id: Annotated[str, Field(description="Official transit stop identifier (e.g. 'DTC_KG_01').")],
    city: Annotated[str, Field(description="City identifier (default: 'delhi').")] = "delhi",
    route_number: Annotated[Optional[str], Field(description="Optional bus route filter (e.g. '534' or 'TMS').")] = None
) -> str:
    """
    Fetches real-time bus arrivals and live GPS telemetry at a stop, including ETA in minutes,
    crowd occupancy, and an interactive micro-map link.
    """
    async with AsyncSessionLocal() as session:
        res = await ETAService.get_stop_eta(session, city, stop_id, route_number)
        return json.dumps(res.model_dump(), indent=2)

@mcp.tool(
    name="plan_transit_trip",
    title="Plan Transit Journey",
    description="Plans an optimal bus journey between two stops or colloquial landmarks, calculating travel time, transfers, and first/last-mile ride suggestions.",
    annotations=ToolAnnotations(
        title="Plan Transit Journey",
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False
    )
)
async def plan_transit_trip(
    origin: Annotated[str, Field(description="Starting stop ID or landmark name (e.g. 'Nehru Place' or 'DTC_NP_01').")],
    destination: Annotated[str, Field(description="Destination stop ID or landmark name (e.g. 'Kashmere Gate' or 'DTC_KG_01').")],
    city: Annotated[str, Field(description="City identifier (default: 'delhi').")] = "delhi",
    preference: Annotated[str, Field(description="Routing preference: 'fastest', 'ac_only', or 'cheapest'.")] = "fastest"
) -> str:
    """
    Plans an optimal bus journey between two stops or landmarks, calculating travel time, transfers,
    and first/last-mile suggestions.
    Preference can be: 'fastest', 'ac_only', or 'cheapest'.
    """
    async with AsyncSessionLocal() as session:
        res = await ETAService.plan_trip(session, city, origin, destination, preference)
        return json.dumps(res.model_dump(), indent=2)

@mcp.tool(
    name="get_fare_and_ticketing_info",
    title="Bus Fare Calculator & Concessions",
    description="Calculates official bus fares, verifies Pink Scheme free pass eligibility for female commuters, and provides on-board ticketing guidance without commercial checkout links.",
    annotations=ToolAnnotations(
        title="Bus Fare Calculator & Concessions",
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False
    )
)
async def get_fare_and_ticketing_info(
    from_stop: Annotated[str, Field(description="Origin bus stop name or ID.")],
    to_stop: Annotated[str, Field(description="Destination bus stop name or ID.")],
    route_number: Annotated[str, Field(description="Bus route number (e.g. '534').")] = "534",
    city: Annotated[str, Field(description="City identifier (default: 'delhi').")] = "delhi",
    passenger_category: Annotated[str, Field(description="Passenger category: 'general', 'woman', 'senior_citizen', 'student'. Note: women travel 100% free under Delhi Pink Scheme.")] = "general"
) -> str:
    """
    Calculates official bus fares, checks concession eligibility (e.g., Delhi Pink Ticket free for women),
    and explains on-board conductor and smart card ticketing methods.
    passenger_category can be: 'general', 'woman', 'senior_citizen', 'student'.
    """
    res = ETAService.get_fare_details(city, route_number, from_stop, to_stop, passenger_category)
    return json.dumps(res.model_dump(), indent=2)

@mcp.tool(
    name="suggest_colloquial_tag",
    title="Suggest Colloquial Stop Tag",
    description="Registers a new crowdsourced landmark nickname or colloquial name for a transit stop in the public database.",
    annotations=ToolAnnotations(
        title="Suggest Colloquial Stop Tag",
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=False,
        open_world_hint=False
    )
)
async def suggest_colloquial_tag(
    stop_id: Annotated[str, Field(description="Target official GTFS stop ID (e.g. 'DTC_KG_01').")],
    tag: Annotated[str, Field(description="Colloquial tag or landmark nickname (e.g. 'Old Kashmere Gate Bus Stand').")],
    city: Annotated[str, Field(description="City identifier (default: 'delhi').")] = "delhi",
    language: Annotated[str, Field(description="Tag language: 'en', 'hi', or 'hinglish'.")] = "en",
    category: Annotated[str, Field(description="Category: 'landmark', 'local_name', 'metro_gate', 'junction'.")] = "landmark"
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

@mcp.tool(
    name="vote_stop_tag",
    title="Vote on Colloquial Stop Tag",
    description="Upvotes or downvotes an existing crowdsourced colloquial stop tag to boost accurate aliases and suppress spam.",
    annotations=ToolAnnotations(
        title="Vote on Colloquial Stop Tag",
        read_only_hint=False,
        destructive_hint=False,
        idempotent_hint=False,
        open_world_hint=False
    )
)
async def vote_stop_tag(
    tag_id: Annotated[str, Field(description="Unique ID of the colloquial stop tag.")],
    vote_type: Annotated[str, Field(description="Vote direction: 'upvote' or 'downvote'.")] = "upvote"
) -> str:
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

@mcp.tool(
    name="list_stop_tags",
    title="List Stop Colloquial Tags",
    description="Lists all public colloquial aliases and community tags registered for a specific stop.",
    annotations=ToolAnnotations(
        title="List Stop Colloquial Tags",
        read_only_hint=True,
        destructive_hint=False,
        idempotent_hint=True,
        open_world_hint=False
    )
)
async def list_stop_tags(
    stop_id: Annotated[str, Field(description="Official transit stop ID to look up.")],
    city: Annotated[str, Field(description="City identifier (default: 'delhi').")] = "delhi"
) -> str:
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
