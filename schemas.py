"""
Database Schemas for GenAds

Each Pydantic model maps to a MongoDB collection named after the lowercase
class name. Example: class User -> collection "user".
"""
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, EmailStr, HttpUrl

class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    password_hash: str = Field(..., description="Password hash")
    avatar_url: Optional[str] = Field(None, description="Avatar image URL")

class Project(BaseModel):
    owner_email: EmailStr = Field(..., description="Owner's email")
    project_name: str = Field(...)
    brand_name: str = Field(...)
    brand_detail: str = Field("", description="Describe the brand")

class VideoJob(BaseModel):
    owner_email: EmailStr = Field(..., description="Owner's email")
    project_id: Optional[str] = Field(None, description="Related project id")
    project_name: str = Field(...)
    brand_name: str = Field(...)
    brand_detail: str = Field("")

    creative_prompt: str = Field(..., description="Creative vision prompt")
    target_audience: str = Field(...)
    video_style: str = Field(...)
    aspect_ratio: Literal["1:1","9:16","16:9","4:5","21:9"] = Field("16:9")
    duration_seconds: int = Field(15, ge=5, le=120)

    product_image_url: Optional[HttpUrl] = None
    brand_logo_url: Optional[HttpUrl] = None
    brand_guideline_url: Optional[HttpUrl] = None
    reference_image_url: Optional[HttpUrl] = None

    status: Literal["queued","processing","completed","failed","finalized"] = Field("processing")
    thumbnail_url: Optional[str] = None
    video_url: Optional[str] = None
    notes: Optional[str] = None
