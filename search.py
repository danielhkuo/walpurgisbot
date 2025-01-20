import discord
from discord.ext import commands
from discord import app_commands
import sqlite3

class SearchCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.DB_FILE = "daily_johans.db"

    @app_commands.command(name="search_daily_johan", description="Search for a Daily Johan by day number.")
    async def search_daily_johan(self, interaction: discord.Interaction, day: int):
        """Searches for a Daily Johan by day number and returns its details."""
        with sqlite3.connect(self.DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT day, message_id, channel_id, media_url FROM daily_johans WHERE day = ?", (day,))
            result = cursor.fetchone()

        if result:
            day_value, message_id, channel_id, media_url = result

            # Construct jump-to-message URL using the guild ID from the interaction
            guild_id = interaction.guild.id if interaction.guild else "@me"
            jump_url = f"https://discord.com/channels/{guild_id}/{channel_id}/{message_id}"

            response = (
                f"**Day {day_value}:**\n"
                f"Media: {media_url}\n"
                f"[Jump to Message]({jump_url})"
            )
            await interaction.response.send_message(response)  # Public response
        else:
            await interaction.response.send_message(f"No Daily Johan found for day {day}.")  # Public response

async def setup(bot):
    await bot.add_cog(SearchCog(bot))