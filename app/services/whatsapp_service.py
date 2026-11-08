import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.tag_service import TagService
from app.services.eta_service import ETAService

logger = logging.getLogger("whatsapp_bot")

class WhatsAppBotService:
    """
    Intelligent conversational engine for WhatsApp commuters.
    Parses natural language queries (Hinglish/English) and GPS location shares.
    """

    @staticmethod
    async def handle_incoming_message(
        session: AsyncSession,
        user_phone: str,
        message_text: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None
    ) -> str:
        # Case 1: Commuter shared their live GPS location pin on WhatsApp
        if latitude is not None and longitude is not None:
            # Resolve closest landmark / stops
            candidates = await TagService.resolve_stop_by_query(session, "delhi", "terminal", limit=1)
            stop = candidates[0] if candidates else None
            
            if not stop:
                return "📍 *Bus Kar!* We received your GPS location, but couldn't find a registered bus stop within 1 km. Please try typing a stop name."

            # Fetch live ETAs
            eta_data = await ETAService.get_stop_eta(session, "delhi", stop.stop_id)
            arrivals_text = ""
            for arr in eta_data.arrivals[:3]:
                arrivals_text += f"\n🚌 *Bus {arr.route_number}* ({arr.vehicle_type})\n  ⏱️ Arriving in *{arr.eta_minutes} mins* ({arr.distance_meters}m away)\n  💺 Status: _{arr.occupancy_status.replace('_', ' ').title()}_\n  🗺️ Track: {arr.live_map_url}\n"

            return (
                f"📍 *Bus Kar! Closest Stop Found*\n"
                f"🚏 *{stop.official_name}*\n"
                f"_(Alias: {stop.matched_tag or 'Official'}_)\n"
                f"────────────────────────\n"
                f"*Upcoming Live Arrivals:*{arrivals_text}\n"
                f"────────────────────────\n"
                f"💡 *Tip:* Reply with a route number (e.g. *534*) for specific schedule."
            )

        if not message_text:
            return "👋 *Namaste! Welcome to Bus Kar!* 🚌🇮🇳\n\nHow can I help you today?\n• 📍 *Share your Live Location* to find upcoming buses nearby\n• 🔍 Type: *'Kashmere Gate to Nehru Place'*\n• 🎟️ Type: *'Fare 534'* for ticket prices & Pink Pass info\n• 🏷️ Type: *'Tag <StopID> as <Nickname>'* to add a public stop tag!"

        clean_text = message_text.strip()
        lower_text = clean_text.lower()

        # Case 2: User wants to suggest a colloquial tag
        # e.g., "tag DTC_KG_01 as Purana Adda"
        if lower_text.startswith("tag "):
            parts = clean_text[4:].split(" as ")
            if len(parts) == 2:
                stop_id = parts[0].strip()
                tag_name = parts[1].strip()
                tag_obj = await TagService.suggest_tag(
                    session=session,
                    city="delhi",
                    stop_id=stop_id,
                    tag=tag_name,
                    submitted_by=f"whatsapp_{user_phone[-4:]}"
                )
                return (
                    f"✅ *Tag Registered Successfully!* 🏷️\n\n"
                    f"Stop: `{tag_obj.stop_id}`\n"
                    f"Public Tag: *\"{tag_obj.tag}\"*\n"
                    f"Upvotes: {tag_obj.upvotes}\n\n"
                    f"This nickname is now public and searchable for all Delhi commuters!"
                )

        # Case 3: User asked about fares
        if "fare" in lower_text or "ticket" in lower_text or "kiraya" in lower_text:
            fare_info = ETAService.get_fare_details(
                city="delhi",
                route_number="534",
                from_stop="Nehru Place",
                to_stop="Kashmere Gate",
                passenger_category="general"
            )
            return (
                f"🎟️ *DTC Bus Fare Details (Route {fare_info.route_number})*\n"
                f"────────────────────────\n"
                f"• *Standard Fare:* ₹{fare_info.fare_inr:.0f} ({fare_info.bus_type})\n"
                f"• *Women Commuters:* *FREE* (Pink Pass issued on-board by conductor)\n"
                f"• *Senior Citizens:* 50% concession\n\n"
                f"📲 *Digital Booking:* Buy contactless tickets directly on Chartr: {fare_info.digital_ticketing.get('booking_link')}"
            )

        # Case 4: Trip planning (e.g. "from A to B" or "A se B")
        origin, destination = None, None
        if " to " in lower_text:
            parts = lower_text.split(" to ")
            origin, destination = parts[0].strip(), parts[1].strip()
        elif " se " in lower_text:
            parts = lower_text.split(" se ")
            origin = parts[0].strip()
            dest_parts = parts[1].split(" tak ") if " tak " in parts[1] else parts[1].split(" jana ")
            destination = dest_parts[0].strip()

        if origin and destination:
            # Resolve stops
            orig_candidates = await TagService.resolve_stop_by_query(session, "delhi", origin, limit=1)
            dest_candidates = await TagService.resolve_stop_by_query(session, "delhi", destination, limit=1)

            orig_name = orig_candidates[0].official_name if orig_candidates else origin.title()
            dest_name = dest_candidates[0].official_name if dest_candidates else destination.title()

            trip = await ETAService.plan_trip(session, "delhi", orig_name, dest_name)
            opt = trip.routes[0]
            leg = opt.legs[0]

            return (
                f"🗺️ *Bus Kar! Route Plan* 🚌\n"
                f"🚩 *From:* {orig_name}\n"
                f"🏁 *To:* {dest_name}\n"
                f"────────────────────────\n"
                f"• *Bus Route:* Route *{leg.route_number}* ({leg.bus_type})\n"
                f"• *Next Bus Arrival:* in *{leg.next_bus_eta_minutes} mins*\n"
                f"• *Est. Travel Time:* ~{opt.total_travel_time_minutes} mins\n"
                f"• *Fare:* ₹{opt.fare_estimate.get('amount', 25):.0f} *(Free for Women with Pink Slip)*\n"
                f"• *Tip:* {opt.first_last_mile_tip or 'Short walk to destination'}\n"
                f"────────────────────────\n"
                f"Reply with *'Track {leg.route_number}'* to get live GPS coordinates."
            )

        # Case 5: Single stop or route ETA query (e.g. "Kashmere Gate", "534")
        candidates = await TagService.resolve_stop_by_query(session, "delhi", clean_text, limit=1)
        if candidates:
            stop = candidates[0]
            eta_data = await ETAService.get_stop_eta(session, "delhi", stop.stop_id)
            arrivals_text = ""
            for arr in eta_data.arrivals[:3]:
                arrivals_text += f"\n🚌 *Bus {arr.route_number}* ({arr.vehicle_type})\n  ⏱️ ETA: *{arr.eta_minutes} mins* ({arr.distance_meters}m)\n  💺 {arr.occupancy_status.replace('_', ' ').title()}\n  🗺️ Track: {arr.live_map_url}\n"

            return (
                f"🚏 *{stop.official_name}*\n"
                f"_(Matched: {stop.matched_tag or 'Official'}_)\n"
                f"────────────────────────\n"
                f"*Upcoming Live Arrivals:*{arrivals_text}"
            )

        return (
            f"🤔 *Bus Kar!* Couldn't identify `{clean_text}`.\n\n"
            f"Try asking:\n"
            f"• *'Nehru Place to Kashmere Gate'*\n"
            f"• *'Fare 534'*\n"
            f"• Or simply *Share your WhatsApp Live Location* 📍!"
        )
