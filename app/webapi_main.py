from openai import AsyncOpenAI
from app.data.db_integration import DB_Controller
from app.services.chat_history import ChatHistory
from app.data.tea_repository import TeaRepository
from app.services.intent_responder import IntentResponder
from app.services.prompt_factory import PromptFactory
from app.core.config import OPENAI_API_KEY, STORAGE_PATH, SYSTEM_PROMPT, MAX_MESSAGES, JSON_PATH

from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.concurrency import run_in_threadpool
from fastapi import FastAPI, WebSocket, Request, WebSocketDisconnect
from app.core.connection_manager import ConnectionManager

chat_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

tea_repo = TeaRepository(json_path=JSON_PATH)
rag_docs, tea_ids, tea_metas = tea_repo.get_data_for_db()

prompt_factory = PromptFactory()
db_controller = DB_Controller(openai_api_key=OPENAI_API_KEY, storage_path=STORAGE_PATH)
system_prompt = SYSTEM_PROMPT

app = FastAPI()
templates = Jinja2Templates(directory=r"D:\Sales_assistant\app\templates")
connection_manager = ConnectionManager()

collection = db_controller.create_collection(
    documents=rag_docs,
    ids=tea_ids,
    metadatas=tea_metas,
)

@app.get("/", response_class=HTMLResponse)
def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await connection_manager.connect(websocket)

    chat_history = ChatHistory()
    intent_responder = IntentResponder(chat_client=chat_client, system_prompt=SYSTEM_PROMPT, tea_repo=tea_repo, chat_history=chat_history, prompt_factory=prompt_factory)

    messages = [
        {"role": "system", "content": system_prompt}
    ]

    try:
        while True:
            user_query = await websocket.receive_text()

            rewritten_data = await chat_history.rewrite_query(history_messages=messages, user_query=user_query)
            rewritten_query = rewritten_data["normalized_query"]
            intent = rewritten_data["intent"]
            detected_tea_name = rewritten_data.get("tea_name")
            print(f"DEBUG: Rewrite -> {rewritten_data}")

            forced_tea_id = None

            where_filter = None

            if intent in ("recommendation", "price", "caffeine", "ingredients", "comparison"):      # Change later for all products
                where_filter = {"type": "tea"}
            elif intent == "cross_sell":
                where_filter = {"type": "accessory"}

            if detected_tea_name:
                print(f"DEBUG: Context-Hit! Versuche Tee '{detected_tea_name}' direkt zu laden.")

                for t_id in tea_ids:
                    t_check = tea_repo.get_by_id(t_id)
                    if t_check and t_check.get("name") == detected_tea_name:
                        forced_tea_id = t_id
                        break
                
                if forced_tea_id:
                    tea_id = forced_tea_id
                    tea_info = tea_repo.get_by_id(tea_id)

                    results = {
                        "ids": [[tea_id]],
                        "documents": [[tea_info["rag_text"]]]
                    }
                    print(f"DEBUG: Skipping Search. Active tea set by context: {tea_id}")
            
            else:
                print(f"DEBUG: Vektorsearch with: '{rewritten_query}'")

                if intent == "recommendation":
                    n_results = 15
                elif intent == "comparison":
                    n_results = 15
                elif intent == "cross_sell":
                    n_results = 10
                else:
                    n_results = 1

                results = await run_in_threadpool(
                    db_controller.query_new,
                    query_text=rewritten_query,
                    n_results=n_results,
                    where=where_filter,
                )

                if results.get("ids") and results["ids"][0]:
                    tea_id = results["ids"][0][0]
                    tea_info = tea_repo.get_by_id(tea_id)
                
                else:
                    tea_id = None
                    tea_info = None

            print("DEBUG: Active tea:", tea_id, tea_info)

            final_answer = await intent_responder.respond(
                intent=intent,
                tea_info=tea_info,
                rewritten_data=rewritten_data,
                results=results,
                history_messages=messages
            )
            if not final_answer:
                print("Entschuldigung, dazu habe ich gerade keine sinnvolle Antwort.")

            #await connection_manager.send_personal_message(f"{user_query}", websocket)     if html sends user message, comment out!
            await connection_manager.send_personal_message(f"{final_answer}", websocket)

            messages.append({"role": "user", "content": user_query})
            messages.append({"role": "assistant", "content": final_answer})

            if len(messages) > MAX_MESSAGES:
                print("History is getting summarized...")

                conversation_part = messages[1:]
                summary = await chat_history.summarize_history(conversation_part)

                messages = [
                    messages[0],
                    {"role": "assistant", "content": f"Zusammenfassung des bisherigen Gesprächs: {summary}"}
                ]
                print("History successfully summarized!")
            else:
                pass
    
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
        await connection_manager.broadcast(f"Client #{client_id} left the chat")