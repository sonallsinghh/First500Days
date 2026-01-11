import sys
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add project root to path for direct script execution
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from openai import OpenAI
from app.config import OPENAI_API_KEY
from app.agent.prompts import SYSTEM_PROMPT
from app.agent.memory import get_memory, update_memory
from app.agent.tools import get_tool_schemas, execute_tool

client = OpenAI(api_key=OPENAI_API_KEY)

# Maximum number of tool-calling iterations to prevent infinite loops
MAX_TOOL_ITERATIONS = 5


def handle_query(query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Fully agentic query handler using OpenAI function calling.
    
    The LLM decides when to use tools dynamically, can call multiple tools,
    and can chain tool calls based on results.
    """
    # Build conversation history
    messages: List[Dict[str, Any]] = []
    
    # Add system prompt
    messages.append({"role": "system", "content": SYSTEM_PROMPT})
    
    # Load session memory if available
    if session_id:
        messages.extend(get_memory(session_id))
    
    # Add current user query
    messages.append({"role": "user", "content": query})
    
    # Get tool schemas for function calling
    tools = get_tool_schemas()
    
    # Track sources from document retrieval
    # This accumulates sources across multiple tool calls if LLM needs to query different documents
    # or if a single retrieval returns chunks from multiple documents
    all_sources = set()
    
    # Multi-step tool calling loop
    iteration = 0
    while iteration < MAX_TOOL_ITERATIONS:
        iteration += 1
        
        # Call LLM with function calling enabled
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools,
            tool_choice="auto",  # Let LLM decide when to use tools
            temperature=0.3
        )
        
        message = response.choices[0].message
        
        # Convert Pydantic model to dict for consistency
        message_dict = {
            "role": message.role,
            "content": message.content
        }
        if message.tool_calls:
            message_dict["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in message.tool_calls
            ]
        
        messages.append(message_dict)
        
        # Check if LLM wants to call a tool
        if message.tool_calls:
            # Execute all tool calls
            for tool_call in message_dict.get("tool_calls", []):
                tool_name = tool_call["function"]["name"]
                tool_args = json.loads(tool_call["function"]["arguments"])  # Parse JSON string
                tool_call_id = tool_call["id"]
                
                # Execute the tool
                try:
                    tool_result = execute_tool(tool_name, tool_args)
                    
                    # Collect sources if this is a document retrieval
                    # Only include sources with high relevance scores (filter out low-relevance matches)
                    if tool_name == "retrieve_documents_tool" and isinstance(tool_result, dict):
                        chunk_metadata = tool_result.get("chunk_metadata", [])
                        
                        if chunk_metadata:
                            # Group chunks by source and get max score per source
                            source_scores = {}
                            for chunk_info in chunk_metadata:
                                source = chunk_info.get("source")
                                score = chunk_info.get("score", 0)
                                if source not in source_scores:
                                    source_scores[source] = []
                                source_scores[source].append(score)
                            
                            # Calculate relevance threshold: top score * 0.5
                            # This ensures we only include sources that are reasonably relevant
                            all_chunk_scores = [c.get("score", 0) for c in chunk_metadata]
                            if all_chunk_scores:
                                top_score = max(all_chunk_scores)
                                relevance_threshold = top_score * 0.5  # 50% of top score
                                
                                # Only include sources where max score meets threshold
                                # This filters out documents that matched by chance with low scores
                                relevant_sources = [
                                    source for source, scores in source_scores.items()
                                    if max(scores) >= relevance_threshold
                                ]
                                all_sources.update(relevant_sources)
                        else:
                            # Fallback: use all sources if no metadata
                            sources = tool_result.get("sources", [])
                            all_sources.update(sources)
                        
                        # Remove sources and metadata from tool result before sending to LLM
                        # This prevents LLM from mentioning document names in the answer
                        tool_result_for_llm = tool_result.copy()
                        tool_result_for_llm.pop("sources", None)
                        tool_result_for_llm.pop("chunk_metadata", None)
                        
                        # Format only the content (chunks) for LLM, not sources
                        result_str = json.dumps(tool_result_for_llm, indent=2)
                    else:
                        # Format other tool results normally
                        if isinstance(tool_result, dict):
                            result_str = json.dumps(tool_result, indent=2)
                        else:
                            result_str = str(tool_result)
                    
                    # Add tool result to conversation
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": result_str
                    })
                except Exception as e:
                    # Handle tool execution errors
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": f"Error executing tool: {str(e)}"
                    })
        else:
            # LLM has finished - no more tool calls needed
            break
    
    # Get final answer from last message
    # Find the last assistant message with content (not a tool call)
    answer = None
    for msg in reversed(messages):
        if msg.get("role") == "assistant" and msg.get("content"):
            answer = msg.get("content")
            break
    
    if not answer:
        answer = "I apologize, but I encountered an issue processing your request."
    
    # Update session memory
    if session_id:
        update_memory(session_id, "user", query)
        update_memory(session_id, "assistant", answer)
    
    return {
        "answer": answer.strip(),
        "source": list(all_sources)
    }


if __name__ == "__main__":
    sid = "test-session"
    
    print("=== Test 1: Date query ===")
    result = handle_query("What is today's date?", sid)
    print(f"Answer: {result['answer']}")
    print(f"Sources: {result['source']}")
    print()
    
    print("=== Test 2: Document retrieval ===")
    result = handle_query("What is the paternity leave policy?", sid)
    print(f"Answer: {result['answer'][:200]}...")
    print(f"Sources: {result['source']}")
    print()
    
    print("=== Test 3: General question ===")
    result = handle_query("Hello, how are you?", sid)
    print(f"Answer: {result['answer']}")
    print(f"Sources: {result['source']}")
