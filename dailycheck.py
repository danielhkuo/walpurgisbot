import sqlite3

from discord.ext import commands, tasks

from config import JOHAN_USER_ID, CHECK_CHANNEL_ID  # Import shared constants
from database import init_db


class DailyCheckCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        init_db()
        self.daily_check.start()

    def cog_unload(self):
        self.daily_check.cancel()

    @tasks.loop(hours=24)
    async def daily_check(self):
        # Connect to DB and find the maximum day archived
        with sqlite3.connect("daily_johans.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(day) FROM daily_johans")
            result = cursor.fetchone()
            latest_day = result[0] if result and result[0] else 0

        # Determine expected latest day (simple logic: next day after latest)
        expected_day = latest_day + 1

        channel = self.bot.get_channel(CHECK_CHANNEL_ID)
        if not channel:
            print(f"Channel with ID {CHECK_CHANNEL_ID} not found.")
            return

        # Send public ping if new entry is missing
        if not latest_day or latest_day < expected_day:
            try:
                # Mention Johan by using <@user_id> syntax
                await channel.send(
                    f"<@{JOHAN_USER_ID}> Reminder: You haven't added Daily Johan for day {expected_day} yet!")
            except Exception as e:
                print(f"Failed to send public reminder: {e}")

        # If a gap is detected, post a public alert
        if latest_day < expected_day - 1:
            try:
                await channel.send(
                    f"Alert: There seems to be a gap in Daily Johans. Last recorded day was {latest_day}.")
            except Exception as e:
                print(f"Failed to send public gap alert: {e}")

    @daily_check.before_loop
    async def before_daily_check(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(DailyCheckCog(bot))
