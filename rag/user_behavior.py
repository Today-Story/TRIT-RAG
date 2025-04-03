import os
import sys
import psycopg2
from dotenv import load_dotenv
from rag.embedding_utils import get_embedding
from rag.pinecone_client import upsert_user_behavior_vector

load_dotenv()

def fetch_user_behavior_text(user_id: int) -> str:
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT
            c.id,
            c.title,
            c.description,
            c.category,
            c.hashtags,
            u.nickname,
            c.creator_id
        FROM contents c
        LEFT JOIN watched_history v ON v.contents_id = c.id AND v.users_id = %s
        LEFT JOIN liked_history l ON l.contents_id = c.id AND l.users_id = %s
        LEFT JOIN playlist_contents_list pcl ON pcl.contents_list_id = c.id
        LEFT JOIN playlist p ON pcl.playlist_id = p.id AND p.user_id = %s
        LEFT JOIN creator cr ON c.creator_id = cr.id
        LEFT JOIN users u ON cr.user_id = u.id
        WHERE v.users_id IS NOT NULL OR l.users_id IS NOT NULL OR p.user_id IS NOT NULL
    """, (user_id, user_id, user_id))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        return ""

    text_blocks = []
    for row in rows:
        title, desc, category, hashtags, creator = row[1], row[2], row[3], row[4], row[5]
        block = f"Title: {title}, Desc: {desc}, Category: {category}, Tags: {hashtags}, Creator: {creator}"
        text_blocks.append(block)

    return "\n".join(text_blocks)

def store_user_behavior_embedding(user_id: int):
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT c.id, c.creator_id
        FROM contents c
        LEFT JOIN watched_history v ON v.contents_id = c.id AND v.users_id = %s
        LEFT JOIN liked_history l ON l.contents_id = c.id AND l.users_id = %s
        LEFT JOIN playlist_contents_list pcl ON pcl.contents_list_id = c.id
        LEFT JOIN playlist p ON pcl.playlist_id = p.id AND p.user_id = %s
        WHERE v.users_id IS NOT NULL OR l.users_id IS NOT NULL OR p.user_id IS NOT NULL
    """, (user_id, user_id, user_id))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        print(f"[user-{user_id}] No behavior data found.")
        return

    content_ids = set()
    creator_ids = set()
    for row in rows:
        if row[0]:
            content_ids.add(str(row[0]))
        if row[1]:
            creator_ids.add(str(row[1]))

    behavior_text = fetch_user_behavior_text(user_id)
    embedding = get_embedding(behavior_text)

    metadata = {
        "source": "user_behavior",
        "length": len(behavior_text),
        "preferred_content_ids": list(content_ids),
        "preferred_creator_ids": list(creator_ids)
    }

    upsert_user_behavior_vector(str(user_id), embedding, metadata)
    print(f"[user-{user_id}] Behavior embedding stored in Pinecone.")

def store_all_user_embeddings():
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users")
    user_ids = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()

    for user_id in user_ids:
        store_user_behavior_embedding(user_id)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "all":
        store_all_user_embeddings()
    else:
        user_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
        store_user_behavior_embedding(user_id)
