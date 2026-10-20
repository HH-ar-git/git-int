import json
import os

from internal.schema.message import BaseTool, ToolDefinition


class WriteFileTool(BaseTool):
    def __init__(self, work_dir: str):
        self.work_dir = work_dir

    def name(self) -> str:
        return "write_file"

    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name(),
            description="创建或覆盖写入一个文件，目录不存在会自动创建。",
            input_schema={
                "type": "object",
                "required": ["path", "content"],
                "properties": {
                    "path": {"type": "string", "description": "相对路径"},
                    "content": {"type": "string", "description": "要写入的内容"},
                },
            },
        )

    def execute(self, arguments: str) -> str:
        args = json.loads(arguments)
        path = args["path"]
        content = args["content"]
        full = os.path.join(self.work_dir, path)

        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)

        return f"已写入: {path}"
