from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.gtfs import GTFSStop
from app.services.tag_service import TagService
from app.schemas.tags import (
    SuggestTagRequest, 
    VoteTagRequest, 
    StopTagResponse, 
    StopTagsListResponse
)

router = APIRouter(prefix="/api/v1/tags", tags=["Crowdsourced Colloquial Stop Tags"])

@router.post("/suggest", response_model=StopTagResponse, operation_id="suggestColloquialTag")
async def suggest_tag(
    req: SuggestTagRequest,
    db: AsyncSession = Depends(get_db)
):
    # Verify stop_id exists
    stmt = select(GTFSStop).where(GTFSStop.stop_id == req.stop_id)
    res = await db.execute(stmt)
    if not res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"GTFS stop_id '{req.stop_id}' not found.")

    tag_obj = await TagService.suggest_tag(
        session=db,
        city=req.city,
        stop_id=req.stop_id,
        tag=req.tag,
        language=req.language,
        category=req.category
    )
    return tag_obj

@router.post("/{tag_id}/vote", response_model=StopTagResponse, operation_id="voteStopTag")
async def vote_tag(
    tag_id: str,
    req: VoteTagRequest,
    db: AsyncSession = Depends(get_db)
):
    tag_obj = await TagService.vote_tag(db, tag_id, req.vote_type)
    if not tag_obj:
        raise HTTPException(status_code=404, detail="Tag ID not found.")
    return tag_obj

@router.get("/stops/{stop_id}", response_model=StopTagsListResponse, operation_id="listStopTags")
async def list_tags_for_stop(
    stop_id: str,
    city: str = Query("delhi"),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(GTFSStop).where(GTFSStop.stop_id == stop_id)
    res = await db.execute(stmt)
    stop = res.scalar_one_or_none()
    if not stop:
        raise HTTPException(status_code=404, detail=f"Stop ID '{stop_id}' not found.")

    tags = await TagService.get_tags_for_stop(db, stop_id)
    return StopTagsListResponse(
        stop_id=stop_id,
        official_name=stop.stop_name,
        city=city,
        tags=tags
    )
