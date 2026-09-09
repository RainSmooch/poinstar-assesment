from src.state import AcademicAgentState
from src.tools.kb_search import search_knowledge_base
from src.tools.web_search import search_web

def retrieve_tools_node(state: AcademicAgentState) -> dict:
    need_kb = state.get("need_kb", True)
    kb_query = state.get("kb_query")
    
    need_web = state.get("need_web", False)
    web_query = state.get("web_query")
    
    kb_results = []
    if need_kb and kb_query and kb_query.strip():
        kb_results = search_knowledge_base(kb_query.strip(), top_k=3)
        
    web_results = []
    if need_web and web_query and web_query.strip():
        web_results = search_web(web_query.strip(), max_results=3)
        
    return {
        "kb_results": kb_results,
        "web_results": web_results
    }
