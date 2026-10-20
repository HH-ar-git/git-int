import sys
from pathlib import Path

# 把项目根目录加入模块搜索路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import os
from dotenv import load_dotenv
from openai import OpenAI

from internal.tools.registry import RegistryImpl
from internal.tools.read_file import ReadFileTool
from internal.tools.write_file import WriteFileTool
from internal.tools.edit_file import EditFileTool
from internal.tools.bash import BashTool
from internal.schema.message import ToolCall


load_dotenv(PROJECT_ROOT / ".env")

API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not API_KEY:
    raise RuntimeError("未在 .env 中找到 DEEPSEEK_API_KEY")

client = OpenAI(api_key=API_KEY, base_url="https://api.deepseek.com")

WORK_DIR = PROJECT_ROOT / "workspace"
WORK_DIR.mkdir(exist_ok=True)

# 注册四大工具
registry = RegistryImpl()
registry.register(ReadFileTool(str(WORK_DIR)))
registry.register(WriteFileTool(str(WORK_DIR)))
registry.register(EditFileTool(str(WORK_DIR)))
registry.register(BashTool(str(WORK_DIR)))


def to_openai_tools(defs):
    return [
        {
            "type": "function",
            "function": {
                "name": d.name,
                "description": d.description,
                "parameters": d.input_schema,
            },
        }
        for d in defs
    ]


TOOLS = to_openai_tools(registry.get_available_tools())

messages = [
    {"role": "system", "content": "你是本地工作区 Agent，严格按用户任务顺序调用工具。"},
    {"role": "user", "content": (
        "按顺序完成：\n"
        "1. write_file 创建 calc.py：定义 add(a,b) 返回 a+b，__main__ 中 print(add(2,3))\n"
        "2. bash 执行 python calc.py\n"
        "3. edit_file 把加法改成乘法（add 返回 a*b）\n"
        "4. read_file 读 calc.py 确认\n"
        "5. bash 再执行 python calc.py\n"
        "最后汇报两次运行输出。"
    )},
]

log = []
for rnd in range(1, 13):
    print(f"\n===== 第 {rnd} 轮 =====")
    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
        temperature=0,
    )
    msg = resp.choices[0].message
    messages.append(msg.model_dump())

    if not msg.tool_calls:
        print("\n[最终回答]")
        print(msg.content)
        break

    for tc in msg.tool_calls:
        name = tc.function.name
        args = tc.function.arguments
        log.append(name)
        print(f"🛠 {name}  args={args}")

        result = registry.execute(ToolCall(
            name=name, arguments=args, tool_call_id=tc.id,
        ))
        print(f"   -> {result.content[:300]}")

        messages.append({
            "role": "tool",
            "tool_call_id": tc.id,
            "content": result.content,
        })

print("\n========== 工具调用统计 ==========")
print(f"总次数: {len(log)}")
for i, n in enumerate(log, 1):
    print(f"  {i}. {n}")
