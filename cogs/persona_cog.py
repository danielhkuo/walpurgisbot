# cogs/persona_cog.py

import logging

import discord
from discord import app_commands
from discord.ext import commands

import dialogues  # Access dialogues to set personas

logger = logging.getLogger(__name__)


class PersonaCog(commands.Cog):
    """
    Cog to manage the active 'persona' used by your dialogues module.
    """

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="set_persona", description="Set the dialogue persona.")
    async def set_persona_command(self, interaction: discord.Interaction, persona: str):
        """
        Sets the 'current_persona' variable in the dialogues module.
        Usage example:
          /set_persona vangogh
        """
        logger.info(f"{interaction.user} invoked /set_persona to {persona}")

        dialogues.set_persona(persona.lower())
        await interaction.response.send_message(
            f"Persona switched to: {dialogues.current_persona}",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(PersonaCog(bot))
