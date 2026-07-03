from fastapi import FastAPI

from src.api.routes import router

app = FastAPI(
    title="AI Article RAG Agent API",
    version="1.0.0",
    description="Daily AI article collector with LangChain RAG, Qdrant, Tavily fallback, and FastAPI.",
)

app.include_router(router)
