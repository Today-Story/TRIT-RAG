from rag.pinecone_client import index

def show_total_vector_count():
    stats = index.describe_index_stats()
    total_count = stats.get('total_vector_count', 0)
    print(f"📦 Pinecone에 저장된 전체 벡터 수: {total_count}")

if __name__ == "__main__":
    show_total_vector_count()
