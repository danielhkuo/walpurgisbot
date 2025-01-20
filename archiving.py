import discord
from discord.ext import commands
from discord import app_commands
import re
import sqlite3
from datetime import datetime, timezone, timedelta
from database import init_db, archive_daily_johan_db
from config import JOHAN_USER_ID  # Import shared Johan user ID

class ArchivingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.JOHAN_USER_ID = JOHAN_USER_ID  # Use the imported value
        init_db()  # Initialize the database

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        await self.bot.process_commands(message)
        if message.author.id != self.JOHAN_USER_ID or not message.attachments:
            return

        # Search for a day number using regex
        match = re.search(
            r"(?:Day\s*#?|\#|daily\s+johan\s+)(\d+)|(^\d+$)",
            message.content,
            re.IGNORECASE
        )
        # Find all number occurrences in the message
        numbers_found = re.findall(r"\d+", message.content)

        if not match:
            await message.channel.send(f"Media detected from Johan (message ID: {message.id}) but no day number found.")
            return

        try:
            day_number = int(match.group(1) or match.group(2))
        except ValueError:
            await message.channel.send(f"Failed to parse a valid day number from message {message.id}.")
            return

        # If multiple numbers found, request manual submission
        if len(numbers_found) > 1:
            await message.channel.send("My snuggy wuggy bear, are u trying to catch up dailies? :Flirt: Please manually submit it.")
            return

        # Check if the message was posted less than 12 hours ago
        now = datetime.now(timezone.utc)
        time_diff = now - message.created_at
        if time_diff < timedelta(hours=12):
            await message.channel.send("Pookie, you posted less than 12 hours ago. I don't know if this is a Daily Johan or not. Please manually submit if it is :heart_eyes:")
            return

        # Check if the auto-detected day number is the immediate next expected
        with sqlite3.connect("daily_johans.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(day) FROM daily_johans")
            result = cursor.fetchone()
            latest_day = result[0] if result and result[0] else 0

        expected_next = latest_day + 1
        if day_number != expected_next:
            await message.channel.send("This isn't the next daily johan number... I don't think. Please manually submit to verify pookie!")
            return

        # Proceed with archiving as normal
        media_url = message.attachments[0].url
        archive_daily_johan_db(day_number, message, media_url, confirmed=True)
        await message.channel.send(f"Automatically archived Day {day_number} for Johan from message {message.id}.")

    @app_commands.command(name="archive_series", description="Archive a message for multiple days.")
    async def archive_series(self, interaction: discord.Interaction, message_id: str, days: str):
        """
        Archive a single message for multiple days.
        - message_id: The ID of the message containing images.
        - days: Comma-separated list of day numbers (e.g., "5,6,7").
        """
        await interaction.response.defer(ephemeral=True)
        try:
            # Parse days from input
            day_list = [int(d.strip()) for d in days.split(",") if d.strip().isdigit()]
            if not day_list:
                await interaction.followup.send("No valid day numbers provided.", ephemeral=True)
                return

            # Fetch the message from the channel where the command is invoked
            channel = interaction.channel
            message = await channel.fetch_message(int(message_id))

            if not message:
                await interaction.followup.send("Message not found.", ephemeral=True)
                return

            media_url = message.attachments[0].url if message.attachments else None
            if not media_url:
                await interaction.followup.send("No media found in the specified message.", ephemeral=True)
                return

            # Archive the message for each provided day
            for day in day_list:
                archive_daily_johan_db(day, message, media_url, confirmed=True)

            await interaction.followup.send(f"Archived message {message_id} for days: {', '.join(map(str, day_list))}", ephemeral=True)

        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ArchivingCog(bot))
