# internal/engine/loop.py
# 对应 Go 版: internal/engine/loop.go
# 第 3 章：引入"慢思考"(Thinking Phase)：先剥夺工具强制模型规划，再放开工具让它行动。
import logging

from internal.provider.interface import LLMProvider
from internal.schema.message import Message, ROLE_SYSTEM, ROLE_USER
from internal.tools.registry import Registry

log = logging.getLogger(__name__)


class AgentEngine:
    def __init__(self, provider: LLMProvider, registry: Registry, work_dir: str, enable_thinking: bool):
        self.provider = provider
        self.registry = registry
        self.work_dir = work_dir
        self.enable_thinking = enable_thinking

    def run(self, user_prompt: str) -> None:
        log.info("[Engine] 引擎启动，锁定工作区: %s", self.work_dir)
        log.info("[Engine] 慢思考模式 (Thinking Phase): %s", self.enable_thinking)

        context_history: list[Message] = [
            Message(
                role=ROLE_SYSTEM,
                content="You are py-tiny-claw, an expert coding assistant. You have full access to tools in the workspace.",
            ),
            Message(
                role=ROLE_USER,
                content=user_prompt,
            ),
        ]

        turn_count = 0

        while True:
            turn_count += 1
            log.info("\n========== [Turn %d] 开始 ==========", turn_count)

            available_tools = self.registry.get_available_tools()

            # ================= Phase 1: Thinking =================


            # ================= Phase 2: Reason =================


            # ================= 执行判断 =================


            # ================= Act + Observe =================
