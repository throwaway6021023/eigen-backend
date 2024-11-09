from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from .llm_provider import CHAT_SYSTEM_MESSAGE, CompletionMessage, create_chat_completion
from .request_models import CreateChatIn
from .response_models import SsePayload

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def read_health():
    return "OK!"


@app.post("/chat")
async def create_chat(create_chat_in: CreateChatIn) -> StreamingResponse:
    completion_message = CompletionMessage(role="user", content=create_chat_in.message)
    response = create_chat_completion([CHAT_SYSTEM_MESSAGE, completion_message])
    sse = async_generator_as_sse(response)
    return EventSourceResponse(sse)


async def async_generator_as_sse(
    generator: AsyncGenerator[str, None],
) -> AsyncGenerator[SsePayload, None]:
    try:
        async for chunk in generator:
            yield SsePayload(data=chunk, event="data").model_dump_json()
    except Exception as e:
        yield SsePayload(data=str(e), event="error").model_dump_json()
    finally:
        yield SsePayload(data="", event="end").model_dump_json()
