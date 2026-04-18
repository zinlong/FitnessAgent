import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv
from memory.short_term_memory import ShortTermMemory
from tools.mcp_server import MCPServer

load_dotenv()

DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
if not DASHSCOPE_API_KEY:
    raise ValueError("Please set DASHSCOPE_API_KEY in .env file")

client = OpenAI(
    api_key=DASHSCOPE_API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)
MODEL_NAME = "qwen-plus"

class FitnessAgent:
    def __init__(self):
        self.memory = ShortTermMemory(max_turns=10)
        self.mcp = MCPServer()
    
    def _call_llm_simple(self, prompt: str) -> str:
        """调用 LLM 获取回复"""
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"抱歉，API 调用失败：{str(e)}"
    
    def run(self, user_input: str) -> str:
        user_lower = user_input.lower().strip()
        
        # ========== 1. 打招呼 ==========
        if user_lower in ["你好", "hello", "hi", "嗨", "您好"]:
            return "你好！我是健身助手 💪\n\n你可以告诉我：\n• 你的身高、体重、健身目标\n• 让我推荐健身计划\n• 搜索健身动作\n• 保存/读取健身计划\n\n试试说：'我是男生，175cm，80kg，想减肥'"
        
        # ========== 2. 感谢 ==========
        if user_lower in ["谢谢", "thank you", "thanks", "谢了", "谢谢了"]:
            return "不客气！坚持锻炼，保持健康 💪 有什么可以继续帮你的吗？"
        
        # ========== 3. 再见 ==========
        if user_lower in ["再见", "bye", "goodbye", "拜拜", "88"]:
            return "再见！加油锻炼，期待下次见面！👋"
        
        # ========== 4. 帮助 ==========
        if user_lower in ["帮助", "help", "?", "？", "怎么用"]:
            return """📋 使用指南：

1️⃣ 告诉我你的信息：
   "我是男生，身高175cm，体重80kg，想减肥"

2️⃣ 获取健身计划：
   "推荐一周的减肥健身计划"

3️⃣ 保存计划到文件：
   "保存计划到 workout.txt"

4️⃣ 读取文件：
   "读取 workout_plan.txt"

5️⃣ 搜索健身动作：
   "搜索深蹲的正确姿势"

6️⃣ 查看我的信息：
   "info"

7️⃣ 清空记忆：
   "clear"

8️⃣ 退出程序：
   "quit"

试试输入吧！"""
        
        # ========== 5. 查看信息 ==========
        if user_lower == "info":
            info = self.memory.get_user_info()
            if info:
                return f"📋 已记录的信息：{json.dumps(info, ensure_ascii=False)}"
            else:
                return "📋 暂无用户信息。请告诉我你的身高、体重、健身目标，例如：'我是男生，175cm，80kg，想减肥'"
        
        # ========== 6. 清空记忆 ==========
        if user_lower == "clear":
            self.memory.clear()
            return "✅ 记忆已清空！"
        
        # ========== 7. 提取用户信息 ==========
        if ("cm" in user_lower or "身高" in user_input) and ("kg" in user_lower or "体重" in user_input):
            height_match = re.search(r'(\d{3})\s*cm', user_lower)
            if not height_match:
                height_match = re.search(r'身高[：:]?\s*(\d{3})', user_input)
            
            weight_match = re.search(r'(\d{2,3})\s*kg', user_lower)
            if not weight_match:
                weight_match = re.search(r'体重[：:]?\s*(\d{2,3})', user_input)
            
            if height_match:
                self.memory.set_user_info("height", height_match.group(1))
            if weight_match:
                self.memory.set_user_info("weight", weight_match.group(1))
            
            if "减肥" in user_input or "减脂" in user_input or "lose weight" in user_lower:
                self.memory.set_user_info("goal", "减肥")
            elif "增肌" in user_input or "gain muscle" in user_lower:
                self.memory.set_user_info("goal", "增肌")
            
            if "男" in user_input or "male" in user_lower:
                self.memory.set_user_info("gender", "男")
            elif "女" in user_input or "female" in user_lower:
                self.memory.set_user_info("gender", "女")
            
            if height_match and weight_match:
                height = int(height_match.group(1))
                weight = int(weight_match.group(1))
                bmi = weight / ((height / 100) ** 2)
                return f"✅ 已记录！身高：{height}cm，体重：{weight}kg，BMI：{bmi:.1f}（{self._get_bmi_status(bmi)}）\n\n继续输入 '推荐健身计划' 获取个性化方案！"
            else:
                return f"✅ 已记录部分信息。{height_match.group(1) if height_match else '身高?'}cm，{weight_match.group(1) if weight_match else '体重?'}kg\n请补充完整信息。"
        
        # ========== 8. 健身计划 ==========
        if any(word in user_lower for word in ["workout", "fitness", "计划", "健身", "plan"]):
            print("  [正在搜索健身计划...]")
            search_query = "best weight loss workout plan for beginners"
            result = self.mcp.call_tool("web_search", {"query": search_query, "max_results": 2})
            
            summary_prompt = f"""请根据以下搜索结果，给用户一个简单的一周健身计划（周一到周日），用中文输出，简洁明了。

搜索结果：
{result[:1200]}

输出格式：
周一：xxx
周二：xxx
...
周日：xxx + 休息建议"""
            
            plan = self._call_llm_simple(summary_prompt)
            return f"📋 为你推荐的健身计划：\n\n{plan}\n\n💡 输入 '保存计划到 workout.txt' 可以保存这份计划！"
        
        # ========== 9. 保存文件 ==========
        if "保存" in user_input and ".txt" in user_input:
            filename_match = re.search(r'(\w+\.txt)', user_input)
            filename = filename_match.group(1) if filename_match else "workout_plan.txt"
            
            content = """周一：慢跑30分钟 + 上肢力量训练
周二：HIIT 20分钟
周三：休息 + 拉伸
周四：游泳40分钟
周五：全身力量训练
周六：快走45分钟
周日：休息 + 瑜伽"""
            
            result = self.mcp.call_tool("file_operation", {
                "action": "write",
                "path": filename,
                "content": content
            })
            return f"{result}\n\n💡 输入 '读取 {filename}' 可以查看内容！"
        
        # ========== 10. 读取文件 ==========
        if "读取" in user_input and ".txt" in user_input:
            filename_match = re.search(r'(\w+\.txt)', user_input)
            if filename_match:
                filename = filename_match.group(1)
                result = self.mcp.call_tool("file_operation", {"action": "read", "path": filename})
                return result
            else:
                return "请指定文件名，例如：'读取 workout_plan.txt'"
        
        # ========== 11. 搜索动作 ==========
        if any(word in user_lower for word in ["搜索", "search", "怎么", "如何", "正确姿势", "动作"]):
            # 提取搜索词
            search_query = user_input
            for kw in ["搜索", "search", "search for", "帮我搜", "查一下"]:
                search_query = search_query.replace(kw, "")
            search_query = search_query.strip()
            if len(search_query) < 2:
                search_query = "深蹲正确姿势"
            
            print(f"  [正在搜索：{search_query}...]")
            result = self.mcp.call_tool("web_search", {"query": search_query, "max_results": 2})
            
            summary_prompt = f"""请根据以下搜索结果，用中文总结出5个要点，帮助用户了解"{search_query}"。

搜索结果：
{result[:1000]}

输出格式：
1. xxx
2. xxx
...
5. xxx"""
            
            summary = self._call_llm_simple(summary_prompt)
            return f"🔍 关于「{search_query}」的搜索结果：\n\n{summary}"
        
        # ========== 12. 默认：用 AI 回复任何其他内容 ==========
        # 这里保证无论输入什么都有回复
        default_prompt = f"""用户说："{user_input}"

请以健身助手的身份友好地回复用户。如果用户的问题与健身无关，可以礼貌地引导回健身话题。

回复要求：
- 简短友好（2-3句话）
- 如果是闲聊，正常回复后可以问健身相关的问题
- 如果用户输入无意义，可以回复帮助信息

请直接输出回复内容，不要加任何前缀。"""
        
        return self._call_llm_simple(default_prompt)
    
    def _get_bmi_status(self, bmi: float) -> str:
        if bmi < 18.5:
            return "偏瘦"
        elif bmi < 24:
            return "正常"
        elif bmi < 28:
            return "超重"
        else:
            return "肥胖"
    
    def chat(self):
        print("=" * 60)
        print("💪 FitnessAgent 健身助手已启动")
        print("=" * 60)
        print("输入 'help' 或 '帮助' 查看使用说明")
        print("输入 'quit' 退出程序")
        print("=" * 60)
        
        while True:
            user = input("\n👤 你: ")
            if user.lower() in ["quit", "exit", "退出"]:
                print("👋 再见！加油锻炼！")
                break
            
            print("💪 Agent: ", end="", flush=True)
            response = self.run(user)
            print(response)

if __name__ == "__main__":
    agent = FitnessAgent()
    agent.chat()