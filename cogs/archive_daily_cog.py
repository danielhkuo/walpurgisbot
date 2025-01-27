# cogs/archive_daily_cog.py

import asyncio
import logging
import re
import sqlite3
from datetime import datetime, timezone, timedelta

import discord
import pytz
from discord.ext import commands, tasks

from config import JOHAN_USER_ID, DEFAULT_CHANNEL_ID, TIMEZONE, DB_FILE
from database import init_db, archive_daily_johan_db, get_existing_message_for_day
from dialogues import get_dialogue

logger = logging.getLogger(__name__)


class ArchiveDailyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.JOHAN_USER_ID = JOHAN_USER_ID
        self.DEFAULT_CHANNEL_ID = DEFAULT_CHANNEL_ID
        self.TIMEZONE = TIMEZONE

        # This attribute holds the timestamp of the most recent archived day.
        self.last_archive_time = None

        # Initialize DB and load last archive time from DB
        init_db()
        self._load_last_archive_time()

        # Start daily reminder task
        self.daily_reminder.start()

    def cog_unload(self):
        self.daily_reminder.cancel()

    def _load_last_archive_time(self):
        """
        Fetch the most recent archive timestamp from 'daily_johans'
        and store it in 'self.last_archive_time'.
        """
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT timestamp
                FROM daily_johans
                WHERE timestamp IS NOT NULL
                ORDER BY day DESC
                LIMIT 1
            """)
            row = cursor.fetchone()

            if not row or not row[0]:
                logger.info("No archived timestamp found. Starting with last_archive_time = None.")
                return

            timestamp_str = row[0]
            logger.debug(f"Loaded last archive timestamp from DB: {timestamp_str}")

            try:
                loaded_dt = datetime.fromisoformat(timestamp_str)
                # Ensure it's UTC
                if loaded_dt.tzinfo is None:
                    loaded_dt = loaded_dt.replace(tzinfo=timezone.utc)
                else:
                    loaded_dt = loaded_dt.astimezone(timezone.utc)

                self.last_archive_time = loaded_dt
                logger.info(f"Set last_archive_time to {self.last_archive_time} from DB on startup.")
            except ValueError as e:
                logger.error(f"Failed to parse timestamp '{timestamp_str}': {e}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        Automatic archiving logic:
          - Only triggers on messages from Johan.
          - Enforces a 12-hour cooldown since last successful archive.
          - Supports multi-day detection if multiple numbers + attachments.
          - Fallback to user reply if day number isn't auto-detected.
        """
        # Let other commands/cogs see the message
        await self.bot.process_commands(message)

        # Only handle messages from Johan
        if message.author.id != self.JOHAN_USER_ID:
            logger.debug(f"Ignored message from user ID {message.author.id}")
            return

        if not message.attachments:
            logger.debug(f"No attachments in message ID {message.id}")
            return

        # Up to 3 attachments
        media_urls = [att.url for att in message.attachments][:3]
        if not media_urls:
            logger.debug(f"No valid media in message ID {message.id}")
            return

        # Check 12-hour cooldown from last_archive_time
        now = datetime.now(timezone.utc)
        if self.last_archive_time:
            time_since_last = now - self.last_archive_time
            if time_since_last < timedelta(hours=12):
                # It's been <12 hours since we last archived
                try:
                    wait_time = timedelta(hours=12) - time_since_last
                    await message.author.send(
                        f"**Cooldown Active**: It's only been {time_since_last} since the last archive. "
                        f"Wait {wait_time} or use a **manual** archive command."
                    )
                    logger.info(f"Cooldown block. DM sent to {self.JOHAN_USER_ID}.")
                except discord.Forbidden:
                    await message.channel.send(
                        f"{message.author.mention}, I can't DM you. Enable DMs or use a manual archive command."
                    )
                    logger.warning(f"Failed to DM user ID {self.JOHAN_USER_ID}.")
                return

        # Retrieve the highest archived day
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(day) FROM daily_johans")
            result = cursor.fetchone()
            latest_day = result[0] if result and result[0] else 0

        expected_next = latest_day + 1
        logger.debug(f"Latest archived day: {latest_day}, expected next day: {expected_next}")

        # Attempt to find day numbers automatically
        numbers_found = re.findall(r"\d+", message.content)
        match = re.search(r"(?:Day\s*#?|\#|daily\s+johan\s+|johan\s+)(\d+)|(^\d+$)",
                          message.content, re.IGNORECASE)

        # Multi-day scenario if multiple numbers + multiple attachments
        if len(numbers_found) >= 2 and len(media_urls) >= 2:
            day_numbers = [int(num) for num in numbers_found[:len(media_urls)]]
            archived_days = []

            for day, media_url in zip(day_numbers, media_urls):
                if get_existing_message_for_day(day):
                    await message.channel.send(get_dialogue("day_already_archived", day=day))
                    logger.info(f"Day {day} already archived. Skipping.")
                    continue
                try:
                    archive_daily_johan_db(day, message, [media_url], confirmed=True)
                    archived_days.append(day)
                    logger.info(f"Auto-archived day {day} from msg {message.id}")
                except ValueError as ve:
                    await message.channel.send(str(ve))
                    logger.error(f"Error archiving day {day}: {ve}")
                    continue

            if archived_days:
                await message.channel.send(
                    get_dialogue("auto_archived_series", days=", ".join(map(str, archived_days))))
                self.last_archive_time = now  # Update cooldown
            return

        # Single-day scenario
        day_number = None
        bypass_verification = False

        if not match:
            # Prompt user to confirm if it’s a Daily Johan
            await message.channel.send(get_dialogue("ask_if_daily_johan", user=self.JOHAN_USER_ID, msg_id=message.id))
            logger.debug(f"Prompted if msg {message.id} is a daily johan.")

            def check_n(m):
                return m.author.id == self.JOHAN_USER_ID and m.channel == message.channel

            try:
                reply = await self.bot.wait_for("message", timeout=60.0, check=check_n)
                reply_content = reply.content.strip().lower()

                if reply_content in ["no", "n"]:
                    logger.info(f"Msg {message.id} is not a daily johan (per user).")
                    return

                # Maybe user typed a day number?
                numbers_in_reply = re.findall(r"\d+", reply.content)
                if numbers_in_reply:
                    if len(numbers_in_reply) >= 2 and len(media_urls) >= 2:
                        # Another multi-day from user
                        day_numbers = [int(num) for num in numbers_in_reply[:len(media_urls)]]
                        archived_days = []

                        for day, media_url in zip(day_numbers, media_urls):
                            if get_existing_message_for_day(day):
                                await message.channel.send(get_dialogue("day_already_archived", day=day))
                                logger.info(f"Day {day} archived. Skipping.")
                                continue
                            try:
                                archive_daily_johan_db(day, message, [media_url], confirmed=True)
                                archived_days.append(day)
                                logger.info(f"Archived day {day} from msg {message.id}")
                            except ValueError as ve:
                                await message.channel.send(str(ve))
                                logger.error(f"Error archiving day {day}: {ve}")
                                continue

                        if archived_days:
                            await message.channel.send(
                                get_dialogue("auto_archived_series", days=", ".join(map(str, archived_days)))
                            )
                            self.last_archive_time = now
                        return
                    else:
                        # Single day
                        day_number = int(numbers_in_reply[0])
                        bypass_verification = True
                else:
                    await message.channel.send(get_dialogue("couldnt_parse_reply"))
                    logger.warning(f"Could not parse day number from user for msg {message.id}.")
                    return

            except asyncio.TimeoutError:
                await message.channel.send("No response from Johan. Aborting auto-archive.")
                logger.warning(f"Timeout waiting for reply for msg {message.id}.")
                return
        else:
            # We found a direct match
            try:
                day_number = int(match.group(1) or match.group(2))
            except ValueError:
                await message.channel.send(get_dialogue("parse_error", msg_id=message.id))
                logger.error(f"Error parsing day for msg {message.id}.")
                return

        # If multiple numbers but not enough attachments => ask manual submission
        if len(numbers_found) > 1:
            await message.channel.send(get_dialogue("multiple_numbers"))
            logger.info(f"Multiple day nums in msg {message.id}; requested manual.")
            return

        # If day_number != expected, prompt verification (unless user input said "we're sure")
        if not bypass_verification and day_number != expected_next:
            await message.channel.send(get_dialogue("verification_prompt", provided=day_number))
            logger.info(f"Day {day_number} != expected {expected_next}; verifying with user.")

            def check_verification(m):
                return m.author.id == self.JOHAN_USER_ID and m.channel == message.channel and \
                    m.content.lower() in ["yes", "no", "y", "n"]

            try:
                verification_reply = await self.bot.wait_for("message", timeout=60.0, check=check_verification)
                if verification_reply.content.strip().lower() in ["yes", "y"]:
                    await message.channel.send(get_dialogue("verification_accepted", provided=day_number))
                else:
                    await message.channel.send(get_dialogue("verification_denied"))
                    return
            except asyncio.TimeoutError:
                await message.channel.send("No verification response. Aborting auto-archive.")
                logger.warning(f"Timeout verifying day {day_number} for msg {message.id}.")
                return

        # Check if day is already archived
        if get_existing_message_for_day(day_number):
            await message.channel.send(get_dialogue("day_already_archived", day=day_number))
            logger.info(f"Day {day_number} already archived.")
            return

        # Archive single day
        try:
            archive_daily_johan_db(day_number, message, media_urls, confirmed=True)
            await message.channel.send(get_dialogue("auto_archived", day=day_number))

            # Update cooldown
            self.last_archive_time = now
            logger.info(f"Archived day {day_number} from msg {message.id} (auto).")

        except ValueError as ve:
            await message.channel.send(str(ve))
            logger.error(f"ValueError archiving day {day_number}: {ve}")
        except Exception as e:
            await message.channel.send(get_dialogue("deletion_error", error=e))
            logger.error(f"Exception archiving day {day_number}: {e}")

    @tasks.loop(minutes=60)
    async def daily_reminder(self):
        """
        Sends a daily reminder based on the last archive time,
        scheduling roughly for 4 PM local if there's a gap.
        """
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(day), timestamp FROM daily_johans WHERE day IS NOT NULL")
            result = cursor.fetchone()
            latest_day = result[0] if result and result[0] else 0
            last_timestamp_str = result[1] if result and result[1] else None

        if not last_timestamp_str:
            logger.info("No daily_johans archived yet. Skipping reminder.")
            return

        # Parse the DB timestamp
        try:
            last_timestamp = datetime.fromisoformat(last_timestamp_str)
            if last_timestamp.tzinfo is None:
                last_timestamp = last_timestamp.replace(tzinfo=timezone.utc)
            else:
                last_timestamp = last_timestamp.astimezone(timezone.utc)
        except Exception as e:
            logger.error(f"Failed to parse last_timestamp from DB: {e}")
            return

        # Convert to local tz
        try:
            bot_timezone = pytz.timezone(self.TIMEZONE)
        except pytz.UnknownTimeZoneError:
            logger.error(f"Unknown timezone: {self.TIMEZONE}. Defaulting to UTC.")
            bot_timezone = pytz.utc

        last_time_local = last_timestamp.astimezone(bot_timezone)
        cutoff_time = last_time_local.replace(hour=16, minute=0, second=0, microsecond=0)

        if last_time_local < cutoff_time:
            next_reminder_local = last_time_local + timedelta(days=1)
        else:
            next_reminder_local = cutoff_time + timedelta(days=1)

        now_local = datetime.now(bot_timezone)
        wait_seconds = (next_reminder_local - now_local).total_seconds()
        if wait_seconds < 0:
            next_reminder_local += timedelta(days=1)
            wait_seconds = (next_reminder_local - now_local).total_seconds()

        logger.info(f"Scheduling next reminder at {next_reminder_local} in {wait_seconds} seconds.")
        await asyncio.sleep(wait_seconds)

        # After sleeping, check how many days are missing
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(day) FROM daily_johans")
            result = cursor.fetchone()
            latest_day = result[0] if result and result[0] else 0

        expected_day = latest_day + 1

        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT day FROM daily_johans WHERE day <= ?", (latest_day,))
            archived_days = {row[0] for row in cursor.fetchall()}

        missing_days = set(range(1, latest_day + 1)) - archived_days
        missed_days = len(missing_days)

        channel = self.bot.get_channel(self.DEFAULT_CHANNEL_ID)
        if not channel:
            logger.error(f"Channel {self.DEFAULT_CHANNEL_ID} not found. Reminder aborted.")
            return

        if missed_days > 0:
            reminder_msg = get_dialogue("daily_reminder_with_missed",
                                        user=self.JOHAN_USER_ID,
                                        day=expected_day,
                                        missed=missed_days)
        else:
            reminder_msg = get_dialogue("daily_reminder",
                                        user=self.JOHAN_USER_ID,
                                        day=expected_day)

        try:
            await channel.send(reminder_msg)
            logger.info(f"Sent reminder for day {expected_day}. Missed = {missed_days}")
        except Exception as e:
            logger.error(f"Failed sending reminder: {e}")

    @daily_reminder.before_loop
    async def before_daily_reminder(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(ArchiveDailyCog(bot))
