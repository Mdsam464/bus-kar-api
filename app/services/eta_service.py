from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.gtfs import GTFSStop, GTFSRoute
from app.services.delhi_otd import DelhiOTDService, DELHI_SEED_ROUTES
from app.schemas.transit import StopETAResponse, TripPlanResponse, TripOption, TripLeg, FareInfoResponse, ConcessionInfo

class ETAService:
    @staticmethod
    async def get_stop_eta(
        session: AsyncSession, 
        city: str, 
        stop_id: str, 
        route_number: Optional[str] = None
    ) -> StopETAResponse:
        # Check stop validity
        query = select(GTFSStop).where(GTFSStop.stop_id == stop_id)
        result = await session.execute(query)
        stop = result.scalar_one_or_none()

        stop_name = stop.stop_name if stop else stop_id
        stop_lat = stop.stop_lat if stop else 28.6139
        stop_lon = stop.stop_lon if stop else 77.2090
        arrivals = await DelhiOTDService.get_live_arrivals(stop_id, stop_lat, stop_lon, route_number)

        return StopETAResponse(
            stop_id=stop_id,
            stop_name=stop_name,
            city=city,
            timestamp=datetime.now(timezone.utc).isoformat(),
            arrivals=arrivals
        )

    @staticmethod
    async def plan_trip(
        session: AsyncSession,
        city: str,
        origin: str,
        destination: str,
        preference: str = "fastest"
    ) -> TripPlanResponse:
        # Simple simulated routing engine between Delhi stops
        bus_type = "AC_LowFloor" if preference == "ac_only" else "Ordinary"
        fare = 25.0 if bus_type == "AC_LowFloor" else 15.0

        legs = [
            TripLeg(
                route_number="534" if preference == "ac_only" else "TMS",
                from_stop=origin,
                to_stop=destination,
                stops_count=8,
                next_bus_eta_minutes=4,
                bus_type=bus_type
            )
        ]

        trip_option = TripOption(
            option_id=1,
            total_travel_time_minutes=32,
            fare_estimate={"currency": "INR", "amount": fare, "type": bus_type},
            transfers=0,
            legs=legs,
            first_last_mile_tip="Destination is 650m from drop stop. Rapido Bike Taxi or E-Rickshaw available at stand."
        )

        return TripPlanResponse(
            origin=origin,
            destination=destination,
            city=city,
            routes=[trip_option]
        )

    @staticmethod
    def get_fare_details(
        city: str,
        route_number: str,
        from_stop: str,
        to_stop: str,
        passenger_category: str = "general"
    ) -> FareInfoResponse:
        bus_type = "AC_LowFloor" if route_number in ["534", "TMS"] else "Ordinary"
        base_fare = DelhiOTDService.calculate_dtc_fare(bus_type, distance_km=10.0)

        concessions = []
        final_fare = base_fare
        if passenger_category.lower() in ["woman", "female"]:
            concessions.append(ConcessionInfo(
                scheme="Delhi Pink Pass Scheme",
                eligible=True,
                final_fare=0.0,
                note="Free travel for women in DTC & Cluster buses. Conductor issues Pink slip on-board."
            ))
            final_fare = 0.0
        elif passenger_category.lower() == "senior_citizen":
            concessions.append(ConcessionInfo(
                scheme="Senior Citizen Concession Pass",
                eligible=True,
                final_fare=base_fare * 0.5,
                note="50% concession with valid Senior Citizen pass"
            ))
            final_fare = base_fare * 0.5

        return FareInfoResponse(
            city=city,
            route_number=route_number,
            from_stop=from_stop,
            to_stop=to_stop,
            fare_inr=final_fare,
            bus_type=bus_type,
            concessions_applicable=concessions,
            digital_ticketing={
                "ticketing_type": "On-Board Conductor & Public Metro Card",
                "payment_modes": ["Cash", "DTC Smart Card", "National Common Mobility Card (NCMC)"],
                "pink_pass_info": "Free physical Pink Slip issued on-board by bus conductor for female commuters. No advance online purchase required."
            }
        )
