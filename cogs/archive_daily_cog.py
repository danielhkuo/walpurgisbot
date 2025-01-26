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
        self.last_archive_time = None
        init_db()
        self.daily_reminder.start()

    def cog_unload(self):
        self.daily_reminder.cancel()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        await self.bot.process_commands(message)

        # Process only messages from Johan
        if message.author.id != self.JOHAN_USER_ID:
            logger.debug(f"Ignored message from user ID {message.author.id}")
            return

        if not message.attachments:
            logger.debug(f"No attachments in message ID {message.id}")
            return

        # Limit to first 3 media URLs
        media_urls = [att.url for att in message.attachments][:3]
        if not media_urls:
            logger.debug(f"No media URLs extracted from message ID {message.id}")
            return

        # Determine next expected day
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(day) FROM daily_johans")
            result = cursor.fetchone()
            latest_day = result[0] if result and result[0] else 0
        expected_next = latest_day + 1
        logger.debug(f"Latest archived day: {latest_day}, Expected next day: {expected_next}")

        # Check for 12-hour cooldown
        now = datetime.now(timezone.utc)
        if self.last_archive_time:
            time_diff = now - self.last_archive_time
            if time_diff < timedelta(hours=12):
                try:
                    await message.author.send(
                        f"**Cooldown Active:** Please wait {timedelta(hours=12) - time_diff} before archiving another Daily Johan."
                    )
                    logger.info(f"Cooldown active. Sent DM to user ID {self.JOHAN_USER_ID}.")
                except discord.Forbidden:
                    await message.channel.send(
                        f"{message.author.mention}, I can't send you a DM. Please allow DMs from server members."
                    )
                    logger.warning(f"Failed to send DM to user ID {self.JOHAN_USER_ID}.")
                return

        # Attempt to find day numbers
        numbers_found = re.findall(r"\d+", message.content)
        match = re.search(
            r"(?:Day\s*#?|\#|daily\s+johan\s+|johan\s+)(\d+)|(^\d+$)",
            message.content,
            re.IGNORECASE
        )

        # MULTI-DAY SCENARIO
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
                    logger.info(f"Archived day {day} from message ID {message.id}.")
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

        day_number = None
        bypass_time_check = False

        if not match:
            # Prompt user
            await message.channel.send(
                get_dialogue("ask_if_daily_johan", user=self.JOHAN_USER_ID, msg_id=message.id)
            )
            logger.debug(f"Asked if message ID {message.id} is a Daily Johan.")

            def check_n(m):
                return m.author.id == self.JOHAN_USER_ID and m.channel == message.channel

            try:
                reply = await self.bot.wait_for("message", timeout=60.0, check=check_n)
                reply_content = reply.content.strip().lower()
                logger.debug(f"Received reply from Johan: {reply_content}")
                if reply_content in ["no", "n"]:
                    logger.info(f"Johan indicated message ID {message.id} is not a Daily Johan.")
                    return

                # Extract numbers from reply
                numbers_in_reply = re.findall(r"\d+", reply.content)
                if numbers_in_reply:
                    if len(numbers_in_reply) >= 2 and len(media_urls) >= 2:
                        day_numbers = [int(num) for num in numbers_in_reply[:len(media_urls)]]
                        archived_days = []
                        for day, media_url in zip(day_numbers, media_urls):
                            if get_existing_message_for_day(day):
                                await message.channel.send(get_dialogue("day_already_archived", day=day))
                                logger.info(f"Day {day} already archived. Skipping.")
                                continue
                            try:
                                archive_daily_johan_db(day, message, [media_url], confirmed=True)
                                archived_days.append(day)
                                logger.info(f"Archived day {day} from message ID {message.id}.")
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
                        day_number = int(numbers_in_reply[0])
                        bypass_time_check = True
                else:
                    await message.channel.send(get_dialogue("couldnt_parse_reply"))
                    logger.warning(f"Could not parse reply content for message ID {message.id}.")
                    return

            except asyncio.TimeoutError:
                await message.channel.send("No response received from Johan.")
                logger.warning(f"Timeout waiting for reply from Johan for message ID {message.id}.")
                return
        else:
            try:
                day_number = int(match.group(1) or match.group(2))
                logger.debug(f"Detected day number {day_number} from message ID {message.id}.")
            except ValueError:
                await message.channel.send(get_dialogue("parse_error", msg_id=message.id))
                logger.error(f"Parse error for day number in message ID {message.id}.")
                return

        # If multiple numbers found (but not multi-day scenario), ask manual submission
        if len(numbers_found) > 1:
            await message.channel.send(get_dialogue("multiple_numbers"))
            logger.info(f"Multiple numbers found in message ID {message.id}; requested manual submission.")
            return

        # Time check (unless bypassed)
        if not bypass_time_check:
            time_diff = now - message.created_at
            is_first_day = (latest_day == 0 and day_number == 1)
            if time_diff < timedelta(hours=12) and not is_first_day:
                await message.channel.send(get_dialogue("recent_post"))
                logger.info(f"Message ID {message.id} posted too recently. 12-hour cooldown active.")
                return

        # If day is unexpected, ask for verification
        if day_number != expected_next:
            await message.channel.send(get_dialogue("verification_prompt", provided=day_number))
            logger.info(f"Day number {day_number} does not match expected day {expected_next}.")

            def check_verification(m):
                return (
                        m.author.id == self.JOHAN_USER_ID
                        and m.channel == message.channel
                        and m.content.lower() in ["yes", "no", "y", "n"]
                )

            try:
                verification_reply = await self.bot.wait_for("message", timeout=60.0, check=check_verification)
                verification_response = verification_reply.content.strip().lower()
                logger.debug(f"Received verification reply: {verification_response}")
                if verification_response in ["yes", "y"]:
                    await message.channel.send(get_dialogue("verification_accepted", provided=day_number))
                    logger.info(f"Johan accepted the day number {day_number}.")
                else:
                    await message.channel.send(get_dialogue("verification_denied"))
                    logger.info(f"Johan denied the day number {day_number}.")

                    # Additional logic to re-ask
                    await message.channel.send(
                        get_dialogue("ask_if_daily_johan", user=self.JOHAN_USER_ID, msg_id=message.id)
                    )
                    try:
                        reply = await self.bot.wait_for("message", timeout=60.0, check=check_n)
                        if re.search(r"\b(yes|yep|affirmative|sure|of course)\b", reply.content, re.IGNORECASE):
                            await message.channel.send(
                                get_dialogue("provide_day_number", user=self.JOHAN_USER_ID, msg_id=message.id)
                            )
                            try:
                                number_reply = await self.bot.wait_for("message", timeout=60.0, check=check_n)
                                match_number = re.search(r"(\d+)", number_reply.content)
                                if match_number:
                                    day_number = int(match_number.group(1))
                                    logger.debug(f"Received new day number {day_number} from Johan.")
                                else:
                                    await message.channel.send(get_dialogue("couldnt_parse_reply"))
                                    logger.warning(f"Could not parse new day from Johan for message {message.id}.")
                                    return
                            except asyncio.TimeoutError:
                                await message.channel.send("No response received from Johan.")
                                logger.warning(
                                    f"Timeout waiting for new day number from Johan for message ID {message.id}.")
                                return
                        else:
                            return
                    except asyncio.TimeoutError:
                        await message.channel.send("No response received from Johan.")
                        logger.warning(f"Timeout waiting for secondary reply from Johan for msg ID {message.id}.")
                        return
            except asyncio.TimeoutError:
                await message.channel.send("No response received from Johan.")
                logger.warning(f"Timeout waiting for verification reply from Johan for msg ID {message.id}.")
                return

        # Check for duplicates
        if get_existing_message_for_day(day_number):
            await message.channel.send(get_dialogue("day_already_archived", day=day_number))
            logger.info(f"Day {day_number} already archived. Skipping.")
            return

        # Single-day archiving
        try:
            archive_daily_johan_db(day_number, message, media_urls, confirmed=True)
            await message.channel.send(get_dialogue("auto_archived", day=day_number))
            self.last_archive_time = now
            logger.info(f"Successfully archived day {day_number} from message ID {message.id}.")
        except ValueError as ve:
            await message.channel.send(str(ve))
            logger.error(f"ValueError while archiving day {day_number}: {ve}")
        except Exception as e:
            await message.channel.send(get_dialogue("deletion_error", error=e))
            logger.error(f"Exception while archiving day {day_number}: {e}")

    @tasks.loop(minutes=60)
    async def daily_reminder(self):
        """
        Sends a daily reminder based on the last archive time.
        """
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(day), timestamp FROM daily_johans WHERE day IS NOT NULL")
            result = cursor.fetchone()
            latest_day = result[0] if result and result[0] else 0
            last_timestamp_str = result[1] if result and result[1] else None

        if not last_timestamp_str:
            logger.info("No Daily Johans archived yet. Skipping reminder.")
            return

        try:
            last_timestamp = datetime.fromisoformat(last_timestamp_str)
            if last_timestamp.tzinfo is None:
                last_timestamp = last_timestamp.replace(tzinfo=timezone.utc)
            else:
                last_timestamp = last_timestamp.astimezone(timezone.utc)
            logger.debug(f"Last archive timestamp: {last_timestamp}")
        except Exception as e:
            logger.error(f"Failed to parse last_timestamp: {e}")
            return

        try:
            bot_timezone = pytz.timezone(self.TIMEZONE)
        except pytz.UnknownTimeZoneError:
            logger.error(f"Unknown timezone specified: {self.TIMEZONE}. Falling back to UTC.")
            bot_timezone = pytz.utc

        last_time_local = last_timestamp.astimezone(bot_timezone)
        logger.debug(f"Last archive time in local timezone: {last_time_local}")

        # 4 PM local
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

        logger.info(f"Scheduling next reminder at {next_reminder_local} ({self.TIMEZONE}) in {wait_seconds} seconds.")

        await asyncio.sleep(wait_seconds)

        # After waiting, perform the reminder
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
            logger.error(f"Channel with ID {self.DEFAULT_CHANNEL_ID} not found.")
            return

        if missed_days > 0:
            reminder_message = get_dialogue("daily_reminder_with_missed",
                                            user=self.JOHAN_USER_ID,
                                            day=expected_day,
                                            missed=missed_days)
        else:
            reminder_message = get_dialogue("daily_reminder",
                                            user=self.JOHAN_USER_ID,
                                            day=expected_day)

        try:
            await channel.send(reminder_message)
            logger.info(f"Sent reminder for day {expected_day}. Missed days: {missed_days}")
        except Exception as e:
            logger.error(f"Failed to send reminder: {e}")

    @daily_reminder.before_loop
    async def before_daily_reminder(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(ArchiveDailyCog(bot))
