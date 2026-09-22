from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from db.models import User
from src.agent.agent import ask_agent
from src.api.auth import get_current_user
from src.api.deps import get_db, get_tenant_id
from src.api.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    session: Session = Depends(get_db),
    tenant_id=Depends(get_tenant_id),
    _user: User = Depends(get_current_user),
):
    result = ask_agent(session, tenant_id, payload.question)
    return ChatResponse(
        answer=result["answer"],
        tools_used=[t["name"] for t in result["tools_used"]],
    )
