import os
from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX = os.getenv("PINECONE_INDEX")

# 새로운 Pinecone 인스턴스 방식
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX)

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
