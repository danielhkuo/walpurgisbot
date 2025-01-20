import asyncio
import os
import re

import discord
from discord.ext import commands
from dotenv import load_dotenv

from database import archive_daily_johan_db, get_existing_message_for_day

load_dotenv()
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Bot is ready. Logged in as {bot.user}")
    try:
        # Global sync without guild-specific parameters
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands globally.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


# Context Menu: Archive Daily Johan
@bot.tree.context_menu(name="Archive Daily Johan")
async def archive_daily_johan_context_menu(interaction: discord.Interaction, message: discord.Message):
    # Attempt automatic scanning for day numbers in the message content
    numbers_found = re.findall(r"\d+", message.content)
    media_attachments = message.attachments
    media_urls = [attachment.url for attachment in media_attachments]

    if not media_urls:
        await interaction.response.send_message("No media found in the selected message.", ephemeral=True)
        return

    # If numbers are found and they match the number of attachments,
    # proceed with automatic assignment.
    if numbers_found:
        day_numbers = [int(num) for num in numbers_found]

        # If there's a one-to-one match between numbers and attachments:
        if len(day_numbers) == len(media_urls):
            # Archive each media to corresponding day
            for day, media_url in zip(day_numbers, media_urls):
                existing_message = get_existing_message_for_day(day)
                if existing_message and str(existing_message[0]) != str(message.id):
                    await interaction.response.send_message(
                        f"Day {day} already has a different Daily Johan. Please resolve duplicates manually.",
                        ephemeral=True
                    )
                    return
                try:
                    archive_daily_johan_db(day, message, [media_url], confirmed=True)
                except ValueError as ve:
                    await interaction.response.send_message(str(ve), ephemeral=True)
                    return
            await interaction.response.send_message(
                f"Automatically archived message {message.id} for days: {', '.join(map(str, day_numbers))} with one media per day.",
                ephemeral=True
            )
            return
        # If one day number found and multiple attachments exist (<= 3):
        elif len(day_numbers) == 1 and len(media_urls) <= 3:
            day = day_numbers[0]
            # Check for existing media as before...
            try:
                archive_daily_johan_db(day, message, media_urls, confirmed=True)
                await interaction.response.send_message(
                    f"Automatically archived message {message.id} for day {day} with {len(media_urls)} media attachments.",
                    ephemeral=True
                )
            except ValueError as ve:
                await interaction.response.send_message(str(ve), ephemeral=True)
            return
        # If multiple numbers found but don't match attachments count or other issues arise:
        else:
            await interaction.response.send_message(
                "Mismatch between the detected numbers and the number of attachments or multiple numbers detected. "
                "Please manually input the correct day number(s).",
                ephemeral=True
            )
            # Fall through to manual input prompt below.

    # Fallback: Prompt for manual input if automatic scanning didn't succeed or encountered issues.
    await interaction.response.send_message(
        "Automatic scanning was inconclusive. Please enter the day number(s) for this Daily Johan (separated by spaces or commas).",
        ephemeral=True
    )

    def check(m):
        return m.author == interaction.user and m.channel == interaction.channel

    try:
        response = await bot.wait_for("message", timeout=30.0, check=check)
        user_input = response.content.strip()

        # Parse input numbers separated by spaces or commas
        numbers_list = [int(x) for x in re.split(r'[\s,]+', user_input) if x.isdigit()]

        if not numbers_list:
            await interaction.followup.send("No valid day numbers provided.", ephemeral=True)
            await response.delete()
            return

        # Recalculate attachments and media URLs in case message context is needed
        media_attachments = message.attachments
        media_urls = [attachment.url for attachment in media_attachments]

        # Check if count of numbers matches number of attachments
        if len(numbers_list) != len(media_urls):
            await interaction.followup.send(
                f"The number of day numbers provided ({len(numbers_list)}) does not match "
                f"the number of attachments ({len(media_urls)}). Please verify your input.",
                ephemeral=True
            )
            await response.delete()
            return

        # Assignment logic for manual input
        if len(numbers_list) == len(media_urls):
            for day, media_url in zip(numbers_list, media_urls):
                existing_message = get_existing_message_for_day(day)
                if existing_message and str(existing_message[0]) != str(message.id):
                    await interaction.followup.send(
                        f"Day {day} already has a different Daily Johan. Please resolve duplicates manually.",
                        ephemeral=True
                    )
                    await response.delete()
                    return
                try:
                    archive_daily_johan_db(day, message, [media_url], confirmed=True)
                except ValueError as ve:
                    await interaction.followup.send(str(ve), ephemeral=True)
                    await response.delete()
                    return
            await interaction.followup.send(
                f"Archived message {message.id} for days: {', '.join(map(str, numbers_list))} with one media per day.",
                ephemeral=True
            )

        await response.delete()

    except asyncio.TimeoutError:
        await interaction.followup.send("You took too long to respond. Please try again.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)


# Context Menu: Delete Daily Johan
@bot.tree.context_menu(name="Delete Daily Johan")
async def delete_daily_johan_context_menu(interaction: discord.Interaction, message: discord.Message):
    import sqlite3
    from database import delete_daily_johan_by_message_id

    # Query all days for which this message is archived
    with sqlite3.connect("daily_johans.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT day FROM daily_johans WHERE message_id = ?", (str(message.id),))
        days = cursor.fetchall()

    if not days:
        await interaction.response.send_message("This message is not archived as any Daily Johan.", ephemeral=True)
        return

    # List all days associated with this message
    day_list = [str(day[0]) for day in days]
    days_str = ", ".join(day_list)

    await interaction.response.send_message(
        f"This will delete the archived Daily Johan(s) for day(s): {days_str}. Are you sure? (yes/no)",
        ephemeral=True
    )

    def check(m):
        return m.author == interaction.user and m.channel == interaction.channel

    try:
        confirmation = await bot.wait_for("message", timeout=30.0, check=check)
        if confirmation.content.strip().lower() not in ("yes", "y"):
            await interaction.followup.send("Deletion cancelled.", ephemeral=True)
            await confirmation.delete()
            return

        # Delete all records associated with this message
        delete_daily_johan_by_message_id(message.id)

        await interaction.followup.send(f"Archived Daily Johan entries for day(s): {days_str} have been deleted.",
                                        ephemeral=True)
        await confirmation.delete()

    except asyncio.TimeoutError:
        await interaction.followup.send("You took too long to respond. Please try again.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)


async def load_cogs():
    # Load all necessary cogs
    await bot.load_extension("archiving")
    await bot.load_extension("deletion")
    await bot.load_extension("status")
    await bot.load_extension("fun")
    await bot.load_extension("dailycheck")
    await bot.load_extension("search")  # Ensure SearchCog is loaded


async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
