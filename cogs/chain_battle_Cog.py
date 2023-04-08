import requests
import asyncio
import os
import re
import chain_responses
import discord
import loggerSettings
from discord import app_commands
from discord.ext import commands

# logging.basicConfig(filename='battlebot.log',format='%(asctime)s %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)
logger = loggerSettings.logging.getLogger("discord")
# logging.basicConfig(level=logging.INFO)


class Chain(commands.Cog):
    def __init__(self, bot: commands.Bot):        #Initialize your chain class instance
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        default_channel = guild.text_channels[0]
        await default_channel.send("Welcome to the DreamBattle Beta! 🤠 Create your own fighter using AI and watch as it comes to life to battle other fighters in epic duels. Imagine and describe, let the AI do the rest \n\nUse /help to get started")


    # global chain_counter
    # global fight_started
    # fight_started = False
    # chain_counter = 0 #Check if this is the first chain or 2nd chain

    #Help function
    @app_commands.command(name="help", description="How to play")
    async def help(self, interaction: discord.Interaction):
        guide = "DreamBattle has two modes: QUICK GAME & CHAIN BATTLE. In QUICK GAME, two players create their own fighters, compete against each other, and AI decides who comes out on top. \n\nIn CHAIN BATTLE players create their fighters and control their fighters actions, outplaying each other to become the last man standing. The fight begins with an opener but stops, then players enter their fighters actions.\n\n*Commands*\nQUICK GAME: Two people create their fighters using the slash commands\n \"/P1 [fighter description]\" and \"/P2 [fighter description]\" \n\nCHAIN BATTLE: Two people create their fighters with:\n \"/controlp1 [fighter description]\" and \"/controlp2 [fighter description]\" \n\nThen to control the actions\n \"/actionp1 [fighter description]\" and \"/actionp2 [fighter description]\""
        embed = discord.Embed(title="DreamBattle Gamemodes", description=guide, color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
        
    #1ST ROUND CREATE PLAYER 1
    @app_commands.command(name="controlp1", description="Control player 1")
    @app_commands.describe(fighter = "Create your fighter")
    async def controlp1(self, interaction: discord.Interaction, *, fighter:str):
        control_player1 = re.sub('[^a-zA-z0-9]', ' ',fighter)
        p1_username = str(interaction.user)
        p1_guild = self.bot.get_guild(interaction.guild_id)
        p1_server = f"{p1_guild}-{p1_guild.id}"
        
        gamemode = "Chain battle" 
        fight_started = await chain_responses.check_chain_battle_start(p1_server)

        if fight_started == True:
            await interaction.response.send_message("CHAIN BATTLE ONGOING. USE /ACTION TO INPUT ACTIONS")
            return
        
        await chain_responses.store_p1_to_DB(p1_server, p1_username, gamemode, control_player1)
        logger.info(f'CONTROL GAMEMODE P1: {p1_username} , {control_player1}')
        await interaction.response.send_message("CONTROL GAMEMODE STARTED. WAITING FOR PLAYER 2")


    #1ST ROUND CREATE PLAYER 2
    @app_commands.command(name="controlp2", description="Control player 2")
    @app_commands.describe(fighter = "Create your fighter")
    async def controlp2(self, interaction:discord.Interaction , *, fighter:str):
        gamemode = "Chain battle"
        guild = self.bot.get_guild(interaction.guild_id)
        server = f"{guild}-{guild.id}"
        # logger.info(f"SERVER:     {server}")

        fight_started = await chain_responses.check_chain_battle_start(server)
        # logger.info(f"FIGHT STARTED:      {fight_started}")
        if fight_started == True:
            await interaction.response.send_message("CHAIN BATTLE ONGOING. USE /ACTION TO INPUT ACTIONS")
            return
        
        read_status = await chain_responses.check_db_read_status(server,gamemode)
        # logger.info(f"READ STATUS:    {read_status}")
        if read_status == False:
            await interaction.response.send_message("CREATE PLAYER 1 FIRST")
            return

        control_player2 = re.sub('[^a-zA-z0-9]', ' ',fighter)
        p2_username = str(interaction.user)
        logger.info(f'CONTROL GAMEMODE STARTED P2: {p2_username} , {control_player2}')
        await interaction.response.send_message(f"CREATING FIGHTERS")
        fight_started = True
        await chain_responses.set_chain_battle_start(server, fight_started)

       #then get p1 info from the server by sorting for the most recent record
        p1_username, control_player1 = await chain_responses.get_p1_from_DB(server, gamemode) 
        
        # logger.info(f"CONTROL PLAYER 1:{p1_username}, {control_player1}")

        try:
            chain_result = await chain_responses.chain_message_handler(p1_username,p2_username,server,control_player1,control_player2)
            if chain_result == "NO NSFW OR PUBLIC FIGURES ALLOWED":
                await interaction.followup.send("WARNING: NO NSFW OR PUBLIC FIGURES ALLOWED")
                return
            if chain_result == "The server had an error while processing your request. Sorry about that!":
                await interaction.channel.send("The server had an error while processing your request. You will not be charged for unused tokens. Sorry about that!")
                return chain_result
            await interaction.channel.send(f"`PLAYER 1:{control_player1}`")
            await interaction.channel.send(file=discord.File('chain_p1.jpg'))
            await interaction.channel.send(f"`PLAYER 2:{control_player2}`")
            await interaction.channel.send(file=discord.File('chain_p2.jpg'))
            await chain_responses.set_control_p2(server,p2_username,gamemode,control_player2)
            await interaction.channel.send(chain_result)
            await chain_responses.input_chain_battle(chain_result, server, gamemode)

        except Exception as e:
            logger.error(e)
            error = str(e)
            if 'RateLimitError' in error or 'server' in error:
                await interaction.channel.send("The server had an error while processing your request. Sorry about that!")
            else:
                await interaction.channel.send(e)
        await chain_responses.close_db_read_status(server,gamemode)

        

    #2ND ROUND PLAYER 1 ACTION1
    @app_commands.command(name="actionp1", description="player 1 action")
    @app_commands.describe(action = "Input Fighter action")
    async def actionp1(self, interaction:discord.Interaction, *, action:str):
        gamemode = "Chain battle"
        p1_guild = self.bot.get_guild(interaction.guild_id)
        p1_server = f"{p1_guild}-{p1_guild.id}"        
        
        chain_battle_start = await chain_responses.check_chain_battle_start(p1_server)

        if chain_battle_start == False:
            logger.warning(f"CHAIN BATTLE NOT STARTED.")
            await interaction.response.send_message("START CHAIN BATTLE WITH /CONTROL COMMANDS FIRST", ephemeral=True )
            return
        else:
            #p1_played = await chain_responses.check_p1_played(p1_server, gamemode)
            player1_data = await chain_responses.get_control_p1(p1_server, gamemode)
            # logger.info(player1_data)
            p1_played = player1_data["p1_played"]
            chain_counter = player1_data["action count"]
            if chain_counter == 0: #Check if this is the first chain or 2nd chain
                action_player1  = action
                logger.info("FIRST CHAIN P1 REGISTERED. ADDING TO DB")
                chain_counter = 1
                p1_played = True
                await chain_responses.input_action(chain_counter, action_player1, p1_server, gamemode, p1_played)
                logger.info("PLAYER 1 ACTION1 ADDED TO DB")
                await interaction.response.send_message("ACTION REGISTERED. WAITING FOR PLAYER 2", delete_after=0)
                embed = discord.Embed(title="Player 1 Action Registered", description="Waiting for Player 2", color=discord.Color.blue())
                await interaction.channel.send(embed=embed)

            elif chain_counter == 1 and p1_played==True: #Check if this is the first chain or 2nd chain
                action_player1  = action
                logger.info("FIRST CHAIN P1 REGISTERED. ADDING TO DB")
                chain_counter = 1
                p1_played = True
                await chain_responses.input_action(chain_counter, action_player1, p1_server, gamemode, p1_played)
                logger.info("PLAYER 1 ACTION1 ADDED TO DB")
                response = await interaction.response.send_message("ACTION REGISTERED. WAITING FOR PLAYER 2", delete_after=0)
                embed = discord.Embed(title="Player 1 Action Registered", description="Waiting for Player 2", color=discord.Color.blue())
                await interaction.channel.send(embed=embed)

            # elif chain_counter == 1: #Check if this is the first chain or 2nd chain
            #     action_player1  = action
            #     logger.info("FIRST CHAIN P1 REGISTERED. ADDING TO DB")
            #     chain_counter = 1
            #     await chain_responses.input_action(chain_counter, action_player1, p1_server, gamemode)
            #     logger.info("PLAYER 1 ACTION1 ADDED TO DB")
            #     await interaction.response.send_message("ACTION REGISTERED. WAITING FOR PLAYER 2")

            #3RD ROUND PLAYER 1 ACTION2
            elif chain_counter == 1 and p1_played==False:
                logger.info(f"CHAIN COUNTER = {chain_counter} ")
                second_action_player1  = action
                logger.info("SECOND CHAIN P1 REGISTERED. ADDING TO DB")
                chain_counter = 2  
                p1_played = True
                await chain_responses.input_action(chain_counter, second_action_player1, p1_server, gamemode, p1_played)
                response = await interaction.response.send_message("SECOND ACTION REGISTERED. WAITING FOR PLAYER 2", delete_after=0)
                embed = discord.Embed(title="Player 1 Action Registered", description="Waiting for Player 2", color=discord.Color.blue())
                await interaction.channel.send(embed=embed)



    #2ND ROUND PLAYER 2 ACTION1
    @app_commands.command(name = "actionp2", description="player 2 action")
    @app_commands.describe(action = "Input Fighter action")
    async def actionp2(self, interaction:discord.Interaction, *, action:str):
        gamemode = "Chain battle"
        guild = self.bot.get_guild(interaction.guild_id)
        server = f"{guild}-{guild.id}"
        logger.info(f"SERVER:     {server}")

        chain_battle_start = await chain_responses.check_chain_battle_start(server)
        if chain_battle_start == False:
            logger.warning(f"CHAIN BATTLE NOT STARTED.")
            await interaction.response.send_message("START CHAIN BATTLE WITH /CONTROL COMMANDS FIRST", ephemeral=True )
            return
        else:
            #chain_counter = await chain_responses.check_chain_counter(server,gamemode)
            Player1_data = await chain_responses.get_control_p1(server, gamemode)
            action_count = str(Player1_data['action count'])
            control_player1 = Player1_data['Fighter']
            action_player1 = Player1_data['P1_action']
            chain_result = Player1_data['fight_output']

            # logger.info("Check if action 1 exists: ", action_player1) #Check if action 1 exists

            # logger.info(f"action_count: {action_count}")
            if action_count == '0':
                await interaction.response.send_message("INPUT ACTION P1 FIRST")
                return
            elif action_count == '1':
                action_player2 = action
                logger.info("FIRST CHAIN P2 REGISTERED")
                try:
                    logger.info("CHAIN BATTLE Player 1",control_player1,action_player1) #Check if player 1 exists
                    response = await interaction.response.send_message("ACTION REGISTERED.", delete_after=0)
                    embed = discord.Embed(title="Player 2 Action Registered", description="Creating chain battle", color=discord.Color.blue())
                    await interaction.channel.send(embed=embed)
                    p1_played = False
                    await chain_responses.set_p1_played(p1_played,server,gamemode)
                except Exception as e:
                    await interaction.response.send_message("WAITING FOR PLAYER 1")
                    return

                try:
                    logger.info("GETTING CONTROL P2")
                    player2_data = await chain_responses.get_control_p2(server, gamemode)
                    # logger.info(player2_data)
                    control_player2 = player2_data["Fighter"]

                    logger.info(f"Making 2nd round:    control_player1: {control_player1}    control_player2: {control_player2}")
                    chain_result2 = await chain_responses.gpt3_chain_fight2(control_player1,control_player2,action_player1,action_player2,chain_result)
                    logger.info("2nd round done")
                    logger.info(f"CHAIN RESULT 2:            {chain_result2}")
                    if chain_result2 == "NO NSFW OR PUBLIC FIGURES ALLOWED":
                        await interaction.channel.send("WARNING: NO NSFW OR PUBLIC FIGURES ALLOWED")
                        return
                    await interaction.channel.send(chain_result2)
                    await chain_responses.input_chain_battle(chain_result2, server, gamemode)

                #Check to see if chain battle is completed
                    chain_result_check = chain_result2
                    chain_result_list = chain_result_check.split('.')
                    chain_result_list = chain_result_list[-4:]
                    chain_check_sentence = '.'.join(chain_result_list)
                    # logger.info("CHAIN CHECK SENTENCE\n",chain_check_sentence)
                    chain_check = await chain_responses.gpt3_fight_completed(chain_check_sentence)
                    chain_check = chain_check.lower()
                    if "2" in chain_check or "completed" in chain_check:
                        logger.info(f'CHAIN COMPLETED SUCCESSFULLY = {chain_check}')
                        await interaction.channel.send("**CHAIN BATTLE COMPLETED**")
                        
                        fight_started = False
                        # Decide fight winner
                        control_player1_text = re.sub('[^a-zA-Z ]+',' ', control_player1)
                        control_player2_text = re.sub('[^a-zA-Z ]+',' ', control_player2)
                        fight_decider = await chain_responses.gpt3_decider(chain_check_sentence, control_player1_text, control_player2_text)
                        # logger.info(fight_decider)
                        if '2' in fight_decider:
                            logger.info(f'Player 2 won the fight')
                            await interaction.channel.send('**PLAYER 2 WON THE FIGHT**')
                        else:
                            logger.info(f'Player 1 won the fight')
                            await interaction.channel.send('**PLAYER 1 WON THE FIGHT**')
                        
                        await chain_responses.set_chain_battle_start(server, fight_started)
                        await chain_responses.set_chain_counter(0,server,gamemode)

                    else:
                        logger.info(f'CHAIN INCOMPLETED= {chain_check}')
                        await interaction.channel.send("**INPUT NEXT ACTION**")
                except Exception as e:
                    logger.error(e)
                    await interaction.channel.send(e)


        #3RD ROUND PLAYER 2 ACTION2
            elif action_count == '2':
                logger.info("round 2")
                second_action_player2 = action
                player2_data = await chain_responses.get_control_p2(server, gamemode)
                # logger.info(player2_data)
                control_player2 = player2_data["Fighter"]
                logger.info(f"Making 2nd round:    control_player1: {control_player1}    control_player2: {control_player2}")
                    
                # logger.info(control_player2,second_action_player2 )
                logger.info("FIRST CHAIN P2 REGISTERED")
                response = await interaction.response.send_message("PLAYER 2 SECOND ACTION REGISTERED", delete_after=0)
                embed = discord.Embed(title="Player 2 Action Registered", description="Creating chain battle", color=discord.Color.blue())
                await interaction.channel.send(embed=embed)
                try:
                    logger.info("Check if player 1 second action exists: ",control_player1,action_player1) #Check if player 1 exists
                except Exception as e:
                    await interaction.channel.send("WAITING FOR PLAYER 1")
                    return

                try:
                    # logger.info(chain_result)
                    chain_result3 = await chain_responses.gpt3_chain_fight3(control_player1,control_player2,action_player1,second_action_player2,chain_result)
                    if chain_result3 == "NO NSFW OR PUBLIC FIGURES ALLOWED":
                        await interaction.channel.send("WARNING: NO NSFW OR PUBLIC FIGURES ALLOWED")
                        return
                    await interaction.channel.send(chain_result3)

                    #Check to see if chain battle is completed
                    chain_result_check = chain_result3
                    chain_result_list = chain_result_check.split('.')
                    chain_result_list = chain_result_list[-4:]
                    chain_check_sentence = '.'.join(chain_result_list)
                    # logger.info("CHAIN CHECK SENTENCE\n",chain_check_sentence)
                    fight_started = False
                    # logger.info(f'CHAIN COMPLETED SUCCESSFULLY = {chain_check_sentence}')
                    await interaction.channel.send("**CHAIN BATTLE COMPLETED**")

                    # Decide fight winner
                    control_player1_text = re.sub('[^a-zA-Z ]+',' ', control_player1)
                    control_player2_text = re.sub('[^a-zA-Z ]+',' ', control_player2)
                    fight_decider2 = await chain_responses.gpt3_decider(chain_check_sentence, control_player1_text, control_player2_text)
                    logger.info(fight_decider2)
                    if '2' in fight_decider2:
                        logger.info(f'Player 2 won the fight')
                        await interaction.channel.send('**PLAYER 2 WON THE FIGHT**')
                    else:
                        logger.info(f'Player 1 won the fight')
                        await interaction.channel.send('**PLAYER 1 WON THE FIGHT**')
                    await chain_responses.set_chain_counter(0,server,gamemode)
                    await chain_responses.set_chain_battle_start(server, fight_started)

                except Exception as e:
                    logger.info(e)
                    await interaction.channel.send(e)
                return

    @commands.Cog.listener()
    async def on_ready(self):
        guild_list=[]
        for guild in self.bot.guilds:
            server = f"{guild}-{guild.id}"
            setting=False
            p1_played = False
            await chain_responses.set_chain_battle_start(server,setting)
            gamemode = "Chain battle"
            await chain_responses.set_chain_counter(0,server,gamemode)
            await chain_responses.set_p1_played(p1_played,server,gamemode)
            logger.info(f"CHAIN BATTLE SET FOR {server}")
            guild_list.append(guild)


        #     synced = await self.bot.tree.sync()
        #     logger.info(f'Synced {len(synced)} commands globally')
            # commandName=['actionp1',"actionp2","controlp1","controlp2", "p1","p2"]
            # for cmd_name in commandName:
            #     cmd = self.bot.get_command(cmd_name)
            #     logger.info(cmd_name)
            #     self.bot.remove_command(cmd_name)
            #     logger.info(f"{cmd_name} removed")

            # synced = await self.bot.tree.sync(guild=guild)
        logger.info(f"GUILD LIST:     {guild_list}")
        synced = await self.bot.tree.sync()
        logger.info(f'Synced {len(synced)} commands globally')
        logger.info(f'Chain Cog is loaded')




async def setup(bot):       #Command to add cog to bot
    logger.info("Adding Chainbattle cog to bot")
    await bot.add_cog(Chain(bot))

