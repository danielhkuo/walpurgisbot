import asyncio
import re
import sqlite3
from datetime import datetime, timezone, timedelta

import discord
from discord import app_commands
from discord.ext import commands

from config import JOHAN_USER_ID  # Import shared Johan user ID
from database import init_db, archive_daily_johan_db, get_existing_message_for_day


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

        day_number = None
        if not match:
            # Ping Johan for a day number if none is found
            await message.channel.send(
                f"<@{self.JOHAN_USER_ID}> Is that a Daily Johan?? I didn't find a day number on that... please give me one! (⌒_⌒;)"
            )

            def check_n(m):
                return m.author.id == self.JOHAN_USER_ID and m.channel == message.channel

            try:
                # Wait for Johan's response
                reply = await self.bot.wait_for("message", timeout=60.0, check=check_n)
                # Attempt to parse a number from Johan's reply
                match_reply = re.search(r"(?:Day\s*#?|\#|daily\s+johan\s+)?(\d+)", reply.content, re.IGNORECASE)
                if match_reply:
                    day_number = int(match_reply.group(1))
                else:
                    await message.channel.send("I- I'm sowwy!!! I couldn't parse a day number from your reply (￣▽￣*)ゞ")
                    return
            except asyncio.TimeoutError:
                await message.channel.send("No response received from Johan.")
                return
        else:
            try:
                day_number = int(match.group(1) or match.group(2))
            except ValueError:
                await message.channel.send(f"Oh no oopsies! (⁄ ⁄•⁄ω⁄•⁄ ⁄) I failed to parse a valid day number from message {message.id}.")
                return

        # If multiple numbers found in the original message, request manual submission
        if len(numbers_found) > 1:
            await message.channel.send(
                "My snuggy wuggy bear, are u trying to catch up dailies? :Flirt: Please manually submit it."
            )
            return

        # Check if the message was posted less than 12 hours ago, unless it's day 1 with no prior entries
        now = datetime.now(timezone.utc)
        time_diff = now - message.created_at

        is_first_day = False
        with sqlite3.connect("daily_johans.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(day) FROM daily_johans")
            result = cursor.fetchone()
            latest_day = result[0] if result and result[0] else 0
            is_first_day = (latest_day == 0)

        if time_diff < timedelta(hours=12) and not (is_first_day and day_number == 1):
            await message.channel.send(
                "Pookie, you posted less than 12 hours ago. I don't know if this is a Daily Johan or not. Please manually submit if it is :heart_eyes:"
            )
            return

        # Check if the auto-detected day number is the immediate next expected
        with sqlite3.connect("daily_johans.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(day) FROM daily_johans")
            result = cursor.fetchone()
            latest_day = result[0] if result and result[0] else 0

        expected_next = latest_day + 1
        if day_number != expected_next:
            await message.channel.send(
                "I- I don't think this is the next daily johan number... (*/▽＼*) Please manually submit to verify pookie!"
            )
            return

        # Proceed with archiving as normal
        media_url = message.attachments[0].url
        try:
            archive_daily_johan_db(day_number, message, [media_url], confirmed=True)
            await message.channel.send(f"Automatically archived Day {day_number} for Johan from message {message.id}.")
        except ValueError as ve:
            await message.channel.send(str(ve))
        except Exception as e:
            await message.channel.send(f"An error occurred: {e}")

    @app_commands.command(name="archive_series", description="Archive a message for multiple days.")
    async def archive_series(self, interaction: discord.Interaction, message_id: str, days: str):
        """
        Archive a single message for multiple days.
        - message_id: The ID of the message containing images.
        - days: Space or comma-separated list of day numbers (e.g., "5,6,7" or "5 6 7").
        """
        await interaction.response.defer(ephemeral=True)
        try:
            # Parse days from input (allowing spaces or commas)
            day_list = [int(d.strip()) for d in re.split(r'[,\s]+', days) if d.strip().isdigit()]
            if not day_list:
                await interaction.followup.send("No valid day numbers provided.", ephemeral=True)
                return

            # Fetch the message from the channel where the command is invoked
            channel = interaction.channel
            message = await channel.fetch_message(int(message_id))

            if not message:
                await interaction.followup.send("Message not found.", ephemeral=True)
                return

            attachments = message.attachments
            if not attachments:
                await interaction.followup.send("No media found in the specified message.", ephemeral=True)
                return

            media_urls = [attachment.url for attachment in attachments]

            # Assignment logic
            if len(day_list) == len(media_urls):
                # Assign each media to a corresponding day
                for day, media_url in zip(day_list, media_urls):
                    # Check if the day already exists
                    existing_message = get_existing_message_for_day(day)
                    if existing_message and str(existing_message[0]) != str(message.id):
                        await interaction.followup.send(
                            f"Day {day} already has a different Daily Johan... please resolve duplicates manually sir.",
                            ephemeral=True
                        )
                        return
                    # Archive each day with its media_url
                    try:
                        archive_daily_johan_db(day, message, [media_url], confirmed=True)
                    except ValueError as ve:
                        await interaction.followup.send(str(ve), ephemeral=True)
                        return
                await interaction.followup.send(
                    f"Success! Archived message {message_id} for days: {', '.join(map(str, day_list))} with one media per day.",
                    ephemeral=True
                )
            elif len(day_list) == 1 and len(media_urls) <= 3:
                # Assign all media to the single day
                day = day_list[0]
                # Check if the day already exists
                existing_media = []
                with sqlite3.connect("daily_johans.db") as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT media_url1, media_url2, media_url3 FROM daily_johans WHERE day = ?", (day,))
                    result = cursor.fetchone()
                    if result:
                        existing_media = list(result)
                        available_slots = [i for i, url in enumerate(existing_media) if url is None]
                        if len(available_slots) < len(media_urls):
                            await interaction.followup.send(
                                f"Cannot add {len(media_urls)} media to day {day}. Only {len(available_slots)} slots available.",
                                ephemeral=True
                            )
                            return
                # Proceed with archiving
                try:
                    archive_daily_johan_db(day, message, media_urls, confirmed=True)
                    await interaction.followup.send(
                        f"Archived message {message_id} for day {day} with {len(media_urls)} media attachments.",
                        ephemeral=True
                    )
                except ValueError as ve:
                    await interaction.followup.send(str(ve), ephemeral=True)
            else:
                # Mismatch between number of days and attachments
                await interaction.followup.send(
                    "Mismatch between the number of days provided and the number of attachments. Please verify your input.",
                    ephemeral=True
                )

        except ValueError:
            await interaction.followup.send(
                "Invalid input. Please enter valid day numbers separated by spaces or commas.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(ArchivingCog(bot))
