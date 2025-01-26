# cogs/deletion_cog.py

import re
import sqlite3
import logging
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from dialogues import get_dialogue
from config import DB_FILE

logger = logging.getLogger(__name__)

class DeletionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="delete_daily_johan", description="Delete a Daily Johan by day number or message link.")
    async def delete_daily_johan(self, interaction: discord.Interaction,
                                 day: Optional[int] = None,
                                 message_link: Optional[str] = None):
        await interaction.response.defer(ephemeral=True)
        logger.info(f"Received delete_daily_johan command from {interaction.user}")

        if not day and not message_link:
            await interaction.followup.send(get_dialogue("provide_day_or_link"), ephemeral=True)
            return

        message_id = None
        target_day = None

        if message_link:
            match = re.search(r"/channels/\d+/(\d+)/(\d+)", message_link)
            if match:
                message_id = match.group(2)
            else:
                await interaction.followup.send(get_dialogue("invalid_message_link"), ephemeral=True)
                return

        if day:
            target_day = day

        entry = None
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            if target_day:
                cursor.execute("SELECT day, message_id FROM daily_johans WHERE day = ?", (target_day,))
                entry = cursor.fetchone()
            elif message_id:
                cursor.execute("SELECT day, message_id FROM daily_johans WHERE message_id = ?", (str(message_id),))
                entry = cursor.fetchone()

        if not entry:
            await interaction.followup.send(get_dialogue("no_entry_found"), ephemeral=True)
            return

        archived_day, archived_message_id = entry

        await interaction.followup.send(
            get_dialogue("confirm_deletion", day=archived_day),
            ephemeral=True
        )

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        try:
            confirmation = await self.bot.wait_for("message", timeout=30.0, check=check)
            if confirmation.content.strip().lower() not in ("yes", "y"):
                await interaction.followup.send(get_dialogue("deletion_cancelled"), ephemeral=True)
                await confirmation.delete()
                return

            with sqlite3.connect(DB_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM daily_johans WHERE day = ?", (archived_day,))
                conn.commit()

            await interaction.followup.send(get_dialogue("deletion_success", day=archived_day), ephemeral=True)
            await confirmation.delete()

        except Exception as e:
            logger.error(f"Error deleting Daily Johan: {e}")
            await interaction.followup.send(get_dialogue("deletion_error", error=str(e)), ephemeral=True)

async def setup(bot):
    await bot.add_cog(DeletionCog(bot))
