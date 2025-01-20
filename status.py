import discord
from discord.ext import commands
from discord import app_commands
import sqlite3
from discord.ui import View, Button

class StatusPaginator(View):
    def __init__(self, results, start, end, per_page=50):
        super().__init__(timeout=180)
        self.results = results
        self.start = start
        self.end = end
        self.per_page = per_page
        self.current_page = 0
        total_days = max(end - start + 1, 0)
        self.max_pages = (total_days // per_page) + (1 if total_days % per_page > 0 else 0)
        self.columns = 5

    def get_page_content(self):
        page_start = self.start + self.current_page * self.per_page
        page_end = min(page_start + self.per_page, self.end + 1)
        lines = []
        lines.append("```")
        for row_start in range(page_start, page_end, self.columns):
            row_cells = []
            for day in range(row_start, min(row_start + self.columns, page_end)):
                emoji = "✅" if day in self.results else "❌"
                row_cells.append(f"{day:4d}:{emoji}")
            lines.append("  ".join(row_cells))
        lines.append("```")
        return "\n".join(lines)

    async def update_message(self, interaction: discord.Interaction):
        content = f"Daily Johan Status (Page {self.current_page + 1}/{self.max_pages}):\n{self.get_page_content()}"
        for item in self.children:
            if isinstance(item, Button):
                if item.custom_id == "prev":
                    item.disabled = self.current_page <= 0
                elif item.custom_id == "next":
                    item.disabled = self.current_page >= self.max_pages - 1
        await interaction.response.edit_message(content=content, view=self)

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary, custom_id="prev")
    async def prev_button(self, interaction: discord.Interaction, button: Button):
        if self.current_page > 0:
            self.current_page -= 1
        await self.update_message(interaction)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary, custom_id="next")
    async def next_button(self, interaction: discord.Interaction, button: Button):
        if self.current_page < self.max_pages - 1:
            self.current_page += 1
        await self.update_message(interaction)

class StatusCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.DB_FILE = "daily_johans.db"

    @app_commands.command(name="daily_johan_status", description="Check the status of Daily Johans in a range of days.")
    async def daily_johan_status(self, interaction: discord.Interaction, start: int = 1, end: int = 30):
        if end < start:
            await interaction.response.send_message("End day must be greater than or equal to start day.", ephemeral=True)
            return

        with sqlite3.connect(self.DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT day FROM daily_johans WHERE day BETWEEN ? AND ?", (start, end))
            results = {row[0] for row in cursor.fetchall()}

        if not results:
            results = set()

        paginator = StatusPaginator(results=results, start=start, end=end, per_page=50)
        content = f"Daily Johan Status (Page 1/{paginator.max_pages}):\n{paginator.get_page_content()}"
        await interaction.response.send_message(content=content, view=paginator, ephemeral=True)

async def setup(bot):
    await bot.add_cog(StatusCog(bot))
