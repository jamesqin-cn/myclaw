#!/bin/bash
# 运行 Simple LLM Chat 脚本
# 用法：./run.sh --provider openrouter --api-key your-key

source .venv/bin/activate
python3 simple_llm.py "$@"
