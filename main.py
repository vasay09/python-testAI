import uvicorn
import json

from ollama import chat
from ollama import ChatResponse
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from loguru import logger

from config import SYSTEM_PROMPT, TOOLS
from functions import add_two_numbers, subtract_two_numbers, save_code, run_command, search, fetch_page

app = FastAPI()

@app.get("/")
async def index():
    with open("index.html", "r", encoding="UTF-8") as f:
        html = f.read()

    return  HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global final_response
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

            available_functions = {
                'add_two_numbers': add_two_numbers,
                'subtract_two_numbers': subtract_two_numbers,
                'save_code': save_code,
                'run_command': run_command,
                'search': search,
                'fetch_page':fetch_page

            }

            response: ChatResponse = chat(
                model='llama3.1',
                messages=chat_history,
                tools=[add_two_numbers, save_code, run_command, search, fetch_page]
            )

            if response.message.tool_calls:
                # There may be multiple tool calls in the response
                for tool in response.message.tool_calls:
                    # Ensure the function is available, and then call it
                    if function_to_call := available_functions.get(tool.function.name):
                        print('Calling function:', tool.function.name)
                        print('Arguments:', tool.function.arguments)
                        output = function_to_call(**tool.function.arguments)
                        print('Function output:', output)
                    else:
                        print('Function', tool.function.name, 'not found')

            # Only needed to chat with the model using the tool call results
            if response.message.tool_calls:
                # Add the function response to messages for the model to use
                chat_history.append(response.message)
                chat_history.append({'role': 'tool', 'content': str(output), 'name': tool.function.name})

                # Get final response from model with function outputs
                final_response = chat(model='llama3.1', messages=chat_history)
                print('Final response:', final_response.message.content)

            else:
                print('No tool calls returned from model')

            #вместо chat_history.append(ai_message.to_dict()) добавляем сообщение в историю!
            chat_history.append({
                "role": "assistant",
                "content": response.message.content
            })

            print(response.message.tool_calls)

            await websocket.send_text(json.dumps({
                "role": "assistant",
                "content": final_response.message.content #response.message.content
            }))


    except WebSocketDisconnect:
        logger.error("Клиент разорвал соединение")



if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
