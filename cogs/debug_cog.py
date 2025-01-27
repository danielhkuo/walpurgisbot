# cogs/debug_cog.py

import logging
import sqlite3
from datetime import datetime, timezone, timedelta

import discord
from discord import app_commands
from discord.ext import commands

from config import DB_FILE

logger = logging.getLogger(__name__)


class DebugCog(commands.Cog):
    """
    Provides a slash command to display debug information about
    the bot's archiving logic, cooldowns, and next expected day.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="debug_info", description="Show debug info for the Walpurgis Bot archiving system.")
    async def debug_info(self, interaction: discord.Interaction):
        """
        Presents ephemeral debug information:
          - Next expected day number
          - Time since previous Daily Johan was archived
          - Time until next auto-archive is possible (cooldown)
          - Whether the 'recent_post' check is currently active
        """
        # Attempt to retrieve the ArchiveDailyCog instance
        archive_cog = self.bot.get_cog("ArchiveDailyCog")
        if not archive_cog:
            await interaction.response.send_message(
                "ArchiveDailyCog not found. Unable to retrieve debug info.",
                ephemeral=True
            )
            return

        # 1) Find the next day number from DB
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(day) FROM daily_johans")
            result = cursor.fetchone()
            latest_day = result[0] if result and result[0] else 0
            next_day_number = latest_day + 1

        # 2) Time since last archive
        last_archive_time = archive_cog.last_archive_time
        time_since_last_str = "N/A (no previous archive)"
        time_until_next_archive_str = "N/A (no previous archive)"
        recent_post_check_active = "No"

        if last_archive_time:
            now_utc = datetime.now(timezone.utc)
            diff = now_utc - last_archive_time
            time_since_last_str = str(diff)

            # If diff < 12 hours, we're in the cooldown window
            if diff < timedelta(hours=12):
                remaining = timedelta(hours=12) - diff
                time_until_next_archive_str = str(remaining)
                recent_post_check_active = "Yes (12-hour cooldown in effect)"
            else:
                time_until_next_archive_str = "Cooldown expired"

        # Format the debug message
        debug_message = (
            f"**Walpurgis Bot Debug Info**\n\n"
            f"**Next Day Number:** {next_day_number}\n"
            f"**Time Since Previous Archive:** {time_since_last_str}\n"
            f"**Time Until Next Archive:** {time_until_next_archive_str}\n"
            f"**recent_post Check Active?:** {recent_post_check_active}\n"
        )

        # Send ephemeral debug info
        await interaction.response.send_message(debug_message, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(DebugCog(bot))
