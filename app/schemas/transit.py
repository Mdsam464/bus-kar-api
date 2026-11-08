from pydantic import BaseModel, Field
from typing import List, Optional

class StopCandidate(BaseModel):
    stop_id: str
    official_name: str
    matched_tag: Optional[str] = None
    tag_upvotes: Optional[int] = 0
    latitude: float
    longitude: float
    confidence: float
    city: str

class ResolveStopResponse(BaseModel):
    query: str
    city: str
    candidates: List[StopCandidate]

class BusArrival(BaseModel):
    route_number: str
    vehicle_id: str
    vehicle_type: str
    eta_minutes: int
    distance_meters: int
    last_ping_seconds_ago: int
    occupancy_status: str
    live_map_url: str

class StopETAResponse(BaseModel):
    stop_id: str
    stop_name: str
    city: str
    timestamp: str
    arrivals: List[BusArrival]

class TripLeg(BaseModel):
    route_number: str
    from_stop: str
    to_stop: str
    stops_count: int
    next_bus_eta_minutes: int
    bus_type: str

class TripOption(BaseModel):
    option_id: int
    total_travel_time_minutes: int
    fare_estimate: dict
    transfers: int
    legs: List[TripLeg]
    first_last_mile_tip: Optional[str] = None

class TripPlanResponse(BaseModel):
    origin: str
    destination: str
    city: str
    routes: List[TripOption]

class ConcessionInfo(BaseModel):
    scheme: str
    eligible: bool
    final_fare: float
    note: str

class FareInfoResponse(BaseModel):
    city: str
    route_number: str
    from_stop: str
    to_stop: str
    fare_inr: float
    bus_type: str
    concessions_applicable: List[ConcessionInfo]
    digital_ticketing: dict
