from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
import os

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
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await seed_initial_data()
    except Exception as e:
        print(f"Database initialization warning in lifespan: {e}")
    yield
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

# Mount MCP Server over SSE
try:
    from mcp.server.transport_security import TransportSecuritySettings
    mcp_security = TransportSecuritySettings(enable_dns_rebinding_protection=False)
    mcp_app = mcp.sse_app(transport_security=mcp_security, host="0.0.0.0")
except Exception:
    mcp_app = mcp.sse_app(host="0.0.0.0")

app.mount("/mcp", mcp_app)

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
        "description_for_model": "Agent-first transit navigation and live bus telemetry engine for Indian city buses (Delhi DTC/DIMTS, expanding to BMTC Bengaluru and BEST Mumbai). Always resolve colloquial stop nicknames using resolveStop. Check real-time arrivals using getLiveBusEta. Plan multi-modal trips using planTransitTrip. Calculate official DTC fares and apply the 100% free Pink Ticket scheme for female passengers using getFareAndTicketing. Register new community nicknames using suggestColloquialTag.",
        "auth": {
            "type": "none"
        },
        "api": {
            "type": "openapi",
            "url": "https://bus-kar-api.vercel.app/openapi.json"
        },
        "logo_url": "https://bus-kar-api.vercel.app/static/icon.png",
        "contact_email": "contactus@touchstonelabs.ai",
        "legal_info_url": "https://bus-kar-api.vercel.app/privacy"
    }

# -------------------------------------------------------------
# HTML TEMPLATES (Dark Theme, Tailwind CSS, Responsive)
# -------------------------------------------------------------

NAVBAR_HTML = """
  <header class="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur sticky top-0 z-50 px-6 py-4">
    <div class="max-w-6xl mx-auto flex items-center justify-between">
      <a href="/" class="flex items-center gap-3">
        <img src="/static/icon-128.png" alt="Bus Kar! Logo" class="w-9 h-9 rounded-xl shadow-lg border border-slate-700/60 object-cover" />
        <div>
          <span class="text-xl font-bold tracking-tight bg-gradient-to-r from-emerald-400 to-teal-300 bg-clip-text text-transparent">Bus Kar!</span>
          <span class="text-xs text-slate-400 block -mt-0.5">Indian Transit Agent API</span>
        </div>
      </a>
      <nav class="hidden md:flex items-center gap-6 text-sm text-slate-300">
        <a href="/" class="hover:text-emerald-400 transition">Home</a>
        <a href="/about" class="hover:text-emerald-400 transition">About & Publisher</a>
        <a href="/support" class="hover:text-emerald-400 transition">Support</a>
        <a href="/privacy" class="hover:text-emerald-400 transition">Privacy</a>
        <a href="/terms" class="hover:text-emerald-400 transition">Terms</a>
      </nav>
      <div class="flex items-center gap-3">
        <a href="/docs" class="px-4 py-1.5 rounded-lg text-sm font-semibold bg-emerald-600 hover:bg-emerald-500 text-white transition shadow-lg shadow-emerald-900/30">
          API Docs →
        </a>
      </div>
    </div>
  </header>
"""

FOOTER_HTML = """
  <footer class="border-t border-slate-800/80 bg-slate-950 px-6 py-8 text-center text-xs text-slate-400">
    <div class="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
      <div class="flex items-center gap-2">
        <img src="/static/icon-128.png" alt="Bus Kar! Logo" class="w-5 h-5 rounded" />
        <span class="font-semibold text-slate-300">Bus Kar!</span>
        <span>• Published by <strong>Bus Kar! Team</strong> / <strong>Touchstone Labs</strong></span>
      </div>
      <div class="flex flex-wrap justify-center gap-4 text-slate-400">
        <a href="/" class="hover:text-white transition">Home</a>
        <a href="/about" class="hover:text-white transition">About & Publisher</a>
        <a href="/support" class="hover:text-white transition">Support</a>
        <a href="/privacy" class="hover:text-white transition">Privacy Policy</a>
        <a href="/terms" class="hover:text-white transition">Terms of Service</a>
        <a href="/docs" class="hover:text-white transition">Swagger API</a>
        <a href="/openapi.json" class="hover:text-white transition">OpenAPI Schema</a>
      </div>
      <p class="text-slate-500">© 2026 Touchstone Labs. Open Source Transit Intelligence.</p>
    </div>
  </footer>
"""

LANDING_HTML = f"""<!DOCTYPE html>
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
  <style>body {{ font-family: 'Plus Jakarta Sans', sans-serif; }}</style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col justify-between">
  {NAVBAR_HTML}

  <!-- Hero -->
  <main class="max-w-6xl mx-auto px-6 py-12 flex-1 flex flex-col justify-center">
    <div class="text-center max-w-3xl mx-auto mb-10">
      <div class="flex justify-center mb-6">
        <img src="/static/icon.png" alt="Bus Kar! 3D Logo" class="w-28 h-28 md:w-36 md:h-36 rounded-3xl shadow-2xl shadow-blue-500/25 border border-slate-700/60 object-cover hover:scale-105 transition duration-300" />
      </div>
      <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 mb-4">
        <span class="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
        Official Public Transit Telemetry API & Verified MCP Server
      </div>
      <h1 class="text-4xl md:text-5xl font-extrabold tracking-tight mb-4 text-white">
        Real-Time Indian Bus Telemetry for <span class="bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent">AI Agents & Humans</span>
      </h1>
      <p class="text-slate-300 text-lg leading-relaxed">
        Agent-first Model Context Protocol (MCP) server & REST API powering Delhi DTC/DIMTS live tracking, crowdsourced colloquial stop tags, and 100% free Pink Ticket concessions.
      </p>
    </div>

    <!-- Publisher Verification Card -->
    <div class="bg-gradient-to-br from-slate-900/90 to-slate-900/40 border border-slate-800 rounded-2xl p-6 md:p-8 mb-10 shadow-xl">
      <div class="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-slate-800 pb-5 mb-5">
        <div>
          <div class="flex items-center gap-2">
            <span class="text-lg">🏛️</span>
            <h2 class="text-lg font-bold text-white">Verified Publisher & Organization Identity</h2>
            <span class="px-2.5 py-0.5 rounded text-[11px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">Verified</span>
          </div>
          <p class="text-xs text-slate-400 mt-1">Proof of official domain, publisher entity, and open source stewardship for ChatGPT & Claude integrations.</p>
        </div>
        <a href="/about" class="text-xs font-semibold text-emerald-400 hover:text-emerald-300 flex items-center gap-1">
          Full Publisher Details →
        </a>
      </div>

      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
        <div class="p-3 bg-slate-950/60 rounded-xl border border-slate-800/80">
          <span class="text-slate-500 block mb-1">Publisher Name</span>
          <span class="font-bold text-slate-200">Bus Kar! Team</span>
        </div>
        <div class="p-3 bg-slate-950/60 rounded-xl border border-slate-800/80">
          <span class="text-slate-500 block mb-1">Organization / Studio</span>
          <span class="font-bold text-slate-200">Touchstone Labs</span>
        </div>
        <div class="p-3 bg-slate-950/60 rounded-xl border border-slate-800/80">
          <span class="text-slate-500 block mb-1">Lead Maintainer</span>
          <span class="font-bold text-slate-200">Mdsam464</span>
        </div>
        <div class="p-3 bg-slate-950/60 rounded-xl border border-slate-800/80">
          <span class="text-slate-500 block mb-1">Official Host Domain</span>
          <span class="font-bold text-emerald-400">bus-kar-api.vercel.app</span>
        </div>
      </div>
    </div>

    <!-- Features Grid -->
    <div class="grid md:grid-cols-3 gap-6 mb-10">
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
        <a href="/mcp/sse" class="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-sm font-medium transition">
          MCP SSE Stream (/mcp/sse)
        </a>
        <a href="/api/v1/transit/stops/resolve?query=Purana+Adda&city=delhi" target="_blank" class="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-sm font-semibold transition">
          Test Sample Query →
        </a>
      </div>
    </div>
  </main>

  {FOOTER_HTML}
</body>
</html>
"""

ABOUT_HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>About & Publisher Verification - Bus Kar! 🚌</title>
  <link rel="icon" type="image/png" href="/static/favicon.png">
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>body {{ font-family: 'Plus Jakarta Sans', sans-serif; }}</style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col justify-between">
  {NAVBAR_HTML}

  <main class="max-w-4xl mx-auto px-6 py-12 flex-1">
    <div class="bg-slate-900/60 border border-slate-800 rounded-3xl p-8 md:p-12 shadow-xl">
      <div class="flex items-center gap-3 mb-4">
        <span class="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          Official Service & Publisher Profile
        </span>
      </div>
      <h1 class="text-3xl font-extrabold mb-4 text-white">About Bus Kar! & Verified Publisher</h1>
      <p class="text-slate-300 text-sm leading-relaxed mb-8">
        Bus Kar! is an open, agent-first transit navigation and live bus telemetry engine tailored specifically for Indian city bus transit networks. It bridges real-time vehicle positions with local, cultural, and colloquial Indian commuting reality.
      </p>

      <div class="space-y-8 text-slate-300 text-sm leading-relaxed">
        <section class="bg-slate-950/70 border border-slate-800 rounded-2xl p-6">
          <h2 class="text-base font-bold text-white mb-4 flex items-center gap-2">
            <span>🏛️</span> Publisher & Organization Details (Proof of Service)
          </h2>
          <dl class="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div>
              <dt class="text-slate-500 mb-1">Publisher Name</dt>
              <dd class="font-bold text-slate-200 text-sm">Bus Kar! Team</dd>
            </div>
            <div>
              <dt class="text-slate-500 mb-1">Parent Organization / Studio</dt>
              <dd class="font-bold text-slate-200 text-sm">Touchstone Labs (Vercel team: touchstone-labs)</dd>
            </div>
            <div>
              <dt class="text-slate-500 mb-1">Lead Maintainer</dt>
              <dd class="font-bold text-slate-200 text-sm">Mdsam464 (<a href="https://github.com/Mdsam464" class="text-emerald-400 hover:underline" target="_blank">github.com/Mdsam464</a>)</dd>
            </div>
            <div>
              <dt class="text-slate-500 mb-1">Verified Web Host & API Domain</dt>
              <dd class="font-bold text-emerald-400 text-sm">https://bus-kar-api.vercel.app</dd>
            </div>
            <div>
              <dt class="text-slate-500 mb-1">Official Support & Developer Contact</dt>
              <dd class="font-bold text-slate-200 text-sm"><a href="mailto:contactus@touchstonelabs.ai" class="text-emerald-400 hover:underline">contactus@touchstonelabs.ai</a></dd>
            </div>
            <div>
              <dt class="text-slate-500 mb-1">Open Source Repository</dt>
              <dd class="font-bold text-slate-200 text-sm"><a href="https://github.com/Mdsam464/bus-kar-api" class="text-emerald-400 hover:underline" target="_blank">github.com/Mdsam464/bus-kar-api</a></dd>
            </div>
          </dl>
        </section>

        <section>
          <h2 class="text-lg font-semibold text-white mb-2">1. Our Core Mission</h2>
          <p>
            Commuters in Indian cities don't search for "Stop 7283A"; they ask for <em>"Purana Adda"</em>, <em>"AIIMS Gate 2"</em>, or <em>"Flyover ke neeche"</em>. Bus Kar! provides an intelligent alias resolution layer that translates these informal nicknames directly into official General Transit Feed Specification (GTFS) stop IDs, connects them to real-time live GPS telemetry, and computes route planning and fair calculations.
          </p>
        </section>

        <section>
          <h2 class="text-lg font-semibold text-white mb-2">2. Social Inclusion: Delhi Pink Scheme</h2>
          <p>
            Public transit policy in Delhi makes bus travel 100% free for all female commuters via the Delhi Government Pink Ticket scheme. Bus Kar! is designed to affirmatively promote this scheme across all AI agent interactions—automatically calculating zero-rupee fares and educating passengers that single-journey Pink Tickets are issued on-board by the bus conductor without pre-booking fees.
          </p>
        </section>

        <section>
          <h2 class="text-lg font-semibold text-white mb-2">3. Telemetry Sources & Data Providers</h2>
          <p>
            Real-time vehicle telemetry, route schedules, and stop coordinates are ingested from authoritative open transit authorities including the <strong>Delhi Open Transit Data (OTD)</strong> portal, <strong>Delhi Transport Corporation (DTC)</strong>, and <strong>Delhi Integrated Multi-Modal Transit System (DIMTS)</strong>.
          </p>
        </section>

        <section>
          <h2 class="text-lg font-semibold text-white mb-2">4. AI Agent & MCP Integration</h2>
          <p>
            Bus Kar! is built natively as both an OpenAPI 3.1 REST service and an Anthropic Model Context Protocol (MCP) server over Server-Sent Events (SSE). It powers Custom GPTs on OpenAI ChatGPT, desktop MCP integrations on Claude, and function calling tools on Google Gemini.
          </p>
        </section>
      </div>
    </div>
  </main>

  {FOOTER_HTML}
</body>
</html>
"""

TERMS_HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Terms of Service - Bus Kar! 🚌</title>
  <link rel="icon" type="image/png" href="/static/favicon.png">
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>body {{ font-family: 'Plus Jakarta Sans', sans-serif; }}</style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col justify-between">
  {NAVBAR_HTML}

  <main class="max-w-4xl mx-auto px-6 py-12 flex-1">
    <div class="bg-slate-900/60 border border-slate-800 rounded-3xl p-8 md:p-12 shadow-xl">
      <h1 class="text-3xl font-extrabold mb-2 text-white">Terms of Service</h1>
      <p class="text-sm text-slate-400 mb-8">Effective Date: November 22, 2026</p>

      <div class="space-y-6 text-slate-300 text-sm leading-relaxed">
        <section>
          <h2 class="text-lg font-semibold text-white mb-2">1. Acceptance of Terms</h2>
          <p>By accessing or integrating with the <strong>Bus Kar!</strong> API, web services, Model Context Protocol (MCP) server, or AI agent Actions (collectively, the "Service"), provided by the <strong>Bus Kar! Team</strong> and <strong>Touchstone Labs</strong>, you agree to comply with and be bound by these Terms of Service.</p>
        </section>

        <section>
          <h2 class="text-lg font-semibold text-white mb-2">2. Description of Service</h2>
          <p>Bus Kar! provides open transit telemetry, live vehicle arrivals, trip planning, fare calculations, and crowdsourced colloquial transit stop resolution for Indian city buses (including Delhi DTC/DIMTS, BMTC, and BEST). The Service is made freely available for commuters, developers, and autonomous AI agents.</p>
        </section>

        <section>
          <h2 class="text-lg font-semibold text-white mb-2">3. Acceptable Use & AI Integration</h2>
          <p>You may use the Service to build AI agent workflows, mobile transit applications, and personal navigation utilities. You agree not to misuse, DDoS, flood, or intentionally degrade the Service through automated abuse.</p>
        </section>

        <section>
          <h2 class="text-lg font-semibold text-white mb-2">4. Live Transit Telemetry & Accuracy Disclaimer</h2>
          <p>Real-time transit telemetry (vehicle locations, estimated arrival countdowns, crowd occupancy) is aggregated from public feeds and live GPS sensors. While we strive for high precision, ETAs are estimates subject to real-world traffic, weather, road diversions, and transit agency scheduling changes. Bus Kar! provides telemetry on an "as-is" and "as-available" basis without warranties of uninterrupted transit operations.</p>
        </section>

        <section>
          <h2 class="text-lg font-semibold text-white mb-2">5. Delhi Pink Scheme & Fare Calculations</h2>
          <p>Fare calculations are based on official published transit authority tariffs (e.g., Delhi Transport Corporation non-AC and AC fare slabs). Under the Delhi Government Pink Pass initiative, female passengers travel 100% free with tickets issued on-board by the conductor. Bus Kar! does not process monetary payments or charge convenience fees for transit tickets.</p>
        </section>

        <section>
          <h2 class="text-lg font-semibold text-white mb-2">6. Crowdsourced Colloquial Stop Submissions</h2>
          <p>Users may suggest colloquial nicknames and landmarks for official transit stops. By submitting a tag, you grant Bus Kar! an irrevocable, royalty-free, perpetual license to incorporate the tag into the public stop alias database for the benefit of all commuters.</p>
        </section>

        <section>
          <h2 class="text-lg font-semibold text-white mb-2">7. Publisher Information & Governing Entity</h2>
          <p>Bus Kar! is maintained by the <strong>Bus Kar! Team</strong> under organization <strong>Touchstone Labs</strong>, lead maintainer <strong>Mdsam464</strong>. Questions regarding these Terms may be directed to <a href="mailto:contactus@touchstonelabs.ai" class="text-emerald-400 underline">contactus@touchstonelabs.ai</a>.</p>
        </section>
      </div>
    </div>
  </main>

  {FOOTER_HTML}
</body>
</html>
"""

SUPPORT_HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Support & Developer Desk - Bus Kar! 🚌</title>
  <link rel="icon" type="image/png" href="/static/favicon.png">
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>body {{ font-family: 'Plus Jakarta Sans', sans-serif; }}</style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col justify-between">
  {NAVBAR_HTML}

  <main class="max-w-4xl mx-auto px-6 py-12 flex-1">
    <div class="bg-slate-900/60 border border-slate-800 rounded-3xl p-8 md:p-12 shadow-xl">
      <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 mb-4">
        Support & Developer Desk
      </div>
      <h1 class="text-3xl font-extrabold mb-4 text-white">How Can We Help You?</h1>
      <p class="text-slate-300 text-sm leading-relaxed mb-8">
        Need assistance integrating Bus Kar! with your ChatGPT Custom GPT, Claude MCP client, or mobile application? We are here to help.
      </p>

      <div class="grid md:grid-cols-2 gap-6 mb-8 text-sm">
        <div class="bg-slate-950/70 border border-slate-800 rounded-2xl p-6">
          <div class="text-2xl mb-2">✉️</div>
          <h2 class="font-bold text-white mb-1">Direct Support Email</h2>
          <p class="text-xs text-slate-400 mb-3">For publisher inquiries, bug reports, or partnership questions.</p>
          <a href="mailto:contactus@touchstonelabs.ai" class="text-emerald-400 font-semibold hover:underline">contactus@touchstonelabs.ai</a>
        </div>

        <div class="bg-slate-950/70 border border-slate-800 rounded-2xl p-6">
          <div class="text-2xl mb-2">💻</div>
          <h2 class="font-bold text-white mb-1">GitHub Issues & Community</h2>
          <p class="text-xs text-slate-400 mb-3">Report technical API anomalies, request city expansions, or submit PRs.</p>
          <a href="https://github.com/Mdsam464/bus-kar-api/issues" class="text-emerald-400 font-semibold hover:underline" target="_blank">github.com/Mdsam464/bus-kar-api/issues →</a>
        </div>
      </div>

      <div class="space-y-6 text-slate-300 text-sm leading-relaxed border-t border-slate-800 pt-8">
        <h2 class="text-lg font-semibold text-white">Frequently Asked Questions</h2>
        
        <div class="bg-slate-950/40 rounded-xl p-4 border border-slate-800/80">
          <h3 class="font-bold text-white mb-1">How do I connect Bus Kar! to my ChatGPT Custom GPT?</h3>
          <p class="text-xs text-slate-400">In the ChatGPT GPT Editor, go to Actions $\rightarrow$ Create new action $\rightarrow$ Import from URL $\rightarrow$ enter <code>https://bus-kar-api.vercel.app/openapi.json</code>. Set Authentication to None and Privacy Policy to <code>https://bus-kar-api.vercel.app/privacy</code>.</p>
        </div>

        <div class="bg-slate-950/40 rounded-xl p-4 border border-slate-800/80">
          <h3 class="font-bold text-white mb-1">Where is the Model Context Protocol (MCP) SSE endpoint?</h3>
          <p class="text-xs text-slate-400">Bus Kar! streams native MCP over Server-Sent Events (SSE) at <code>https://bus-kar-api.vercel.app/mcp/sse</code>. You can configure it directly in your Claude Desktop or remote agent configuration.</p>
        </div>

        <div class="bg-slate-950/40 rounded-xl p-4 border border-slate-800/80">
          <h3 class="font-bold text-white mb-1">Why is bus travel free for women in Delhi?</h3>
          <p class="text-xs text-slate-400">Under the Delhi Government Pink Ticket scheme, all female commuters travel 100% free on DTC and DIMTS buses with single-journey zero-rupee tickets issued on-board by conductors. Our API automatically applies this concession.</p>
        </div>
      </div>
    </div>
  </main>

  {FOOTER_HTML}
</body>
</html>
"""

PRIVACY_HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Privacy Policy - Bus Kar! 🚌</title>
  <link rel="icon" type="image/png" href="/static/favicon.png">
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>body {{ font-family: 'Plus Jakarta Sans', sans-serif; }}</style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col justify-between">
  {NAVBAR_HTML}

  <main class="max-w-4xl mx-auto px-6 py-12 flex-1">
    <div class="bg-slate-900/60 border border-slate-800 rounded-3xl p-8 md:p-12 shadow-xl">
      <h1 class="text-3xl font-extrabold mb-2 text-white">Privacy Policy</h1>
      <p class="text-sm text-slate-400 mb-8">Effective Date: November 22, 2026</p>

      <div class="space-y-6 text-slate-300 text-sm leading-relaxed">
        <section>
          <h2 class="text-lg font-semibold text-white mb-2">1. Overview & Publisher Information</h2>
          <p>Bus Kar! ("we", "our", or "the service") is an agent-first open public transit API and Model Context Protocol (MCP) server providing real-time telemetry, trip routing, and colloquial stop resolution for Indian city buses. Bus Kar! is developed and published by the <strong>Bus Kar! Team</strong> under organization <strong>Touchstone Labs</strong> (Vercel team: <code>touchstone-labs</code>), lead-maintained by <strong>Mdsam464</strong> (<a href="https://github.com/Mdsam464/bus-kar-api" class="text-emerald-400 underline" target="_blank">github.com/Mdsam464/bus-kar-api</a>). We respect your privacy and are committed to transparent data practices.</p>
        </section>

        <section>
          <h2 class="text-lg font-semibold text-white mb-2">2. Information We Do NOT Collect</h2>
          <p>Bus Kar! does <strong>not</strong> collect, require, sell, or store Personally Identifiable Information (PII) such as your full name, email address, physical home address, government ID, or financial payment details.</p>
        </section>

        <section>
          <h2 class="text-lg font-semibold text-white mb-2">3. Transit Telemetry & Location Data</h2>
          <p>When you query bus arrivals or plan journeys:
            <ul class="list-disc pl-5 mt-2 space-y-1 text-slate-400">
              <li>Transit queries (stop IDs, landmarks, route numbers) are processed in-memory to calculate distances, ETAs, and fare estimates.</li>
              <li>GPS coordinates provided to locate nearby stops are processed ephemerally and are never logged, tracked, or associated with user identities.</li>
            </ul>
          </p>
        </section>

        <section>
          <h2 class="text-lg font-semibold text-white mb-2">4. Crowdsourced Colloquial Stop Nicknames</h2>
          <p>Community stop tags submitted by users (e.g. colloquial landmark nicknames like "Purana Adda" or "AIIMS Gate 2") are stored publicly in our transit alias database to assist other commuters. Submissions do not record personal account data.</p>
        </section>

        <section>
          <h2 class="text-lg font-semibold text-white mb-2">5. Third-Party AI Platforms & Data Sources</h2>
          <p>Bus Kar! integrates with OpenAI ChatGPT, Anthropic Claude, and Google Gemini via Model Context Protocol (MCP) and OpenAPI Actions. Queries passed from these platforms are subject to their respective privacy terms. Open transit vehicle data is sourced from public transit authorities including Delhi Open Transit Data (OTD), DTC, and DIMTS.</p>
        </section>

        <section>
          <h2 class="text-lg font-semibold text-white mb-2">6. Contact & Open Source</h2>
          <p>For questions or privacy inquiries, contact the Bus Kar! project maintainers via email at <a href="mailto:contactus@touchstonelabs.ai" class="text-emerald-400 underline">contactus@touchstonelabs.ai</a> or visit our open-source repository at <a href="https://github.com/Mdsam464/bus-kar-api" class="text-emerald-400 underline" target="_blank">github.com/Mdsam464/bus-kar-api</a>.</p>
        </section>
      </div>
    </div>
  </main>

  {FOOTER_HTML}
</body>
</html>
"""

# -------------------------------------------------------------
# ROUTES: Homepage, About, Privacy, Terms, Support
# -------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """
    Returns the public website HTML landing page by default.
    Only returns JSON if requested explicitly via ?format=json or Accept: application/json without text/html.
    """
    accept_header = request.headers.get("accept", "")
    format_param = request.query_params.get("format", "")
    if format_param == "json" or ("application/json" in accept_header and "text/html" not in accept_header):
        return JSONResponse(content={
            "service": settings.app_name,
            "status": "online",
            "publisher": "Bus Kar! Team",
            "organization": "Touchstone Labs (touchstone-labs)",
            "maintainer": "Mdsam464",
            "website": "https://bus-kar-api.vercel.app",
            "about_url": "https://bus-kar-api.vercel.app/about",
            "privacy_url": "https://bus-kar-api.vercel.app/privacy",
            "terms_url": "https://bus-kar-api.vercel.app/terms",
            "support_url": "https://bus-kar-api.vercel.app/support",
            "repository": "https://github.com/Mdsam464/bus-kar-api",
            "city": "Delhi (DTC / DIMTS)",
            "docs_url": "/docs",
            "openapi_url": "/openapi.json",
            "mcp_enabled": True,
            "mcp_endpoint": "/mcp/sse",
            "features": [
                "Colloquial stop resolution with crowdsourced public tags",
                "Real-time GTFS-RT bus ETAs & live tracking links",
                "Multi-modal trip planning & first/last-mile suggestions",
                "DTC fare calculator with Pink Scheme free pass rules"
            ]
        })
    return HTMLResponse(content=LANDING_HTML)

@app.get("/about", response_class=HTMLResponse, include_in_schema=False)
async def about():
    return HTMLResponse(content=ABOUT_HTML)

@app.get("/privacy", response_class=HTMLResponse, include_in_schema=False)
async def privacy():
    return HTMLResponse(content=PRIVACY_HTML)

@app.get("/terms", response_class=HTMLResponse, include_in_schema=False)
async def terms():
    return HTMLResponse(content=TERMS_HTML)

@app.get("/support", response_class=HTMLResponse, include_in_schema=False)
async def support():
    return HTMLResponse(content=SUPPORT_HTML)

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=settings.debug)
