from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Literal
from app.database import get_db
from app.services.tag_service import TagService
from app.services.eta_service import ETAService
from app.schemas.transit import (
    ResolveStopResponse, 
    StopETAResponse, 
    TripPlanResponse, 
    FareInfoResponse
)

router = APIRouter(prefix="/api/v1/transit", tags=["Transit Operations"])

@router.get("/stops/resolve", response_model=ResolveStopResponse)
async def resolve_stop(
    query: str = Query(..., description="Colloquial stop name, landmark, or street"),
    city: str = Query("delhi", description="Transit city"),
    limit: int = Query(3, ge=1, le=10),
    db: AsyncSession = Depends(get_db)
):
    candidates = await TagService.resolve_stop_by_query(db, city, query, limit)
    return ResolveStopResponse(query=query, city=city, candidates=candidates)

@router.get("/stops/{stop_id}/eta", response_model=StopETAResponse)
async def get_stop_eta(
    stop_id: str,
    city: str = Query("delhi"),
    route_number: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    return await ETAService.get_stop_eta(db, city, stop_id, route_number)

@router.get("/trip/plan", response_model=TripPlanResponse)
async def plan_trip(
    origin: str = Query(..., description="Origin stop or colloquial landmark"),
    destination: str = Query(..., description="Destination stop or colloquial landmark"),
    city: str = Query("delhi"),
    preference: Literal["fastest", "ac_only", "cheapest"] = Query("fastest"),
    db: AsyncSession = Depends(get_db)
):
    return await ETAService.plan_trip(db, city, origin, destination, preference)

@router.get("/fare", response_model=FareInfoResponse)
async def get_fare(
    from_stop: str = Query(...),
    to_stop: str = Query(...),
    route_number: str = Query("534"),
    city: str = Query("delhi"),
    passenger_category: Literal["general", "woman", "senior_citizen", "student"] = Query("general")
):
    return ETAService.get_fare_details(city, route_number, from_stop, to_stop, passenger_category)
