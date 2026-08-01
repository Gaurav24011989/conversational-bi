from uuid import UUID

from langchain_core.messages import HumanMessage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import query_agent
from app.models import Conversation, Message, MessageRole, Project
from app.schemas import ConversationCreate, MessageCreate, QueryResponse
from app.services.audit_service import audit_service
from app.services.cache import rate_limiter
from app.services.datasource_service import datasource_service
from app.services.schema_service import schema_service


class ConversationService:
    async def create(
        self,
        db: AsyncSession,
        project_id: UUID,
        user_id: UUID,
        data: ConversationCreate,
    ) -> Conversation:
        conv = Conversation(
            project_id=project_id,
            datasource_id=data.datasource_id,
            user_id=user_id,
            title=data.title,
        )
        db.add(conv)
        await db.flush()
        return conv

    async def get(self, db: AsyncSession, conversation_id: UUID) -> Conversation | None:
        result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
        return result.scalar_one_or_none()

    async def list_messages(self, db: AsyncSession, conversation_id: UUID) -> list[Message]:
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
        )
        return list(result.scalars().all())

    async def send_message(
        self,
        db: AsyncSession,
        conversation: Conversation,
        user_id: UUID,
        org_id: UUID,
        data: MessageCreate,
    ) -> tuple[Message, Message]:
        allowed, msg = await rate_limiter.check_rate_limit(user_id, org_id)
        if not allowed:
            raise ValueError(msg)

        user_msg = Message(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content=data.content,
        )
        db.add(user_msg)
        await db.flush()

        ds = await datasource_service.get(db, conversation.datasource_id)
        if not ds:
            raise ValueError("Data source not found")

        schema_context = await schema_service.get_schema_for_agent(
            db, ds.id, org_id, conversation.project_id
        )
        config = datasource_service.get_connection_config(ds)
        history = await self.list_messages(db, conversation.id)

        agent_state = {
            "messages": [HumanMessage(content=m.content) for m in history if m.role == MessageRole.USER][-5:],
            "org_id": str(org_id),
            "project_id": str(conversation.project_id),
            "datasource_id": str(ds.id),
            "datasource_name": ds.name,
            "dialect": ds.type.value,
            "connection_config": {
                "host": config.host,
                "port": config.port,
                "database": config.database,
                "username": config.username,
                "password": config.password,
                "schema_name": config.schema_name,
                "ssl_mode": config.ssl_mode,
                "auth_source": config.auth_source,
            },
            "allowed_tables": ds.allowed_tables,
            "schema_context": schema_context,
            "natural_language_query": data.content,
            "generated_query": None,
            "query_language": None,
            "explanation": None,
            "visualization_draft": None,
            "follow_up_questions": [],
            "query_result": None,
            "visualization": None,
            "response": None,
            "error": None,
            "trace_id": None,
        }

        result = await query_agent.ainvoke(agent_state)
        response_data = result.get("response", {})

        assistant_msg = Message(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=response_data.get("explanation") or response_data.get("generated_query") or "Query processed",
            response_data=response_data,
        )
        db.add(assistant_msg)
        await db.flush()

        execution = response_data.get("execution", {})
        await audit_service.log_query(
            db=db,
            org_id=org_id,
            project_id=conversation.project_id,
            user_id=user_id,
            datasource_id=ds.id,
            action="query",
            natural_language_query=data.content,
            generated_query=response_data.get("generated_query"),
            row_count=execution.get("row_count"),
            duration_ms=execution.get("duration_ms"),
            trace_id=result.get("trace_id"),
        )

        return user_msg, assistant_msg


conversation_service = ConversationService()
