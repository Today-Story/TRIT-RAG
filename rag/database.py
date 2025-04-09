import os
import json
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def load_documents_from_postgres():
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )
    cursor = conn.cursor()

    cursor.execute("SELECT id, category, title, description FROM contents")
    contents = [
        {
            "id": row[0],
            "type": "content",
            "category": row[1],
            "title": row[2],
            "desc": row[3] or ""
        }
        for row in cursor.fetchall()
    ]

    cursor.execute("""
        SELECT l.id, l.place_name, l.address, l.latitude, l.longitude, l.google_map_id, c.id as contents_id, c.category
        FROM location l
        JOIN contents_location cl ON l.id = cl.location_id
        JOIN contents c ON cl.contents_id = c.id
    """)
    locations = [
        {
            "id": row[0],
            "type": "location",
            "title": row[1],
            "desc": row[2] or "",
            "latitude": float(row[3]),
            "longitude": float(row[4]),
            "google_map_id": row[5],
            "contents_id": row[6],
            "category": row[7]
        }
        for row in cursor.fetchall()
    ]

    cursor.execute("""
        SELECT c.id, u.nickname, c.category, u.country, c.youtube, c.introduction
        FROM creator c
        JOIN users u ON c.user_id = u.id
    """)
    creators = [
        {
            "id": row[0],
            "name": row[1],
            "category": row[2],
            "country": row[3],
            "youtube": row[4],
            "introduction": row[5]
        }
        for row in cursor.fetchall()
    ]

    cursor.close()
    conn.close()
    return contents, locations, creators

def save_recommendation_to_db(data: dict):
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )
    cursor = conn.cursor()

    # dict인 경우 None 처리 (중복 안전성 보장)
    contents_id = data.get("contents_id")
    creator_id = data.get("creator_id")
    if isinstance(contents_id, dict):
        contents_id = None
    if isinstance(creator_id, dict):
        creator_id = None

    cursor.execute(
        """
        INSERT INTO recommendation_history (user_id, needs, category, contents_id, creator_id, reason)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            data["user_id"],
            data["needs"],
            data["category"],
            contents_id,
            creator_id,
            json.dumps(data["reason"])
        )
    )

    conn.commit()
    cursor.close()
    conn.close()

def get_recommendations_by_user(user_id: int) -> list:
    load_dotenv()
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, needs, category, contents_id, creator_id, reason, created_at
        FROM recommendation_history
        WHERE user_id = %s
        ORDER BY created_at DESC
    """, (user_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    return [
        {
            "id": row[0],
            "needs": row[1],
            "category": row[2],
            "contentsId": row[3],
            "creatorId": row[4],
            "reason": row[5],
            "createdAt": row[6].isoformat()
        }
        for row in rows
    ]
