from fastapi import APIRouter
from app.main import mongo_client

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "ok"}

@router.get("/db-health")
async def db_health_check():
    try:
        mongo_client.server_info()
        return {"status": "connected to MongoDB"}
    except Exception as e:
        return {"status": "MongoDB connection failed", "error": str(e)}
