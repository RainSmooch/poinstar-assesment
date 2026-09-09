from typing import Annotated, List, Dict, Any, Optional
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AcademicAgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    is_in_scope: bool
    rejection_message: Optional[str]
    thinking_process: Optional[str]
    need_kb: Optional[bool]
    kb_query: Optional[str]
    need_web: Optional[bool]
    web_query: Optional[str]
    kb_results: Optional[List[Dict[str, Any]]]
    web_results: Optional[List[Dict[str, Any]]]
