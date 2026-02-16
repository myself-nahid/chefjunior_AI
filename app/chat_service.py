import os
import openai
from dotenv import load_dotenv
from typing import Dict, List
from fastapi import UploadFile
from openai import OpenAI

from .prompts import CHEF_AVATAR_PROMPT
from .models import ChatMessage
from .websocket_manager import manager 

load_dotenv()

# Initialize OpenAI client with only API key
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    client = OpenAI(api_key=api_key)
else:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

conversation_histories: Dict[str, List[Dict[str, str]]] = {}

def get_initial_prompt():
    return {"role": "system", "content": CHEF_AVATAR_PROMPT}

async def process_audio_and_get_response(client_id: str, audio_file: UploadFile):
    
    # logs to verify we received the file correctly
    print(f"Received audio file for client: {client_id}")
    print(f"Filename: {audio_file.filename}")
    print(f"Content-Type: {audio_file.content_type}")
    
    try:
        transcription_response = client.audio.transcriptions.create(
            model="whisper-1",
            # Pass a tuple with filename, file-like object, and content type
            file=(audio_file.filename, audio_file.file, audio_file.content_type),
            response_format="json"
        )

        transcribed_text = transcription_response.text

        await manager.send_personal_message(f"You said: \"{transcribed_text}\"", client_id)
        
        ai_response = await generate_avatar_response(client_id, transcribed_text)

        await manager.send_personal_message(ai_response, client_id)

    except Exception as e:
        print(f"Error processing audio: {e}")
        error_message = "I'm sorry, I had trouble understanding your audio. Could you try again?"
        await manager.send_personal_message(error_message, client_id)

async def generate_avatar_response(client_id: str, user_message: str) -> str:
    if client_id not in conversation_histories:
        conversation_histories[client_id] = [get_initial_prompt()]

    conversation_histories[client_id].append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=conversation_histories[client_id],
            temperature=0.7,
        )
        
        ai_message = response.choices[0].message.content
        conversation_histories[client_id].append({"role": "assistant", "content": ai_message})
        return ai_message

    except Exception as e:
        print(f"Error generating OpenAI response: {e}")
        return "I'm sorry, something went wrong. Can you please ask me again?"

def clear_history(client_id: str):
    if client_id in conversation_histories:
        del conversation_histories[client_id]