import os
from openai import OpenAI
from internal.provider.interface import LLMProvider
from internal.schema.message import (
    Message, ROLE_SYSTEM, ROLE_USER, ROLE_ASSISTANT,
    ToolCall, ToolDefinition
)

class OpenAIProvider(LLMProvider):
    def __init__(self, client: OpenAI, model: str):
        self.client = client
        self.model = model

    def generate(self, msgs: list[Message], available_tools: list[ToolDefinition] | None):
        # 第1步：内部Message → OpenAI消息格式
        openai_msgs = []
        for msg in msgs:
            if msg.role == ROLE_SYSTEM:
                openai_msgs.append({"role": "system", "content": msg.content})
            elif msg.role == ROLE_USER:
                if msg.tool_call_id != "":
                    openai_msgs.append({
                        "role": "tool",
                        "content": msg.content,
                        "tool_call_id": msg.tool_call_id
                    })
                else:
                    openai_msgs.append({"role": "user", "content": msg.content})
            elif msg.role == ROLE_ASSISTANT:
                assist_item = {"role": "assistant"}
                if msg.content:
                    assist_item["content"] = msg.content
                if len(msg.tool_calls) > 0:
                    tc_list = []
                    for tc in msg.tool_calls:
                        tc_list.append({
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.name,
                                "arguments": tc.arguments
                            }
                        })
                    assist_item["tool_calls"] = tc_list
                openai_msgs.append(assist_item)

        # 第2步：ToolDefinition → openai tools格式，调用API
        openai_tools = []
        if available_tools is not None:
            for td in available_tools:
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": td.name,
                        "description": td.description,
                        "parameters": td.input_schema
                    }
                })

        params = {
            "model": self.model,
            "messages": openai_msgs
        }
        if len(openai_tools) > 0:
            params["tools"] = openai_tools

        resp = self.client.chat.completions.create(**params)
        if len(resp.choices) == 0:
            raise RuntimeError("API返回空choices")
        choice = resp.choices[0].message

        # 第3步：API响应转回内部Message
        result_msg = Message(role=ROLE_ASSISTANT, content=choice.content or "")
        if choice.tool_calls:
            for tc in choice.tool_calls:
                result_msg.tool_calls.append(ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=tc.function.arguments
                ))
        return result_msg


def new_deepseek_provider(model: str) -> OpenAIProvider:
    """构造DeepSeek Provider，复用OpenAIProvider"""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("环境变量 DEEPSEEK_API_KEY 未设置，请配置！")
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )
    return OpenAIProvider(client, model)
