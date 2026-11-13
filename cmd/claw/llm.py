"""
LLM 调用封装
使用 OpenAI 兼容接口，支持任意兼容的 API 地址
"""
import os
from openai import OpenAI


class LLM:
    def __init__(self):
        self.client = OpenAI(
            base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
            api_key=os.getenv("LLM_API_KEY", ""),
        )
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    def chat(self, messages: list[dict], temperature: float = 0.3) -> str:
        """
        调用大模型，返回文本回复
        messages 格式: [{"role": "system"/"user"/"assistant", "content": "..."}]
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
        )
        return response.choices[0].message.content
