from fastapi import APIRouter

from app.api.v1 import auth, conversations, datasources, projects

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(projects.router)
api_router.include_router(datasources.router)
api_router.include_router(conversations.router)
