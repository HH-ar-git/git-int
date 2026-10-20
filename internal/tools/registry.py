from internal.schema.message import (
    BaseTool, Registry, ToolCall, ToolResult, ToolDefinition,
)


class RegistryImpl(Registry):
    def __init__(self):
        self.tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        name = tool.name()
        if name in self.tools:
            print(f"[Warning] 工具 '{name}' 已存在，将被覆盖。")
        self.tools[name] = tool
        print(f"[Registry] 挂载工具: {name}")

    def get_available_tools(self) -> list[ToolDefinition]:
        return [t.definition() for t in self.tools.values()]

    def execute(self, call: ToolCall) -> ToolResult:
        tool = self.tools.get(call.name)
        if tool is None:
            return ToolResult(
                tool_call_id=call.tool_call_id,
                content=f"错误：找不到工具 {call.name}",
                is_error=True,
            )
        try:
            output = tool.execute(call.arguments)
            return ToolResult(
                tool_call_id=call.tool_call_id,
                content=output,
                is_error=False,
            )
        except Exception as e:
            return ToolResult(
                tool_call_id=call.tool_call_id,
                content=f"工具执行异常: {e}",
                is_error=True,
            )
