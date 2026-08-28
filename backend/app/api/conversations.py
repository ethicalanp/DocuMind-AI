from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import SessionLocal

from app.dependencies.auth import get_current_user

from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message


router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"]
)


# ==========================================
# Database Dependency
# ==========================================

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# ==========================================
# Create Conversation Request
# ==========================================

class ConversationCreate(BaseModel):

    title: str | None = None


# ==========================================
# Create Conversation
# ==========================================

@router.post("/")
def create_conversation(
    request: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    conversation = Conversation(
        user_id=current_user.id,
        title=request.title or "New Conversation"
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return {
        "message": "Conversation created successfully",

        "conversation": {
            "id": conversation.id,
            "title": conversation.title,
            "created_at": conversation.created_at
        }
    }


# ==========================================
# Get User Conversations
# ==========================================

@router.get("/")
def get_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    conversations = (
        db.query(Conversation)
        .filter(
            Conversation.user_id == current_user.id
        )
        .order_by(
            Conversation.created_at.desc()
        )
        .all()
    )

    return {
        "conversations": [
            {
                "id": conversation.id,
                "title": conversation.title,
                "created_at": conversation.created_at
            }

            for conversation in conversations
        ]
    }


# ==========================================
# Get Conversation Messages
# ==========================================

@router.get("/{conversation_id}/messages")
def get_messages(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
        .first()
    )

    if conversation is None:

        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )


    messages = (
        db.query(Message)
        .filter(
            Message.conversation_id == conversation_id
        )
        .order_by(
            Message.created_at.asc()
        )
        .all()
    )


    return {
        "conversation_id": conversation_id,

        "messages": [
            {
                "id": message.id,
                "role": message.role,
                "content": message.content,
                "created_at": message.created_at
            }

            for message in messages
        ]
    }