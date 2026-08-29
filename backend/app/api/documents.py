import os
import shutil
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile
)
from fastapi.responses import FileResponse

from sqlalchemy.orm import Session

from app.core.database import SessionLocal

from app.dependencies.auth import get_current_user

from app.models.user import User
from app.models.document import Document
from app.models.document_chunk import DocumentChunk

from app.services.document_service import extract_text

from app.RAG.chunking import chunk_text

from app.services.embedding_service import create_embedding

from app.services.vector_service import add_chunk
from app.services.vector_service import delete_document_chunks

from app.services.retrieval_service import (
    retrieve_relevant_chunks
)


router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
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
# Upload Configuration
# ==========================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]
UPLOAD_DIR = str(PROJECT_ROOT / "uploads")

os.makedirs(
    UPLOAD_DIR,
    exist_ok=True
)


ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt"
}


# ==========================================
# Upload Document
# ==========================================

@router.post("/upload")
def upload_document(
    file: UploadFile = File(...),

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    )
):

    # --------------------------------------
    # 1. Validate file extension
    # --------------------------------------

    extension = os.path.splitext(
        file.filename
    )[1].lower()

    if extension not in ALLOWED_EXTENSIONS:

        raise HTTPException(
            status_code=400,
            detail="Only PDF, DOCX and TXT files are allowed"
        )


    # --------------------------------------
    # 2. Create user-specific folder
    # --------------------------------------

    user_folder = os.path.join(
        UPLOAD_DIR,
        str(current_user.id)
    )

    os.makedirs(
        user_folder,
        exist_ok=True
    )


    # --------------------------------------
    # 3. Create file path
    # --------------------------------------

    file_path = os.path.join(
        user_folder,
        file.filename
    )


    # --------------------------------------
    # 4. Save uploaded file
    # --------------------------------------

    try:

        with open(
            file_path,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Could not save file: {str(e)}"
        )


    # --------------------------------------
    # 5. Extract text
    # --------------------------------------

    try:

        extracted_text = extract_text(
            file_path
        )

    except Exception as e:

        if os.path.exists(file_path):
            os.remove(file_path)

        raise HTTPException(
            status_code=400,
            detail=f"Could not process document: {str(e)}"
        )


    # --------------------------------------
    # 6. Validate extracted text
    # --------------------------------------

    if not extracted_text.strip():

        if os.path.exists(file_path):
            os.remove(file_path)

        raise HTTPException(
            status_code=400,
            detail="Could not extract any text from the document"
        )


    # --------------------------------------
    # 7. Create Document record
    # --------------------------------------

    document = Document(
        filename=file.filename,
        file_path=file_path,
        user_id=current_user.id,
        status="processing"
    )

    db.add(document)

    db.commit()

    db.refresh(document)


    # --------------------------------------
    # 8. Create text chunks
    # --------------------------------------

    try:

        chunks = chunk_text(
            extracted_text
        )

    except Exception as e:

        document.status = "failed"

        db.commit()

        raise HTTPException(
            status_code=500,
            detail=f"Could not create document chunks: {str(e)}"
        )


    # --------------------------------------
    # 9. Validate chunks
    # --------------------------------------

    if not chunks:

        document.status = "failed"

        db.commit()

        raise HTTPException(
            status_code=400,
            detail="No usable text chunks were created"
        )


    # --------------------------------------
    # 10. Store chunks + embeddings
    # --------------------------------------

    try:

        for index, chunk in enumerate(chunks):

            # Create database chunk
            document_chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=index,
                chunk_text=chunk
            )

            db.add(document_chunk)

            # Get database ID
            db.flush()


            # Create embedding
            embedding = create_embedding(
                chunk
            )


            # Store vector in ChromaDB
            add_chunk(
                chunk_id=document_chunk.id,
                document_id=document.id,
                user_id=current_user.id,
                filename=document.filename,
                text=chunk,
                embedding=embedding
            )


    except Exception as e:

        document.status = "failed"

        db.commit()

        raise HTTPException(
            status_code=500,
            detail=f"Could not process document embeddings: {str(e)}"
        )


    # --------------------------------------
    # 11. Mark document as processed
    # --------------------------------------

    document.status = "processed"

    db.commit()

    db.refresh(document)


    # --------------------------------------
    # 12. Return response
    # --------------------------------------

    return {

        "message": "Document uploaded successfully",

        "document": {

            "id": document.id,

            "filename": document.filename,

            "status": document.status,

            "chunk_count": len(chunks),

            "created_at": document.created_at

        }

    }


# ==========================================
# Get Current User's Documents
# ==========================================

@router.get("/")
def get_documents(

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    )

):

    documents = (

        db.query(Document)

        .filter(
            Document.user_id == current_user.id
        )

        .order_by(
            Document.created_at.desc()
        )

        .all()

    )


    return {

        "documents": [

            {

                "id": document.id,

                "filename": document.filename,

                "status": document.status,

                "created_at": document.created_at

            }

            for document in documents

        ]

    }


# ==========================================
# Semantic Search
# ==========================================

@router.get("/search")
def search_documents(

    query: str,

    top_k: int = 5,

    current_user: User = Depends(
        get_current_user
    )

):

    results = retrieve_relevant_chunks(

        query=query,

        user_id=current_user.id,

        top_k=top_k

    )


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


    matches = []


    for index in range(
        len(documents)
    ):

        matches.append(

            {

                "text": documents[index],

                "metadata": metadatas[index],

                "distance": distances[index]

            }

        )


    return {

        "query": query,

        "results": matches

    }


# ==========================================
# Get Document Chunks
# ==========================================

@router.get("/{document_id}/chunks")
def get_document_chunks(

    document_id: int,

    current_user: User = Depends(
        get_current_user
    ),

    db: Session = Depends(
        get_db
    )

):

    # Find user's document
    document = (

        db.query(Document)

        .filter(

            Document.id == document_id,

            Document.user_id == current_user.id

        )

        .first()

    )


    if document is None:

        raise HTTPException(

            status_code=404,

            detail="Document not found"

        )


    # Get chunks
    chunks = (

        db.query(DocumentChunk)

        .filter(

            DocumentChunk.document_id == document_id

        )

        .order_by(

            DocumentChunk.chunk_index.asc()

        )

        .all()

    )


    return {

        "document_id": document.id,

        "filename": document.filename,

        "chunk_count": len(chunks),

        "chunks": [

            {

                "id": chunk.id,

                "chunk_index": chunk.chunk_index,

                "text": chunk.chunk_text,

                "created_at": chunk.created_at

            }

            for chunk in chunks

        ]

    }


@router.get("/{document_id}/download")
def download_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.user_id == current_user.id
        )
        .first()
    )

    if document is None or not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="Document file not found")

    return FileResponse(
        document.file_path,
        filename=document.filename,
        media_type="application/octet-stream"
    )


@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.user_id == current_user.id
        )
        .first()
    )

    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    delete_document_chunks(document.id)
    db.query(DocumentChunk).filter(
        DocumentChunk.document_id == document.id
    ).delete(synchronize_session=False)

    if os.path.exists(document.file_path):
        os.remove(document.file_path)

    db.delete(document)
    db.commit()

    return {"message": "Document deleted successfully"}