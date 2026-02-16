from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from .websocket_manager import manager
from .chat_service import generate_avatar_response, process_audio_and_get_response, clear_history

app = FastAPI(
    title="ChefJunior App Backend",
    description="This is the backend for the ChefJunior App, including the avatar chat service.",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the ChefJunior App Backend!"}

@app.post("/ws/chat/upload-audio/{client_id}")
async def upload_audio(client_id: str, file: UploadFile = File(...)):
    """
    Accepts an audio file, transcribes it, and sends the AI response
    back through the WebSocket connection for the given client_id.
    """
    await process_audio_and_get_response(client_id, file)
    
    # Return a simple acknowledgement to the HTTP request
    return {"status": "success", "message": "Audio is being processed."}

@app.websocket("/ws/chat/{client_id}")
async def websocket_chat_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(client_id, websocket)
    
    # Send a welcome message upon connection
    await manager.send_personal_message(f"Hello! I'm Dwane, your personal cooking assistant. You can talk to me with your voice or by typing!", client_id)

    try:
        while True:
            # This endpoint now primarily handles TEXT input. Audio is handled by the POST endpoint.
            data = await websocket.receive_text()
            
            # Generate response from the AI using the text data
            ai_response = await generate_avatar_response(client_id, data)
            
            # Send the AI response back to the user
            await manager.send_personal_message(ai_response, client_id)
            
    except WebSocketDisconnect:
        print(f"Client #{client_id} disconnected.")
        manager.disconnect(client_id)
        clear_history(client_id)