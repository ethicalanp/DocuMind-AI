from app.services.embedding_service import create_embedding
from app.services.vector_service import search_chunks


def retrieve_relevant_chunks(
    query: str,
    user_id: int,
    top_k: int = 5
):

    # ==========================================
    # 1. Create embedding for the question
    # ==========================================

    query_embedding = create_embedding(
        query
    )


    # ==========================================
    # 2. Search ChromaDB
    # ==========================================

    results = search_chunks(
        query_embedding=query_embedding,
        user_id=user_id,
        top_k=top_k
    )


    # ==========================================
    # 3. Return retrieval results
    # ==========================================

    return results