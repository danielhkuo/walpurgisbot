import re
import sqlite3
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands


class DeletionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.DB_FILE = "daily_johans.db"

    @app_commands.command(name="delete_daily_johan", description="Delete a Daily Johan by day number or message link.")
    async def delete_daily_johan(self, interaction: discord.Interaction, day: Optional[int] = None,
                                 message_link: Optional[str] = None):
        await interaction.response.defer(ephemeral=True)
        if not day and not message_link:
            await interaction.followup.send("Please provide either a day number or a message link to me!", ephemeral=True)
            return

        message_id = None
        target_day = None

        if message_link:
            match = re.search(r"/channels/\d+/(\d+)/(\d+)", message_link)
            if match:
                message_id = match.group(2)
            else:
                await interaction.followup.send("Hmmm... that might be an invalid message link format.", ephemeral=True)
                return

        if day:
            target_day = day

        entry = None
        with sqlite3.connect(self.DB_FILE) as conn:
            cursor = conn.cursor()
            if target_day:
                cursor.execute("SELECT day, message_id FROM daily_johans WHERE day = ?", (target_day,))
                entry = cursor.fetchone()
            elif message_id:
                cursor.execute("SELECT day, message_id FROM daily_johans WHERE message_id = ?", (str(message_id),))
                entry = cursor.fetchone()

        if not entry:
            await interaction.followup.send("｡ﾟ･ (>﹏<) ･ﾟ｡ I couldn't find an archived Daily Johan for that input.", ephemeral=True)
            return

        archived_day, archived_message_id = entry

        await interaction.followup.send(
            f"Ummm... are you sure you want to delete the archived Daily Johan for day {archived_day}? (yes/no)",
            ephemeral=True
        )

        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        try:
            confirmation = await self.bot.wait_for("message", timeout=30.0, check=check)
            if confirmation.content.strip().lower() not in ("yes", "y"):
                await interaction.followup.send("OK! Deletion cancelled.", ephemeral=True)
                await confirmation.delete()
                return

            with sqlite3.connect(self.DB_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM daily_johans WHERE day = ?", (archived_day,))
                conn.commit()

            await interaction.followup.send(f"Goodbye! Archived Daily Johan for day {archived_day} has been deleted 。。。ミヽ(。＞＜)ノ",
                                            ephemeral=True)
            await confirmation.delete()

        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(DeletionCog(bot))
