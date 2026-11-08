import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index
from app.database import Base

class StopTag(Base):
    __tablename__ = "stop_tags"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    stop_id = Column(String(100), ForeignKey("gtfs_stops.stop_id", ondelete="CASCADE"), nullable=False, index=True)
    city = Column(String(50), nullable=False, index=True, default="delhi")
    tag = Column(String(150), nullable=False)
    tag_normalized = Column(String(150), nullable=False, index=True)
    language = Column(String(10), default="en") # 'en', 'hi', 'kn', etc.
    category = Column(String(50), default="landmark") # 'landmark', 'metro_gate', 'slang', 'junction'
    upvotes = Column(Integer, default=1)
    downvotes = Column(Integer, default=0)
    status = Column(String(20), default="public") # 'public', 'flagged', 'verified'
    submitted_by = Column(String(100), default="anonymous")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_stop_tag_city_norm", "city", "tag_normalized"),
    )
