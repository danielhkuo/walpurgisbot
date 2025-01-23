# dailycheck.py

import asyncio
import logging
import sqlite3
from datetime import datetime, timezone, timedelta

import pytz
from discord.ext import commands

from config import JOHAN_USER_ID, DEFAULT_CHANNEL_ID, TIMEZONE
from database import init_db
from dialogues import get_dialogue

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the bot's timezone
try:
    BOT_TIMEZONE = pytz.timezone(TIMEZONE)
except pytz.UnknownTimeZoneError:
    logger.error(f"Unknown timezone specified: {TIMEZONE}. Falling back to UTC.")
    BOT_TIMEZONE = pytz.utc


class DailyCheckCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        init_db()
        self.reminder_task = self.bot.loop.create_task(self.scheduler())

    def cog_unload(self):
        if self.reminder_task:
            self.reminder_task.cancel()

    async def scheduler(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                await self.send_daily_reminder()
            except Exception as e:
                logger.error(f"Error in daily reminder scheduler: {e}")
            # Sleep for a short duration to prevent tight loop in case of errors
            await asyncio.sleep(60)

    async def send_daily_reminder(self):
        with sqlite3.connect("daily_johans.db") as conn:
            cursor = conn.cursor()
            # Fetch the latest archived day and its timestamp
            cursor.execute("SELECT MAX(day), timestamp FROM daily_johans WHERE day IS NOT NULL")
            result = cursor.fetchone()
            latest_day = result[0] if result and result[0] else 0
            last_timestamp_str = result[1] if result and result[1] else None

        if not last_timestamp_str:
            logger.info("No Daily Johans archived yet.")
            return

        # Parse the last timestamp
        try:
            last_timestamp = datetime.fromisoformat(last_timestamp_str)
            if last_timestamp.tzinfo is None:
                # Assume UTC if no timezone info
                last_timestamp = last_timestamp.replace(tzinfo=timezone.utc)
            else:
                last_timestamp = last_timestamp.astimezone(timezone.utc)
        except Exception as e:
            logger.error(f"Failed to parse last_timestamp: {e}")
            return

        # Convert last_timestamp to BOT_TIMEZONE
        last_time_local = last_timestamp.astimezone(BOT_TIMEZONE)

        # Determine next reminder time
        # If last archive was before 4 PM local time, schedule reminder at same time next day
        # If last archive was after 4 PM local time, schedule reminder at 4 PM local time next day
        cutoff_time = last_time_local.replace(hour=16, minute=0, second=0, microsecond=0)  # 4 PM local time

        if last_time_local < cutoff_time:
            next_reminder_local = last_time_local + timedelta(days=1)
        else:
            # Schedule at 4 PM local time next day
            next_reminder_local = cutoff_time + timedelta(days=1)

        # Calculate how much time to wait until next_reminder
        now_local = datetime.now(BOT_TIMEZONE)
        wait_seconds = (next_reminder_local - now_local).total_seconds()

        if wait_seconds < 0:
            # If the time has already passed today, set to next day
            next_reminder_local += timedelta(days=1)
            wait_seconds = (next_reminder_local - now_local).total_seconds()

        logger.info(f"Scheduling next reminder at {next_reminder_local} {BOT_TIMEZONE} (in {wait_seconds} seconds).")

        # Schedule the reminder
        await asyncio.sleep(wait_seconds)

        # After waiting, perform the reminder
        with sqlite3.connect("daily_johans.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(day) FROM daily_johans")
            result = cursor.fetchone()
            latest_day = result[0] if result and result[0] else 0

        expected_day = latest_day + 1

        # Fetch all archived days up to latest_day
        with sqlite3.connect("daily_johans.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT day FROM daily_johans WHERE day <= ?", (latest_day,))
            archived_days = {row[0] for row in cursor.fetchall()}

        # Identify missing days
        missing_days = set(range(1, latest_day + 1)) - archived_days
        missed_days = len(missing_days)

        # Send reminder if it's time
        channel = self.bot.get_channel(DEFAULT_CHANNEL_ID)
        if not channel:
            logger.error(f"Channel with ID {DEFAULT_CHANNEL_ID} not found.")
            return

        # Prepare reminder message
        if missed_days > 0:
            reminder_message = get_dialogue(
                "daily_reminder_with_missed",
                user=JOHAN_USER_ID,
                day=expected_day,
                missed=missed_days
            )
        else:
            reminder_message = get_dialogue(
                "daily_reminder",
                user=JOHAN_USER_ID,
                day=expected_day
            )

        try:
            await channel.send(reminder_message)
            logger.info(f"Sent reminder for day {expected_day}. Missed days: {missed_days}")
        except Exception as e:
            logger.error(f"Failed to send reminder: {e}")

        # Reschedule the next reminder
        # Restart the scheduler
        self.reminder_task = self.bot.loop.create_task(self.scheduler())


async def setup(bot):
    await bot.add_cog(DailyCheckCog(bot))
