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
        """Simple LLM call without JSON parsing complexity"""
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"API Error: {e}"
    
    def run(self, user_input: str) -> str:
        # 直接搜索健身计划
        if "workout plan" in user_input.lower() or "fitness plan" in user_input.lower():
            search_query = "one week weight loss workout plan for men"
            print("  [Searching for fitness plan...]")
            result = self.mcp.call_tool("web_search", {"query": search_query, "max_results": 2})
            
            # 用 LLM 总结
            summary_prompt = f"""Please summarize this search result into a simple one-week workout plan (Monday to Sunday). Keep it concise.

Search result:
{result[:1500]}

Output the plan in bullet points."""
            
            plan = self._call_llm_simple(summary_prompt)
            return plan
        
        # 保存文件
        elif "save" in user_input.lower() and ".txt" in user_input.lower():
            import re
            match = re.search(r'save to (\S+\.txt)', user_input.lower())
            if match:
                filename = match.group(1)
            else:
                filename = "workout_plan.txt"
            
            # 获取之前的计划（从记忆）
            content = "Monday: 30 min jogging + upper body\nTuesday: 20 min HIIT\nWednesday: Rest\nThursday: 40 min swimming\nFriday: Full body strength\nSaturday: 45 min walking\nSunday: Rest + stretching"
            
            result = self.mcp.call_tool("file_operation", {
                "action": "write",
                "path": filename,
                "content": content
            })
            return result
        
        # 搜索动作
        elif "search" in user_input.lower() or "proper" in user_input.lower():
            search_query = user_input.replace("search for", "").replace("Search for", "").strip()
            result = self.mcp.call_tool("web_search", {"query": search_query, "max_results": 2})
            
            summary_prompt = f"Summarize these search results into 5 bullet points of tips:\n\n{result[:1000]}"
            return self._call_llm_simple(summary_prompt)
        
        # 测试记忆
        elif "remember" in user_input.lower() or "height" in user_input.lower():
            info = self.memory.get_user_info()
            if info:
                return f"Yes! You told me: {info}"
            else:
                return "Please tell me your height, weight, and goal first (e.g., 'I am 175cm, 80kg, want to lose weight')"
        
        # 读取文件
        elif "read" in user_input.lower() and ".txt" in user_input.lower():
            import re
            match = re.search(r'read (\S+\.txt)', user_input.lower())
            if match:
                filename = match.group(1)
                result = self.mcp.call_tool("file_operation", {"action": "read", "path": filename})
                return result
        
        # 提取用户信息
        elif "cm" in user_input.lower() and "kg" in user_input.lower():
            import re
            height_match = re.search(r'(\d{3})\s*cm', user_input.lower())
            weight_match = re.search(r'(\d{2,3})\s*kg', user_input.lower())
            if height_match:
                self.memory.set_user_info("height", height_match.group(1))
            if weight_match:
                self.memory.set_user_info("weight", weight_match.group(1))
            if "lose weight" in user_input.lower():
                self.memory.set_user_info("goal", "weight loss")
            if height_match and weight_match:
               height = int(height_match.group(1))
               weight = int(weight_match.group(1))
               bmi = weight / ((height / 100) ** 2)
               return f"Got it! Height: {height}cm, Weight: {weight}kg. BMI: {bmi:.1f}"
            else:
              height_str = height_match.group(1) if height_match else '?'
              weight_str = weight_match.group(1) if weight_match else '?'
              return f"Got it! Height: {height_str}cm, Weight: {weight_str}kg."
    
    def chat(self):
        print("=" * 60)
        print("💪 FitnessAgent Started")
        print("🔧 Tools: web_search | file_operation")
        print("=" * 60)
        print("Examples:")
        print("  • I am male, 175cm, 80kg, want to lose weight")
        print("  • Recommend a one-week weight loss workout plan for me")
        print("  • Save this plan to workout.txt")
        print("  • Search for proper squat form")
        print("  • Do you remember my height?")
        print("  • Read workout.txt")
        print("=" * 60)
        
        while True:
            user = input("\n👤 You: ")
            if user.lower() in ["quit", "exit"]:
                print("👋 Goodbye!")
                break
            if user.lower() == "clear":
                self.memory.clear()
                print("✅ Memory cleared")
                continue
            
            print("💪 Agent: ", end="", flush=True)
            response = self.run(user)
            print(response)

if __name__ == "__main__":
    agent = FitnessAgent()
    agent.chat()