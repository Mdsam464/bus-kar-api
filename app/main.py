from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from app.config import settings
from app.database import engine, Base, AsyncSessionLocal
from app.models.gtfs import GTFSStop, GTFSRoute
from app.models.stop_tag import StopTag
from app.services.delhi_otd import DELHI_SEED_STOPS, DELHI_SEED_ROUTES
from app.services.tag_service import normalize_text
from app.routers.transit import router as transit_router
from app.routers.tags import router as tags_router
from app.routers.whatsapp import router as whatsapp_router
from app.mcp_server import mcp

async def seed_initial_data():
    """Populates initial Delhi GTFS stops, routes, and community tags if empty."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(GTFSStop))
        if not result.scalars().first():
            print("Seeding initial Delhi transit stops & colloquial tags...")
            # Add stops & tags
            for stop_data in DELHI_SEED_STOPS:
                stop = GTFSStop(
                    stop_id=stop_data["stop_id"],
                    city=stop_data["city"],
                    stop_name=stop_data["stop_name"],
                    stop_desc=stop_data["stop_desc"],
                    stop_lat=stop_data["stop_lat"],
                    stop_lon=stop_data["stop_lon"]
                )
                session.add(stop)

                for tag_item in stop_data["tags"]:
                    tag = StopTag(
                        stop_id=stop_data["stop_id"],
                        city=stop_data["city"],
                        tag=tag_item["tag"],
                        tag_normalized=normalize_text(tag_item["tag"]),
                        category=tag_item.get("category", "landmark"),
                        upvotes=tag_item.get("upvotes", 1),
                        status="public",
                        submitted_by="system_seed"
                    )
                    session.add(tag)

            # Add routes
            for route_data in DELHI_SEED_ROUTES:
                route = GTFSRoute(
                    route_id=route_data["route_id"],
                    city=route_data["city"],
                    route_short_name=route_data["route_short_name"],
                    route_long_name=route_data["route_long_name"],
                    bus_type=route_data["bus_type"]
                )
                session.add(route)

            await session.commit()
            print("Transit database seeded successfully!")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create DB tables and seed
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await seed_initial_data()
    except Exception as e:
        print(f"Database initialization warning in lifespan: {e}")
    yield
    # Shutdown
    try:
        await engine.dispose()
    except Exception:
        pass

app = FastAPI(
    title="Bus Kar! 🚌",
    version="1.0.0",
    description="Bus Kar! - Agent-First Transit API and Model Context Protocol (MCP) server for Indian City Bus Telemetry & Crowdsourced Colloquial Stops.",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(transit_router)
app.include_router(tags_router)
app.include_router(whatsapp_router)

# Mount MCP Server over SSE for OpenAI and remote AI agent integrations
app.mount("/mcp", mcp.sse_app())

@app.get("/")
async def root():
    return {
        "service": settings.app_name,
        "status": "online",
        "city": "Delhi (DTC / DIMTS)",
        "docs_url": "/docs",
        "mcp_enabled": True,
        "features": [
            "Colloquial stop resolution with crowdsourced public tags",
            "Real-time GTFS-RT bus ETAs & live tracking links",
            "Multi-modal trip planning & first/last-mile suggestions",
            "DTC fare calculator with Pink Scheme free pass rules"
        ]
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=settings.debug)
