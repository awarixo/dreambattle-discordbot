import os
import openai
import asyncio
import requests
import discord
from datetime import datetime
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()


OPENAI_KEY = os.getenv("OPENAI_API_KEY")
print(OPENAI_KEY)
TOKEN = os.getenv("DISCORD_TOKEN")





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