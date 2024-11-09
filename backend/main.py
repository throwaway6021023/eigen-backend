import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from .llm_provider import CHAT_SYSTEM_MESSAGE, CompletionMessage, create_chat_completion
from .request_models import CreateChatIn, CreateContextIn
from .response_models import SsePayload
from .store import ChatStore


# Create a store instance at startup and close it at shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.store = ChatStore()
    await app.state.store.create_search_index()
    yield
    await app.state.store.close()


app = FastAPI(lifespan=lifespan)
logger = logging.getLogger(__name__)

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
    # Get previous messages for this session
    previous_messages = await app.state.store.get_messages(create_chat_in.session_id)

    # Create new user message
    user_message = CompletionMessage(role="user", content=create_chat_in.message)

    # Combine system message, previous messages, and new message
    messages = [CHAT_SYSTEM_MESSAGE] + previous_messages + [user_message]

    # Get response from LLM
    response = create_chat_completion(messages, app.state.store)

    # Store the user message
    await app.state.store.add_message(create_chat_in.session_id, user_message)

    # Create SSE response
    async def wrapped_response():
        accum = ""
        async for chunk in response:
            if chunk["type"] == "text":
                accum += chunk["text"]
            yield chunk
        # After getting full response, store the assistant's message
        await app.state.store.add_message(
            create_chat_in.session_id,
            CompletionMessage(role="assistant", content=accum),
        )

    sse = async_generator_as_sse(wrapped_response())
    return EventSourceResponse(sse)


@app.post("/context")
async def create_context(create_context_in: CreateContextIn):
    """Store new context data for future reference"""
    context_id = await app.state.store.add_context(
        title=create_context_in.title, content=create_context_in.content
    )

    return {"status": "success", "context_id": context_id}


async def async_generator_as_sse(
    generator: AsyncGenerator[str, None],
) -> AsyncGenerator[SsePayload, None]:
    try:
        async for chunk in generator:
            if chunk["type"] == "text":
                yield SsePayload(data=chunk["text"], event="data").model_dump_json()
            elif chunk["type"] == "component":
                yield SsePayload(
                    data=chunk["component"], event="component"
                ).model_dump_json()
    except Exception as e:
        logger.exception("Error in async generator")
        yield SsePayload(data=str(e), event="error").model_dump_json()
    finally:
        yield SsePayload(data="", event="end").model_dump_json()
