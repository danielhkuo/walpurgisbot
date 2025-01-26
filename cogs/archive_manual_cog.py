# cogs/archive_manual_cog.py

import logging
import re
import sqlite3

import discord
from discord import app_commands
from discord.ext import commands

from config import DB_FILE
from database import archive_daily_johan_db, get_existing_message_for_day
from dialogues import get_dialogue

logger = logging.getLogger(__name__)


class ArchiveManualCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="manual_archive", description="Manually archive a message for one or more days.")
    async def manual_archive(self, interaction: discord.Interaction, message_id: str, days: str):
        """
        Manually archive a single message for one or multiple days.
        - message_id: The ID of the message containing images.
        - days: Space or comma-separated list of day numbers (e.g., "5,6,7" or "5 6 7").
        """
        logger.info(f"Received manual_archive command from {interaction.user} for message {message_id}, days={days}")
        await interaction.response.defer(ephemeral=True)
        try:
            day_list = [int(d.strip()) for d in re.split(r'[ ,]+', days) if d.strip().isdigit()]
            if not day_list:
                await interaction.followup.send(get_dialogue("no_valid_day_numbers"), ephemeral=True)
                return

            channel = interaction.channel
            try:
                message = await channel.fetch_message(int(message_id))
            except discord.NotFound:
                await interaction.followup.send(
                    get_dialogue("message_not_found", msg_id=message_id),
                    ephemeral=True
                )
                return
            except discord.HTTPException as e:
                logger.error(f"HTTPException while fetching message {message_id}: {e}")
                await interaction.followup.send("An error occurred while fetching the message.", ephemeral=True)
                return

            attachments = message.attachments
            if not attachments:
                await interaction.followup.send(get_dialogue("no_media_found"), ephemeral=True)
                return

            media_urls = [attachment.url for attachment in attachments]

            if len(day_list) == len(media_urls):
                # One media per day
                for day, media_url in zip(day_list, media_urls):
                    existing_message = get_existing_message_for_day(day)
                    if existing_message and str(existing_message[0]) != str(message.id):
                        await interaction.followup.send(
                            get_dialogue("day_taken_resolve_dupes", day=day),
                            ephemeral=True
                        )
                        return
                    try:
                        archive_daily_johan_db(day, message, [media_url], confirmed=True)
                    except ValueError as ve:
                        await interaction.followup.send(str(ve), ephemeral=True)
                        return

                await interaction.followup.send(
                    get_dialogue("successful_media_archive",
                                 message_id=message.id,
                                 day_list=", ".join(map(str, day_list))),
                    ephemeral=True
                )
            elif len(day_list) == 1 and len(media_urls) <= 3:
                # Multiple attachments for a single day
                day = day_list[0]
                with sqlite3.connect(DB_FILE) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT media_url1, media_url2, media_url3 FROM daily_johans WHERE day = ?",
                        (day,)
                    )
                    result = cursor.fetchone()
                    if result:
                        existing_media = list(result)
                        available_slots = [i for i, url in enumerate(existing_media) if url is None]
                        if len(available_slots) < len(media_urls):
                            await interaction.followup.send(
                                get_dialogue("not_enough_slots",
                                             media_count=len(media_urls),
                                             day=day,
                                             slots=len(available_slots)
                                             ),
                                ephemeral=True
                            )
                            return
                try:
                    archive_daily_johan_db(day, message, media_urls, confirmed=True)
                    await interaction.followup.send(
                        get_dialogue("auto_archived", day=day),
                        ephemeral=True
                    )
                except ValueError as ve:
                    await interaction.followup.send(str(ve), ephemeral=True)
            else:
                await interaction.followup.send(
                    get_dialogue("mismatch_days_attachments"),
                    ephemeral=True
                )

        except ValueError:
            await interaction.followup.send(get_dialogue("invalid_input"), ephemeral=True)
        except Exception as e:
            logger.error(f"Unexpected error in manual_archive: {e}")
            await interaction.followup.send(get_dialogue("deletion_error", error=e), ephemeral=True)


async def setup(bot):
    await bot.add_cog(ArchiveManualCog(bot))
