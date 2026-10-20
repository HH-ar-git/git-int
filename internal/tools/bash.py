import json
import subprocess

from internal.schema.message import BaseTool, ToolDefinition

MAX_OUTPUT = 8000
TIMEOUT = 30


class BashTool(BaseTool):
    def __init__(self, work_dir: str):
        self.work_dir = work_dir

    def name(self) -> str:
        return "bash"

    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name(),
            description="在工作区执行 bash 命令，30 秒超时，输出自动截断。",
            input_schema={
                "type": "object",
                "required": ["command"],
                "properties": {
                    "command": {"type": "string", "description": "要执行的命令"},
                },
            },
        )

    def execute(self, arguments: str) -> str:
        args = json.loads(arguments)
        cmd = args["command"]

        try:
            p = subprocess.run(
                ["bash", "-c", cmd],
                cwd=self.work_dir,
                capture_output=True,
                text=True,
                timeout=TIMEOUT,
            )
            out = p.stdout + p.stderr
            if p.returncode != 0:
                out = f"[exit {p.returncode}]\n" + out
        except subprocess.TimeoutExpired:
            out = f"[超时: 命令超过 {TIMEOUT}s 被强制终止]"

        if not out.strip():
            out = "命令执行成功，无输出。"

        if len(out) > MAX_OUTPUT:
            out = out[:MAX_OUTPUT] + f"\n...[输出已截断，原始长度 {len(out)}]"

        return out
