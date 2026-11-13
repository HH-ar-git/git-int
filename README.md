# TinyClaw 终端版微型编程智能体

## 项目结构

```
py-tiny-claw/
├── cmd/
│   └── claw/
│       ├── __init__.py
│       ├── main.py          # 终端对话入口
│       ├── engine.py         # ReAct 引擎（两阶段）
│       ├── registry.py       # 工具注册表
│       ├── llm.py            # 大模型调用封装
│       └── tools/
│           ├── __init__.py
│           ├── file_tools.py # read_file / write_file / edit_file
│           └── bash_tool.py  # bash 命令执行
├── workspace/               # 工作目录，所有文件操作都在这里
├── .env.example             # 环境变量示例
└── requirements.txt         # Python 依赖
```

## 快速开始

1. 安装依赖：
   ```
   pip install -r requirements.txt
   ```

2. 配置 API Key：
   复制 `.env.example` 为 `.env`，填入你的 `LLM_API_KEY` 和其他配置

3. 运行：
   ```
   python -m cmd.claw.main
   ```

## 功能说明

### 四项核心任务
1. **终端对话模式**：循环输入问题，exit 退出
2. **两阶段 ReAct**：先慢思考做规划，再进入"思考→行动→观察"循环
3. **工具与 Registry**：read_file / write_file / edit_file / bash 四个工具统一注册执行
4. **只读并发、涉写串行**：多个只读工具同时执行，写工具按顺序执行

### 工具列表
| 工具 | 说明 | 类型 |
|---|---|---|
| read_file | 读取文件内容 | 只读（可并发） |
| write_file | 写入文件 | 写（串行） |
| edit_file | 编辑文件内容 | 写（串行） |
| bash | 执行 shell 命令 | 写（串行） |
