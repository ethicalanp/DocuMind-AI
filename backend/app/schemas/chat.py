from pydantic import BaseModel
from typing import List


class Source(BaseModel):

    document_id: int

    filename: str

    chunk_id: int


class ChatResponse(BaseModel):

    conversation_id: int

    question: str

    answer: str

    grounded: bool

    sources: List[Source]

    metadata: dict