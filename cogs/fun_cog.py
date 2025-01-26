# cogs/fun_cog.py

import logging
import re
from datetime import datetime, timezone

import discord
from discord.ext import commands, tasks

from config import DEFAULT_CHANNEL_ID

logger = logging.getLogger(__name__)


class FunCog(commands.Cog):
    """
    A collection of fun or whimsical features:
    1) A daily task announcing Walpurgisnacht on April 30
    2) Responding to certain words/phrases in chat with memes
    """

    def __init__(self, bot):
        self.bot = bot
        self.default_channel_id = DEFAULT_CHANNEL_ID

        if self.default_channel_id == 0:
            logger.warning("DEFAULT_CHANNEL_ID is not set. Walpurgisnacht announcements will not be sent.")

        # Start the daily check task
        self.walpurgisnacht_announcer.start()

    def cog_unload(self):
        self.walpurgisnacht_announcer.cancel()

    @tasks.loop(hours=24)
    async def walpurgisnacht_announcer(self):
        """
        Announce Walpurgisnacht in the default channel on April 30.
        Runs every 24 hours.
        """
        today = datetime.now(timezone.utc)
        # Customize your desired date here
        if today.month == 4 and today.day == 30:
            channel = self.bot.get_channel(self.default_channel_id)
            if channel:
                logger.info("Sending Walpurgisnacht message.")
                await channel.send("TONIGHT IS WALPURGIS!!!")
            else:
                logger.warning(f"Channel with ID {self.default_channel_id} not found. Cannot send announcement.")

    @walpurgisnacht_announcer.before_loop
    async def before_walpurgisnacht_announcer(self):
        logger.debug("Waiting for bot to be ready before starting Walpurgisnacht announcer.")
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        Respond to certain trigger words/phrases in chat:
          - "cringe"
          - "massive"
          - "erm" with variable e/r/m
          - "ripbozo" or "rip bozo"
          - "lebron"
        """
        # Prevent the bot from responding to its own messages
        if message.author == self.bot.user:
            return

        # 1) Respond to "cringe"
        if re.search(r'\bcringe\b', message.content, re.IGNORECASE):
            logger.debug("Detected 'cringe'. Sending meme.")
            await message.channel.send(
                "https://tenor.com/view/cringe-comp-cringe-shrek-shrek-cringe-compilation-snap-gif-11981937")

        # 2) Respond to "massive"
        if re.search(r'\bmassive\b', message.content, re.IGNORECASE):
            logger.debug("Detected 'massive'. Sending meme.")
            await message.channel.send(
                "https://tenor.com/view/ninja-any-haircut-recommendations-low-taper-fade-you-know-what-else-is-massive-gif-3708438262570242561")

        # 3) Respond to "erm" with any length of e's, r's, or m's (case-insensitive)
        if re.search(r'\b[eE]+[rR]+[mM]+\b', message.content):
            logger.debug("Detected 'erm'. Sending meme.")
            await message.channel.send(
                "https://tenor.com/view/jungwon-jungwon-glasses-jungwon-um-ackshually-jungwon-um-actually-gif-16607372845996584568")

        # 4) Respond to "ripbozo" or "rip bozo"
        if re.search(r'\brip\s*bozo\b', message.content, re.IGNORECASE):
            logger.debug("Detected 'rip bozo'. Sending meme.")
            await message.channel.send("https://tenor.com/view/rip-bozo-gif-22294771")

        # 5) Respond to "lebron"
        if re.search(r'\blebron\b', message.content, re.IGNORECASE):
            logger.debug("Detected 'lebron'. Sending heartfelt message.")
            response = (
                "Boy oh boy where do I even begin. Lebron... honey, my pookie bear. "
                "I have loved you ever since I first laid eyes on you. The way you drive into the paint and strike fear into your enemies' eyes. "
                "Your silky smooth touch around the rim, and that gorgeous jumpshot. I would do anything for you. I wish it were possible to freeze time "
                "so I would never have to watch you retire. You had a rough childhood, but you never gave up hope. You are even amazing off the court, you're a great husband and father, sometimes I even call you dad. "
                "I forever dread and weep, thinking of the day you will one day retire. I would sacrifice my own life if it were the only thing that could put a smile on your beautiful face. "
                "You have given me so much joy, and heartbreak over the years. I remember when you first left Cleveland and it's like my heart got broken into a million pieces. "
                "But a tear still fell from my right eye when I watched you win your first ring in Miami, because deep down, my glorious king deserved it. I just wanted you to return home. "
                "Then alas, you did, my sweet baby boy came home and I rejoiced. 2015 was a hard year for us baby, but in 2016 you made history happen. You came back from 3-1 and I couldn't believe it. "
                "I was crying, bawling even, and I heard my glorious king exclaim these words, \"CLEVELAND, THIS IS FOR YOU!\" Not only have you changed the game of basketball and the world forever, but you've eternally changed my world. "
                "And now you're getting older, but still the goat, my goat. I love you pookie bear, my glorious king, LeBron James.☺️♥️🫶🏻"
            )
            await message.channel.send(response)


async def setup(bot):
    await bot.add_cog(FunCog(bot))
