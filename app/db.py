# app/db.py
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import time

mongo_client = MongoClient("mongodb://localhost:27017")
db = mongo_client["chatbot_db"]
conversations = db["conversations"]

def wait_for_mongodb():
    max_tries = 30
    tries = 0
    while tries < max_tries:
        try:
            mongo_client.admin.command('ismaster')
            return True
        except ConnectionFailure:
            tries += 1
            time.sleep(1)
    return False

