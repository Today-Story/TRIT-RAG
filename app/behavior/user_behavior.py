from datetime import datetime
import psycopg2
from app.core.config import settings
from app.recommender.embedding import get_embedding
from app.database.pinecone_client import (
    upsert_user_behavior_vector,
    fetch_existing_user_metadata,
)

def fetch_user_behavior_text(user_id: int) -> str:
    conn = psycopg2.connect(
        dbname=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        host=settings.DB_HOST,
        port=settings.DB_PORT
    )
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT
            c.id, c.title, c.description, c.category, u.nickname,
            c.creator_id, ARRAY_AGG(h.name) AS hashtags
        FROM contents c
        LEFT JOIN watched_history v ON v.contents_id = c.id AND v.users_id = %s
        LEFT JOIN liked_history l ON l.contents_id = c.id AND l.users_id = %s
        LEFT JOIN playlist_contents_list pcl ON pcl.contents_list_id = c.id
        LEFT JOIN playlist p ON pcl.playlist_id = p.id AND p.user_id = %s
        LEFT JOIN creator cr ON c.creator_id = cr.id
        LEFT JOIN users u ON cr.user_id = u.id
        LEFT JOIN hashtags_contents_mapping hcm ON hcm.contents_id = c.id
        LEFT JOIN hashtags h ON hcm.hashtags_id = h.id
        WHERE v.users_id IS NOT NULL OR l.users_id IS NOT NULL OR p.user_id IS NOT NULL
        GROUP BY c.id, u.nickname, c.title, c.description, c.category, c.creator_id
    """, (user_id, user_id, user_id))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if not rows:
        return ""

    text_blocks = []
    for row in rows:
        title, desc, category, creator, hashtags = row[1], row[2], row[3], row[4], row[6] or []
        hashtags_str = ", ".join(hashtags)
        block = f"Title: {title}, Desc: {desc}, Category: {category}, Tags: {hashtags_str}, Creator: {creator}"
        text_blocks.append(block)

    return "\n".join(text_blocks)

def get_last_activity_time(user_id: int):
    conn = psycopg2.connect(
        dbname=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        host=settings.DB_HOST,
        port=settings.DB_PORT
    )
    cursor = conn.cursor()
    cursor.execute("""
        SELECT MAX(latest) FROM (
            SELECT MAX(watched_at) AS latest FROM watched_history WHERE users_id = %s
            UNION ALL
            SELECT MAX(liked_at) FROM liked_history WHERE users_id = %s
            UNION ALL
            SELECT MAX(p.updated_at) FROM playlist_contents_list pcl
                JOIN playlist p ON pcl.playlist_id = p.id
                WHERE p.user_id = %s
        ) AS combined;
    """, (user_id, user_id, user_id))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result and result[0] else None

def store_user_behavior_embedding(user_id: int):
    last_activity_time = get_last_activity_time(user_id)
    if not last_activity_time:
        print(f"[user-{user_id}] No behavior data found.")
        return

    existing = fetch_existing_user_metadata(str(user_id))
    last_updated = existing.get("last_updated_at")
    if last_updated and last_activity_time <= datetime.fromisoformat(last_updated):
        print(f"[user-{user_id}] No new activity since last update.")
        return

    conn = psycopg2.connect(
        dbname=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        host=settings.DB_HOST,
        port=settings.DB_PORT
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

    content_ids = {str(row[0]) for row in rows if row[0]}
    creator_ids = {str(row[1]) for row in rows if row[1]}

    behavior_text = fetch_user_behavior_text(user_id)
    embedding = get_embedding(behavior_text)

    metadata = {
        "source": "user_behavior",
        "length": len(behavior_text),
        "preferred_content_ids": list(content_ids),
        "preferred_creator_ids": list(creator_ids),
        "last_updated_at": datetime.utcnow().isoformat()
    }

    upsert_user_behavior_vector(str(user_id), embedding, metadata)
    print(f"[user-{user_id}] Behavior embedding stored in Pinecone.")

def store_all_user_embeddings():
    conn = psycopg2.connect(
        dbname=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        host=settings.DB_HOST,
        port=settings.DB_PORT
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
        try:
            user_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
            store_user_behavior_embedding(user_id)
        except Exception as e:
            print(f"❌ Error: {e}")
