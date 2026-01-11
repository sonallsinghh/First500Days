from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List

from app.services.chat_service import process_chat

router = APIRouter()


class AskRequest(BaseModel):
    query: str
    session_id: Optional[str] = None


class AskResponse(BaseModel):
    answer: str
    source: List[str]
    session_id: str


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/ask", response_model=AskResponse)
def ask_agent(request: AskRequest):
    result = process_chat(
        query=request.query,
        session_id=request.session_id
    )

    return AskResponse(**result)
