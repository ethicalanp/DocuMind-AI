from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base
from app.models.user import User
from app.api.auth import router as auth_router
from app.models.document import Document
from app.api.documents import router as documents_router
from app.models.document_chunk import DocumentChunk
from app.api.chat import router as chat_router
from app.models.conversation import Conversation
from app.models.message import Message
from app.api.conversations import router as conversations_router


Base.metadata.create_all(bind=engine)

app=FastAPI(
    title="DocuMind AI",
    description="AI-Powered Business Assistent",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|10\.10\.10\.174)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(chat_router)
app.include_router(conversations_router)


@app.get("/")
def root():
    return{"message":"DocuMind AI API is running"}


@app.get("/health")
def health():
    return {"status": "ok", "service": "documind-api"}



