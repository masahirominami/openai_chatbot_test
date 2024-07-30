# file2.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from openai import AzureOpenAI
import os
from datetime import datetime
import uuid
import logging
import json
from app.db import conversations  # Import from app/db.py
# importing necessary functions from dotenv library
from dotenv import load_dotenv, dotenv_values 

# loading variables from .env file
load_dotenv() 

router = APIRouter()

logger = logging.getLogger(__name__)

# AzureOpenAI
client = AzureOpenAI(
  api_key = os.getenv("AZURE_OPENAI_API_KEY"),
  api_version = "2024-02-01",
  azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
)

class Query(BaseModel):
    user_input: str = Field(..., min_length=1, description="User input text")
    conversation_id: str = None

def get_conversation_history(conversation_id):
    if conversation_id:
        history = conversations.find({"conversation_id": conversation_id}).sort("timestamp", 1)
        return [
            {"role": "user" if doc["type"] == "user_input" else "assistant", "content": doc["content"]}
            for doc in history
        ]
    return []

def reduce_messages(messages, max_len):
    str = json.dumps(messages)
    while len(str) > max_len:
        del messages[1]
        str = json.dumps(messages)

    return messages

@router.post("/query")
async def query(query: Query):
#    if not openai.api_key:
#        raise HTTPException(status_code=500, detail="OpenAI API key not configured")

    try:
        conversation_id = query.conversation_id or str(uuid.uuid4())
        conversation_history = get_conversation_history(conversation_id)
        
        messages = [{"role": "system", "content": "You are a helpful assistant."}]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": query.user_input})

        user_document = {
            "conversation_id": conversation_id,
            "type": "user_input",
            "content": query.user_input,
            "timestamp": datetime.utcnow()
        }
        conversations.insert_one(user_document)
        messages = reduce_messages(messages, 4000)

        response = client.chat.completions.create(
            model="gpt-35-turbo",
            messages=messages
        )

        ai_response = response.choices[0].message.content

        ai_document = {
            "conversation_id": conversation_id,
            "type": "ai_response",
            "content": ai_response,
            "timestamp": datetime.utcnow()
        }
        conversations.insert_one(ai_document)

        logger.info(f"Processed query for conversation {conversation_id}")
        return {"response": ai_response, "messages": messages, "conversation_id": conversation_id}

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

