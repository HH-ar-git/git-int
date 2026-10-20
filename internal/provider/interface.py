from abc import ABC, abstractmethod
from internal.schema.message import Message, ToolDefinition

class LLMProvider(ABC):
    @abstractmethod
    def generate(self, messages: list[Message], available_tools: list[ToolDefinition] | None) -> Message:
        pass
