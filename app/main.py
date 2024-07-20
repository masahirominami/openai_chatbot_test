from fastapi import FastAPI
from app.routes import query
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import time
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Set up MongoDB connection
mongo_client = MongoClient("mongodb://localhost:27017")
db = mongo_client["chatbot_db"]
conversations = db["conversations"]

def wait_for_mongodb():
    max_tries = 30
    tries = 0
    while tries < max_tries:
        try:
            # The ismaster command is cheap and does not require auth.
            mongo_client.admin.command('ismaster')
            return True
        except ConnectionFailure:
            tries += 1
            time.sleep(1)
    return False

if not wait_for_mongodb():
    logger.error("Unable to connect to MongoDB. Exiting...")
    sys.exit(1)

logger.info("Successfully connected to MongoDB")

# Include the router
app.include_router(query.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
