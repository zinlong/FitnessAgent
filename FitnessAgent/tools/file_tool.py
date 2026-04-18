import os
from typing import Optional

class FileTool:
    @staticmethod
    def get_tool_spec():
        return {
            "name": "file_operation",
            "description": "File read/write operations",
            "input_schema": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["read", "write", "append"]},
                    "path": {"type": "string", "description": "File path"},
                    "content": {"type": "string", "description": "Content to write (for write/append)"}
                },
                "required": ["action", "path"]
            }
        }
    
    @staticmethod
    def execute(action: str = None, path: str = None, content: Optional[str] = None, 
                operation: str = None, filename: str = None, **kwargs) -> str:
        """兼容多种参数名"""
        # 处理参数别名
        if action is None and operation is not None:
            action = operation
        if path is None and filename is not None:
            path = filename
        
        if action is None:
            return "❌ Missing 'action' parameter (read/write/append)"
        if path is None:
            return "❌ Missing 'path' parameter"
        
        try:
            if action == "read":
                if not os.path.exists(path):
                    return f"❌ File not found: {path}"
                with open(path, 'r', encoding='utf-8') as f:
                    return f"📄 File content:\n{f.read()}"
            
            elif action == "write":
                os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(content or "")
                return f"✅ Saved to: {path}"
            
            elif action == "append":
                os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
                with open(path, 'a', encoding='utf-8') as f:
                    f.write(content or "")
                return f"✅ Appended to: {path}"
            
            else:
                return f"❌ Unsupported action: {action} (use read/write/append)"
        except Exception as e:
            return f"❌ File operation failed: {str(e)}"