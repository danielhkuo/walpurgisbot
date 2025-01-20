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
                media_url1 TEXT,
                media_url2 TEXT,
                media_url3 TEXT,
                user_id TEXT,
                user_mention TEXT,
                confirmed BOOLEAN
            )
        """)
        conn.commit()


def archive_daily_johan_db(day_number, message, media_urls, confirmed=True):
    """
    Archive a Daily Johan entry.

    Args:
        day_number (int): The day number to archive.
        message (discord.Message): The Discord message object.
        media_urls (list of str): List of media URLs to archive (max 3).
        confirmed (bool): Whether the archiving is confirmed.

    Raises:
        ValueError: If attempting to add more than 3 media URLs to a day.
    """
    media_urls = media_urls[:3]  # Cap at 3 media URLs
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # Check if the day already exists
        cursor.execute("SELECT media_url1, media_url2, media_url3 FROM daily_johans WHERE day = ?", (day_number,))
        result = cursor.fetchone()

        if result:
            # Day exists, append new media URLs if space available
            existing_media = list(result)
            available_slots = [i for i, url in enumerate(existing_media) if url is None]

            if not available_slots and len(media_urls) > 0:
                raise ValueError(f"Day {day_number} already has the maximum number of media attachments.")

            # Assign new media URLs to available slots
            for media_url in media_urls:
                if not available_slots:
                    break
                slot = available_slots.pop(0)
                existing_media[slot] = media_url

            # Update the record with new media URLs
            cursor.execute("""
                UPDATE daily_johans 
                SET message_id = ?, channel_id = ?, timestamp = ?, media_url1 = ?, media_url2 = ?, media_url3 = ?, 
                    user_id = ?, user_mention = ?, confirmed = ?
                WHERE day = ?
            """, (
                str(message.id),
                str(message.channel.id),
                str(message.created_at),
                existing_media[0],
                existing_media[1],
                existing_media[2],
                str(message.author.id),
                message.author.mention,
                confirmed,
                day_number
            ))
        else:
            # Insert a new record with the first media URL
            cursor.execute("""
                INSERT INTO daily_johans 
                (day, message_id, channel_id, timestamp, media_url1, media_url2, media_url3, user_id, user_mention, confirmed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                day_number,
                str(message.id),
                str(message.channel.id),
                str(message.created_at),
                media_urls[0] if len(media_urls) > 0 else None,
                media_urls[1] if len(media_urls) > 1 else None,
                media_urls[2] if len(media_urls) > 2 else None,
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


def search_daily_johan(day_number):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT message_id, channel_id, media_url1, media_url2, media_url3
            FROM daily_johans 
            WHERE day = ?
        """, (day_number,))
        return cursor.fetchall()
