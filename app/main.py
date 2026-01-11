from fastapi import FastAPI
from app.routes import router

app = FastAPI(title="AI Agent RAG")

app.include_router(router)