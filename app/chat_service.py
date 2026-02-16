import os
import openai
from dotenv import load_dotenv
from typing import Dict, List

from .prompts import CHEF_AVATAR_PROMPT
from .models import ChatMessage

load_dotenv()

from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Store conversation history in memory (for production, use Redis or a database)
conversation_histories: Dict[str, List[Dict[str, str]]] = {}

def get_initial_prompt():
    return {"role": "system", "content": CHEF_AVATAR_PROMPT}

async def generate_avatar_response(client_id: str, user_message: str) -> str:
    if client_id not in conversation_histories:
        conversation_histories[client_id] = [get_initial_prompt()]

    # Add user message to history
    conversation_histories[client_id].append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model="gpt-4",  
            messages=conversation_histories[client_id],
            temperature=0.7,
        )
        
        ai_message = response.choices[0].message.content
        
        # Add AI response to history
        conversation_histories[client_id].append({"role": "assistant", "content": ai_message})
        
        return ai_message

    except Exception as e:
        print(f"Error generating OpenAI response: {e}")
        return "I'm sorry, something went wrong. Can you please ask me again?"

def clear_history(client_id: str):
    if client_id in conversation_histories:
        del conversation_histories[client_id]