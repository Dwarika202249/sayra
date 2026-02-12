import asyncio
from ddgs import DDGS

class WebSearch:
    def __init__(self):
        pass 

    def search(self, query, max_results=3):
        """
        Performs a web search using the official 'ddgs' library.
        Fix: Passes query as a positional argument to avoid TypeError.
        """
        try:
            print(f"[WebSearch]: Searching for '{query}'...")
            
            # Official 'ddgs' usage with Positional Argument
            with DDGS() as ddgs:
                # FIX: 'keywords' hata kar seedha 'query' pass kiya hai
                # max_results abhi bhi keyword argument ki tarah kaam karega
                results = list(ddgs.text(query, max_results=max_results))
            
            if not results:
                print(f"[WebSearch Warning]: No results found for '{query}'.")
                return None
            
            # Formatting for Brain
            summary = "Web Search Results:\n"
            for i, res in enumerate(results, 1):
                # 'body' is the standard key in the new library
                body = res.get('body', 'No description')
                summary += f"{i}. {res['title']}: {body}\n"
            
            return summary
            
        except Exception as e:
            print(f"[Search Critical Error]: {e}")
            return None

# Global Instance
web_searcher = WebSearch()