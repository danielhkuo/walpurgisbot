import discord
from discord import app_commands
from discord.ext import commands

import dialogues  # Import the dialogues module to access its variables and functions dynamically


class PersonaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="set_persona", description="Set the dialogue persona.")
    async def set_persona_command(self, interaction: discord.Interaction, persona: str):
        dialogues.set_persona(persona.lower())
        # Reference current_persona dynamically from the dialogues module
        await interaction.response.send_message(f"Persona switched to: {dialogues.current_persona}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(PersonaCog(bot))
