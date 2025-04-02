import os
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
