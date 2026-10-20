from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ToolDefinition:
    name: str
    description: str
    input_schema: dict


@dataclass
class ToolCall:
    name: str
    arguments: str          # JSON 字符串
    tool_call_id: str


@dataclass
class ToolResult:
    tool_call_id: str
    content: str
    is_error: bool = False


class BaseTool(ABC):
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def definition(self) -> ToolDefinition:
        ...

    @abstractmethod
    def execute(self, arguments: str) -> str:
        ...


class Registry(ABC):
    @abstractmethod
    def register(self, tool: BaseTool) -> None:
        ...

    @abstractmethod
    def get_available_tools(self) -> list[ToolDefinition]:
        ...

    @abstractmethod
    def execute(self, call: ToolCall) -> ToolResult:
        ...
