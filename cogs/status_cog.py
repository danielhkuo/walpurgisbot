# cogs/status_cog.py

import logging
import math
import sqlite3
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput

from config import DB_FILE

logger = logging.getLogger(__name__)


class JumpModal(Modal, title="Jump to Page"):
    page_input = TextInput(label="Enter page number", style=discord.TextStyle.short)

    def __init__(self, paginator: "StatusPaginator"):
        super().__init__()
        self.paginator = paginator

    async def on_submit(self, interaction: discord.Interaction):
        try:
            page = int(self.page_input.value.strip()) - 1
            if 0 <= page < self.paginator.max_pages:
                self.paginator.current_page = page
                await self.paginator.update_message(interaction)
            else:
                await interaction.response.send_message("Invalid page number.", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("Please enter a valid number.", ephemeral=True)


class StatusPaginator(View):
    def __init__(self, results, start, end, per_page):
        super().__init__(timeout=180)
        self.results = results
        self.start = start
        self.end = end
        self.per_page = per_page
        self.current_page = 0
        total_days = max(end - start + 1, 0)
        self.max_pages = math.ceil(total_days / per_page)

    def get_page_content(self):
        page_start = self.start + self.current_page * self.per_page
        page_end = min(page_start + self.per_page, self.end + 1)
        lines = []
        for day in range(page_start, page_end):
            status = "✅" if day in self.results else "❌"
            lines.append(f"Day {day}: {status}")
        return "\n".join(lines)

    async def update_message(self, interaction: discord.Interaction):
        content = f"Daily Johan Status (Page {self.current_page + 1}/{self.max_pages}):\n{self.get_page_content()}"
        for item in self.children:
            if isinstance(item, Button):
                if item.custom_id == "first":
                    item.disabled = self.current_page <= 0
                elif item.custom_id == "prev":
                    item.disabled = self.current_page <= 0
                elif item.custom_id == "next":
                    item.disabled = self.current_page >= self.max_pages - 1
                elif item.custom_id == "last":
                    item.disabled = self.current_page >= self.max_pages - 1

        await interaction.response.edit_message(content=content, view=self)

    @discord.ui.button(label="⏮", style=discord.ButtonStyle.primary, custom_id="first")
    async def first_button(self, interaction: discord.Interaction, button: Button):
        self.current_page = 0
        await self.update_message(interaction)

    @discord.ui.button(label="◀", style=discord.ButtonStyle.primary, custom_id="prev")
    async def prev_button(self, interaction: discord.Interaction, button: Button):
        if self.current_page > 0:
            self.current_page -= 1
        await self.update_message(interaction)

    @discord.ui.button(label="▶", style=discord.ButtonStyle.primary, custom_id="next")
    async def next_button(self, interaction: discord.Interaction, button: Button):
        if self.current_page < self.max_pages - 1:
            self.current_page += 1
        await self.update_message(interaction)

    @discord.ui.button(label="⏭", style=discord.ButtonStyle.primary, custom_id="last")
    async def last_button(self, interaction: discord.Interaction, button: Button):
        self.current_page = self.max_pages - 1
        await self.update_message(interaction)

    @discord.ui.button(label="🔢", style=discord.ButtonStyle.secondary, custom_id="jump")
    async def jump_button(self, interaction: discord.Interaction, button: Button):
        modal = JumpModal(self)
        await interaction.response.send_modal(modal)


class StatusCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="daily_johan_status", description="Check the status of Daily Johans in a range of days.")
    async def daily_johan_status(self, interaction: discord.Interaction,
                                 start: int = 1, end: Optional[int] = None):
        logger.info(f"daily_johan_status invoked by {interaction.user}, range={start}-{end}")
        if end is None:
            with sqlite3.connect(DB_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT MAX(day) FROM daily_johans")
                max_day = cursor.fetchone()[0]
                end = max_day if max_day else start

        if end < start:
            await interaction.response.send_message(
                "End day must be greater than or equal to start day.",
                ephemeral=True
            )
            return

        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT day FROM daily_johans WHERE day BETWEEN ? AND ?", (start, end))
            results = {row[0] for row in cursor.fetchall()}

        paginator = StatusPaginator(results=results, start=start, end=end, per_page=20)
        content = f"Daily Johan Status (Page 1/{paginator.max_pages}):\n{paginator.get_page_content()}"
        await interaction.response.send_message(content=content, view=paginator, ephemeral=True)


async def setup(bot):
    await bot.add_cog(StatusCog(bot))
