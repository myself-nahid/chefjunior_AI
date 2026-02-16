from openai import OpenAI
from app.core.config import settings
from fastapi import UploadFile

# Initialize OpenAI client with only API key
if settings.OPENAI_API_KEY:
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
else:
    raise ValueError("OPENAI_API_KEY is not configured")

SYSTEM_PROMPT = """
You are 'Dwane', a friendly and encouraging cooking assistant for kids using the ChefJunior App.
Keep answers short, fun, and educational. If they ask about recipes, guide them step by step.
"""

async def transcribe_audio(audio_file: UploadFile) -> str:
    # IMPORTANT: Pass tuple (filename, file_obj, content_type)
    file_tuple = (audio_file.filename, audio_file.file, audio_file.content_type)
    
    transcript = client.audio.transcriptions.create(
        model="whisper-1",
        file=file_tuple,
        response_format="json"
    )
    return transcript.text

async def get_gpt_response(history: list) -> str:
    # Ensure system prompt is first
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        temperature=0.7
    )
    return response.choices[0].message.content