from collections import deque
from typing import List, Dict

class ShortTermMemory:
    def __init__(self, max_turns: int = 10):
        self.max_turns = max_turns
        self.messages: deque = deque(maxlen=max_turns)
        self.user_profile: Dict[str, str] = {}
    
    def add(self, role: str, content: str):
        self.messages.append({"""role""": role, """content""": content})
    
    def get_history(self) -> List[Dict[str, str]]:
        return list(self.messages)
    
    def clear(self):
        self.messages.clear()
    
    def set_user_info(self, key: str, value: str):
        self.user_profile[key] = value
    
    def get_user_info(self, key: str = None):
        if key:
            return self.user_profile.get(key, None)
        return self.user_profile
    
    def calculate_bmi(self, height_cm: float, weight_kg: float) -> float:
        height_m = height_cm / 100
        return round(weight_kg / (height_m ** 2), 1)
    
    def get_bmi_status(self, bmi: float) -> str:
        if bmi < 18.5:
            return "偏瘦"
        elif bmi < 24:
            return "正常"
        elif bmi < 28:
            return "超重"
        else:
            return "肥胖"
