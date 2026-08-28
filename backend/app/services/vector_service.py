import chromadb


CHROMA_PATH = "chroma_db"


# ==========================================
# ChromaDB Client
# ==========================================

client = chromadb.PersistentClient(
    path=CHROMA_PATH
)


# ==========================================
# Collection
# ==========================================

collection = client.get_or_create_collection(
    name="document_chunks"
)


# ==========================================
# Add Chunk
# ==========================================

def add_chunk(
    chunk_id: int,
    document_id: int,
    user_id: int,
    filename: str,
    text: str,
    embedding: list
):

    collection.add(
        ids=[str(chunk_id)],

        embeddings=[embedding],

        documents=[text],

        metadatas=[
            {
                "document_id": document_id,
                "user_id": user_id,
                "chunk_id": chunk_id,
                "filename": filename
            }
        ]
    )


# ==========================================
# Search Similar Chunks
# ==========================================

def search_chunks(
    query_embedding: list,
    user_id: int,
    top_k: int = 5
):

    results = collection.query(
        query_embeddings=[query_embedding],

        n_results=top_k,

        where={
            "user_id": user_id
        }
    )

    return results