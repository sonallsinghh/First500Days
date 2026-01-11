import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Tuple, List

# Add project root to path for direct script execution
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


# Tool registry - maps function names to actual functions
TOOL_REGISTRY = {}


def get_current_date() -> str:
    """
    Returns today's date in ISO format.
    
    Examples:
    - "What is today's date?" -> Returns current date
    - "How many days left this year?" -> Can calculate from current date
    - "Is today a weekend?" -> Can determine from current date
    """
    return datetime.utcnow().strftime("%Y-%m-%d")


def retrieve_documents_tool(query: str) -> Dict[str, Any]:
    """
    Search internal documents using semantic search.
    
    Use this tool when you need to find information from company documents,
    policies, product specifications, FAQs, or any internal knowledge base.
    
    Args:
        query: The search query to find relevant information
        
    Returns:
        Dictionary with 'chunks' (list of text chunks), 'sources' (list of source files),
        and 'chunk_metadata' (list of chunk info with similarity scores)
    """
    from app.rag.retriever import retrieve_documents
    
    chunks, sources, chunk_metadata = retrieve_documents(query)
    return {
        "chunks": chunks,
        "sources": sources,
        "num_results": len(chunks),
        "chunk_metadata": chunk_metadata  # Include metadata for source filtering
    }


# Register tools
TOOL_REGISTRY["get_current_date"] = get_current_date
TOOL_REGISTRY["retrieve_documents_tool"] = retrieve_documents_tool


# OpenAI function calling schemas
def get_tool_schemas() -> List[Dict[str, Any]]:
    """
    Returns OpenAI function calling schemas for all available tools.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "get_current_date",
                "description": "Get the current date in ISO format (YYYY-MM-DD). Use this for questions about today's date, what day it is, date calculations, or determining if today is a weekend.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "retrieve_documents_tool",
                "description": "Search internal company documents, policies, product specifications, FAQs, or knowledge base using semantic search. Use this when the user asks about company policies, HR topics, product features, specifications, or any information that might be in internal documents.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query to find relevant information in the documents"
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    ]


def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Any:
    """
    Execute a tool by name with given arguments.
    
    Args:
        tool_name: Name of the tool to execute
        arguments: Arguments to pass to the tool
        
    Returns:
        Result from the tool execution
    """
    if tool_name not in TOOL_REGISTRY:
        raise ValueError(f"Unknown tool: {tool_name}")
    
    tool_func = TOOL_REGISTRY[tool_name]
    return tool_func(**arguments)

