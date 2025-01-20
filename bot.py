import discord
from discord.ext import commands
import asyncio
from dotenv import load_dotenv
import os

from config import JOHAN_USER_ID  # Import shared constants if needed

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

# Context Menu: Archive Daily Johan
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
        media_urls = [attachment.url for attachment in media_attachments]

        if not media_urls:
            await interaction.followup.send("No media found in the selected message.", ephemeral=True)
            await response.delete()
            return

        # Assignment logic
        if len(numbers_list) == len(media_urls):
            # Assign each media to a corresponding day
            for day, media_url in zip(numbers_list, media_urls):
                # Check if the day already exists
                existing_message = get_existing_message_for_day(day)
                if existing_message and str(existing_message[0]) != str(message.id):
                    await interaction.followup.send(
                        f"Day {day} already has a different Daily Johan. Please resolve duplicates manually.",
                        ephemeral=True
                    )
                    await response.delete()
                    return
                # Archive each day with its media_url
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
        elif len(numbers_list) == 1 and len(media_urls) <= 3:
            # Assign all media to the single day
            day = numbers_list[0]
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
                        await response.delete()
                        return
            # Proceed with archiving
            try:
                archive_daily_johan_db(day, message, media_urls, confirmed=True)
                await interaction.followup.send(
                    f"Archived message {message.id} for day {day} with {len(media_urls)} media attachments.",
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

        await response.delete()

    except ValueError:
        await interaction.followup.send("Invalid input. Please enter valid day numbers separated by spaces or commas.", ephemeral=True)
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
