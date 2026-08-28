from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import SessionLocal

from app.core.config import (
    RAG_DISTANCE_THRESHOLD
)

from app.dependencies.auth import get_current_user

from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message

from app.services.retrieval_service import (
    retrieve_relevant_chunks
)

from app.services.llm_service import (
    generate_answer
)

from app.schemas.chat import ChatResponse


# ==========================================
# Router
# ==========================================

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
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
# Request Model
# ==========================================

class ChatRequest(BaseModel):

    conversation_id: int

    question: str

    top_k: int = 5


# ==========================================
# Chat Endpoint
# ==========================================

@router.post(
    "/",
    response_model=ChatResponse
)
def chat(

    request: ChatRequest,

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    )

):

    # ======================================
    # 1. Validate Question
    # ======================================

    question = request.question.strip()

    if not question:

        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )


    # ======================================
    # 2. Validate Top K
    # ======================================

    if request.top_k < 1:

        raise HTTPException(
            status_code=400,
            detail="top_k must be at least 1"
        )

    if request.top_k > 10:

        raise HTTPException(
            status_code=400,
            detail="top_k cannot be greater than 10"
        )


    # ======================================
    # 3. Validate Conversation
    # ======================================

    conversation = (

        db.query(Conversation)

        .filter(

            Conversation.id
            == request.conversation_id,

            Conversation.user_id
            == current_user.id

        )

        .first()

    )


    if conversation is None:

        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )


    # ======================================
    # 4. Load Conversation History
    # ======================================

    previous_messages = (

        db.query(Message)

        .filter(

            Message.conversation_id
            == conversation.id

        )

        .order_by(

            Message.created_at.asc()

        )

        .all()

    )


    # ======================================
    # 5. Limit Conversation History
    # ======================================

    recent_messages = previous_messages[-10:]


    # ======================================
    # 6. Retrieve Relevant Document Chunks
    # ======================================

    try:

        results = retrieve_relevant_chunks(

            query=question,

            user_id=current_user.id,

            top_k=request.top_k

        )

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=f"Document retrieval failed: {str(e)}"

        )


    # ======================================
    # 7. Extract Retrieval Results
    # ======================================

    documents = results.get(
        "documents",
        [[]]
    )[0]

    metadatas = results.get(
        "metadatas",
        [[]]
    )[0]

    distances = results.get(
        "distances",
        [[]]
    )[0]


    # ======================================
    # 8. Check Retrieval Results
    # ======================================

    if not documents:

        return {

            "conversation_id":
                conversation.id,

            "question":
                question,

            "answer": (
                "I couldn't find relevant "
                "information in your uploaded "
                "documents."
            ),

            "grounded": False,

            "sources": [],

            "metadata": {

                "retrieval_count": 0,

                "best_distance": None,

                "threshold":
                    RAG_DISTANCE_THRESHOLD,

                "history_messages_used":
                    len(recent_messages)

            }

        }


    # ======================================
    # 9. Find Best Distance
    # ======================================

    best_distance = min(
        distances
    )


    # ======================================
    # 10. RAG Distance Threshold
    # ======================================

    if (
        best_distance
        > RAG_DISTANCE_THRESHOLD
    ):

        return {

            "conversation_id":
                conversation.id,

            "question":
                question,

            "answer": (
                "I couldn't find relevant "
                "information in your uploaded "
                "documents."
            ),

            "grounded": False,

            "sources": [],

            "metadata": {

                "retrieval_count":
                    len(documents),

                "best_distance":
                    best_distance,

                "threshold":
                    RAG_DISTANCE_THRESHOLD,

                "history_messages_used":
                    len(recent_messages)

            }

        }


    # ======================================
    # 11. Build Document Context
    # ======================================

    context_parts = []


    for index, document in enumerate(
        documents
    ):

        metadata = metadatas[index]


        filename = metadata.get(
            "filename",
            "Unknown document"
        )


        document_id = metadata.get(
            "document_id"
        )


        chunk_id = metadata.get(
            "chunk_id"
        )


        context_parts.append(

            f"""
Source {index + 1}

Document:
{filename}

Document ID:
{document_id}

Chunk ID:
{chunk_id}

Content:
{document}
"""

        )


    document_context = "\n\n".join(
        context_parts
    )


    # ======================================
    # 12. Build Conversation Context
    # ======================================

    conversation_context = ""


    for message in recent_messages:

        conversation_context += (

            f"{message.role.upper()}: "
            f"{message.content}\n"

        )


    # ======================================
    # 13. Build Final Context
    # ======================================

    final_context = f"""

CONVERSATION HISTORY

{conversation_context}


DOCUMENT CONTEXT

{document_context}

"""


    # ======================================
    # 14. Generate LLM Answer
    # ======================================

    try:

        llm_result = generate_answer(

            question=question,

            context=final_context

        )

    except Exception as e:

        raise HTTPException(

            status_code=500,

            detail=f"LLM generation failed: {str(e)}"

        )


    # ======================================
    # 15. Extract LLM Result
    # ======================================

    answer = llm_result.get(
        "answer",
        ""
    )


    llm_grounded = llm_result.get(
        "grounded",
        False
    )


    # ======================================
    # 16. Validate LLM Answer
    # ======================================

    if not answer.strip():

        raise HTTPException(

            status_code=500,

            detail="LLM returned an empty answer"

        )


    # ======================================
    # 17. Save User Message
    # ======================================

    user_message = Message(

        conversation_id=
            conversation.id,

        role="user",

        content=question

    )


    db.add(
        user_message
    )


    # ======================================
    # 18. Save Assistant Message
    # ======================================

    assistant_message = Message(

        conversation_id=
            conversation.id,

        role="assistant",

        content=answer

    )


    db.add(
        assistant_message
    )


    # ======================================
    # 19. Build Sources
    # ======================================

    sources = []


    for index, metadata in enumerate(
        metadatas
    ):

        document_id = metadata.get(
            "document_id"
        )

        filename = metadata.get(
            "filename",
            "Unknown document"
        )

        chunk_id = metadata.get(
            "chunk_id"
        )


        # Only add valid sources

        if (
            document_id is not None
            and chunk_id is not None
        ):

            sources.append({

                "document_id":
                    document_id,

                "filename":
                    filename,

                "chunk_id":
                    chunk_id

            })


    # ======================================
    # 20. Commit Messages
    # ======================================

    try:

        db.commit()

        db.refresh(
            assistant_message
        )

    except Exception as e:

        db.rollback()

        raise HTTPException(

            status_code=500,

            detail=f"Could not save messages: {str(e)}"

        )


    # ======================================
    # 21. Final Response
    # ======================================

    return {

        "conversation_id":
            conversation.id,

        "question":
            question,

        "answer":
            answer,

        "grounded":
            llm_grounded,

        "sources":
            sources,

        "metadata": {

            "retrieval_count":
                len(documents),

            "best_distance":
                best_distance,

            "threshold":
                RAG_DISTANCE_THRESHOLD,

            "history_messages_used":
                len(recent_messages)

        }

    }