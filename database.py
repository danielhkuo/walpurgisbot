# database.py

import sqlite3
from datetime import datetime

import pytz

from config import TIMEZONE

DB_FILE = "daily_johans.db"


def init_db():
    """
    Initialize the database by creating the daily_johans table if it doesn't exist.
    """
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

    # Determine the timezone for timestamp
    try:
        bot_timezone = pytz.timezone(TIMEZONE)
    except pytz.UnknownTimeZoneError:
        # Fallback to UTC if an invalid timezone is provided
        bot_timezone = pytz.utc

    # Get the current time in the configured timezone
    timestamp = datetime.now(bot_timezone).isoformat()

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

            # Update the record with new media URLs and other details
            cursor.execute("""
                UPDATE daily_johans 
                SET message_id = ?, channel_id = ?, timestamp = ?, media_url1 = ?, media_url2 = ?, media_url3 = ?, 
                    user_id = ?, user_mention = ?, confirmed = ?
                WHERE day = ?
            """, (
                str(message.id),
                str(message.channel.id),
                timestamp,
                existing_media[0],
                existing_media[1],
                existing_media[2],
                str(message.author.id),
                message.author.mention,
                confirmed,
                day_number
            ))
        else:
            # Insert a new record with the provided media URLs and details
            cursor.execute("""
                INSERT INTO daily_johans 
                (day, message_id, channel_id, timestamp, media_url1, media_url2, media_url3, user_id, user_mention, confirmed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                day_number,
                str(message.id),
                str(message.channel.id),
                timestamp,
                media_urls[0] if len(media_urls) > 0 else None,
                media_urls[1] if len(media_urls) > 1 else None,
                media_urls[2] if len(media_urls) > 2 else None,
                str(message.author.id),
                message.author.mention,
                confirmed
            ))
        conn.commit()


def get_existing_day_for_message(message_id):
    """
    Retrieve the day number associated with a given message ID.

    Args:
        message_id (str): The Discord message ID.

    Returns:
        tuple or None: The day number if found, else None.
    """
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT day FROM daily_johans WHERE message_id = ?", (str(message_id),))
        return cursor.fetchone()


def get_existing_message_for_day(day_number):
    """
    Retrieve the message ID associated with a given day number.

    Args:
        day_number (int): The day number.

    Returns:
        tuple or None: The message ID if found, else None.
    """
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT message_id FROM daily_johans WHERE day = ?", (day_number,))
        return cursor.fetchone()


def delete_daily_johan_by_message_id(message_id):
    """
    Delete a Daily Johan entry based on the message ID.

    Args:
        message_id (str): The Discord message ID to delete.
    """
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM daily_johans WHERE message_id = ?", (str(message_id),))
        conn.commit()


def search_daily_johan(day_number):
    """
    Search for a Daily Johan by day number.

    Args:
        day_number (int): The day number to search for.

    Returns:
        list of tuples: Each tuple contains message_id, channel_id, media_url1, media_url2, media_url3.
    """
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT message_id, channel_id, media_url1, media_url2, media_url3
            FROM daily_johans 
            WHERE day = ?
        """, (day_number,))
        return cursor.fetchall()


def insert_bulk_daily_johans(data):
    """
    Insert multiple Daily Johan entries into the database.

    Args:
        data (list of dict): List of dictionaries containing Daily Johan data.

    Raises:
        ValueError: If the data format is incorrect.
    """
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        for record in data:
            day = record.get("day")
            message_id = record.get("message_id")
            channel_id = record.get("channel_id")
            timestamp = record.get("timestamp")
            media_url1 = record.get("media_url1")
            media_url2 = record.get("media_url2")
            media_url3 = record.get("media_url3")
            user_id = record.get("user_id")
            user_mention = record.get("user_mention")
            confirmed = record.get("confirmed", True)

            if not day or not message_id or not channel_id or not timestamp or not user_id or not user_mention:
                raise ValueError("Missing required fields in data.")

            # Check if the day already exists
            cursor.execute("SELECT * FROM daily_johans WHERE day = ?", (day,))
            if cursor.fetchone():
                # Optionally, skip or update existing records
                # Here, we'll skip existing records
                continue

            cursor.execute("""
                INSERT INTO daily_johans 
                (day, message_id, channel_id, timestamp, media_url1, media_url2, media_url3, user_id, user_mention, confirmed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                day,
                message_id,
                channel_id,
                timestamp,
                media_url1,
                media_url2,
                media_url3,
                user_id,
                user_mention,
                confirmed
            ))
        conn.commit()


def clear_daily_johans_table():
    """
    Clears all records from the daily_johans table.
    """
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM daily_johans")
        conn.commit()
