# database.py

import sqlite3
from datetime import datetime

import pytz

from config import TIMEZONE


def init_db():
    with sqlite3.connect("daily_johans.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_johans (
                day INTEGER PRIMARY KEY,
                message_id TEXT NOT NULL,
                media_url1 TEXT,
                media_url2 TEXT,
                media_url3 TEXT,
                timestamp TEXT NOT NULL
            );
        """)
        conn.commit()


def archive_daily_johan_db(day, message, media_urls, confirmed=True):
    # Create a timezone-aware datetime object based on the configured timezone
    try:
        bot_timezone = pytz.timezone(TIMEZONE)
    except pytz.UnknownTimeZoneError:
        # Fallback to UTC if an invalid timezone is provided
        bot_timezone = pytz.utc

    timestamp = datetime.now(bot_timezone).isoformat()

    with sqlite3.connect("daily_johans.db") as conn:
        cursor = conn.cursor()
        # Assign media URLs to columns, up to 3
        media_url1 = media_urls[0] if len(media_urls) > 0 else None
        media_url2 = media_urls[1] if len(media_urls) > 1 else None
        media_url3 = media_urls[2] if len(media_urls) > 2 else None

        try:
            cursor.execute("""
                INSERT INTO daily_johans (day, message_id, media_url1, media_url2, media_url3, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (day, str(message.id), media_url1, media_url2, media_url3, timestamp))
            conn.commit()
        except sqlite3.IntegrityError:
            raise ValueError(f"Day {day} is already archived.")
