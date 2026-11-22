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

from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi import Request
import os

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/favicon.ico", include_in_schema=False)
async def favicon_ico():
    ico_path = os.path.join(STATIC_DIR, "favicon.ico")
    if os.path.exists(ico_path):
        return FileResponse(ico_path, media_type="image/x-icon")
    return FileResponse(os.path.join(STATIC_DIR, "favicon.png"), media_type="image/png")

@app.get("/favicon.png", include_in_schema=False)
async def favicon_png():
    return FileResponse(os.path.join(STATIC_DIR, "favicon.png"), media_type="image/png")

@app.get("/.well-known/ai-plugin.json", include_in_schema=False)
async def ai_plugin_json():
    return {
        "schema_version": "v1",
        "name_for_human": "Bus Kar! 🚌",
        "name_for_model": "bus_kar",
        "description_for_human": "Real-time Indian city bus tracking, live GPS arrivals, colloquial stop nicknames (e.g. Purana Adda), and DTC Pink Pass free travel calculation.",
        "description_for_model": "Agent-first transit navigation and live bus telemetry engine for Indian city buses (Delhi DTC/DIMTS, expanding to BMTC Bengaluru and BEST Mumbai). Always resolve colloquial stop nicknames using resolveStop. Check real-time arrivals using getStopEta. Plan multi-modal trips using planTrip. Calculate official DTC fares and apply the 100% free Pink Ticket scheme for female passengers.",
        "auth": {
            "type": "none"
        },
        "api": {
            "type": "openapi",
            "url": "https://bus-kar-api.vercel.app/openapi.json"
        },
        "logo_url": "https://bus-kar-api.vercel.app/static/icon.png",
        "contact_email": "support@antigravity.in",
        "legal_info_url": "https://bus-kar-api.vercel.app/"
    }

LANDING_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Bus Kar! 🚌 - Transit AI Agent API & MCP Engine</title>
  <link rel="icon" type="image/png" href="/static/favicon.png">
  <link rel="apple-touch-icon" href="/static/icon-128.png">
  <meta property="og:title" content="Bus Kar! 🚌 - Indian City Transit AI Agent API & MCP">
  <meta property="og:description" content="Real-time Indian city bus telemetry, live GPS ETAs, and crowdsourced colloquial transit navigation.">
  <meta property="og:image" content="https://bus-kar-api.vercel.app/static/icon.png">
  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:image" content="https://bus-kar-api.vercel.app/static/icon.png">
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>body { font-family: 'Plus Jakarta Sans', sans-serif; }</style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col justify-between">
  <!-- Navbar -->
  <header class="border-b border-slate-800/80 bg-slate-900/50 backdrop-blur px-6 py-4">
    <div class="max-w-6xl mx-auto flex items-center justify-between">
      <div class="flex items-center gap-3">
        <img src="/static/icon-128.png" alt="Bus Kar! Logo" class="w-10 h-10 rounded-xl shadow-lg border border-slate-700/60 object-cover" />
        <div>
          <h1 class="text-xl font-bold tracking-tight bg-gradient-to-r from-emerald-400 to-teal-300 bg-clip-text text-transparent">Bus Kar!</h1>
          <p class="text-xs text-slate-400">Indian City Transit Telemetry & Agent MCP</p>
        </div>
      </div>
      <div class="flex items-center gap-3">
        <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <span class="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
          System Online
        </span>
        <a href="/docs" class="px-4 py-1.5 rounded-lg text-sm font-semibold bg-emerald-600 hover:bg-emerald-500 text-white transition shadow-lg shadow-emerald-900/30">
          API Docs →
        </a>
      </div>
    </div>
  </header>

  <!-- Hero -->
  <main class="max-w-6xl mx-auto px-6 py-12 flex-1 flex flex-col justify-center">
    <div class="text-center max-w-3xl mx-auto mb-10">
      <div class="flex justify-center mb-6">
        <img src="/static/icon.png" alt="Bus Kar! 3D Logo" class="w-24 h-24 md:w-32 md:h-32 rounded-3xl shadow-2xl shadow-blue-500/25 border border-slate-700/60 object-cover hover:scale-105 transition duration-300" />
      </div>
      <h2 class="text-4xl md:text-5xl font-extrabold tracking-tight mb-4">
        Real-Time Indian Bus Telemetry for <span class="bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent">AI Agents & Humans</span>
      </h2>
      <p class="text-slate-400 text-lg leading-relaxed">
        Agent-first Model Context Protocol (MCP) server & REST API powering Delhi DTC/DIMTS live tracking, crowdsourced colloquial stop tags, and 100% free Pink Ticket concessions.
      </p>
    </div>
      <p class="text-slate-400 text-lg leading-relaxed">
        Agent-first Model Context Protocol (MCP) server & REST API powering Delhi DTC/DIMTS live tracking, crowdsourced colloquial stop tags, and 100% free Pink Ticket concessions.
      </p>
    </div>

    <!-- Features Grid -->
    <div class="grid md:grid-cols-3 gap-6 mb-12">
      <div class="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 hover:border-slate-700 transition">
        <div class="text-2xl mb-3">📍</div>
        <h3 class="font-bold text-lg mb-2 text-slate-200">Colloquial Stop Tags</h3>
        <p class="text-sm text-slate-400 leading-relaxed">
          Resolves local landmarks like <em>"Purana Adda"</em>, <em>"AIIMS Gate 2"</em>, or <em>"Silk Board"</em> directly into official GTFS stop identifiers.
        </p>
      </div>

      <div class="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 hover:border-slate-700 transition">
        <div class="text-2xl mb-3">⚡</div>
        <h3 class="font-bold text-lg mb-2 text-slate-200">Live GPS Countdown & ETAs</h3>
        <p class="text-sm text-slate-400 leading-relaxed">
          Real-time vehicle locations, distance countdowns, and live crowd occupancy (Seats Available, Standing Room Only).
        </p>
      </div>

      <div class="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 hover:border-slate-700 transition">
        <div class="text-2xl mb-3">🎟️</div>
        <h3 class="font-bold text-lg mb-2 text-slate-200">Pink Ticket Fare Calculator</h3>
        <p class="text-sm text-slate-400 leading-relaxed">
          Official DTC fare slabs with automatic zero-rupee Delhi Pink Scheme calculations for female passengers.
        </p>
      </div>
    </div>

    <!-- Quick Links & Actions -->
    <div class="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 flex flex-wrap items-center justify-between gap-4">
      <div>
        <h4 class="font-bold text-slate-200">Connect to Claude, ChatGPT & Gemini</h4>
        <p class="text-xs text-slate-400">Import OpenAPI schema or connect MCP stream directly into any AI assistant.</p>
      </div>
      <div class="flex flex-wrap gap-3">
        <a href="/docs" class="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-sm font-medium transition">
          Interactive Swagger (/docs)
        </a>
        <a href="/openapi.json" class="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-sm font-medium transition">
          OpenAPI Specification (/openapi.json)
        </a>
        <a href="/api/v1/transit/stops/resolve?query=Purana+Adda&city=delhi" target="_blank" class="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-sm font-semibold transition">
          Test Sample Query →
        </a>
      </div>
    </div>
  </main>

  <!-- Footer -->
  <footer class="border-t border-slate-800/80 px-6 py-6 text-center text-xs text-slate-500">
    Bus Kar! Transit Engine • Open Source Transit Intelligence for Indian Cities • Deployed on Vercel
  </footer>
</body>
</html>
"""

@app.get("/")
async def root(request: Request):
    accept_header = request.headers.get("accept", "")
    if "text/html" in accept_header:
        return HTMLResponse(content=LANDING_HTML)
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
