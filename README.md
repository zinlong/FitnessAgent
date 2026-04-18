#  FitnessAgent - 智能健身助手

基于通义千问 + MCP 协议的 AI 健身助手。

## 功能

-  搜索健身信息
-  保存健身计划到文件
-  记住用户信息（身高、体重、目标）
-  BMI 计算

## 运行步骤

1. 安装 Python 3.10+
2. 安装依赖：`pip install -r requirements.txt`
3. 获取通义千问 API Key：https://dashscope.console.aliyun.com/
4. 创建 `.env` 文件，填入：`DASHSCOPE_API_KEY=sk-xxx`
5. 运行：`python agent.py`
