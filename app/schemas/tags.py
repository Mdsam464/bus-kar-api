from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class SuggestTagRequest(BaseModel):
    city: str = Field(default="delhi", description="Transit city name, e.g. delhi, bengaluru, mumbai")
    stop_id: str = Field(..., description="GTFS stop_id to associate tag with")
    tag: str = Field(..., min_length=2, max_length=150, description="Colloquial tag or landmark alias")
    language: str = Field(default="en", description="Language code: en, hi, kn, mr, etc.")
    category: str = Field(default="landmark", description="landmark, metro_gate, slang, junction")

class VoteTagRequest(BaseModel):
    vote_type: str = Field(..., pattern="^(upvote|downvote)$")

class StopTagResponse(BaseModel):
    id: str
    stop_id: str
    city: str
    tag: str
    language: str
    category: str
    upvotes: int
    downvotes: int
    status: str
    created_at: datetime

class StopTagsListResponse(BaseModel):
    stop_id: str
    official_name: str
    city: str
    tags: List[StopTagResponse]
