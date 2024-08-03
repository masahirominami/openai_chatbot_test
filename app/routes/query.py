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
import tiktoken

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

def generate_prompt_messages(conversation_id, latest_prompt):
    conversation_history = get_conversation_history(conversation_id)
    
    messages = [{"role": "system", "content": "You are a helpful assistant."}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": latest_prompt})

    user_document = {
        "conversation_id": conversation_id,
        "type": "user_input",
        "content": latest_prompt, 
        "timestamp": datetime.utcnow()
    }
    conversations.insert_one(user_document)
    return reduce_messages(messages, int(os.getenv("AZURE_OPENAI_MAX_TOKENS")))

def generate_summarized_messages(conversation_id, messages, last_ai_answer):
    messages_to_sum = messages.copy()
    messages_to_sum.append({"role": "assistant", "content":last_ai_answer})
    messages_to_sum.append({"role": "user", "content": """
        DO understand the language of the conversation.
        DO Summarize the conversation so far in less than 20 sentences, in the original language.
        DO Answer them in a markdown format bulleted list.
        DO NOT translate the conversation in English.
        """ })

    response = client.chat.completions.create(
        model=os.getenv("AZURE_OPENAI_MODEL_NAME"), #"gpt-35-turbo",
        messages=messages_to_sum,
        max_tokens=int(os.getenv("AZURE_OPENAI_MAX_RESPONSE_TOKENS"))
    )

    ai_response = response.choices[0].message.content

    messages = reduce_messages(messages, int(os.getenv("AZURE_OPENAI_MAX_TOKENS")))

    ai_document = {
        "conversation_id": conversation_id,
        "type": "ai_response",
        "content": ai_response,
        "timestamp": datetime.utcnow()
    }
    conversations.insert_one(ai_document)
    return ai_response

# def generate_summarized_message(message):
#     messages = [{"role": "system", "content": "You are a helpful assistant."}]
#     messages.append({"role": "user", "content": f"DO understand the language of {message} . Then summarize the {message} in that language. DO NOT translate it in English." })
# 
#     response = client.chat.completions.create(
#         model=os.getenv("AZURE_OPENAI_MODEL_NAME"), #"gpt-35-turbo",
#         messages=messages
#     )
# 
#     ai_response = response.choices[0].message.content
# 
#     return ai_response

def reduce_messages(messages, max_len):
    string = json.dumps(messages)
    # while len(str) > max_len:
    while num_tokens_from_string(string, os.getenv("AZURE_OPENAI_TIKTOKEN_ENCODING")) > max_len:
        del messages[1]
        string = json.dumps(messages)

    return messages

# cf. https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
def num_tokens_from_string(string, encoding_name):
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

@router.post("/query")
async def query(query: Query):
#    if not openai.api_key:
#        raise HTTPException(status_code=500, detail="OpenAI API key not configured")

    try:
        conversation_id = query.conversation_id or str(uuid.uuid4())

        # user_prompt = generate_summarized_message(query.user_input)
        # messages = generate_prompt_messages(conversation_id, user_prompt)
        messages = generate_prompt_messages(conversation_id, query.user_input)

        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_MODEL_NAME"), # "gpt-35-turbo",
            messages=messages,
            max_tokens=int(os.getenv("AZURE_OPENAI_MAX_RESPONSE_TOKENS"))
        )

        ai_response = response.choices[0].message.content

        # summary_of_ai_response = generate_summarized_message(ai_response)

        ai_document = {
            "conversation_id": conversation_id,
            "type": "ai_response",
            "content": ai_response,
            # "content": summary_of_ai_response,
            "timestamp": datetime.utcnow()
        }
        conversations.insert_one(ai_document)

        summary = generate_summarized_messages(conversation_id, messages, ai_response) 

        logger.info(f"Processed query for conversation {conversation_id}")
        return {"response": ai_response, "messages": messages, "summary": summary, "conversation_id": conversation_id}

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

