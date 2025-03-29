import uvicorn
import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from loguru import logger

app = FastAPI()

@app.get("/")
async def index():
    with open("index.html", "r", encoding="UTF-8") as f:
        html = f.read()

    return  HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await  websocket.accept()

    try:
        while True:
            data_frontend = await websocket.receive_text()
            user_input = data_frontend.strip()
            logger.debug(f"Сообщение от фронта: {user_input}")

            response = {
                "role":"assistant",
                "content":"Привет я тебя вижу в 2 часа ночи!"
            }

            await websocket.send_text(json.dumps(response))

    except WebSocketDisconnect:
        logger.error("Клиент разорвал соединение")



if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
