import json
import os

from internal.schema.message import BaseTool, ToolDefinition


class ReadFileTool(BaseTool):
    def __init__(self, work_dir: str):
        self.work_dir = work_dir

    def name(self) -> str:
        return "read_file"

    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name(),
            description="读取工作区内的文本文件，传入相对路径。",
            input_schema={
                "type": "object",
                "required": ["path"],
                "properties": {
                    "path": {"type": "string", "description": "工作区下相对文件路径"},
                },
            },
        )

    def execute(self, arguments: str) -> str:
        args = json.loads(arguments)
        rel = args["path"]
        full = os.path.join(self.work_dir, rel)

        # 防越界
        if not os.path.realpath(full).startswith(os.path.realpath(self.work_dir)):
            raise RuntimeError("路径越界")

        if not os.path.exists(full):
            raise RuntimeError(f"文件不存在: {rel}")

        with open(full, "r", encoding="utf-8") as f:
            return f.read()
