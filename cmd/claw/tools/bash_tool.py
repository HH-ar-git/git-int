"""
bash 工具：在 workspace 目录下执行 shell 命令
"""
import subprocess
import os

WORKSPACE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "workspace")


def run_bash(command: str) -> str:
    """
    执行 bash/shell 命令（在 workspace 目录下）
    注意：bash 可能是写操作，默认按串行处理
    :param command: 要执行的命令字符串
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            timeout=30,
            errors="replace",
        )
        output = ""
        if result.stdout:
            output += f"[标准输出]\n{result.stdout}\n"
        if result.stderr:
            output += f"[错误输出]\n{result.stderr}\n"
        if result.returncode != 0:
            output += f"[退出码] {result.returncode}"
        return output if output else f"命令执行成功，无输出（退出码 {result.returncode}）"
    except subprocess.TimeoutExpired:
        return "[错误] 命令执行超时（30秒）"
    except Exception as e:
        return f"[错误] 命令执行失败: {e}"
