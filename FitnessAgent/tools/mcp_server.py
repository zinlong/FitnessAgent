from .web_search_tool import WebSearchTool
from .file_tool import FileTool

class MCPServer:
    def __init__(self):
        self.tools = {
            "web_search": WebSearchTool,
            "file_operation": FileTool,
        }
    
    def list_tools(self) -> list:
        return [tool.get_tool_spec() for tool in self.tools.values()]
    
    def _normalize_args(self, tool_name: str, arguments: dict) -> dict:
        """将不同参数名映射为标准参数名"""
        normalized = dict(arguments)
        
        if tool_name == "web_search":
            # 支持 query, q, search, keyword
            if "q" in normalized and "query" not in normalized:
                normalized["query"] = normalized.pop("q")
            if "search" in normalized and "query" not in normalized:
                normalized["query"] = normalized.pop("search")
            if "keyword" in normalized and "query" not in normalized:
                normalized["query"] = normalized.pop("keyword")
            # 支持 max_results, limit, num_results
            if "limit" in normalized and "max_results" not in normalized:
                normalized["max_results"] = normalized.pop("limit")
            if "num_results" in normalized and "max_results" not in normalized:
                normalized["max_results"] = normalized.pop("num_results")
        
        elif tool_name == "file_operation":
            # 映射各种可能的参数名到标准名
            if "filename" in normalized and "path" not in normalized:
                normalized["path"] = normalized.pop("filename")
            if "file" in normalized and "path" not in normalized:
                normalized["path"] = normalized.pop("file")
            if "operation" in normalized and "action" not in normalized:
                normalized["action"] = normalized.pop("operation")
            if "op" in normalized and "action" not in normalized:
                normalized["action"] = normalized.pop("op")
        
        return normalized
    
    def call_tool(self, tool_name: str, arguments: dict) -> str:
        if tool_name not in self.tools:
            return f"❌ Tool not found: {tool_name}"
        
        tool_class = self.tools[tool_name]
        normalized_args = self._normalize_args(tool_name, arguments)
        
        try:
            return tool_class.execute(**normalized_args)
        except TypeError as e:
            return f"❌ Parameter error: {e}"