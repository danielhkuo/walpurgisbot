# cogs/db_manage_cog.py

import asyncio
import json
import sqlite3
from io import BytesIO  # Import BytesIO from the io module

import discord
from discord import app_commands
from discord.ext import commands

from database import (
    init_db,
    insert_bulk_daily_johans
)


class DBManageCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.awaiting_import = {}  # Maps user IDs to asyncio.Event
        init_db()

    async def cog_load(self):
        self.bot.add_listener(self.on_dm_message, "on_message")

    @app_commands.command(name="export_db", description="Export the Daily Johans database as a JSON file.")
    @commands.has_permissions(administrator=True)
    async def export_db(self, interaction: discord.Interaction):
        """Exports the daily_johans table to a JSON file and sends it to the user via DM."""
        await interaction.response.defer(ephemeral=True)
        user = interaction.user

        # Fetch data from the database
        try:
            with sqlite3.connect("../daily_johans.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM daily_johans")
                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                data = [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            await interaction.followup.send(f"Failed to export database: {e}", ephemeral=True)
            return

        # Serialize data to JSON
        try:
            json_data = json.dumps(data, indent=4)
        except Exception as e:
            await interaction.followup.send(f"Failed to serialize data to JSON: {e}", ephemeral=True)
            return

        # Create a Discord file using BytesIO
        file = discord.File(fp=BytesIO(json_data.encode()), filename="daily_johans_export.json")

        # Send the file via DM
        try:
            await user.send("Here is your exported Daily Johans database:", file=file)
            await interaction.followup.send("Database exported successfully! Check your DMs.", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send(
                "I couldn't send you a DM. Please make sure your DMs are open and try again.", ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(f"Failed to send the file: {e}", ephemeral=True)

    @app_commands.command(name="import_db", description="Import the Daily Johans database from a JSON file.")
    @commands.has_permissions(administrator=True)
    async def import_db(self, interaction: discord.Interaction):
        """Initiates the import process by prompting the user to upload a JSON file via DM."""
        await interaction.response.defer(ephemeral=True)
        user = interaction.user

        # Check if the user is already in the import process
        if user.id in self.awaiting_import:
            await interaction.followup.send("You are already in the process of importing a database.", ephemeral=True)
            return

        # Send DM to the user with instructions
        try:
            await user.send(
                "Please upload the `daily_johans_export.json` file you wish to import within the next 60 seconds."
            )
            await interaction.followup.send(
                "I've sent you a DM with instructions on how to import the database.", ephemeral=True
            )
        except discord.Forbidden:
            await interaction.followup.send(
                "I couldn't send you a DM. Please make sure your DMs are open and try again.", ephemeral=True
            )
            return
        except Exception as e:
            await interaction.followup.send(f"Failed to send DM: {e}", ephemeral=True)
            return

        # Set up an event to wait for the file
        event = asyncio.Event()
        self.awaiting_import[user.id] = {"event": event, "data": None}

        # Wait for the user to upload the file within 60 seconds
        try:
            await asyncio.wait_for(event.wait(), timeout=60.0)
        except asyncio.TimeoutError:
            del self.awaiting_import[user.id]
            try:
                await user.send("You took too long to upload the file. Please try the import command again.")
            except:
                pass
            return

        # Retrieve the uploaded data
        file_content = self.awaiting_import[user.id]["data"]
        del self.awaiting_import[user.id]

        if not file_content:
            await user.send("No valid file was uploaded. Import aborted.")
            return

        # Parse JSON data
        try:
            data = json.loads(file_content)
            if not isinstance(data, list):
                raise ValueError("JSON data must be a list of records.")
        except json.JSONDecodeError as e:
            await user.send(f"Failed to parse JSON: {e}")
            return
        except ValueError as e:
            await user.send(f"Invalid data format: {e}")
            return

        # Insert data into the database
        try:
            # Optional: Clear existing data before import
            # Uncomment the next line if you want to clear the table before importing
            # clear_daily_johans_table()

            # Insert bulk data
            insert_bulk_daily_johans(data)
            await user.send("Database imported successfully!")
        except Exception as e:
            await user.send(f"Failed to import data into the database: {e}")

    async def on_dm_message(self, message: discord.Message):
        """Listens for DMs with attachments to process import files."""
        if message.author.bot:
            return  # Ignore bot messages

        user_id = message.author.id
        if user_id not in self.awaiting_import:
            return  # Not awaiting import from this user

        if not message.attachments:
            await message.author.send("Please attach a `daily_johans_export.json` file to proceed with the import.")
            return

        # Process the first attachment
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
            await message.author.send(f"Failed to read the uploaded file: {e}")
            self.awaiting_import[user_id]["event"].set()

    @export_db.error
    async def export_db_error(self, interaction: discord.Interaction, error):
        """Handles errors for the export_db command."""
        if isinstance(error, commands.MissingPermissions):
            await interaction.response.send_message(
                "You don't have permission to use this command.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"An error occurred: {error}", ephemeral=True
            )

    @import_db.error
    async def import_db_error(self, interaction: discord.Interaction, error):
        """Handles errors for the import_db command."""
        if isinstance(error, commands.MissingPermissions):
            await interaction.response.send_message(
                "You don't have permission to use this command.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"An error occurred: {error}", ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(DBManageCog(bot))
