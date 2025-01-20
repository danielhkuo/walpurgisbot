import discord
from discord.ext import commands
import re
import sqlite3
from database import init_db, archive_daily_johan_db

class ArchivingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.JOHAN_USER_ID = 474030685577936916
        init_db()  # Initialize the database

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        await self.bot.process_commands(message)
        if message.author.id != self.JOHAN_USER_ID or not message.attachments:
            return

        match = re.search(
            r"(?:Day\s*#?|\#|daily\s+johan\s+)(\d+)|(^\d+$)",
            message.content,
            re.IGNORECASE
        )
        day_number = None
        if match:
            try:
                day_number = int(match.group(1) or match.group(2))
            except ValueError:
                pass

        if day_number is not None:
            media_url = message.attachments[0].url
            archive_daily_johan_db(day_number, message, media_url, confirmed=True)
            print(f"Automatically archived Day {day_number} for Johan from message {message.id}.")
        else:
            print(f"Media detected from Johan (message ID: {message.id}) but no day number found.")

async def setup(bot):
    await bot.add_cog(ArchivingCog(bot))
