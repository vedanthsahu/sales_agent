from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from config.domains import is_valid_domain
from services.mongo_service import create_session, end_session, get_chat_history, get_session

router = APIRouter()


class SessionStartRequest(BaseModel):
    user_id: str = Field(..., min_length=1)


class SessionStartResponse(BaseModel):
    session_id: str
    user_id: str


class SessionEndRequest(BaseModel):
    session_id: str = Field(..., min_length=1)


@router.post("/session/start", response_model=SessionStartResponse)
async def start_session(request: SessionStartRequest):
    session_id = await create_session(request.user_id)
    return {"session_id": session_id, "user_id": request.user_id}


@router.post("/session/end")
async def close_session(request: SessionEndRequest):
    await end_session(request.session_id)
    return {"status": "ok"}


@router.get("/history")
async def get_history(session_id: str, domain: str):
    if not session_id:
        raise HTTPException(status_code=400, detail="Session required")
    if not is_valid_domain(domain):
        raise HTTPException(status_code=400, detail="Invalid domain")

    session = await get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = await get_chat_history(session_id=session_id, domain=domain)
    return {"session_id": session_id, "domain": domain, "messages": messages}
