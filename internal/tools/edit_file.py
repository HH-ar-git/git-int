import json
import os

from internal.schema.message import BaseTool, ToolDefinition


class EditFileTool(BaseTool):
    def __init__(self, work_dir: str):
        self.work_dir = work_dir

    def name(self) -> str:
        return "edit_file"

    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name=self.name(),
            description=(
                "对文件做局部替换。old_text 必须在文件中唯一命中；"
                "0 处或多处命中都会报错，不擅自替换。"
            ),
            input_schema={
                "type": "object",
                "required": ["path", "old_text", "new_text"],
                "properties": {
                    "path": {"type": "string"},
                    "old_text": {"type": "string", "description": "要被替换的原文"},
                    "new_text": {"type": "string", "description": "替换后的新文"},
                },
            },
        )

    def execute(self, arguments: str) -> str:
        args = json.loads(arguments)
        path = args["path"]
        old_text = args["old_text"]
        new_text = args["new_text"]

        full = os.path.join(self.work_dir, path)
        if not os.path.exists(full):
            raise RuntimeError(f"文件不存在: {path}")

        with open(full, "r", encoding="utf-8") as f:
            content = f.read()

        new_content = fuzzy_replace(content, old_text, new_text)

        with open(full, "w", encoding="utf-8") as f:
            f.write(new_content)

        return f"已在 {path} 完成一处替换。"


def fuzzy_replace(original: str, old: str, new: str) -> str:
    # L1 精确
    c = original.count(old)
    if c == 1:
        return original.replace(old, new)
    if c > 1:
        raise RuntimeError(f"L1 命中 {c} 处，需更多上下文")

    # L2 换行归一化
    no = original.replace("\r\n", "\n")
    nold = old.replace("\r\n", "\n")
    c2 = no.count(nold)
    if c2 == 1:
        return no.replace(nold, new)
    if c2 > 1:
        raise RuntimeError(f"L2 命中 {c2} 处，需更多上下文")

    # L3 去首尾空白
    s = nold.strip()
    if s:
        c3 = no.count(s)
        if c3 == 1:
            return no.replace(s, new)
        if c3 > 1:
            raise RuntimeError(f"L3 命中 {c3} 处，需更多上下文")

    # L4 逐行去缩进
    return line_by_line_replace(no, nold, new)


def line_by_line_replace(content: str, old: str, new: str) -> str:
    file_lines = content.splitlines(keepends=True)
    old_lines = [ln for ln in old.splitlines() if ln.strip()]
    if not old_lines:
        raise RuntimeError("old_text 全是空白")

    old_stripped = [ln.strip() for ln in old_lines]
    n = len(old_stripped)

    match_count = 0
    match_start = -1
    for i in range(len(file_lines) - n + 1):
        if all(file_lines[i + j].strip() == old_stripped[j] for j in range(n)):
            match_count += 1
            match_start = i

    if match_count == 0:
        raise RuntimeError("L4 未匹配到 old_text")
    if match_count > 1:
        raise RuntimeError(f"L4 命中 {match_count} 处，需更多上下文")

    head = file_lines[:match_start]
    tail = file_lines[match_start + n:]
    new_block = [ln + "\n" for ln in new.splitlines()]
    return "".join(head + new_block + tail)
