from fastapi import FastAPI

app = FastAPI(title="AI Agent RAG")

@app.get("/health")
def health():
    return {"status": "ok"}
