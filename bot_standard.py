import os
import openai
import asyncio
import requests
import discord
import config
from datetime import datetime
from discord.ext import commands
from dotenv import load_dotenv, find_dotenv

os.chdir('c:/Users/HP/Desktop/School-coding/Python/AI-battlegame/Discord BattleBot/standard/')
load_dotenv(find_dotenv())

TOKEN = config.DISCORD_TOKEN
OPENAI_KEY = config.OPENAI_API_KEY2
print(OPENAI_KEY)
# TOKEN = os.getenv("DISCORD_BOT_TOKEN")
# print(TOKEN)
# openai.api_key = os.getenv("OPENAI_API_KEY2")



def run_discord_bot():
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix= '/', intents = intents, application_id= "1048012904584183898")
    print(os.getcwd())

    async def load():       #Load the cogs in the cogs folder
        for file in os.listdir('./cogs'):
            if file.endswith('.py'):
                await bot.load_extension(f'cogs.{file[:-3]}')

    @bot.event
    async def on_ready():
        print(f'{bot.user} Online.')
    
    # @bot.event
    # async def on_message(message):
    #     await bot.process_commands(message)
    #     if message.content[0] == '/':
    #         return
    #     if message.author == bot.user:
    #         return
    #     await message.channel.send("I'm listening...")

    
    asyncio.run(load())     #Load the cogs in the cogs folder before running bot
    bot.run(TOKEN)