import discord
from discord.ext import commands
import asyncio
from dotenv import load_dotenv
import os
from database import archive_daily_johan_db, get_existing_day_for_message, get_existing_message_for_day

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
    await interaction.response.send_message("Please enter the day number for this Daily Johan.", ephemeral=True)

    def check(m):
        return m.author == interaction.user and m.channel == interaction.channel

    try:
        response = await bot.wait_for("message", timeout=30.0, check=check)
        day_number = int(response.content)
        media_url = message.attachments[0].url if message.attachments else None
        if not media_url:
            await interaction.followup.send("No media found in the selected message.", ephemeral=True)
            await response.delete()
            return

        # Check if this message is already archived for any day
        existing_day_for_message = get_existing_day_for_message(message.id)
        if existing_day_for_message:
            existing_day = existing_day_for_message[0]
            if existing_day != day_number:
                await interaction.followup.send(
                    f"This message is already archived as Daily Johan for day {existing_day}.",
                    ephemeral=True
                )
                await response.delete()
                return

        # Check if another entry for this day exists (different message)
        existing_message_for_day = get_existing_message_for_day(day_number)
        if existing_message_for_day and str(existing_message_for_day[0]) != str(message.id):
            await interaction.followup.send(
                f"A different Daily Johan for day {day_number} already exists. Do you want to override it? (yes/no)",
                ephemeral=True
            )
            confirm_msg = await bot.wait_for("message", timeout=30.0, check=check)
            confirm = confirm_msg.content.strip().lower()
            if confirm not in ("yes", "y"):
                await interaction.followup.send("Archiving cancelled.", ephemeral=True)
                await response.delete()
                await confirm_msg.delete()
                return
            await interaction.followup.send(f"Overriding the existing Daily Johan for day {day_number}.", ephemeral=True)
            await confirm_msg.delete()

        archive_daily_johan_db(day_number, message, media_url, confirmed=True)
        await interaction.followup.send(f"Archived Daily Johan as Day {day_number}.", ephemeral=True)
        await response.delete()

    except ValueError:
        await interaction.followup.send("Invalid input. Please enter a valid day number.", ephemeral=True)
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
    # Load all necessary cogs
    await bot.load_extension("archiving")
    await bot.load_extension("deletion")
    await bot.load_extension("status")
    await bot.load_extension("fun")
    await bot.load_extension("dailycheck")  # Added dailycheck to load all cogs

async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())