"""
ReAct 引擎：两阶段执行
阶段一：慢思考（规划）—— 分析任务、制定计划，不调用工具
阶段二：行动循环 —— 思考→行动→观察，直到给出最终回答
"""
from cmd.claw.llm import LLM
from cmd.claw.registry import Registry


class ReActEngine:
    def __init__(self):
        self.llm = LLM()
        self.registry = Registry()
        self.max_steps = 10  # 最多循环步数，防止死循环

    def run(self, user_query: str) -> str:
        """
        完整执行一轮智能体任务
        ：用户的问题/任务
        ：最终回答
        """
        print("\n" + "=" * 60)
        print(f"收到任务: {user_query}")
        print("=" * 60)

        # ===== 阶段一：慢思考（规划） =====
        print("\n【阶段一：慢思考 / 任务规划】")
        plan = self._slow_thinking(user_query)
        print(f"规划结果:\n{plan}")

        # ===== 阶段二：行动循环 =====
        print("\n【阶段二：行动循环（思考→行动→观察）】")
        final_answer = self._act_loop(user_query, plan)

        print("\n" + "=" * 60)
        print(f"最终回答: {final_answer}")
        print("=" * 60 + "\n")
        return final_answer

    def _slow_thinking(self, user_query: str) -> str:
        """
        第一阶段：慢思考，只做规划，不调用工具
        让模型先想清楚要做什么、分几步、用哪些工具
        """
        tools_desc = self.registry.get_tools_description()
        system_prompt = f"""你是一个任务规划专家。请分析用户的任务，制定一个清晰的执行计划。

要求：
1. 不要调用任何工具，只做思考和规划
2. 分析任务目标是什么、需要分几步完成
3. 每一步大概需要用什么工具
4. 输出简洁明了的计划清单

{tools_desc}
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"任务: {user_query}\n\n请给出你的执行计划。"},
        ]
        plan = self.llm.chat(messages, temperature=0.2)
        return plan.strip()

    def _act_loop(self, user_query: str, plan: str) -> str:
        """
        第二阶段：行动循环
        思考 → 行动（调用工具）→ 观察（工具结果）→ 再思考...
        直到模型输出 FINAL_ANSWER
        """
        tools_desc = self.registry.get_tools_description()
        system_prompt = f"""你是一个终端编程智能体，按照 ReAct 范式执行任务。

{tools_desc}

工作规则：
1. 如果需要调用工具，按如下格式输出：
   工具名(参数名="参数值", 参数名2="参数值2")
2. 一次可以输出多个工具调用，每行一个
3. 如果你已经有足够的信息可以回答用户了，输出：
   FINAL_ANSWER: 你的最终回答
4. 不要输出多余的解释，只输出工具调用或 FINAL_ANSWER
5. 注意：路径都是相对于 workspace 目录的

参考执行计划：
{plan}
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query},
        ]

        for step in range(1, self.max_steps + 1):
            print(f"\n--- 第 {step} 轮 ---")

            # 1. 模型思考 + 输出行动
            response = self.llm.chat(messages, temperature=0.3)
            print(f"[模型输出]\n{response}")

            # 2. 检查是否是最终回答
            if "FINAL_ANSWER:" in response or "FINAL_ANSWER：" in response:
                # 提取最终回答
                for marker in ["FINAL_ANSWER:", "FINAL_ANSWER："]:
                    if marker in response:
                        answer = response.split(marker, 1)[1].strip()
                        return answer

            # 3. 解析工具调用
            calls = self.registry.parse_action(response)
            if not calls:
                # 没解析到工具调用，也没有 FINAL_ANSWER，可能是模型在自言自语
                # 把它的话作为思考，再问一次要不要调用工具
                messages.append({"role": "assistant", "content": response})
                messages.append({
                    "role": "user",
                    "content": "如果你需要调用工具，请按格式输出工具调用；如果已经可以回答，请输出 FINAL_ANSWER。"
                })
                continue

            # 4. 执行工具调用（自动并发只读 / 串行写）
            results = self.registry.execute_calls(calls)

            # 5. 把观察结果加回对话
            observation_text = "工具执行结果：\n"
            for r in results:
                observation_text += f"【{r['tool']}】\n{r['result']}\n\n"
            print(f"[观察结果]\n{observation_text}")

            messages.append({"role": "assistant", "content": response})
            messages.append({"role": "user", "content": observation_text + "请继续下一步：调用工具或输出 FINAL_ANSWER。"})

        # 超过最大步数，强制让模型总结
        messages.append({
            "role": "user",
            "content": "已经执行了很多步了，请基于现有信息直接给出 FINAL_ANSWER。"
        })
        response = self.llm.chat(messages, temperature=0.3)
        if "FINAL_ANSWER:" in response:
            return response.split("FINAL_ANSWER:", 1)[1].strip()
        return response
