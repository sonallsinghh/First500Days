cat <<'EOF' > README.md
# Agentic RAG System with Tool Calling

## System Architecture

### Overview
This is a fully agentic AI system that uses OpenAI function calling to dynamically decide when to use tools. The LLM has agency to call tools, observe results, and perform multi-step reasoning before generating a final response.

---

## Tech Stack Used

### Backend & API
- Python 3.10+
- FastAPI
- Pydantic

### LLM & Agent
- OpenAI API
- OpenAI Function Calling
- Prompt Engineering

### Retrieval-Augmented Generation (RAG)
- FAISS
- Sentence Transformers (all-MiniLM-L6-v2)
- PyPDF
- tiktoken

### Agent Capabilities
- Tool Registry Pattern
- Session-based Memory (sliding window)
- Multi-step tool execution

### Deployment & Infrastructure
- Azure App Service
- Uvicorn
- Environment Variables

---

## Setup Instructions

### Local Setup

1. Clone Repository
git clone https://github.com/sonallsinghh/First500Days.git

2. Create Virtual Environment
python -m venv venv
source venv/bin/activate

3. Install Dependencies
pip install -r requirements.txt

4. Configure Environment Variables
Create a .env file with:
OPENAI_API_KEY=your_openai_api_key

5. Build FAISS Index
python -c "from app.rag.index import build_index; build_index('data/documents')"

6. Run Application
uvicorn app.main:app --reload

7. Test API
Open:
http://127.0.0.1:8000/docs

---

### Azure Deployment

1. Create Azure App Service
Runtime: Python 3.10
OS: Linux

2. Configure Environment Variables
OPENAI_API_KEY=<your_key>

3. Deploy using GitHub Actions, Azure CLI, or ZIP deploy

4. Ensure FAISS index is included or built at startup

5. Access API
https://<app-name>.azurewebsites.net/docs

---

## Design Decisions

1. Fully Agentic Architecture
The LLM is given tool awareness and allowed to decide when to answer directly, retrieve documents, or call utility tools. This avoids rigid routing and enables flexible reasoning.

2. OpenAI Function Calling
Function calling enables explicit tool invocation, multi-step reasoning, and tool chaining while keeping agent behavior observable and auditable.

3. Tool Registry Pattern
All tools are centrally registered and dynamically executed, making the system easy to extend without modifying core agent logic.

4. Session-Based Memory
Conversation history is stored per session using a sliding window approach to balance context retention and token efficiency.

5. FAISS + Local Embeddings
FAISS provides fast, deterministic retrieval without external dependencies. Local embeddings reduce cost and increase control.

6. Separation of Concerns
Routes handle HTTP, the service layer manages sessions, the orchestrator controls agent logic, tools encapsulate external actions, and the RAG layer handles retrieval.

---

## Limitations & Future Improvements

### Current Limitations
- In-memory session memory (lost on restart)
- No authentication or authorization
- No OCR for scanned PDFs
- Synchronous tool execution
- No automated RAG evaluation metrics

### Future Improvements
- Redis or database-backed memory
- Role-based document access
- OCR integration using Tesseract or Azure Form Recognizer
- Parallel tool execution
- RAG quality evaluation
- Hybrid semantic and keyword search
- Conversation summarization for long sessions

---

## Final Notes
This system is intentionally designed to be explainable, extensible, and production-oriented. The architecture mirrors real-world enterprise agentic systems while remaining minimal and maintainable.
EOF
