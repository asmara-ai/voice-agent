import os
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from src.routes.openai_route import openai_router
from src.handlers.socket_handler import handle_websocket
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from src.handlers.mcp_handler import MCPHub
import json
import traceback

mcp_hub = MCPHub()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        with open("config.json") as f:
            d = json.load(f)
            config = d.get("mcp-shopify", {})
            await mcp_hub.connect_to_server("mcp-shopify", config=config)

    except Exception as e:
        print(f"Initialization error: {e}")
        traceback.print_exc()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API endpoint
app.include_router(openai_router)


# WebSocket endpoint
@app.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    await handle_websocket(websocket, mcp_hub)


@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    file_path = f"../client/dist/{full_path}"
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse("../client/dist/index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8080)
