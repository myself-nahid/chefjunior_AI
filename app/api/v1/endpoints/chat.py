from fastapi import APIRouter, WebSocket, WebSocketDisconnect, UploadFile, File, Depends
from typing import List, Dict
from app.services.chat_service import transcribe_audio, get_gpt_response

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, client_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_personal_message(self, message: str, client_id: str):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_text(message)

manager = ConnectionManager()

# Simple in-memory history (Use Redis for production)
chat_histories: Dict[str, List[dict]] = {}

@router.websocket("/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(client_id, websocket)
    if client_id not in chat_histories:
        chat_histories[client_id] = []
    
    await manager.send_personal_message("Hello! I am Dwane. Let's cook!", client_id)

    try:
        while True:
            data = await websocket.receive_text()
            
            # 1. Update History
            chat_histories[client_id].append({"role": "user", "content": data})
            
            # 2. Get AI Response
            ai_response = await get_gpt_response(chat_histories[client_id])
            
            # 3. Update History & Send
            chat_histories[client_id].append({"role": "assistant", "content": ai_response})
            await manager.send_personal_message(ai_response, client_id)
            
    except WebSocketDisconnect:
        manager.disconnect(client_id)

@router.post("/upload-audio/{client_id}")
async def upload_audio(client_id: str, file: UploadFile = File(...)):
    # 1. Transcribe
    text = await transcribe_audio(file)
    
    # 2. Notify User via WebSocket
    await manager.send_personal_message(f"🎤 You said: {text}", client_id)
    
    # 3. Process with GPT
    if client_id not in chat_histories:
        chat_histories[client_id] = []
        
    chat_histories[client_id].append({"role": "user", "content": text})
    ai_response = await get_gpt_response(chat_histories[client_id])
    chat_histories[client_id].append({"role": "assistant", "content": ai_response})
    
    # 4. Send Response via WebSocket
    await manager.send_personal_message(ai_response, client_id)
    
    return {"status": "processing", "transcription": text}