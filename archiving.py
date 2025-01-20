import re
import sqlite3
from datetime import datetime, timezone, timedelta

import discord
from discord import app_commands
from discord.ext import commands

from config import JOHAN_USER_ID
from database import init_db, archive_daily_johan_db, get_existing_message_for_day
from dialogues import get_dialogue


class ArchivingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.JOHAN_USER_ID = JOHAN_USER_ID
        init_db()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        await self.bot.process_commands(message)
        if message.author.id != self.JOHAN_USER_ID or not message.attachments:
            return

        match = re.search(r"(?:Day\s*#?|\#|daily\s+johan\s+)(\d+)|(^\d+$)", message.content, re.IGNORECASE)
        numbers_found = re.findall(r"\d+", message.content)

        day_number = None
        if not match:
            await message.channel.send(
                get_dialogue("ask_for_number", user=self.JOHAN_USER_ID, msg_id=message.id)
            )

            def check_n(m):
                return m.author.id == self.JOHAN_USER_ID and m.channel == message.channel

            try:
                reply = await self.bot.wait_for("message", timeout=60.0, check=check_n)
                match_reply = re.search(r"(?:Day\s*#?|\#|daily\s+johan\s+)?(\d+)", reply.content, re.IGNORECASE)
                if match_reply:
                    day_number = int(match_reply.group(1))
                else:
                    await message.channel.send(get_dialogue("couldnt_parse_reply"))
                    return
            except asyncio.TimeoutError:
                await message.channel.send("No response received from Johan.")
                return
        else:
            try:
                day_number = int(match.group(1) or match.group(2))
            except ValueError:
                await message.channel.send(get_dialogue("parse_error", msg_id=message.id))
                return

        if len(numbers_found) > 1:
            await message.channel.send(get_dialogue("multiple_numbers"))
            return

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
            await message.channel.send(get_dialogue("recent_post"))
            return

        with sqlite3.connect("daily_johans.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(day) FROM daily_johans")
            result = cursor.fetchone()
            latest_day = result[0] if result and result[0] else 0

        expected_next = latest_day + 1
        if day_number != expected_next:
            await message.channel.send(get_dialogue("not_next_number"))
            return

        media_url = message.attachments[0].url
        try:
            archive_daily_johan_db(day_number, message, [media_url], confirmed=True)
            await message.channel.send(get_dialogue("auto_archived", day=day_number))
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
            day_list = [int(d.strip()) for d in re.split(r'[ ,]+', days) if d.strip().isdigit()]
            if not day_list:
                await interaction.followup.send(get_dialogue("no_valid_day_numbers"), ephemeral=True)
                return

            # Fetch the message from the channel where the command is invoked
            channel = interaction.channel
            message = await channel.fetch_message(int(message_id))

            if not message:
                await interaction.followup.send(get_dialogue("message_not_found"), ephemeral=True)
                return

            attachments = message.attachments
            if not attachments:
                await interaction.followup.send(get_dialogue("no_media_found"), ephemeral=True)
                return

            media_urls = [attachment.url for attachment in attachments]

            # Assignment logic
            if len(day_list) == len(media_urls):
                # Assign each media to a corresponding day
                for day, media_url in zip(day_list, media_urls):
                    # Check if the day already exists
                    existing_message = get_existing_message_for_day(day)
                    if existing_message and str(existing_message[0]) != str(message.id):
                        await interaction.followup.send(get_dialogue("day_taken_resolve_dupes", day=day),
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
                    get_dialogue("successful_media_archive", message_id=message.id,
                                 day_list=", ".join(map(str, day_list))),
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
                                get_dialogue("not_enough_slots", media_count=len(media_urls), day=day,
                                             slots=len(available_slots)),
                                ephemeral=True
                            )
                            return
                # Proceed with archiving
                try:
                    archive_daily_johan_db(day, message, media_urls, confirmed=True)
                    await interaction.followup.send(
                        get_dialogue("auto_archived", day=day), ephemeral=True
                    )
                except ValueError as ve:
                    await interaction.followup.send(str(ve), ephemeral=True)
            else:
                # Mismatch between number of days and attachments
                await interaction.followup.send(
                    get_dialogue("mismatch_days_attachments"),
                    ephemeral=True
                )

        except ValueError:
            await interaction.followup.send(
                get_dialogue("invalid_input"), ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(ArchivingCog(bot))
