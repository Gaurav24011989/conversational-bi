from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rbac import require_project_access
from app.core.security import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import (
    ClarificationResponse,
    ConversationCreate,
    ConversationResponse,
    MessageCreate,
    MessageResponse,
    QueryResponse,
)
from app.services.conversation_service import conversation_service

router = APIRouter(tags=["conversations"])


def _build_query_response(msg, conv_id: UUID) -> QueryResponse | ClarificationResponse:
    data = msg.response_data or {}
    if data.get("type") == "clarification":
        return ClarificationResponse(
            message_id=msg.id,
            conversation_id=conv_id,
            questions=data.get("questions", []),
            trace_id=data.get("trace_id"),
        )
    return QueryResponse(
        message_id=msg.id,
        conversation_id=conv_id,
        natural_language_query=data.get("natural_language_query", ""),
        generated_query=data.get("generated_query"),
        query_language=data.get("query_language"),
        datasource=data.get("datasource"),
        execution=data.get("execution", {"status": "error"}),
        data=data.get("data"),
        visualization=data.get("visualization"),
        follow_up_questions=data.get("follow_up_questions", []),
        trace_id=data.get("trace_id"),
        error=data.get("error"),
    )


@router.post("/projects/{project_id}/conversations", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    project_id: UUID,
    data: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await require_project_access(db, current_user, project_id, "query")
    conv = await conversation_service.create(db, project_id, current_user.id, data)
    return conv


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conv = await conversation_service.get(db, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await require_project_access(db, current_user, conv.project_id, "view")
    return conv


@router.post("/conversations/{conversation_id}/messages", response_model=QueryResponse)
async def send_message(
    conversation_id: UUID,
    data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conv = await conversation_service.get(db, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await require_project_access(db, current_user, conv.project_id, "query")

    try:
        _, assistant_msg = await conversation_service.send_message(
            db, conv, current_user.id, current_user.org_id, data
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return _build_query_response(assistant_msg, conv.id)


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
async def list_messages(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conv = await conversation_service.get(db, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await require_project_access(db, current_user, conv.project_id, "view")
    messages = await conversation_service.list_messages(db, conversation_id)
    return messages
