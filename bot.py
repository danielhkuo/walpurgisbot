import discord
from discord.ext import commands
import asyncio
from dotenv import load_dotenv
import os
import re
from database import archive_daily_johan_db, get_existing_day_for_message, get_existing_message_for_day, delete_daily_johan_by_message_id

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


@bot.tree.context_menu(name="Archive Daily Johan")
async def archive_daily_johan_context_menu(interaction: discord.Interaction, message: discord.Message):
    await interaction.response.send_message("Please enter the day number(s) for this Daily Johan (separated by spaces or commas).", ephemeral=True)

    def check(m):
        return m.author == interaction.user and m.channel == interaction.channel

    try:
        response = await bot.wait_for("message", timeout=30.0, check=check)
        user_input = response.content.strip()

        # Parse input numbers separated by spaces or commas
        numbers_list = [int(x) for x in re.split(r'[\s,]+', user_input) if x.isdigit()]

        media_attachments = message.attachments
        media_url = media_attachments[0].url if media_attachments else None
        if not media_url:
            await interaction.followup.send("No media found in the selected message.", ephemeral=True)
            await response.delete()
            return

        # Check if count of numbers matches number of attachments
        if len(numbers_list) != len(media_attachments):
            await interaction.followup.send(
                f"The number of day numbers provided ({len(numbers_list)}) does not match "
                f"the number of attachments ({len(media_attachments)}). "
                "Please verify and try again.",
                ephemeral=True
            )
            await response.delete()
            return

        # If multiple numbers found and count matches attachments, proceed with archiving each.
        for day_number in numbers_list:
            archive_daily_johan_db(day_number, message, media_url, confirmed=True)

        await interaction.followup.send(
            f"Archived Daily Johan for day(s): {', '.join(map(str, numbers_list))}.",
            ephemeral=True
        )
        await response.delete()

    except ValueError:
        await interaction.followup.send("Invalid input. Please enter valid day numbers.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)

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

    except Exception as e:
        await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)


async def load_cogs():
    await bot.load_extension("archiving")
    await bot.load_extension("deletion")
    await bot.load_extension("status")
    await bot.load_extension("fun")
    await bot.load_extension("dailycheck")
    await bot.load_extension("search")

async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())