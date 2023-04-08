import os
import openai
import asyncio
import requests
import logging
import discord
import loggerSettings
from datetime import datetime
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
logger = loggerSettings.logging.getLogger("discord")


# logging.basicConfig(filename='battlebot.log',format='%(asctime)s %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
TOKEN = os.getenv("DISCORD_TOKEN")




def run_discord_bot():
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix= '/', intents = intents, application_id= "1048012904584183898")

    

    async def load():       #Load the cogs in the cogs folder
        for file in os.listdir('./cogs'):
            if file.endswith('.py'):
                await bot.load_extension(f'cogs.{file[:-3]}')
    
    

    @bot.event
    async def on_ready():
        logger.info(f'{bot.user} Online.')
    
    
    # logger = logging.getLogger("discord")
    
    asyncio.run(load())     #Load the cogs in the cogs folder before running bot
    bot.run(TOKEN, root_logger=True)