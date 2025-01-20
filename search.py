import sqlite3

import discord
from discord import app_commands
from discord.ext import commands


class SearchCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.DB_FILE = "daily_johans.db"

    @app_commands.command(name="search_daily_johan", description="Search for a Daily Johan by day number.")
    async def search_daily_johan(self, interaction: discord.Interaction, day: int):
        """Searches for a Daily Johan by day number and returns its details."""
        with sqlite3.connect(self.DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT message_id, channel_id, media_url1, media_url2, media_url3 
                FROM daily_johans 
                WHERE day = ?
            """, (day,))
            results = cursor.fetchall()

        if results:
            messages_info = []
            for row in results:
                message_id, channel_id, media_url1, media_url2, media_url3 = row
                guild_id = interaction.guild.id if interaction.guild else "@me"
                jump_url = f"https://discord.com/channels/{guild_id}/{channel_id}/{message_id}"

                # Collect non-None media URLs
                media_urls = [url for url in [media_url1, media_url2, media_url3] if url]

                media_links = "\n".join([f"Media {i + 1}: {url}" for i, url in enumerate(media_urls)])

                messages_info.append(f"**Day {day}:**\n{media_links}\n[Jump to Message]({jump_url})")

            response = "\n\n".join(messages_info)
            await interaction.response.send_message(response)
        else:
            await interaction.response.send_message(f"No Daily Johan found for day {day}.")


async def setup(bot):
    await bot.add_cog(SearchCog(bot))
