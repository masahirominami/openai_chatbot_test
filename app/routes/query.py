from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import openai
import os
from datetime import datetime
import uuid
import logging
from app.main import conversations

router = APIRouter()

logger = logging.getLogger(__name__)

# Set up OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

class Query(BaseModel):
    user_input: str
    conversation_id: str = None

def get_conversation_history(conversation_id):
    if conversation_id:
        history = conversations.find({"conversation_id": conversation_id}).sort("timestamp", 1)
        return [
            {"role": "user" if doc["type"] == "user_input" else "assistant", "content": doc["content"]}
            for doc in history
        ]
    return []

@router.post("/query")
async def query(query: Query):
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

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        )

        ai_response = response.choices[0].message['content']

        ai_document = {
            "conversation_id": conversation_id,
            "type": "ai_response",
            "content": ai_response,
            "timestamp": datetime.utcnow()
        }
        conversations.insert_one(ai_document)

        logger.info(f"Processed query for conversation {conversation_id}")
        return {"response": ai_response, "conversation_id": conversation_id}

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
