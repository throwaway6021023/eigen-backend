import json
from typing import TYPE_CHECKING, Literal

import openai
from pydantic import BaseModel

from .settings import settings
from .tools import COMPONENT_FNS, TOOL_FNS, TOOLS

if TYPE_CHECKING:
    from .store import ChatStore

_client = openai.AsyncOpenAI(
    api_key=settings.OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
)


class CompletionMessage(BaseModel):
    role: Literal["system", "user", "assistant", "function"]
    content: str


class FunctionResultCompletionMessage(CompletionMessage):
    name: str


CHAT_SYSTEM_MESSAGE = CompletionMessage(
    role="system",
    content="""
You are an AI representative of Eigen, an AI-first company focused on enterprise solutions. Your role is to engage visitors on eigen.net in a direct, pragmatic, and thoughtful manner.

Core Behaviors:
- Act as a friendly sales agent promoting Eigen's capabilities and case studies without being overly pushy.
- For example, if a visitor states their sector, you should respond with a relevant case study so they can see how Eigen has helped others in their industry.
- If a visitor message is too vague, ask follow-up questions to better understand their needs.
- Maintain a tone that is intelligent and no-nonsense, avoiding consultant-speak or overly formal language
- Engage in discovery by asking about visitors' names, companies, and needs when appropriate
- Tailor responses based on the user's context and industry
- Be direct and honest - if you don't have specific information, acknowledge it and offer to connect the user with a partner
- If a user asks to contact Eigen, render a contact form right away instead of asking them for more information.

Key Responsibilities:
- Help visitors understand Eigen's capabilities and offerings
- Guide users to relevant case studies and resources
- Facilitate connections with the team when appropriate
- Present interactive components (forms, lists) when relevant to the conversation

Style Guidelines:
- Be concise but thorough
- Use natural, conversational language
- Mirror the direct communication style of Eigen's partners
- Focus on practical value and real-world applications
- Maintain professionalism while being approachable

If you're unsure about any information or if a question requires specific expertise, suggest connecting the user with hello@eigen.net for direct partner engagement.
""",
)


async def create_chat_completion(
    messages: list[CompletionMessage], store: "ChatStore", depth: int = 0
):
    if depth > 3:
        yield {
            "type": "text",
            "text": "I'm sorry, I'm having trouble understanding your request. Please try again.",
        }
        return

    response = await _client.chat.completions.create(
        model=settings.LLM_MODEL_NAME,
        messages=messages,
        stream=True,
        tools=TOOLS,
        tool_choice="auto",
    )
    # Define variables to hold the streaming content and function call
    streaming_content = ""
    function_call = {"name": "", "arguments": ""}

    # Loop through the response chunks
    async for chunk in response:
        # Handle errors
        if not chunk.choices:
            messages.append(
                CompletionMessage(
                    role="assistant",
                    content="Sorry, there was an error. Please try again.",
                )
            )
            yield {
                "type": "text",
                "text": "Sorry, there was an error. Please try again.",
            }
            break

        # Get the first choice
        delta = chunk.choices[0].delta

        # If there's a function call, save it for later
        if delta.tool_calls:
            for tool_call in delta.tool_calls:
                if tool_call.function.name:
                    function_call["name"] += tool_call.function.name
                if tool_call.function.arguments:
                    function_call["arguments"] += tool_call.function.arguments

        # If it's content, add it to the streaming content and yield it
        elif delta.content:
            streaming_content += delta.content
            yield {
                "type": "text",
                "text": delta.content,
            }

        # Check finish reason
        if chunk.choices[0].finish_reason == "stop":
            messages.append(
                CompletionMessage(role="assistant", content=streaming_content)
            )

        elif chunk.choices[0].finish_reason == "tool_calls":
            if function_call["name"] in COMPONENT_FNS:
                component_output = COMPONENT_FNS[function_call["name"]].run(
                    **json.loads(function_call["arguments"])
                )
                yield {
                    "type": "component",
                    "component": component_output,
                }
            else:
                function_output = await call_function(
                    function_call["name"], function_call["arguments"], store
                )
                messages.append(
                    FunctionResultCompletionMessage(
                        role="function",
                        content=function_output,
                        name=function_call["name"],
                    )
                )
                async for chunk in create_chat_completion(messages, store, depth + 1):
                    yield chunk


async def call_function(
    function_name: str, function_arguments: str, store: "ChatStore"
) -> str:
    """Calls a function and returns the result."""

    # Ensure the function is defined
    if function_name not in TOOL_FNS:
        return "Function not defined."

    # Convert the function arguments from a string to a dict
    function_arguments_dict = json.loads(function_arguments)

    # Call the function and return the result
    return await TOOL_FNS[function_name].run(**function_arguments_dict, store=store)
