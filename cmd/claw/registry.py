"""
工具注册表 Registry
负责：登记工具、查找工具、统一执行工具
支持：只读工具并发执行，写工具串行执行
"""
import re
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from cmd.claw.tools.file_tools import read_file, write_file, edit_file
from cmd.claw.tools.bash_tool import run_bash


class Tool:
    """单个工具的定义"""
    def __init__(self, name: str, description: str, params_desc: str, is_readonly: bool, func):
        self.name = name
        self.description = description
        self.params_desc = params_desc
        self.is_readonly = is_readonly  # 是否只读操作
        self.func = func

    def execute(self, **kwargs) -> str:
        """执行工具。参数不对时返回错误说明，不抛出异常"""
        try:
            return self.func(**kwargs)
        except TypeError as e:
            return f"[错误] 工具 {self.name} 参数不正确: {e}"


class Registry:
    def __init__(self):
        self.tools: dict[str, Tool] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        """注册四个内置工具"""
        self.register(Tool(
            name="read_file",
            description="读取指定文件的完整内容",
            params_desc='filename: 文件名（相对 workspace 目录）',
            is_readonly=True,  # 只读，可以并发
            func=read_file,
        ))
        self.register(Tool(
            name="write_file",
            description="写入文件，会覆盖原有内容",
            params_desc='filename: 文件名；content: 要写入的完整内容',
            is_readonly=False,  # 写操作，必须串行
            func=write_file,
        ))
        self.register(Tool(
            name="edit_file",
            description="编辑文件，把 old_text 替换成 new_text",
            params_desc='filename: 文件名；old_text: 要替换的原文；new_text: 替换后的新内容',
            is_readonly=False,  # 写操作，必须串行
            func=edit_file,
        ))
        self.register(Tool(
            name="bash",
            description="执行 shell 命令",
            params_desc='command: 要执行的命令字符串',
            is_readonly=False,  # bash 可能写文件，默认按串行处理
            func=run_bash,
        ))

    def register(self, tool: Tool):
        self.tools[tool.name] = tool

    def get_tool_names(self) -> list[str]:
        return list(self.tools.keys())

    def get_tools_description(self) -> str:
        """生成给模型看的工具说明"""
        lines = ["可用工具列表："]
        for t in self.tools.values():
            lines.append(f"- {t.name}: {t.description}")
            lines.append(f"  参数: {t.params_desc}")
        return "\n".join(lines)

    @staticmethod
    def _scan_args(text: str, start: int):
        """
        从 start 位置开始扫描，找到与 '(' 配对的 ')'
        正确处理引号内的括号和转义字符，避免内容里出现 ) 就被截断
        """
        depth = 1
        quote = None
        i = start
        while i < len(text):
            ch = text[i]
            if quote:
                if ch == "\\":
                    i += 2
                    continue
                if ch == quote:
                    quote = None
            else:
                if ch in ('"', "'"):
                    quote = ch
                elif ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                    if depth == 0:
                        return text[start:i]
            i += 1
        return None

    @staticmethod
    def _parse_args(arg_str: str) -> dict:
        """解析参数名="值"，支持引号内的转义字符"""
        args = {}
        pattern = r'(\w+)\s*=\s*("(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\')'
        for m in re.finditer(pattern, arg_str):
            key = m.group(1)
            raw = m.group(2)[1:-1]
            # 还原转义字符
            raw = raw.replace('\\n', '\n').replace('\\"', '"').replace("\\'", "'").replace('\\\\', '\\')
            args[key] = raw
        return args

    def parse_action(self, text: str) -> list[dict]:
        """
        从模型输出中解析出要执行的工具调用
        支持格式：工具名(参数名="参数值", 参数名2="参数值2")
        支持一次输出多个工具调用，参数值内部可包含括号、换行和转义引号
        返回: [{"tool": "read_file", "args": {"filename": "a.txt"}}, ...]
        """
        calls = []
        for m in re.finditer(r'\b(\w+)\s*\(', text):
            tool_name = m.group(1)
            if tool_name not in self.tools:
                continue
            args_str = self._scan_args(text, m.end())
            if args_str is None:
                continue
            args = self._parse_args(args_str)
            calls.append({"tool": tool_name, "args": args})
        return calls

    def execute_calls(self, calls: list[dict]) -> list[dict]:
        """
        批量执行工具调用
        策略：把只读的放一起并发执行，写的按顺序串行执行
        返回: [{"tool": "...", "result": "..."}, ...]
        """
        results = []

        # 分类：只读 vs 写
        readonly_calls = []
        write_calls = []
        for c in calls:
            tool = self.tools.get(c["tool"])
            if tool and tool.is_readonly:
                readonly_calls.append(c)
            else:
                write_calls.append(c)

        # 1. 并发执行只读工具
        if readonly_calls:
            print(f"  [并发] 同时执行 {len(readonly_calls)} 个只读工具: {[c['tool'] for c in readonly_calls]}")
            with ThreadPoolExecutor(max_workers=len(readonly_calls)) as executor:
                future_to_call = {}
                for c in readonly_calls:
                    tool = self.tools[c["tool"]]
                    future = executor.submit(tool.execute, **c["args"])
                    future_to_call[future] = c
                for future in as_completed(future_to_call):
                    c = future_to_call[future]
                    try:
                        result = future.result()
                    except Exception as e:
                        result = f"[工具执行异常] {e}"
                    results.append({"tool": c["tool"], "result": result})

        # 2. 串行执行写工具
        for c in write_calls:
            tool = self.tools.get(c["tool"])
            if not tool:
                results.append({"tool": c["tool"], "result": f"[错误] 未知工具: {c['tool']}"})
                continue
            print(f"  [串行] 执行写工具: {c['tool']}")
            try:
                result = tool.execute(**c["args"])
            except Exception as e:
                result = f"[工具执行异常] {e}"
            results.append({"tool": c["tool"], "result": result})

        return results
