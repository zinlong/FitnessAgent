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
        """Call LLM for response"""
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Sorry, API error: {str(e)}"
    
    def run(self, user_input: str) -> str:
        user_lower = user_input.lower().strip()
        
        # ========== 1. Greetings ==========
        if user_lower in ["hello", "hi", "hey", "greetings", "你好"]:
            return "Hello! I'm your Fitness Assistant 💪\n\nTell me your height, weight, and goal. For example:\n'I am male, 175cm, 80kg, want to lose weight'"
        
        # ========== 2. Thanks ==========
        if user_lower in ["thanks", "thank you", "thx"]:
            return "You're welcome! Keep exercising and stay healthy 💪 Anything else I can help with?"
        
        # ========== 3. Goodbye ==========
        if user_lower in ["goodbye", "bye", "see you", "quit", "exit"]:
            return "Goodbye! Keep working out and stay fit! 👋"
        
        # ========== 4. Help ==========
        if user_lower in ["help", "?"]:
            return """📋 Help Guide:

1️⃣ Tell me your info:
   "I am male, 175cm, 80kg, want to lose weight"

2️⃣ Get workout plan:
   "Recommend a one-week weight loss workout plan"

3️⃣ Save plan to file:
   "Save this plan to workout.txt"

4️⃣ Read file:
   "Read workout_plan.txt"

5️⃣ Search exercises:
   "Search for proper squat form"

6️⃣ View my info:
   "info"

7️⃣ Clear memory:
   "clear"

8️⃣ Exit:
   "quit"

Try it now!"""
        
        # ========== 5. View user info ==========
        if user_lower == "info":
            info = self.memory.get_user_info()
            if info:
                return f"📋 Your info: {json.dumps(info, ensure_ascii=False)}"
            else:
                return "📋 No user info yet. Tell me your height, weight, and goal. Example: 'I am male, 175cm, 80kg, want to lose weight'"
        
        # ========== 6. Clear memory ==========
        if user_lower == "clear":
            self.memory.clear()
            return "✅ Memory cleared!"
        
        # ========== 7. Extract user info ==========
        if ("cm" in user_lower or "height" in user_lower) and ("kg" in user_lower or "weight" in user_lower):
            height_match = re.search(r'(\d{3})\s*cm', user_lower)
            weight_match = re.search(r'(\d{2,3})\s*kg', user_lower)
            
            if height_match:
                self.memory.set_user_info("height", height_match.group(1))
            if weight_match:
                self.memory.set_user_info("weight", weight_match.group(1))
            
            if "lose weight" in user_lower or "weight loss" in user_lower:
                self.memory.set_user_info("goal", "weight loss")
            elif "gain muscle" in user_lower or "muscle gain" in user_lower:
                self.memory.set_user_info("goal", "muscle gain")
            
            if "male" in user_lower or "man" in user_lower:
                self.memory.set_user_info("gender", "male")
            elif "female" in user_lower or "woman" in user_lower:
                self.memory.set_user_info("gender", "female")
            
            if height_match and weight_match:
                height = int(height_match.group(1))
                weight = int(weight_match.group(1))
                bmi = weight / ((height / 100) ** 2)
                status = self._get_bmi_status(bmi)
                return f"✅ Recorded! Height: {height}cm, Weight: {weight}kg, BMI: {bmi:.1f} ({status})\n\nType 'Recommend workout plan' to get a personalized plan!"
            else:
                return f"✅ Recorded: {height_match.group(1) if height_match else '?'}cm, {weight_match.group(1) if weight_match else '?'}kg\nPlease provide complete info."
        
        # ========== 8. Workout plan ==========
        if any(word in user_lower for word in ["workout", "fitness", "plan", "recommend"]):
            print("  [Searching for workout plan...]")
            search_query = "best weight loss workout plan for beginners"
            result = self.mcp.call_tool("web_search", {"query": search_query, "max_results": 2})
            
            summary_prompt = f"""Based on the search results below, give the user a simple one-week workout plan (Monday to Sunday). Output in English, concise.

Search results:
{result[:1200]}

Output format:
Monday: xxx
Tuesday: xxx
...
Sunday: xxx + rest advice"""
            
            plan = self._call_llm_simple(summary_prompt)
            return f"📋 Your recommended workout plan:\n\n{plan}\n\n💡 Type 'Save this plan to workout.txt' to save this plan!"
        
        # ========== 9. Save file ==========
        if "save" in user_lower and ".txt" in user_lower:
            filename_match = re.search(r'(\w+\.txt)', user_input)
            filename = filename_match.group(1) if filename_match else "workout_plan.txt"
            
            content = """Monday: 30 min jogging + upper body strength
Tuesday: 20 min HIIT
Wednesday: Rest + stretching
Thursday: 40 min swimming
Friday: Full body strength training
Saturday: 45 min brisk walking
Sunday: Rest + yoga"""
            
            result = self.mcp.call_tool("file_operation", {
                "action": "write",
                "path": filename,
                "content": content
            })
            return f"{result}\n\n💡 Type 'Read {filename}' to view the content!"
        
        # ========== 10. Read file ==========
        if "read" in user_lower and ".txt" in user_lower:
            filename_match = re.search(r'(\w+\.txt)', user_input)
            if filename_match:
                filename = filename_match.group(1)
                result = self.mcp.call_tool("file_operation", {"action": "read", "path": filename})
                return result
            else:
                return "Please specify the filename, e.g., 'Read workout_plan.txt'"
        
        # ========== 11. Search exercises ==========
        if any(word in user_lower for word in ["search", "how to", "proper", "form", "technique"]):
            search_query = user_input
            for kw in ["search", "search for", "search for proper", "how to", "tell me about"]:
                search_query = search_query.replace(kw, "")
            search_query = search_query.strip()
            if len(search_query) < 3:
                search_query = "proper squat form"
            
            print(f"  [Searching: {search_query}...]")
            result = self.mcp.call_tool("web_search", {"query": search_query, "max_results": 2})
            
            summary_prompt = f"""Based on the search results below, summarize 5 key tips in English to help the user understand "{search_query}".

Search results:
{result[:1000]}

Output format:
1. xxx
2. xxx
...
5. xxx"""
            
            summary = self._call_llm_simple(summary_prompt)
            return f"🔍 Search results for '{search_query}':\n\n{summary}"
        
        # ========== 12. Default: AI response for anything else ==========
        default_prompt = f"""User said: "{user_input}"

Respond as a friendly fitness assistant in English. Keep it short (2-3 sentences). If the message is not fitness-related, respond normally then gently guide back to fitness.

Just output the response directly, no prefixes."""
        
        return self._call_llm_simple(default_prompt)
    
    def _get_bmi_status(self, bmi: float) -> str:
        if bmi < 18.5:
            return "Underweight"
        elif bmi < 24:
            return "Normal"
        elif bmi < 28:
            return "Overweight"
        else:
            return "Obese"
    
    def chat(self):
        print("=" * 60)
        print("💪 FitnessAssistant Started")
        print("=" * 60)
        print("Type 'help' for instructions")
        print("Type 'quit' to exit")
        print("=" * 60)
        
        while True:
            user = input("\n👤 You: ")
            if user.lower() in ["quit", "exit"]:
                print("👋 Goodbye! Stay fit!")
                break
            
            print("💪 Agent: ", end="", flush=True)
            response = self.run(user)
            print(response)

if __name__ == "__main__":
    agent = FitnessAgent()
    agent.chat()