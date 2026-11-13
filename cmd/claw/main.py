"""
TinyClaw 终端对话入口
运行方式：python -m cmd.claw.main  或  直接运行本文件
"""
import os
import sys

# 把项目根目录加到 sys.path，保证直接运行也能找到包
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

from cmd.claw.engine import ReActEngine


def main():
    # 检查 API Key
    if not os.getenv("LLM_API_KEY"):
        print("=" * 50)
        print("错误：未配置 LLM_API_KEY")
        print("请在项目根目录创建 .env 文件，参考 .env.example")
        print("=" * 50)
        sys.exit(1)

    engine = ReActEngine()

    print("=" * 50)
    print("  TinyClaw 终端对话模式已启动")
    print("  输入你的问题（输入 exit 退出）")
    print("=" * 50)

    while True:
        try:
            user_input = input("\n你: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n再见！")
            break

        if not user_input:
            continue
        if user_input.lower() == "exit":
            print("再见！")
            break

        try:
            engine.run(user_input)
        except Exception as e:
            print(f"\n[出错了] {e}")
            print("程序继续运行，你可以再试一次。")


if __name__ == "__main__":
    main()
