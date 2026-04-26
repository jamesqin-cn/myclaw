#!/usr/bin/env python3
"""
Custom LLM Chat Script
一个简单的命令行大模型交互脚本，支持工具调用
"""

import os
import json
import requests
import subprocess
import re
from typing import Optional, Dict, Any


class CustomClient:
    """自定义大模型客户端"""
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
    
    def chat(self, messages: list[dict], model: str = "default", **kwargs) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
            **kwargs
        }
        response = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


def build_messages(prompt: str, history: Optional[list[dict]] = None, 
                   include_system: bool = False, system_prompt: str = "") -> list[dict]:
    """构建消息列表"""
    messages = []
    
    # 如果需要包含系统提示，将其作为第一条 user 消息
    if include_system and system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    # 添加历史消息
    if history:
        messages.extend(history)
    
    # 添加当前用户消息
    messages.append({"role": "user", "content": prompt})
    
    return messages


def get_skills_content() -> str:
    """读取 SKILL.md 文件内容"""
    skill_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "SKILL.md")
    try:
        with open(skill_file, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""
    except Exception as e:
        return f"⚠️ 读取 SKILL.md 失败：{e}"


def get_system_prompt() -> str:
    """获取系统提示，告诉 AI 如何请求执行命令"""
    skills = get_skills_content()
    skills_section = ""
    if skills:
        skills_section = f"""
## 可用技能

{skills}
"""
    
    return f"""你是一个智能助手，可以执行系统命令来帮助用户。

当你需要执行系统命令时，请使用以下格式返回：

```command
你的命令
```

例如：
```command
ls -la
```
或
```command
pwd
```

执行命令后，我会将输出结果返回给你，你可以继续基于结果提供帮助。

注意事项：
1. 只在必要时才执行命令
2. 命令应该简洁明确
3. 避免执行危险操作（如 rm -rf /）
4. 如果需要执行复杂操作，请先说明你的意图
{skills_section}
"""


def execute_command(command: str, timeout: int = 30) -> str:
    """执行系统命令并返回结果"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        output = ""
        if result.stdout:
            output += f"📤 标准输出:\n{result.stdout}\n"
        if result.stderr:
            output += f"❌ 错误输出:\n{result.stderr}\n"
        output += f"💡 退出码：{result.returncode}"
        return output
    except subprocess.TimeoutExpired:
        return f"❌ 命令执行超时（>{timeout}秒）"
    except Exception as e:
        return f"❌ 执行命令时出错：{e}"


def parse_command_response(content: str) -> Optional[str]:
    """从 AI 回复中提取命令"""
    # 匹配 ```command ... ``` 格式
    pattern = r'```command\s*(.*?)\s*```'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def interactive_chat(client: LLMClient, model: str = "openrouter/free"):
    """交互式聊天模式"""
    print("\n" + "="*60)
    print("欢迎使用 Custom LLM Chat!")
    print("输入 'quit' 或 'exit' 退出")
    print("输入 'clear' 清空对话历史")
    print("输入 'history' 查看对话历史")
    print("="*60 + "\n")
    
    system_prompt = get_system_prompt()
    history: list[dict] = []
    
    # 检查 SKILL.md 是否存在
    skills = get_skills_content()
    if skills:
        print("✅ 已加载 SKILL.md 技能文件")
    
    while True:
        try:
            prompt = input("\n👤 你：").strip()
            
            if not prompt:
                continue
            
            if prompt.lower() in ["quit", "exit", "q"]:
                print("再见！")
                break
            
            if prompt.lower() == "clear":
                history = []
                print("对话历史已清空")
                continue
            
            if prompt.lower() == "history":
                if history:
                    print("\n--- 对话历史 ---")
                    for msg in history:
                        role = "👤 你" if msg["role"] == "user" else "🤖 AI"
                        print(f"{role}: {msg['content'][:100]}...")
                else:
                    print("暂无对话历史")
                continue
            
            # 构建消息并发送（首次对话包含系统提示）
            include_system = len(history) == 0
            messages = build_messages(prompt, history, include_system, system_prompt if include_system else "")
            
            print("🤖 AI: ", end="", flush=True)
            
            response = client.chat(messages, model=model)
            
            # 检查是否包含命令
            command = parse_command_response(response)
            if command:
                print("\n")
                print(f"⚙️  检测到命令：{command}")
                print("-" * 40)
                
                # 执行命令
                command_output = execute_command(command)
                print(command_output)
                print("-" * 40)
                
                # 将命令输出添加到历史
                history.append({"role": "assistant", "content": response})
                history.append({
                    "role": "user",
                    "content": f"命令执行结果:\n{command_output}"
                })
                
                # 将命令结果发送给 AI，获取最终回复
                print("🤖 AI: ", end="", flush=True)
                followup_messages = build_messages("请根据以上命令执行结果继续回答。", history)
                final_response = client.chat(followup_messages, model=model)
                print(final_response)
                
                # 更新历史
                history.append({"role": "assistant", "content": final_response})
            else:
                print(response)
                # 更新历史
                history.append({"role": "assistant", "content": response})
            
            # 限制历史长度，避免 token 溢出
            if len(history) > 24:
                # 只保留最近的 24 条用户/AI 对话
                history = history[-24:]
                
        except KeyboardInterrupt:
            print("\n\n再见！")
            break
        except Exception as e:
            print(f"\n❌ 错误：{e}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Custom LLM Chat - 命令行大模型交互工具")
    parser.add_argument("--api-key", type=str, help="API Key")
    parser.add_argument("--base-url", type=str, help="API 基础 URL")
    parser.add_argument("--model", type=str, help="模型名称")
    parser.add_argument("--prompt", type=str, help="单次查询模式的消息")
    
    args = parser.parse_args()
    
    # 获取 API Key
    api_key = args.api_key or os.getenv("LLM_API_KEY", "WELCOME_TO_USE_THIS_PUBLIC_FREE_KEY_ON_YOUR_CLAW")
    if not api_key:
        print("❌ 错误：请通过 --api-key 参数或 LLM_API_KEY 环境变量提供 API Key")
        print("\n示例:")
        print("  python3 simple_llm.py --api-key your-key --base-url https://openrouter.ai/api/v1")
        print("  LLM_API_KEY=your-key LLM_BASE_URL=https://openrouter.ai/api/v1 LLM_MODEL=openrouter/free python3 simple_llm.py")
        return
    
    # 获取 Base URL
    base_url = args.base_url or os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
    
    # 获取 Model，默认值：openrouter/free
    model = args.model or os.getenv("LLM_MODEL", "openrouter/free")
    
    # 创建客户端
    client = CustomClient(api_key, base_url)
    
    # 单次查询模式或交互模式
    if args.prompt:
        # 单次查询模式
        messages = build_messages(args.prompt)
        try:
            response = client.chat(messages, model=model)
            print(f"\n🤖 AI: {response}")
        except Exception as e:
            print(f"\n❌ 错误：{e}")
    else:
        # 交互模式
        interactive_chat(client, model)


if __name__ == "__main__":
    main()
