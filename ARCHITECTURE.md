# System Architecture

## Overview
This is a **fully agentic AI system** that uses OpenAI function calling to dynamically decide when to use tools. The LLM has agency to call tools, see results, and chain multiple tool calls together.

---

## Request Flow

```
HTTP Request → FastAPI → Routes → Chat Service → Orchestrator → LLM (with tools) → Response
```

---

## File-by-File Architecture

### 🌐 **API Layer**

#### `app/main.py`
- **Purpose**: FastAPI application entry point
- **Responsibilities**:
  - Creates FastAPI app instance
  - Suppresses multiprocessing warnings
  - Includes routes from `routes.py`
- **Key Code**: `app = FastAPI(title="AI Agent RAG")`

#### `app/routes.py`
- **Purpose**: HTTP endpoint definitions
- **Responsibilities**:
  - Defines `/health` endpoint
  - Defines `/ask` POST endpoint (main chat endpoint)
  - Validates request/response with Pydantic models
- **Key Models**:
  - `AskRequest`: `{query: str, session_id: Optional[str]}`
  - `AskResponse`: `{answer: str, source: List[str], session_id: str}`
- **Flow**: Receives request → Calls `chat_service.process_chat()` → Returns response

---

### 🔧 **Service Layer**

#### `app/services/chat_service.py`
- **Purpose**: Business logic for chat requests
- **Responsibilities**:
  - Creates session_id if missing (UUID generation)
  - Calls orchestrator
  - Returns unified response format
- **Key Function**: `process_chat(query, session_id)`
- **Flow**: Session management → Orchestrator → Format response

---

### 🧠 **Agent Layer** (Core Intelligence)

#### `app/agent/orchestrator.py` ⭐ **CORE FILE**
- **Purpose**: Fully agentic query handler using OpenAI function calling
- **Responsibilities**:
  - Manages conversation with LLM
  - Provides tools to LLM via function calling
  - Executes tool calls when LLM requests them
  - Supports multi-step tool calling (up to 5 iterations)
  - Manages session memory
  - Collects sources from document retrievals
- **Key Flow**:
  1. Build conversation history (system prompt + memory + user query)
  2. Get tool schemas
  3. **Loop** (up to 5 iterations):
     - Call LLM with tools available
     - If LLM wants to call tool → Execute tool → Add result to conversation
     - If LLM responds → Break loop
  4. Extract final answer
  5. Update session memory
  6. Return answer + sources
- **Key Features**:
  - `tool_choice="auto"` - LLM decides when to use tools
  - Multi-iteration support for tool chaining
  - Error handling for tool execution

#### `app/agent/tools.py` ⭐ **TOOL DEFINITIONS**
- **Purpose**: Defines all available tools and their schemas
- **Responsibilities**:
  - Implements tool functions
  - Registers tools in `TOOL_REGISTRY`
  - Provides OpenAI function calling schemas
  - Executes tools dynamically
- **Available Tools**:
  1. **`get_current_date()`**
     - Returns: Current date in ISO format (YYYY-MM-DD)
     - Use case: Date/time questions
  2. **`retrieve_documents_tool(query)`**
     - Returns: `{chunks: List[str], sources: List[str], num_results: int}`
     - Use case: Search internal documents
- **Key Functions**:
  - `get_tool_schemas()` - Returns OpenAI function schemas
  - `execute_tool(name, args)` - Executes tool by name

#### `app/agent/prompts.py`
- **Purpose**: System prompts and templates
- **Contents**:
  - `SYSTEM_PROMPT`: Instructions for LLM about available tools
  - `ANSWER_PROMPT`: Template for RAG answers (legacy, not used in agentic flow)

#### `app/agent/memory.py`
- **Purpose**: Session-based conversation memory
- **Responsibilities**:
  - Stores conversation history per session_id
  - Maintains sliding window (last 6 messages: 3 user + 3 assistant)
  - In-memory storage (dict-based)
- **Key Functions**:
  - `get_memory(session_id)` - Returns conversation history
  - `update_memory(session_id, role, content)` - Adds message to history

---

### 📚 **RAG Layer** (Retrieval-Augmented Generation)

#### `app/rag/retriever.py`
- **Purpose**: Semantic document search using FAISS
- **Responsibilities**:
  - Loads FAISS index and metadata on import
  - Encodes queries using sentence transformers
  - Searches FAISS index for similar embeddings
  - Returns top-k semantically similar chunks
- **Key Function**: `retrieve_documents(query, top_k=5, similarity_threshold=0.05)`
- **Returns**: `(chunks: List[str], sources: List[str])`
- **Technology**: 
  - FAISS (vector similarity search)
  - Sentence Transformers (all-MiniLM-L6-v2)

#### `app/rag/index.py`
- **Purpose**: Build FAISS index from documents
- **Responsibilities**:
  - Loads documents from directory
  - Creates embeddings
  - Builds FAISS index
  - Saves index and metadata
- **Key Function**: `build_index(doc_dir)`
- **Output**: `faiss_index/index.faiss` and `faiss_index/meta.pkl`

#### `app/rag/ingest.py`
- **Purpose**: Document processing and chunking
- **Responsibilities**:
  - Loads text files from directory
  - Chunks documents (250 tokens, 50 token overlap)
  - Returns structured document list
- **Key Functions**:
  - `chunk_text(text, chunk_size=250, overlap=50)`
  - `load_documents(doc_dir)`

---

### ⚙️ **Configuration**

#### `app/config.py`
- **Purpose**: Environment configuration
- **Responsibilities**:
  - Loads `.env` file
  - Exports `OPENAI_API_KEY`
  - Validates API key presence

---

## Data Flow Example

### Example: "What is today's date?"

```
1. HTTP POST /ask
   ↓
2. routes.py: ask_agent()
   ↓
3. chat_service.py: process_chat()
   - Creates session_id if needed
   ↓
4. orchestrator.py: handle_query()
   - Builds messages: [system, memory, user_query]
   - Gets tool schemas
   ↓
5. LLM Call (OpenAI API)
   - LLM sees tools available
   - LLM decides: "I need get_current_date tool"
   - Returns: tool_call for get_current_date()
   ↓
6. orchestrator.py: execute_tool()
   - Calls tools.execute_tool("get_current_date", {})
   ↓
7. tools.py: get_current_date()
   - Returns: "2026-01-11"
   ↓
8. orchestrator.py: Add tool result to conversation
   - messages.append({role: "tool", content: "2026-01-11"})
   ↓
9. LLM Call (OpenAI API) - Second iteration
   - LLM sees tool result
   - LLM formats natural response: "Today's date is January 11, 2026"
   ↓
10. orchestrator.py: Extract answer
    - Updates memory
    - Returns: {answer: "...", source: []}
    ↓
11. chat_service.py: Format response
    - Adds session_id
    ↓
12. routes.py: Return HTTP response
```

### Example: "Does iPhone 17 support wireless charging?"

```
1-4. Same as above
   ↓
5. LLM Call
   - LLM decides: "I need retrieve_documents_tool"
   - Returns: tool_call for retrieve_documents_tool("iPhone 17 wireless charging")
   ↓
6. orchestrator.py: execute_tool()
   ↓
7. tools.py: retrieve_documents_tool()
   ↓
8. rag/retriever.py: retrieve_documents()
   - Encodes query → FAISS search → Returns chunks
   ↓
9. orchestrator.py: Add tool result
   - Collects sources: ["iPhone_17_256GB_Product_FAQs_Single_Page.pdf"]
   ↓
10. LLM Call - Second iteration
    - LLM sees retrieved chunks
    - LLM answers based on retrieved content
    ↓
11. orchestrator.py: Extract answer + sources
    - Returns: {answer: "Yes...", source: ["iPhone_17_..."]}
```

---

## Key Design Decisions

### 1. **Fully Agentic Architecture**
- LLM decides when to use tools (not pre-routing)
- Supports multi-step tool calling
- Tool results inform next LLM call

### 2. **Session Memory**
- In-memory storage (not persistent)
- Sliding window (last 6 messages)
- Enables conversational context

### 3. **Semantic Search**
- FAISS for fast vector similarity
- Sentence transformers for embeddings
- No keyword matching - pure semantic

### 4. **Tool Registry Pattern**
- Centralized tool registration
- Dynamic tool execution
- Easy to add new tools

---

## Technology Stack

- **FastAPI**: Web framework
- **OpenAI API**: LLM with function calling
- **FAISS**: Vector similarity search
- **Sentence Transformers**: Embeddings
- **Pydantic**: Request/response validation
- **Python 3.10+**: Runtime

---

## Adding New Tools

1. **Implement tool function** in `app/agent/tools.py`:
   ```python
   def my_new_tool(param: str) -> Dict:
       # Tool logic
       return {"result": "..."}
   ```

2. **Register tool**:
   ```python
   TOOL_REGISTRY["my_new_tool"] = my_new_tool
   ```

3. **Add schema** in `get_tool_schemas()`:
   ```python
   {
       "type": "function",
       "function": {
           "name": "my_new_tool",
           "description": "...",
           "parameters": {...}
       }
   }
   ```

4. **Update SYSTEM_PROMPT** in `prompts.py` to mention new tool

That's it! The orchestrator will automatically make it available to the LLM.

---

## File Dependencies

```
main.py
  └─ routes.py
      └─ services/chat_service.py
          └─ agent/orchestrator.py
              ├─ agent/prompts.py (SYSTEM_PROMPT)
              ├─ agent/memory.py
              └─ agent/tools.py
                  ├─ rag/retriever.py
                  │   ├─ faiss_index/index.faiss
                  │   └─ faiss_index/meta.pkl
                  └─ (tool implementations)
```

---

## Session Flow

```
User Query (session_id: "abc123")
  ↓
Load memory for "abc123" → [previous conversation]
  ↓
Add user query to conversation
  ↓
LLM processes (with tools available)
  ↓
Tool calls executed (if any)
  ↓
LLM generates final answer
  ↓
Save to memory: [old messages, new user query, new answer]
  ↓
Return answer + sources
```

---

## Error Handling

- **Tool execution errors**: Caught and returned as tool result
- **LLM API errors**: Propagated up (handled by FastAPI)
- **Missing tools**: ValueError raised
- **Max iterations**: Loop breaks after 5 iterations (prevents infinite loops)

---

## Performance Considerations

- **FAISS index**: Loaded once at import (fast searches)
- **Embedding model**: Loaded once at import (reused)
- **Memory**: In-memory dict (fast, but not persistent)
- **Tool execution**: Synchronous (could be async for parallel tools)

---

This architecture enables a fully agentic system where the LLM has agency to decide tool usage dynamically based on context.

