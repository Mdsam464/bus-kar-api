import re
from typing import List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.gtfs import GTFSStop
from app.models.stop_tag import StopTag
from app.schemas.transit import StopCandidate

def normalize_text(text: str) -> str:
    """Normalizes text by removing punctuation, extra spaces and lowercase."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", "", text)
    return " ".join(text.split())

class TagService:
    @staticmethod
    async def suggest_tag(
        session: AsyncSession,
        city: str,
        stop_id: str,
        tag: str,
        language: str = "en",
        category: str = "landmark",
        submitted_by: str = "agent_user"
    ) -> StopTag:
        norm_tag = normalize_text(tag)

        # Check if identical tag already exists for this stop
        query = select(StopTag).where(
            StopTag.stop_id == stop_id,
            StopTag.tag_normalized == norm_tag
        )
        result = await session.execute(query)
        existing = result.scalar_one_or_none()

        if existing:
            existing.upvotes += 1
            await session.commit()
            await session.refresh(existing)
            return existing

        new_tag = StopTag(
            stop_id=stop_id,
            city=city.lower(),
            tag=tag.strip(),
            tag_normalized=norm_tag,
            language=language,
            category=category,
            upvotes=1,
            downvotes=0,
            status="public",
            submitted_by=submitted_by
        )
        session.add(new_tag)
        await session.commit()
        await session.refresh(new_tag)
        return new_tag

    @staticmethod
    async def vote_tag(session: AsyncSession, tag_id: str, vote_type: str) -> Optional[StopTag]:
        query = select(StopTag).where(StopTag.id == tag_id)
        result = await session.execute(query)
        tag_obj = result.scalar_one_or_none()

        if not tag_obj:
            return None

        if vote_type == "upvote":
            tag_obj.upvotes += 1
        elif vote_type == "downvote":
            tag_obj.downvotes += 1
            # Auto-flag if heavily downvoted
            if tag_obj.downvotes > 3 and tag_obj.downvotes > (tag_obj.upvotes * 3):
                tag_obj.status = "flagged"

        await session.commit()
        await session.refresh(tag_obj)
        return tag_obj

    @staticmethod
    async def get_tags_for_stop(session: AsyncSession, stop_id: str) -> List[StopTag]:
        query = select(StopTag).where(
            StopTag.stop_id == stop_id,
            StopTag.status != "flagged"
        ).order_by(StopTag.upvotes.desc())
        result = await session.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def resolve_stop_by_query(
        session: AsyncSession, 
        city: str, 
        query: str, 
        limit: int = 3
    ) -> List[StopCandidate]:
        """
        Resolves colloquial names using crowdsourced tags and official stop names.
        """
        norm_query = normalize_text(query)
        candidates = []

        # 1. Search in crowdsourced stop tags
        tag_stmt = select(StopTag, GTFSStop).join(
            GTFSStop, StopTag.stop_id == GTFSStop.stop_id
        ).where(
            StopTag.city == city.lower(),
            StopTag.status != "flagged"
        )
        tag_results = (await session.execute(tag_stmt)).all()

        scored_matches = {}
        for tag_row, stop_row in tag_results:
            tag_norm = tag_row.tag_normalized
            # Match score heuristic
            score = 0.0
            if norm_query == tag_norm:
                score = 0.95
            elif norm_query in tag_norm or tag_norm in norm_query:
                score = 0.80
            else:
                # token overlap
                q_tokens = set(norm_query.split())
                t_tokens = set(tag_norm.split())
                overlap = len(q_tokens.intersection(t_tokens))
                if overlap > 0:
                    score = 0.50 + (0.15 * overlap)

            if score > 0.4:
                # Upvote booster
                upvote_boost = min(0.15, tag_row.upvotes * 0.01)
                final_score = min(0.99, score + upvote_boost)
                
                # Keep best matching tag per stop
                if stop_row.stop_id not in scored_matches or scored_matches[stop_row.stop_id]["confidence"] < final_score:
                    scored_matches[stop_row.stop_id] = {
                        "stop_id": stop_row.stop_id,
                        "official_name": stop_row.stop_name,
                        "matched_tag": tag_row.tag,
                        "tag_upvotes": tag_row.upvotes,
                        "latitude": stop_row.stop_lat,
                        "longitude": stop_row.stop_lon,
                        "confidence": round(final_score, 2),
                        "city": stop_row.city
                    }

        # 2. Also check official stop names
        stop_stmt = select(GTFSStop).where(GTFSStop.city == city.lower())
        all_stops = (await session.execute(stop_stmt)).scalars().all()

        for stop in all_stops:
            stop_norm = normalize_text(stop.stop_name)
            if norm_query in stop_norm or any(token in stop_norm for token in norm_query.split()):
                if stop.stop_id not in scored_matches:
                    scored_matches[stop.stop_id] = {
                        "stop_id": stop.stop_id,
                        "official_name": stop.stop_name,
                        "matched_tag": None,
                        "tag_upvotes": 0,
                        "latitude": stop.stop_lat,
                        "longitude": stop.stop_lon,
                        "confidence": 0.75,
                        "city": stop.city
                    }

        sorted_candidates = sorted(
            scored_matches.values(), 
            key=lambda x: x["confidence"], 
            reverse=True
        )[:limit]

        return [StopCandidate(**c) for c in sorted_candidates]
