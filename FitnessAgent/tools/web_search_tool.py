from duckduckgo_search import DDGS
import time

class WebSearchTool:
    """MCP 网页搜索工具"""
    
    @staticmethod
    def get_tool_spec():
        return {
            "name": "web_search",
            "description": "Search the internet for fitness, workout, and diet information",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search keyword, e.g., 'weight loss workout plan', 'proper squat form'"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Number of results to return, default 3",
                        "default": 3
                    }
                },
                "required": ["query"]
            }
        }
    
    @staticmethod
    def execute(query: str = None, max_results: int = 3, 
                q: str = None, limit: int = None, **kwargs) -> str:
        """
        Execute web search - compatible with multiple parameter names
        
        Args:
            query: Search keyword (standard)
            q: Alternative parameter name for query
            max_results: Number of results (standard)
            limit: Alternative parameter name for max_results
        """
        # 处理参数别名
        if query is None and q is not None:
            query = q
        if max_results == 3 and limit is not None:
            max_results = limit
        
        if not query:
            return "❌ Missing 'query' parameter. Please provide what to search for."
        
        try:
            # 添加重试机制
            results = []
            for attempt in range(2):
                try:
                    with DDGS() as ddgs:
                        results = list(ddgs.text(query, max_results=max_results))
                    break
                except Exception as e:
                    if attempt == 0:
                        time.sleep(1)
                    else:
                        return f"🔍 Search failed after 2 attempts: {str(e)}"
            
            if not results:
                return f"🔍 No results found for '{query}'"
            
            output = f"🔍 Search results for '{query}':\n\n"
            for i, r in enumerate(results, 1):
                title = r.get('title', 'No title')
                body = r.get('body', 'No description')
                href = r.get('href', '#')
                
                output += f"{i}. {title}\n"
                output += f"   {body[:200]}{'...' if len(body) > 200 else ''}\n"
                output += f"   🔗 {href}\n\n"
            
            return output
            
        except Exception as e:
            return f"❌ Search error: {str(e)}"