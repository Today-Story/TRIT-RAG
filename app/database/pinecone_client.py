from pinecone import Pinecone
from app.core.config import settings

# Pinecone 인스턴스 초기화
pc = Pinecone(api_key=settings.PINECONE_API_KEY)
index = pc.Index(settings.PINECONE_INDEX)

def upsert_user_behavior_vector(user_id: str, embedding: list[float], metadata: dict = None):
    index.upsert(vectors=[
        {
            "id": f"user-{user_id}",
            "values": embedding,
            "metadata": metadata or {}
        }
    ])

def query_similar_users(embedding: list[float], top_k: int = 5):
    return index.query(vector=embedding, top_k=top_k, include_metadata=True)

def fetch_existing_user_metadata(user_id: str) -> dict:
    """
    Pinecone에서 특정 user_id의 벡터 메타데이터를 가져옴
    """
    response = index.query(
        id=f"user-{user_id}",
        top_k=1,
        include_metadata=True
    )
    if response and response.matches:
        return response.matches[0].metadata or {}
    return {}
