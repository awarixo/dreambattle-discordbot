import requests
import asyncio
import os
import re
import chain_responses
import discord
import logging
from discord import app_commands
from discord.ext import commands
import chain_responses
import loggerSettings
from threading import Thread


logger = loggerSettings.logging.getLogger("discord")

class Quick(commands.Cog):
    def __init__(self, bot: commands.Bot):        #Initialize your chain class instance
        self.bot = bot

    
    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f'Quick Cog is loaded')
    
    #QUICK FIGHT CREATE PLAYER 1
    @app_commands.command(name="p1", description="Quick fight create player 1")
    @app_commands.describe(fighter = "Create your fighter")
    async def p1(self, interaction: discord.Interaction, *, fighter:str):
        
        classic_player1 = re.sub(r'\W+', ' ',fighter)
        print(f"CLASSIC_PLAYER1: {classic_player1}")
        p1_username = re.sub(r'\W+', '-', str(interaction.user))
        p1_guild = self.bot.get_guild(interaction.guild_id)
        p1_server = f"{p1_guild}-{p1_guild.id}"
        gamemode = "Quick game"

         ## CHECK IF PLAYER IS IN USERS NODE, IF NOT ADD PLAYER ##
        users_list = await chain_responses.get_users_list()
        player_registered = await chain_responses.check_player_exist(p1_username,users_list)
        if player_registered == False:
            await chain_responses.set_new_player(p1_username, p1_server)
        else:
            token_check = await chain_responses.check_user_tokens(p1_username,users_list)
            if token_check < 1:
                await interaction.response.send_message("You have exhausted your Dreambattle Tokens, use the /subscribe command to reload your account", ephemeral=True)
                return
        ############## IF PLAYER IS IN USERS NODE, CHECK IF USER HAS TOKEN>0, IF NOT SEND ERROR "TOKENS EXHAUSTED" #############
        # await chain_responses.update_fighters_timestamps(p1_username, gamemode)

        await chain_responses.store_p1_to_DB(p1_server, p1_username, gamemode, classic_player1)
        await interaction.response.send_message("WAITING FOR PLAYER 2")
        logger.info(f'CLASSIC PLAYER 1 {p1_guild}:{p1_username}, {classic_player1}')
        
    

    #QUICK FIGHT CREATE PLAYER 2
    @app_commands.command(name="p2", description="Quick fight create player 2")
    @app_commands.describe(fighter = "Create your fighter")
    async def p2(self, interaction: discord.Interaction, *, fighter:str):
        gamemode = "Quick game"
        guild = self.bot.get_guild(interaction.guild_id)
        server = f"{guild}-{guild.id}"
        classic_player2 = re.sub(r'\W+', ' ',fighter)
        p2_username = re.sub(r'\W+', '-', str(interaction.user))

        read_status = await chain_responses.check_db_read_status(server,gamemode)
        print(f"READ STATUS:    {read_status}")
        if read_status == False:
            await interaction.response.send_message("CREATE PLAYER 1 FIRST")
            return

        
        #then get p1 info from the server
        p1_username, classic_player1 = await chain_responses.get_p1_from_DB(server, gamemode) 
        
        ## CHECK IF PLAYER IS IN USERS NODE, IF NOT ADD PLAYER ##
        users_list = await chain_responses.get_users_list()
        player_registered = await chain_responses.check_player_exist(p2_username,users_list)
        if player_registered == False:
            await chain_responses.set_new_player(p2_username, server)
        else:

            token_check = await chain_responses.check_user_tokens(p2_username,users_list)
            if p1_username == p2_username:
                if token_check < 2:
                    await interaction.response.send_message("You have exhausted your Dreambattle Tokens, use the /subscribe command to reload your account", ephemeral=True)
                    return
            else:
                if token_check < 1:
                    await interaction.response.send_message("You have exhausted your Dreambattle Tokens, use the /subscribe command to reload your account", ephemeral=True)
                    return
        ############## IF PLAYER IS IN USERS NODE, CHECK IF USER HAS TOKEN>0, IF NOT SEND ERROR "TOKENS EXHAUSTED" #############
        
        logger.info(f'CLASSIC PLAYER 2 {guild}:{p2_username}, {classic_player2}')
        logger.info(f'STARTING QUICK FIGHT: {guild}')
        await interaction.response.send_message("CREATING FIGHTERS")




        logger.info(f"CLASSIC PLAYER 1:{p1_username}, {classic_player1}")
        try:
            logger.info(f"QUICK GAME THREAD CREATED")
            classic_result = await chain_responses.message_handler(p1_username,p2_username,server,classic_player1,classic_player2)
            if classic_result == "NO NSFW OR PUBLIC FIGURES ALLOWED":
                await interaction.channel.send("WARNING: NO NSFW OR PUBLIC FIGURES ALLOWED")
                return
            if classic_result == "The server had an error while processing your request. Sorry about that!":
                await interaction.channel.send("The server had an error while processing your request. You will not be charged for unused tokens. Sorry about that!")
                return classic_result
            await interaction.channel.send(f"`PLAYER 1:{classic_player1}`")
            await interaction.channel.send(file=discord.File('quick_p1.jpg'))
            await interaction.channel.send(f"`PLAYER 2:{classic_player2}`")
            await interaction.channel.send(file=discord.File('quick_p2.jpg'))
            await interaction.channel.send(classic_result)
        except Exception as e:
            print(e)
            error = str(e).lower()
            if 'error' in error:
                await interaction.channel.send("The server had an error while processing your request. Sorry about that!")
            else:
                await interaction.channel.send(e)
        await chain_responses.close_db_read_status(server,gamemode)
        result_check = classic_result
        result_list = result_check.split('.')
        result_list = result_list[-5:]
        check_sentence = '.'.join(result_list)
        check_sentence = check_sentence.lower()
            # Decide fight winner
        classic_player1_text = re.sub('[^a-zA-Z ]+',' ', classic_player1)
        classic_player2_text = re.sub('[^a-zA-Z ]+',' ', classic_player2)
        fight_decider = await chain_responses.gpt3_decider(check_sentence, classic_player1_text, classic_player2_text)
        if '2' in fight_decider:
            logger.info(f'Player 2 won the fight')
            await interaction.channel.send('**PLAYER 2 WON THE FIGHT**')
            await chain_responses.add_player_experience(p2_username,p1_username,15,5)

        else:
            logger.info(f'Player 1 won the fight')
            await interaction.channel.send('**PLAYER 1 WON THE FIGHT**')
            await chain_responses.add_player_experience(p1_username,p2_username,15,5)

        
        #### Remove one player from each player token
        await chain_responses.deduct_token(p1_username)
        await chain_responses.deduct_token(p2_username)

        # thread = await Thread(target=quick_game_thread, args=(p1_username,p2_username,server,classic_player1,classic_player2))
        # thread.start()
        # thread.join()



# async def quick_game_thread(self, interaction: discord.Interaction, p1_username,p2_username,server,classic_player1,classic_player2):
#     try:
#         logger.info(f"QUICK GAME THREAD CREATED")
#         classic_result = await chain_responses.message_handler(p1_username,p2_username,server,classic_player1,classic_player2)
#         if classic_result == "NO NSFW OR PUBLIC FIGURES ALLOWED":
#             await interaction.channel.send("WARNING: NO NSFW OR PUBLIC FIGURES ALLOWED")
#             return
#         if classic_result == "The server had an error while processing your request. Sorry about that!":
#             await interaction.channel.send("The server had an error while processing your request. You will not be charged for unused tokens. Sorry about that!")
#             return classic_result
#         await interaction.channel.send(f"`PLAYER 1:{classic_player1}`")
#         await interaction.channel.send(file=discord.File('quick_p1.jpg'))
#         await interaction.channel.send(f"`PLAYER 2:{classic_player2}`")
#         await interaction.channel.send(file=discord.File('quick_p2.jpg'))
#         await interaction.channel.send(classic_result)
#     except Exception as e:
#         print(e)
#         error = str(e)
#         if 'RateLimitError' in error:
#             await interaction.channel.send("The server had an error while processing your request. Sorry about that!")
#         else:
#             await interaction.channel.send(e)
#     await chain_responses.close_db_read_status(server,gamemode)


async def setup(bot):       #Command to add cog to bot
    await bot.add_cog(Quick(bot))
