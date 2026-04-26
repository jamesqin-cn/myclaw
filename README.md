# 🦞 300 行手把手教你写一只迷你小龙虾

> 从零开始，用 Python 实现一个支持工具调用的 Mini LLM Agent

---

## 🎯 你会学到什么

本教程带你从最简单的一次问答出发，一步步构建一个完整的 **迷你 AI Agent**（我们叫它"小龙虾"）：

| 阶段 | 目标 | 关键概念 |
|------|------|---------|
| **第一步** | 单次聊天 | HTTP 请求、Chat Completions API |
| **第二步** | 多轮对话 | 对话历史、上下文管理 |
| **第三步** | 执行系统命令 | 工具调用（Tool Use）、Agentic Loop |
| **第四步** | 加载技能文件 | SKILL 注入、可扩展提示工程 |

**什么是 Agent（智能体）？** 简单说，就是让 AI 不只会"说"，还能"做"——能调用工具、执行操作、拿到结果后继续推理。小龙虾就是最小化的 Agent。

---

## 🛠 环境准备

```bash
# Python 3.10+，创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装唯一依赖
pip install requests
```

你还需要一个支持 **OpenAI Chat Completions 格式** 的 API Key。推荐使用 [OpenRouter](https://openrouter.ai)（注册即有免费额度）。

---

## 第一步：单次聊天 🐣

> **目标**：发一条消息，收到一条回复，搞定。
>
> **技术术语**：调用 `Chat Completions` 接口，发送 `messages` 列表，获取模型输出。
>
> **通俗解释**：就是给 AI 写一封信，然后读它的回信。

### 原理

所有主流大模型 API 都遵循同一个格式：

```
你 → POST /chat/completions → { messages: [{role: "user", content: "你好"}] }
AI ← { choices: [{ message: { role: "assistant", content: "你好！" } }] }
```

`messages` 就是一个数组，每条消息有两个字段：
- `role`：谁说的（`user` = 你，`assistant` = AI）
- `content`：说了什么

### 代码

```python
# lobster_v1.py — 第一步：单次聊天
import os
import requests

API_KEY  = os.getenv("LLM_API_KEY", "your-key")
BASE_URL = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
MODEL    = os.getenv("LLM_MODEL",    "openrouter/free")


def chat_once(prompt: str) -> str:
    """发一条消息，返回 AI 回复文本"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type":  "application/json",
    }
    payload = {
        "model":    MODEL,
        "messages": [{"role": "user", "content": prompt}],
    }
    resp = requests.post(f"{BASE_URL}/chat/completions",
                         headers=headers, json=payload)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


if __name__ == "__main__":
    prompt = input("👤 你：")
    reply  = chat_once(prompt)
    print(f"🤖 AI：{reply}")
```

**运行一下：**

```bash
python3 lobster_v1.py
👤 你：你好，介绍一下自己
🤖 AI：你好！我是一个 AI 助手……
```

就这 30 行，小龙虾的雏形已经在了。🦞

---

## 第二步：多轮对话 🐠

> **目标**：让 AI 记住你之前说过的话，实现连续对话。
>
> **技术术语**：维护 **对话历史（Conversation History）**，每次请求时携带完整的上下文（Context）。
>
> **通俗解释**：AI 本身没有记忆，每次请求都是"全新的"。要让它"记得"，得把之前所有对话都打包一起发给它——就像每次通话都把之前的聊天记录念一遍给对方听。

### 关键变化：messages 变成一个"滚动的日记本"

```
第1轮：messages = [ {user: "你好"} ]
第2轮：messages = [ {user: "你好"}, {assistant: "你好！"}, {user: "你叫什么名字？"} ]
第3轮：messages = [ ..前两轮.., {assistant: "我叫..."}, {user: "你会什么？"} ]
```

### 代码

和 v1 相比，新增代码用 `# ★ NEW` 标出：

```python
# lobster_v2.py — 第二步：多轮对话

import os
import requests

API_KEY  = os.getenv("LLM_API_KEY", "your-key")
BASE_URL = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
MODEL    = os.getenv("LLM_MODEL",    "openrouter/free")


def call_api(messages: list[dict]) -> str:
    """调用 API，传入完整消息列表"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type":  "application/json",
    }
    payload = {"model": MODEL, "messages": messages}
    resp = requests.post(f"{BASE_URL}/chat/completions",
                         headers=headers, json=payload)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def run():                                                # ★ NEW
    history: list[dict] = []                              # ★ NEW 存储对话历史

    print("输入 quit 退出，clear 清空历史\n")              # ★ NEW

    while True:                                           # ★ NEW
        prompt = input("👤 你：").strip()                  # ★ NEW

        if not prompt:                                    # ★ NEW
            continue                                      # ★ NEW
        if prompt.lower() in ("quit", "exit", "q"):      # ★ NEW
            print("再见！"); break                         # ★ NEW
        if prompt.lower() == "clear":                     # ★ NEW
            history = []                                  # ★ NEW
            print("历史已清空\n"); continue                # ★ NEW

        # ★ NEW：把当前问题追加到历史，一起发给 AI
        history.append({"role": "user", "content": prompt})           # ★ NEW
        reply = call_api(history)                                      # ★ NEW
        print(f"🤖 AI：{reply}\n")

        # ★ NEW：把 AI 回复也存入历史，供下轮使用
        history.append({"role": "assistant", "content": reply})       # ★ NEW

        # ★ NEW：历史太长会超出 token 限制，保留最近 20 条
        if len(history) > 20:                                         # ★ NEW
            history = history[-20:]                                    # ★ NEW


if __name__ == "__main__":
    run()
```

**运行效果：**

```
👤 你：我叫 James
🤖 AI：你好 James！

👤 你：我叫什么名字？
🤖 AI：你刚才告诉我你叫 James！
```

AI 现在有记忆了。🧠

---

## 第三步：执行系统命令（工具调用） ⚙️

> **目标**：让 AI 能主动调用系统命令，拿到真实数据再回答。
>
> **技术术语**：**工具调用（Tool Use / Function Calling）**、**Agentic Loop（智能体循环）**。
>
> **通俗解释**：我们给 AI "一套工具"的使用说明，告诉它"如果要执行命令，就用这个格式写出来"。然后我们的程序读懂格式、真正去执行，把结果返回给 AI，让它继续回答。就像给助理一部电话——它自己可以打电话问别人，再来告诉你答案。

### Agentic Loop 是什么？

```
用户提问
    ↓
AI 推理 → 需要信息吗？
    ↓              ↓
   需要           不需要
    ↓              ↓
生成命令        直接回答
    ↓
本地执行命令
    ↓
把结果还给 AI
    ↓
AI 基于结果再次推理 → 给出最终答案
```

这个"提问 → 工具 → 结果 → 再推理"的循环就叫 **Agentic Loop**。

### 约定命令格式

我们用一个简单的 Markdown 代码块作为"信号"：

````
```command
ls -la
```
````

AI 只要在回复里包含这段，就代表它想执行命令。

### 代码

```python
# lobster_v3.py — 第三步：执行系统命令

import os
import re                   # ★ NEW
import subprocess           # ★ NEW
import requests

API_KEY  = os.getenv("LLM_API_KEY", "your-key")
BASE_URL = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
MODEL    = os.getenv("LLM_MODEL",    "openrouter/free")

# ★ NEW：系统提示，教 AI 如何"呼叫"命令
SYSTEM_PROMPT = """你是一个智能助手，可以执行系统命令来帮助用户。

当你需要执行系统命令时，使用如下格式：

\```command
你的命令
\```

执行后我会把结果返回给你，你再继续回答用户。

注意：只在必要时执行命令，避免危险操作（如 rm -rf /）。
"""


def call_api(messages: list[dict]) -> str:
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type":  "application/json",
    }
    payload = {"model": MODEL, "messages": messages}
    resp = requests.post(f"{BASE_URL}/chat/completions",
                         headers=headers, json=payload)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def parse_command(text: str) -> str | None:           # ★ NEW
    """从 AI 回复中提取 ```command ... ``` 里的命令"""  # ★ NEW
    m = re.search(r'```command\s*(.*?)\s*```',        # ★ NEW
                  text, re.DOTALL)                    # ★ NEW
    return m.group(1).strip() if m else None           # ★ NEW


def run_command(cmd: str, timeout: int = 30) -> str:  # ★ NEW
    """本地执行命令，返回输出文本"""                    # ★ NEW
    try:                                               # ★ NEW
        r = subprocess.run(cmd, shell=True,            # ★ NEW
                           capture_output=True,        # ★ NEW
                           text=True, timeout=timeout) # ★ NEW
        out = ""                                       # ★ NEW
        if r.stdout: out += f"stdout:\n{r.stdout}"    # ★ NEW
        if r.stderr: out += f"stderr:\n{r.stderr}"    # ★ NEW
        out += f"exit code: {r.returncode}"           # ★ NEW
        return out                                     # ★ NEW
    except subprocess.TimeoutExpired:                 # ★ NEW
        return "命令超时"                              # ★ NEW
    except Exception as e:                            # ★ NEW
        return f"执行出错：{e}"                        # ★ NEW


def run():
    history: list[dict] = []
    print("输入 quit 退出，clear 清空历史\n")

    # ★ NEW：首次对话把系统提示作为第一条 user 消息注入
    first_turn = True                                  # ★ NEW

    while True:
        prompt = input("👤 你：").strip()

        if not prompt: continue
        if prompt.lower() in ("quit", "exit", "q"):
            print("再见！"); break
        if prompt.lower() == "clear":
            history = []; first_turn = True            # ★ NEW
            print("历史已清空\n"); continue

        # ★ NEW：首次把系统提示拼到第一条用户消息前
        if first_turn:                                 # ★ NEW
            full_prompt = SYSTEM_PROMPT + "\n\n用户问：" + prompt  # ★ NEW
            first_turn = False                         # ★ NEW
        else:                                          # ★ NEW
            full_prompt = prompt                       # ★ NEW

        history.append({"role": "user", "content": full_prompt})
        reply = call_api(history)

        # ★ NEW：检测命令，进入 Agentic Loop
        cmd = parse_command(reply)                     # ★ NEW
        if cmd:                                        # ★ NEW
            print(f"\n⚙️  执行命令：{cmd}")             # ★ NEW
            print("-" * 40)                            # ★ NEW
            result = run_command(cmd)                  # ★ NEW
            print(result)                              # ★ NEW
            print("-" * 40)                            # ★ NEW

            # ★ NEW：把命令结果作为 user 消息还给 AI
            history.append({"role": "assistant", "content": reply})      # ★ NEW
            history.append({"role": "user",                              # ★ NEW
                            "content": f"命令执行结果：\n{result}\n请继续回答。"})  # ★ NEW
            reply = call_api(history)                  # ★ NEW

        print(f"🤖 AI：{reply}\n")
        history.append({"role": "assistant", "content": reply})

        if len(history) > 24:
            history = history[-24:]


if __name__ == "__main__":
    run()
```

**运行效果：**

```
👤 你：当前目录有哪些文件？

⚙️  执行命令：ls -la
----------------------------------------
stdout:
total 32
-rw-r--r--  1 james  staff  8177 Apr 26 simple_llm.py
...
exit code: 0
----------------------------------------
🤖 AI：当前目录包含以下文件：simple_llm.py（8177 字节）……
```

小龙虾的爪子伸出来了！🦞🦀

---

## 第四步：加载技能文件（SKILL 注入） 📖

> **目标**：让小龙虾通过读取外部文件来"学技能"，无需改代码就能扩展能力。
>
> **技术术语**：**提示工程（Prompt Engineering）**、**动态上下文注入（Dynamic Context Injection）**、**可扩展插件架构**。
>
> **通俗解释**：就像给员工一本《操作手册》，告诉他遇到什么情况该怎么做。我们把手册写在 `SKILL.md` 里，每次对话时偷偷塞进 AI 的"记忆开头"，AI 就会按手册行事——而且改手册不用改代码。

### SKILL.md 示例

```markdown
# Skills

## 天气查询

当用户询问天气时，执行：

\```command
curl -s "https://wttr.in/城市名?format=%t%l%w"
\```

示例：北京天气 → `curl -s "https://wttr.in/北京?format=%t%l%w"`
```

### 代码

```python
# lobster_v4.py — 第四步：加载技能文件

import os
import re
import subprocess
import requests

API_KEY  = os.getenv("LLM_API_KEY", "your-key")
BASE_URL = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
MODEL    = os.getenv("LLM_MODEL",    "openrouter/free")

BASE_SYSTEM_PROMPT = """你是一个智能助手，可以执行系统命令来帮助用户。

当你需要执行系统命令时，使用如下格式：

\```command
你的命令
\```

执行后我会把结果返回给你，你再继续回答用户。
注意：只在必要时执行命令，避免危险操作（如 rm -rf /）。
"""


def load_skill_file() -> str:                          # ★ NEW
    """读取同目录下的 SKILL.md，返回内容；不存在则返回空"""  # ★ NEW
    path = os.path.join(os.path.dirname(              # ★ NEW
               os.path.abspath(__file__)), "SKILL.md") # ★ NEW
    if not os.path.exists(path):                      # ★ NEW
        return ""                                      # ★ NEW
    with open(path, encoding="utf-8") as f:           # ★ NEW
        return f.read()                                # ★ NEW


def build_system_prompt() -> str:                     # ★ NEW
    """每次构建系统提示时，动态拼入最新的 SKILL.md"""    # ★ NEW
    skill = load_skill_file()                          # ★ NEW
    if skill:                                          # ★ NEW
        return BASE_SYSTEM_PROMPT + "\n## 可用技能\n\n" + skill  # ★ NEW
    return BASE_SYSTEM_PROMPT                          # ★ NEW


def call_api(messages: list[dict]) -> str:
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type":  "application/json",
    }
    payload = {"model": MODEL, "messages": messages}
    resp = requests.post(f"{BASE_URL}/chat/completions",
                         headers=headers, json=payload)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def parse_command(text: str) -> str | None:
    m = re.search(r'```command\s*(.*?)\s*```', text, re.DOTALL)
    return m.group(1).strip() if m else None


def run_command(cmd: str, timeout: int = 30) -> str:
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True,
                           text=True, timeout=timeout)
        out = ""
        if r.stdout: out += f"stdout:\n{r.stdout}"
        if r.stderr: out += f"stderr:\n{r.stderr}"
        out += f"exit code: {r.returncode}"
        return out
    except subprocess.TimeoutExpired:
        return "命令超时"
    except Exception as e:
        return f"执行出错：{e}"


def run():
    print("\n🦞 迷你小龙虾启动！")

    # ★ NEW：每次启动时读取 SKILL.md，打印加载状态
    skill = load_skill_file()                          # ★ NEW
    if skill:                                          # ★ NEW
        print("✅ 已加载 SKILL.md")                    # ★ NEW
    else:                                              # ★ NEW
        print("（未找到 SKILL.md，以基础模式运行）")    # ★ NEW

    print("输入 quit 退出，clear 清空历史\n")
    history: list[dict] = []
    first_turn = True

    while True:
        prompt = input("👤 你：").strip()

        if not prompt: continue
        if prompt.lower() in ("quit", "exit", "q"):
            print("再见！"); break
        if prompt.lower() == "clear":
            history = []; first_turn = True
            print("历史已清空\n"); continue

        if first_turn:
            # ★ NEW：每次 clear 后首轮重新构建系统提示（包含最新 SKILL.md）
            system = build_system_prompt()             # ★ NEW
            full_prompt = system + "\n\n用户问：" + prompt  # ★ NEW（改用 build_system_prompt）
            first_turn = False
        else:
            full_prompt = prompt

        history.append({"role": "user", "content": full_prompt})
        reply = call_api(history)

        cmd = parse_command(reply)
        if cmd:
            print(f"\n⚙️  执行命令：{cmd}")
            print("-" * 40)
            result = run_command(cmd)
            print(result)
            print("-" * 40)

            history.append({"role": "assistant", "content": reply})
            history.append({"role": "user",
                            "content": f"命令执行结果：\n{result}\n请继续回答。"})
            reply = call_api(history)

        print(f"🤖 AI：{reply}\n")
        history.append({"role": "assistant", "content": reply})

        if len(history) > 24:
            history = history[-24:]


if __name__ == "__main__":
    run()
```

**现在，只需编辑 SKILL.md 就能给小龙虾添加新技能，完全不用碰代码。**

```
👤 你：深圳今天天气怎样？

⚙️  执行命令：curl -s "https://wttr.in/深圳?format=%t%l%w"
----------------------------------------
stdout:
+28°C 深圳 ⛅
exit code: 0
----------------------------------------
🤖 AI：深圳今天气温 28°C，天气多云，适合出行 ☀️
```

---

## 🧩 完整演进路线图

```
lobster_v1.py          lobster_v2.py          lobster_v3.py          lobster_v4.py
──────────────         ──────────────         ──────────────         ──────────────
chat_once()     →→→    run() + history  →→→   + SYSTEM_PROMPT  →→→   + SKILL.md
                                              + parse_command()       + load_skill_file()
                                              + run_command()         + build_system_prompt()
                                              Agentic Loop
```

每一步都只新增 **10~20 行核心代码**，思路是：
1. 先能"说话"（API 调用）
2. 再能"记住"（历史管理）
3. 再能"做事"（命令执行 + Agentic Loop）
4. 再能"学技能"（动态提示注入）

---

## 🚀 运行本项目

本仓库已包含第四步的完整版本 `simple_llm.py`：

```bash
# 安装依赖
python3 -m venv .venv && source .venv/bin/activate
pip install requests

# 配置环境变量
export LLM_API_KEY=your-openrouter-key
export LLM_BASE_URL=https://openrouter.ai/api/v1
export LLM_MODEL=openrouter/free

# 启动！
python3 simple_llm.py
```

### 扩展技能

直接编辑 `SKILL.md`，按如下格式追加即可：

````markdown
## 新技能名称

当用户询问 XXX 时，执行：

```command
your-command-here
```
````

无需重启，下次 `clear` 后即可生效。

---

## 📁 项目结构

```
myclaw/
├── simple_llm.py      # 完整版小龙虾（第四步）
├── SKILL.md           # 技能文件（可自由扩展）
├── README.md          # 本教程
└── run.sh             # 快捷启动脚本
```

---

## 💡 下一步你可以探索

- **流式输出（Streaming）**：把 `stream: true` 加到请求，像打字机一样逐字显示回复
- **多工具支持**：解析多个 ` ```command ``` ` 块，一次执行多个命令
- **工具结果再循环**：命令执行后允许 AI 继续生成新命令，直到它说"完成"
- **接入 MCP**：使用标准化的 Model Context Protocol，接入更多外部工具

---

*🦞 恭喜你！你已经手写了一只会思考、会执行、会学技能的迷你小龙虾 Agent。*
