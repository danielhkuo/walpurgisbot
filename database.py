import sqlite3

DB_FILE = "daily_johans.db"

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_johans (
                day INTEGER PRIMARY KEY,
                message_id TEXT,
                channel_id TEXT,
                timestamp TEXT,
                media_url TEXT,
                user_id TEXT,
                user_mention TEXT,
                confirmed BOOLEAN
            )
        """)
        conn.commit()

def archive_daily_johan_db(day_number, message, media_url, confirmed=True):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO daily_johans 
            (day, message_id, channel_id, timestamp, media_url, user_id, user_mention, confirmed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            day_number,
            str(message.id),
            str(message.channel.id),
            str(message.created_at),
            media_url,
            str(message.author.id),
            message.author.mention,
            confirmed
        ))
        conn.commit()

def get_existing_day_for_message(message_id):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT day FROM daily_johans WHERE message_id = ?", (str(message_id),))
        return cursor.fetchone()

def get_existing_message_for_day(day_number):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT message_id FROM daily_johans WHERE day = ?", (day_number,))
        return cursor.fetchone()

def delete_daily_johan_by_message_id(message_id):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM daily_johans WHERE message_id = ?", (str(message_id),))
        conn.commit()
