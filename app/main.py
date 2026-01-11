import warnings
import multiprocessing

# Suppress multiprocessing resource tracker warnings (harmless)
warnings.filterwarnings("ignore", category=UserWarning, module="multiprocessing.resource_tracker")

from fastapi import FastAPI
from app.routes import router

app = FastAPI(title="AI Agent RAG")

app.include_router(router)