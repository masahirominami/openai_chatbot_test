# app/main.py
from fastapi import FastAPI
from app.routes.query import router as query_router 
from app.routes.health import router as health_router 
import logging
import sys
from app.db import wait_for_mongodb  # Import from app/db.py
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if not wait_for_mongodb():
    logger.error("Unable to connect to MongoDB. Exiting...")
    sys.exit(1)

logger.info("Successfully connected to MongoDB")

# Include the router
app.include_router(query_router)
app.include_router(health_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

