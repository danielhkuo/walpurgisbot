# cogs/db_manage_cog.py

import asyncio
import json
import logging
import sqlite3
from io import BytesIO

import discord
from discord import app_commands
from discord.ext import commands

from config import DB_FILE
from database import init_db, insert_bulk_daily_johans

logger = logging.getLogger(__name__)


class DBManageCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.awaiting_import = {}
        init_db()

    async def cog_load(self):
        # Listen for DMs with attachments to handle import files
        self.bot.add_listener(self.on_dm_message, "on_message")

    @app_commands.command(name="export_db", description="Export the Daily Johans database as a JSON file.")
    @commands.has_permissions(administrator=True)
    async def export_db(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user = interaction.user

        try:
            with sqlite3.connect(DB_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM daily_johans")
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                data = [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"Failed to export database: {e}")
            await interaction.followup.send(f"Failed to export database: {e}", ephemeral=True)
            return

        try:
            json_data = json.dumps(data, indent=4)
        except Exception as e:
            logger.error(f"Failed to serialize data to JSON: {e}")
            await interaction.followup.send(f"Failed to serialize data: {e}", ephemeral=True)
            return

        file = discord.File(fp=BytesIO(json_data.encode()), filename="daily_johans_export.json")

        try:
            await user.send("Here is your exported Daily Johans database:", file=file)
            await interaction.followup.send("Database exported successfully! Check your DMs.", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send(
                "I couldn't send you a DM. Please make sure your DMs are open and try again.",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Failed to send the file: {e}")
            await interaction.followup.send(f"Failed to send the file: {e}", ephemeral=True)

    @app_commands.command(name="import_db", description="Import the Daily Johans database from a JSON file.")
    @commands.has_permissions(administrator=True)
    async def import_db(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user = interaction.user

        if user.id in self.awaiting_import:
            await interaction.followup.send("You are already in the process of importing a database.", ephemeral=True)
            return

        try:
            await user.send("Please upload the `daily_johans_export.json` file within the next 60 seconds.")
            await interaction.followup.send("Check your DMs for import instructions.", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send(
                "I couldn't send you a DM. Make sure your DMs are open.",
                ephemeral=True
            )
            return
        except Exception as e:
            logger.error(f"Failed to send DM for import instructions: {e}")
            await interaction.followup.send(f"Failed to send DM: {e}", ephemeral=True)
            return

        event = asyncio.Event()
        self.awaiting_import[user.id] = {"event": event, "data": None}

        try:
            await asyncio.wait_for(event.wait(), timeout=60.0)
        except asyncio.TimeoutError:
            del self.awaiting_import[user.id]
            try:
                await user.send("You took too long. Please run /import_db again.")
            except:
                pass
            return

        file_content = self.awaiting_import[user.id]["data"]
        del self.awaiting_import[user.id]

        if not file_content:
            await user.send("No valid file was uploaded. Import aborted.")
            return

        try:
            data = json.loads(file_content)
            if not isinstance(data, list):
                raise ValueError("JSON must be a list of records.")
        except json.JSONDecodeError as e:
            await user.send(f"Failed to parse JSON: {e}")
            return
        except ValueError as e:
            await user.send(f"Invalid data format: {e}")
            return

        try:
            insert_bulk_daily_johans(data)
            await user.send("Database imported successfully!")
        except Exception as e:
            logger.error(f"Failed to import data: {e}")
            await user.send(f"Failed to import data: {e}")

    async def on_dm_message(self, message: discord.Message):
        if message.author.bot:
            return

        user_id = message.author.id
        if user_id not in self.awaiting_import:
            return

        if not message.attachments:
            await message.author.send("Please attach the `.json` file.")
            return

        attachment = message.attachments[0]
        if not attachment.filename.endswith(".json"):
            await message.author.send("Invalid file type. Please upload a `.json` file.")
            return

        try:
            file_bytes = await attachment.read()
            file_content = file_bytes.decode()
            self.awaiting_import[user_id]["data"] = file_content
            self.awaiting_import[user_id]["event"].set()
        except Exception as e:
            logger.error(f"Failed to read uploaded file: {e}")
            self.awaiting_import[user_id]["event"].set()

    @export_db.error
    async def export_db_error(self, interaction: discord.Interaction, error):
        if isinstance(error, commands.MissingPermissions):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        else:
            await interaction.response.send_message(f"An error occurred: {error}", ephemeral=True)

    @import_db.error
    async def import_db_error(self, interaction: discord.Interaction, error):
        if isinstance(error, commands.MissingPermissions):
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
        else:
            await interaction.response.send_message(f"An error occurred: {error}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(DBManageCog(bot))
