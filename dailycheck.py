import sqlite3
from datetime import datetime, timezone, timedelta

from discord.ext import commands, tasks

from config import JOHAN_USER_ID, DEFAULT_CHANNEL_ID  # Import shared constants
from database import init_db
from dialogues import get_dialogue


class DailyCheckCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        init_db()
        self.daily_check.start()

    def cog_unload(self):
        self.daily_check.cancel()

    @tasks.loop(hours=24)
    async def daily_check(self):
        # Connect to DB and find the maximum day archived and its timestamp
        with sqlite3.connect("daily_johans.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(day) FROM daily_johans")
            result = cursor.fetchone()
            latest_day = result[0] if result and result[0] else 0

            last_timestamp = None
            if latest_day:
                cursor.execute("SELECT timestamp FROM daily_johans WHERE day = ? ORDER BY timestamp DESC LIMIT 1",
                               (latest_day,))
                timestamp_result = cursor.fetchone()
                last_timestamp = timestamp_result[0] if timestamp_result else None

        # Determine expected latest day
        expected_day = latest_day + 1

        channel = self.bot.get_channel(DEFAULT_CHANNEL_ID)
        if not channel:
            print(f"Channel with ID {DEFAULT_CHANNEL_ID} not found.")
            return

        # Check if less than 12 hours have passed since the last archive
        send_reminder = True
        if last_timestamp:
            try:
                # Assuming timestamp is stored in ISO format in UTC
                last_time = datetime.fromisoformat(last_timestamp)
                now = datetime.now(timezone.utc)
                if now - last_time < timedelta(hours=12):
                    send_reminder = False
            except Exception as e:
                print(f"Error parsing timestamp: {e}")

        # Send reminder if conditions met
        if send_reminder and (not latest_day or latest_day < expected_day):
            try:
                await channel.send(get_dialogue("daily_reminder", user=JOHAN_USER_ID, day=expected_day))
            except Exception as e:
                print(f"Failed to send public reminder: {e}")

        # If a gap is detected, post a public alert
        if latest_day < expected_day - 1:
            try:
                await channel.send(get_dialogue("gap_alert", latest_day=latest_day))
            except Exception as e:
                print(f"Failed to send public gap alert: {e}")

    @daily_check.before_loop
    async def before_daily_check(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(DailyCheckCog(bot))
