# backup.py

import asyncio
import re

import discord
from discord import app_commands
from discord.ext import commands

from config import JOHAN_USER_ID
from database import archive_daily_johan_db, get_existing_message_for_day

PASSWORD = "jecslide"  # Password for running the backup command


class BackupCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.stop_requested = False  # Flag for panic button

    @app_commands.command(name="scrape_backup",
                          description="Run a one-time automatic scraping backup (requires password).")
    @app_commands.describe(
        password="The required password to run this command.",
        channels="Comma separated list of channel IDs to scan."
    )
    async def scrape_backup(self, interaction: discord.Interaction, password: str, channels: str):
        # Check password
        if password != PASSWORD:
            await interaction.response.send_message("Incorrect password.", ephemeral=True)
            return

        # Parse channel IDs from input
        try:
            channel_ids = [int(cid.strip()) for cid in channels.split(",") if cid.strip().isdigit()]
        except Exception:
            await interaction.response.send_message("Invalid channel list provided.", ephemeral=True)
            return

        # Fetch channel objects from IDs
        scan_channels = []
        for cid in channel_ids:
            channel = self.bot.get_channel(cid)
            if channel and isinstance(channel, discord.TextChannel):
                scan_channels.append(channel)
            else:
                await interaction.followup.send(f"Channel ID {cid} is invalid or not accessible.", ephemeral=True)

        if not scan_channels:
            await interaction.response.send_message("No valid channels to scan.", ephemeral=True)
            return

        # Warning message with caution
        await interaction.response.send_message(
            "⚠️ Caution: This operation can break the database. Proceeding with backup...",
            ephemeral=True
        )

        # Reset stop flag at the start of a new backup
        self.stop_requested = False

        # Begin processing backup
        await self.process_backup(interaction, scan_channels)

    @app_commands.command(name="panic_stop", description="Stop the ongoing backup process immediately.")
    async def panic_stop(self, interaction: discord.Interaction):
        self.stop_requested = True
        await interaction.response.send_message("Panic stop initiated. The backup process will halt soon.",
                                                ephemeral=True)

    async def process_backup(self, interaction: discord.Interaction, channels):
        await interaction.followup.send("Starting backup process...", ephemeral=True)

        for channel in channels:
            if self.stop_requested:
                await interaction.followup.send("Backup process was stopped by panic button.", ephemeral=True)
                return

            try:
                async for message in channel.history(limit=None, oldest_first=True):
                    if self.stop_requested:
                        await interaction.followup.send("Backup process was stopped by panic button.", ephemeral=True)
                        return

                    if message.author.id != JOHAN_USER_ID or not message.attachments:
                        continue

                    media_urls = [att.url for att in message.attachments][:3]  # limit to 3 media
                    if not media_urls:
                        continue

                    numbers_found = re.findall(r"\d+", message.content)
                    explicit_pattern = re.search(
                        r"(?:Day\s*#?\s*|\#|\b(?:daily\s+johan|johan)\s+)(\d+)",
                        message.content,
                        re.IGNORECASE
                    )

                    day_numbers = []
                    if explicit_pattern:
                        day_numbers = [int(explicit_pattern.group(1))]
                    else:
                        day_numbers = [int(num) for num in numbers_found] if numbers_found else []

                    if len(media_urls) >= 2 and len(day_numbers) >= 2:
                        for day, media_url in zip(day_numbers[:len(media_urls)], media_urls):
                            if get_existing_message_for_day(day):
                                continue
                            try:
                                archive_daily_johan_db(day, message, [media_url], confirmed=True)
                            except Exception:
                                pass
                        continue

                    if day_numbers and len(day_numbers) == 1:
                        day = day_numbers[0]
                        if not get_existing_message_for_day(day):
                            try:
                                archive_daily_johan_db(day, message, media_urls, confirmed=True)
                            except Exception:
                                pass
                        continue

                    prompt = f"Review message {message.jump_url} in {channel.mention}. " \
                             f"Reply with a day number to archive, or 'no' to skip. " \
                             f"If series, reply with multiple days separated by commas/spaces."
                    await interaction.followup.send(prompt, ephemeral=True)

                    def check(m):
                        return m.author == interaction.user and m.channel == interaction.channel

                    try:
                        response = await self.bot.wait_for("message", timeout=60.0, check=check)
                        content = response.content.strip().lower()
                        if content in ["no", "n"]:
                            continue

                        user_numbers = re.findall(r"\d+", content)
                        if not user_numbers:
                            await interaction.followup.send("No valid day numbers provided. Skipping message.",
                                                            ephemeral=True)
                            # No continue here needed; naturally proceeds to next message
                        else:
                            if len(user_numbers) >= 2 and len(media_urls) >= 2:
                                days = [int(num) for num in user_numbers][:len(media_urls)]
                                for day, media_url in zip(days, media_urls):
                                    if get_existing_message_for_day(day):
                                        continue
                                    try:
                                        archive_daily_johan_db(day, message, [media_url], confirmed=True)
                                    except Exception:
                                        pass
                                # Continue to next message after series archiving
                            else:
                                day = int(user_numbers[0])
                                if not get_existing_message_for_day(day):
                                    try:
                                        archive_daily_johan_db(day, message, media_urls, confirmed=True)
                                    except Exception:
                                        pass
                    except asyncio.TimeoutError:
                        await interaction.followup.send("Timed out waiting for response. Skipping message.",
                                                        ephemeral=True)
                        # Skip to next message after timeout
                        continue

            except discord.Forbidden:
                await interaction.followup.send(f"Missing permissions to read history in channel {channel.mention}.",
                                                ephemeral=True)
            except Exception as e:
                await interaction.followup.send(f"An error occurred in channel {channel.mention}: {e}", ephemeral=True)

        await interaction.followup.send("Backup process completed.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(BackupCog(bot))
