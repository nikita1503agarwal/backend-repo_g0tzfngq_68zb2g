import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import User, Project, VideoJob

app = FastAPI(title="GenAds API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helpers
class SignUpRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class SignInRequest(BaseModel):
    email: EmailStr
    password: str


@app.get("/")
def read_root():
    return {"message": "GenAds Backend Running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = os.getenv("DATABASE_NAME") or "❌ Not Set"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"

    return response


# Auth endpoints (simple demo - storing hashed password is expected in real apps)
@app.post("/auth/signup")
def signup(payload: SignUpRequest):
    # Very simple demo: store user with a naive hash
    import hashlib
    existing = db["user"].find_one({"email": payload.email}) if db else None
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    password_hash = hashlib.sha256(payload.password.encode()).hexdigest()
    user = User(name=payload.name, email=payload.email, password_hash=password_hash)
    _id = create_document("user", user)
    return {"id": _id, "name": user.name, "email": user.email}


@app.post("/auth/signin")
def signin(payload: SignInRequest):
    import hashlib
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    u = db["user"].find_one({"email": payload.email})
    if not u:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if u.get("password_hash") != hashlib.sha256(payload.password.encode()).hexdigest():
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"message": "signed_in", "email": payload.email, "name": u.get("name"), "avatar_url": u.get("avatar_url")}


# Dashboard data
@app.get("/dashboard/summary")
def dashboard_summary(email: EmailStr):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    total = db["videojob"].count_documents({"owner_email": email})
    processing = db["videojob"].count_documents({"owner_email": email, "status": {"$in": ["queued", "processing"]}})
    latest_docs = list(db["videojob"].find({"owner_email": email}).sort("created_at", -1).limit(20))
    for d in latest_docs:
        d["id"] = str(d["_id"]) ; d.pop("_id", None)
    return {"total": total, "processing": processing, "videos": latest_docs}


# Create video - step submission
class StepOne(BaseModel):
    owner_email: EmailStr
    project_name: str
    brand_name: str
    brand_detail: str

class StepTwo(BaseModel):
    owner_email: EmailStr
    project_name: str
    brand_name: str
    brand_detail: str
    creative_prompt: str
    target_audience: str
    video_style: str
    aspect_ratio: str
    duration_seconds: int

class StepThree(BaseModel):
    owner_email: EmailStr
    project_name: str
    brand_name: str
    brand_detail: str
    creative_prompt: str
    target_audience: str
    video_style: str
    aspect_ratio: str
    duration_seconds: int
    product_image_url: Optional[str] = None
    brand_logo_url: Optional[str] = None
    brand_guideline_url: Optional[str] = None
    reference_image_url: Optional[str] = None


@app.post("/video/create")
def create_video(job: StepThree):
    # Persist a VideoJob with status queued/processing, return id
    vj = VideoJob(**job.model_dump(), status="processing")
    _id = create_document("videojob", vj)
    return {"id": _id, "status": vj.status}


@app.get("/video/{job_id}")
def get_video(job_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    try:
        doc = db["videojob"].find_one({"_id": ObjectId(job_id)})
    except Exception:
        doc = None
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    doc["id"] = str(doc["_id"]) ; doc.pop("_id", None)
    return doc


@app.post("/video/{job_id}/finalize")
def finalize_video(job_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    try:
        db["videojob"].update_one({"_id": ObjectId(job_id)}, {"$set": {"status": "finalized"}})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id")
    return {"id": job_id, "status": "finalized"}


# Simple file upload endpoints (store to temp, return URL placeholder)
UPLOAD_DIR = "/tmp/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    path = os.path.join(UPLOAD_DIR, file.filename)
    with open(path, "wb") as f:
        f.write(await file.read())
    # In real app, upload to cloud storage and return URL
    return {"url": f"/uploads/{file.filename}"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
