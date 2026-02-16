from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from .websocket_manager import manager
from .chat_service import generate_avatar_response, clear_history

app = FastAPI(
    title="ChefJunior App Backend",
    description="This is the backend for the ChefJunior App, including the avatar chat service.",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the ChefJunior App Backend!"}

@app.websocket("/ws/chat/{client_id}")
async def websocket_chat_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(client_id, websocket)
    
    # Send a welcome message upon connection
    await manager.send_personal_message(f"Hello! I'm Dwane, your personal cooking assistant. What would you like to cook today?", client_id)

    try:
        while True:
            data = await websocket.receive_text()
            
            # Generate response from the AI
            ai_response = await generate_avatar_response(client_id, data)
            
            # Send the AI response back to the user
            await manager.send_personal_message(ai_response, client_id)
            
    except WebSocketDisconnect:
        print(f"Client #{client_id} disconnected.")
        manager.disconnect(client_id)
        clear_history(client_id) # Clean up conversation history