import requests
import asyncio
import os
import chain_responses
import discord
from discord import app_commands
from discord.ext import commands
import chain_responses

class Quick(commands.Cog):
    def __init__(self, bot: commands.Bot):        #Initialize your chain class instance
        self.bot = bot

    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Quick Cog is loaded')
    
    #QUICK FIGHT CREATE PLAYER 1
    @app_commands.command(name="p1", description="Quick fight create player 1")
    @app_commands.describe(fighter = "Create your fighter")
    async def p1(self, interaction: discord.Interaction, *, fighter:str):
        global classic_player1, p1_username
        classic_player1 = fighter
        p1_username = interaction.user
        print(f'CLASSIC PLAYER 1:{p1_username}, {classic_player1}')
        await interaction.response.send_message("WAITING FOR PLAYER 2")
    

    #QUICK FIGHT CREATE PLAYER 2
    @app_commands.command(name="p2", description="Quick fight create player 2")
    @app_commands.describe(fighter = "Create your fighter")
    async def p2(self, interaction: discord.Interaction, *, fighter:str):
        global classic_player1, classic_player2, p1_username,p2_username
        try:
            print(classic_player1)
        except Exception as e:
            await interaction.response.send_message("CREATE PLAYER 1 FIRST")
            return
        if classic_player1 == '0':
            await interaction.response.send_message("CREATE PLAYER 1 FIRST")
            return
        classic_player2 = fighter
        p2_username = interaction.user
        print(f'CLASSIC PLAYER 2:{p2_username}, {classic_player2}')
        await interaction.response.send_message("CREATING FIGHTERS")

        try:
            classic_result = await chain_responses.message_handler(p1_username,p2_username,classic_player1,classic_player2)
            if classic_result == "NO NSFW OR PUBLIC FIGURES ALLOWED":
                await interaction.channel.send("WARNING: NO NSFW OR PUBLIC FIGURES ALLOWED")
                return
            await interaction.channel.send(f"`PLAYER 1:{classic_player1}`")
            await interaction.channel.send(file=discord.File('quick_p1.jpg'))
            await interaction.channel.send(f"`PLAYER 2:{classic_player2}`")
            await interaction.channel.send(file=discord.File('quick_p2.jpg'))
            await interaction.channel.send(classic_result)
            classic_player1 = '0'
        except Exception as e:
            print(e)
            await interaction.channel.send(e)



async def setup(bot):       #Command to add cog to bot
    await bot.add_cog(Quick(bot), guilds=[discord.Object(id=1047862232987484190)])
