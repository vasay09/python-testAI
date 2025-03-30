import uvicorn
import json

from ollama import chat
from ollama import ChatResponse
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from loguru import logger

from config import HELICONE_API_KEY, GROQ_API_KEY, SYSTEM_PROMPT, TOOLS, OLLAMA_TOOLS

app = FastAPI()

@app.get("/")
async def index():
    with open("index.html", "r", encoding="UTF-8") as f:
        html = f.read()

    return  HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await  websocket.accept()

    chat_history = [{
        "role": "system",
        "content": SYSTEM_PROMPT
    }]

    try:
        while True:
            data_frontend = await websocket.receive_text()
            user_input = data_frontend.strip()
            logger.debug(f"Сообщение от фронта: {user_input}")

            chat_history.append({
                "role": "user",
                "content": user_input
            })

            response: ChatResponse = chat(
                'llama3.1',
                messages=chat_history,
                #tools=[add_two_numbers, subtract_two_numbers_tool],
            )

            #вместо chat_history.append(ai_message.to_dict()) добавляем сообщение в историю!
            chat_history.append({
                "role": "assistant",
                "content": response.message.content
            })

            print(response.message)

            await websocket.send_text(json.dumps({
                "role": "assistant",
                "content": response.message.content
            }))


    except WebSocketDisconnect:
        logger.error("Клиент разорвал соединение")



if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
