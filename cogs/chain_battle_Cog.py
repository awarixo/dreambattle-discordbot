import requests
import asyncio
import os
import re
import chain_responses
import discord
import loggerSettings
import math
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View
from StringProgressBar import progressBar

# logging.basicConfig(filename='battlebot.log',format='%(asctime)s %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)
logger = loggerSettings.logging.getLogger("discord")
# logging.basicConfig(level=logging.INFO)


class Chain(commands.Cog):
    def __init__(self, bot: commands.Bot):        #Initialize your chain class instance
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        default_channel = guild.text_channels[0]
        server = f"{guild}-{guild.id}"
        setting=False
        p1_played = False
        await chain_responses.set_chain_battle_start(server,setting)
        gamemode = "Chain battle"
        await chain_responses.set_chain_counter(0,server,gamemode)
        await chain_responses.set_p1_played(p1_played,server,gamemode)
        await chain_responses.set_p2_played(p1_played,server,gamemode)
        logger.info(f"CHAIN BATTLE SET FOR {server}")
        await default_channel.send("Welcome to the DreamBattle Beta! 🤠 Create your own fighter using AI and watch as it comes to life to battle other fighters in epic duels. Imagine and describe, let the AI do the rest \n\nUse /help to get started")


    #Help function
    @app_commands.command(name="help", description="How to play")
    async def help(self, interaction: discord.Interaction):
        guide = "DreamBattle has two modes: QUICK GAME & CHAIN BATTLE. In QUICK GAME, two players create their own fighters, compete against each other, and AI decides who comes out on top. \n\nIn CHAIN BATTLE players create their fighters and control their fighters actions, outplaying each other to become the last man standing. The fight begins with an opener but stops, then players enter their fighters actions.\n\n*Commands*\nQUICK GAME: Two people create their fighters using the slash commands\n \"/P1 [fighter description]\" and \"/P2 [fighter description]\" \n\nCHAIN BATTLE: Two people create their fighters with:\n \"/controlp1 [fighter description]\" and \"/controlp2 [fighter description]\" \n\nThen to control the actions\n \"/actionp1 [fighter action]\" and \"/actionp2 [fighter action]\""
        embed = discord.Embed(title="DreamBattle Gamemodes", description=guide, color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

#--------------------------------Button class for stats----------------------------------------------
    class Myview(discord.ui.View):
        def __init__(self):
            super().__init__()
            self.value = None
            self.page = 1

        @discord.ui.button(label="Chainbattle Fighters")
        async def button_one(self, interaction: discord.Interaction, button: discord.ui.Button):
            embed = discord.Embed(title=f"{interaction.user}'s Chainbattle Fighters", color=discord.Color.dark_teal())
            username = re.sub(r'\W+', '-', str(interaction.user)) + f'-{interaction.user.id}'
            gamemode="Chain battle"
            chain_list = await chain_responses.get_player_list(username,gamemode)
            fighters_str = ""

            for i, fighter in enumerate(chain_list[(self.page-1)*10:self.page*10], start=(self.page-1)*10+1):
                fighters_str += f"`{i}. {fighter}`\n"
            embed.add_field(name="Chainbattle Fighters", value=fighters_str)

            first_page = discord.ui.Button(label="<<", disabled=self.page == 1)
            prev_page = discord.ui.Button(label="<", disabled=self.page == 1)
            next_page= discord.ui.Button(label=">", disabled=self.page*10 >= len(chain_list))
            last_page = discord.ui.Button(label=">>", disabled=self.page*10 >= len(chain_list))
            buttons = [first_page, prev_page, next_page, last_page]

            # Use the outer class name to instantiate the nested class
            view = self.fighterview(page=1, myview=self, fighter_list="chain")
            for button in buttons:
                view.add_item(button)

            # Assign callbacks before sending the message
            prev_page.callback = view.prev_page_callback
            next_page.callback = view.next_page_callback
            first_page.callback = view.first_page_callback
            last_page.callback = view.last_page_callback
            self.message = await interaction.response.edit_message(embed=embed, view=view)


        @discord.ui.button(label="Quickgame Fighters")
        async def button_two(self, interaction: discord.Interaction, button: discord.ui.Button):
            embed = discord.Embed(title=f"{interaction.user}'s Quickgame Fighters", color=discord.Color.dark_teal())
            username = re.sub(r'\W+', '-', str(interaction.user)) + f'-{interaction.user.id}'
            gamemode="Quick game"
            quick_list = await chain_responses.get_player_list(username, gamemode)
            fighters_str = ""
            for i, fighter in enumerate(quick_list[(self.page-1)*10:self.page*10], start=(self.page-1)*10+1):
                fighters_str += f"`{i}. {fighter}`\n"
            embed.add_field(name="Quickgame Fighters", value=fighters_str)

            first_page = discord.ui.Button(label="<<", disabled=self.page == 1)
            prev_page = discord.ui.Button(label="<", disabled=self.page == 1)
            next_page= discord.ui.Button(label=">", disabled=self.page*10 >= len(quick_list))
            last_page = discord.ui.Button(label=">>", disabled=self.page*10 >= len(quick_list))
            buttons = [first_page, prev_page, next_page, last_page]

            # Use the outer class name to instantiate the nested class
            view = self.fighterview(page=1, myview=self, fighter_list="quick")
            for button in buttons:
                view.add_item(button)

            # Assign callbacks before sending the message
            prev_page.callback = view.prev_page_callback
            next_page.callback = view.next_page_callback
            first_page.callback = view.first_page_callback
            last_page.callback = view.last_page_callback
            self.message = await interaction.response.edit_message(embed=embed, view=view)


################################## Define the nested class inside the outer class #########################################
        class fighterview(discord.ui.View):
            def __init__(self, page, myview, fighter_list):
                super().__init__()
                self.value = None
                self.page = page
                self.myview = myview
                self.list = fighter_list


            async def update_embed(self, interaction: discord.Interaction):
                username = re.sub(r'\W+', '-', str(interaction.user)) + f'-{interaction.user.id}'
                if self.list == "quick":
                    title= "Quickgame"
                    gamemode="Quick game"
                else:
                    title= "Chainbattle"
                    gamemode="Chain battle"
                fighter_list = await chain_responses.get_player_list(username,gamemode)

                embed = discord.Embed(title=f"{interaction.user}'s {title} Fighters", color=discord.Color.dark_teal())
                fighters_str = ""
                # print(f"fighter_list {fighter_list}")
                for i, fighter in enumerate(fighter_list[(self.page-1)*10:self.page*10], start=(self.page-1)*10+1):
                    fighters_str += f"`{i}. {fighter}`\n"
                embed.add_field(name=f"{title} Fighters", value=fighters_str)
                # print(f"page = {self.page}")

                # Update the button states based on the current page
                self.children[0].disabled = self.page == 1 # first page button
                self.children[1].disabled = self.page == 1 # prev page button
                self.children[2].disabled = self.page*10 >= len(fighter_list) # next page button
                self.children[3].disabled = self.page*10 >= len(fighter_list) # last page button

                self.myview.message = await interaction.response.edit_message(embed=embed, view=self)

                # await self.myview.message.edit(embed=embed, view=self)
                # await self.myview.interaction.response.edit_message(embed=embed, view=self)

            async def prev_page_callback(self, interaction: discord.Interaction):
                    self.page -= 1
                    await self.update_embed(interaction)

            async def next_page_callback(self, interaction: discord.Interaction):
                    self.page += 1
                    await self.update_embed(interaction)

            async def first_page_callback(self, interaction: discord.Interaction):
                    self.page = 1
                    await self.update_embed(interaction)

            async def last_page_callback(self, interaction: discord.Interaction):
                    username = re.sub(r'\W+', '-', str(interaction.user)) + f'-{interaction.user.id}'
                    if self.list == "quick":
                        title= "Quickgame"
                        gamemode="Quick game"
                    else:
                        title= "Chainbattle"
                        gamemode="Chain battle"
                    fighter_list = await chain_responses.get_player_list(username,gamemode)
                    self.page = (len(fighter_list) - 1) // 10 + 1
                    await self.update_embed(interaction)




    @app_commands.command(name="stats", description="Player information")
    async def info(self, interaction: discord.Interaction):

        username = re.sub(r'\W+', '-', str(interaction.user)) + f'-{interaction.user.id}'
        guild = self.bot.get_guild(interaction.guild_id)
        server = f"{guild}-{guild.id}"
        # Retrieve user's stats from your game database
        try:
            user_experience, user_level, user_token, user_status = await chain_responses.get_user_stats(username)
        except Exception as e:
            print(e)
            await chain_responses.set_new_player(username, server)
            user_experience, user_level, user_token, user_status = await chain_responses.get_user_stats(username)
        level_counter, player_xp, new_level_xp = chain_responses.add_player_level(user_experience)
        bardata = progressBar.filledBar(new_level_xp, player_xp, size=10)
        print(player_xp,new_level_xp,bardata)

        # Create an embedded message with user's stats
        embed = discord.Embed(title=f"Dreambattle {interaction.user} stats", description="Player Info", color=discord.Color.dark_teal())
        embed.set_thumbnail(url=interaction.user.avatar)
        embed.add_field(name=f"Level: {user_level}", value=f"XP: **{player_xp}/{new_level_xp}**\n{bardata[0]}", inline= False)
        #embed.add_field(name="ChainBattle Win rate", value=f"{user_level}", inline= True)
        embed.add_field(name="Status", value=f"{user_status}", inline= True)
        embed.add_field(name="Tokens Remaining", value=f"{user_token}", inline= True)
        view = self.Myview()

        # Send embedded message back to user
        await interaction.response.send_message( embed=embed,view=view, ephemeral=True)
        return
    


#--------------------------------Button class for rankings----------------------------------------------
    class Rankview(discord.ui.View):
        def __init__(self,separator, username, server, guild):
            super().__init__()
            self.value = None
            self.page = 1
            self.separator = separator
            self.username = username
            self.server = server
            self.guild = guild
            
            # Update the button states based on the current page
            self.children[0].disabled = self.page == 1 # first page button
            self.children[1].disabled = self.page == 1 # prev page button

        # def create_embed (self,data):
        #     embed = discord.Embed(title="Example")
        #     for item in data:
        #         embed.add_field(name = item, value= item, inline=False)
        #     return embed
        
        # async def update_message(self,data):
        #     await self.message.edit(embed=self.create_embed(data), view = self)
        

        async def update_embed(self, interaction: discord.Interaction):
            username = self.username
            server = self.server
            embed = discord.Embed(title=f"{self.guild} Chainbattle rankings", color=discord.Color.dark_teal())
            rankings_str = ""
            server_rankings = await chain_responses.get_server_rankings(server)
            print(f"server_rankings {server_rankings}")
            
            # Retrieve top 10 from database
            for i, fighter in enumerate(server_rankings[(self.page-1)*10:self.page*10], start=(self.page-1)*10+1):
                ranked_points = fighter[1]
                ranked_user = fighter[0]
                ranked_username_list = ranked_user.split('-')
                ranked_username_list = ranked_username_list[:-1]
                ranked_username = '-'.join(ranked_username_list)
                print(len(ranked_username))
                rankings_str += f"`{i}. {ranked_username}"
                spaces = 25 - len(ranked_username) - len(str(i))
                while spaces > 0:
                    rankings_str += " "
                    spaces-=1
                rankings_str += f"{ranked_points}rp`\n"
            embed.add_field(name="RANKED TOP 10🔥🔥", value=rankings_str)


            #Find user rank
            for i, fighter in enumerate(server_rankings, start=1):
                if fighter[0] == username:
                    ranking_username_list = username.split('-')
                    ranking_username_list = ranking_username_list[:-1]
                    ranking_username = '-'.join(ranking_username_list)
                    user_ranking_str = f"`{i}. {ranking_username}"
                    spaces = 25 - len(ranking_username) - len(str(i))
                    while spaces > 0:
                        user_ranking_str += " "
                        spaces-=1
                    user_ranking_str += f"{fighter[1]}rp`\n"
                    embed.add_field(name="Your Rank 🤓", value=user_ranking_str)

            # Update the button states based on the current page
            self.children[0].disabled = self.page == 1 # first page button
            self.children[1].disabled = self.page == 1 # prev page button
            self.children[2].disabled = self.page*10 >= len(server_rankings) # next page button
            self.children[3].disabled = self.page*10 >= len(server_rankings) # last page button

            self.message = await interaction.response.edit_message(embed=embed, view=self)



        
        
        @discord.ui.button(label="<<")
        async def first_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            self.page = 1
            await self.update_embed(interaction)

        
        @discord.ui.button(label="<")
        async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            self.page -= 1
            await self.update_embed(interaction)

        @discord.ui.button(label=">")
        async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            self.page += 1
            await self.update_embed(interaction)


        @discord.ui.button(label=">>")
        async def last_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            
            server = self.server
            server_rankings = await chain_responses.get_server_rankings(server)
            page_no = math.ceil(len(server_rankings)/10 )
            self.page = page_no
            await self.update_embed(interaction)



    
    @app_commands.command(name="rankings", description="Server Chainbattle rankings ⚔️")
    async def rankings(self, interaction: discord.Interaction):
        username = re.sub(r'\W+', '-', str(interaction.user)) + f'-{interaction.user.id}'
        guild = self.bot.get_guild(interaction.guild_id)
        server = f"{guild}-{guild.id}"
        
        # Retrieve top 10 from database
        try:
            rankings_str = ""
            server_rankings = await chain_responses.get_server_rankings(server)
            print(f"server_rankings {server_rankings}")
            for i, fighter in enumerate(server_rankings[0:10], start=1):
                ranked_points = fighter[1]
                ranked_user = fighter[0]
                ranked_username_list = ranked_user.split('-')
                ranked_username_list = ranked_username_list[:-1]
                ranked_username = '-'.join(ranked_username_list)
                print(len(ranked_username))
                rankings_str += f"`{i}. {ranked_username}"
                spaces = 25 - len(ranked_username) - len(str(i))
                while spaces > 0:
                    rankings_str += " "
                    spaces-=1
                rankings_str += f"{ranked_points}rp`\n"
        except Exception as e:
            print(e)

        #Find user rank
        for i, fighter in enumerate(server_rankings, start=1):
            if fighter[0] == username:
                ranking_username_list = username.split('-')
                ranking_username_list = ranking_username_list[:-1]
                ranking_username = '-'.join(ranking_username_list)
                user_ranking_str = f"`{i}. {ranking_username}"
                spaces = 25 - len(ranking_username) - len(str(i))
                while spaces > 0:
                    user_ranking_str += " "
                    spaces-=1
                user_ranking_str += f"{fighter[1]}rp`\n"


        # Create an embedded message with user's stats
        embed = discord.Embed(title=f"⚔️{guild} Chainbattle rankings⚔️", color=discord.Color.dark_teal())
        embed.add_field(name="RANKED TOP 10🔥🔥", value=rankings_str)
        embed.add_field(name="Your Rank 🤓", value=user_ranking_str)
# embed.set_thumbnail(url=interaction.user.avatar)
        ranked_view = self.Rankview(separator=10, username=username, server=server, guild=guild)
        ranked_view.data = server_rankings


        # Send embedded message back to user
        await interaction.response.send_message(embed=embed,view=ranked_view, ephemeral=True)
        return

    #1ST ROUND CREATE PLAYER 1
    @app_commands.command(name="controlp1", description="Control player 1")
    @app_commands.describe(fighter = "Create your fighter")
    async def controlp1(self, interaction: discord.Interaction, *, fighter:str):
        # if not interaction.user.verified:
        #     await interaction.response.send_message("VERIFY YOUR DISCORD ACCOUNT")
        #     return

        control_player1 = re.sub(r'\W+', ' ',fighter)
        p1_username = re.sub(r'\W+', '-', str(interaction.user)) + f'-{interaction.user.id}'
        p1_guild = self.bot.get_guild(interaction.guild_id)
        p1_server = f"{p1_guild}-{p1_guild.id}"
        gamemode = "Chain battle"
        fight_started = await chain_responses.check_chain_battle_start(p1_server)

        if fight_started == True:
            await interaction.response.send_message("CHAIN BATTLE ONGOING. USE /ACTION TO INPUT ACTIONS")
            return

        ## CHECK IF PLAYER IS IN USERS NODE, IF NOT ADD PLAYER ##
        users_list = await chain_responses.get_users_list()
        player_registered = await chain_responses.check_player_exist(p1_username,users_list)
        if player_registered == False:
            await chain_responses.set_new_player(p1_username,p1_server)
        else:
            token_check = await chain_responses.check_user_tokens(p1_username,users_list)
            if token_check < 1:
                await interaction.response.send_message("You have exhausted your Dreambattle Tokens, use the /subscribe command to reload your account", ephemeral=True)
                return
        ############## IF PLAYER IS IN USERS NODE, CHECK IF USER HAS TOKEN>0, IF NOT SEND ERROR "TOKENS EXHAUSTED" #############
        # await chain_responses.update_fighters_timestamps(p1_username, gamemode)
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
        control_player2 = re.sub(r'\W+', ' ',fighter)
        p2_username = re.sub(r'\W+', '-', str(interaction.user)) + f'-{interaction.user.id}'

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
        #then get p1 info from the server
        p1_username, control_player1 = await chain_responses.get_p1_from_DB(server, gamemode)

        ## CHECK IF PLAYER IS IN USERS NODE, IF NOT ADD PLAYER ##
        users_list = await chain_responses.get_users_list()
        player_registered = await chain_responses.check_player_exist(p2_username,users_list)
        if player_registered == False:
            await chain_responses.set_new_player(p2_username,server)
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

        logger.info(f'CONTROL GAMEMODE STARTED P2: {p2_username} , {control_player2}')
        await interaction.response.send_message(f"CREATING FIGHTERS")
        fight_started = True
        await chain_responses.set_chain_battle_start(server, fight_started)


        # logger.info(f"CONTROL PLAYER 1:{p1_username}, {control_player1}")

        try:
            chain_result = await chain_responses.chain_message_handler(p1_username,p2_username,server,control_player1,control_player2)
            if chain_result == "NO NSFW OR PUBLIC FIGURES ALLOWED":
                await interaction.followup.send("WARNING: NO NSFW OR PUBLIC FIGURES ALLOWED")
                await chain_responses.close_db_read_status(server,gamemode)
                fight_started = False
                await chain_responses.set_chain_battle_start(server, fight_started)
                return
            if chain_result == "The server had an error while processing your request. Sorry about that!":
                await interaction.channel.send("The server had an error while processing your request. You will not be charged for unused tokens. Sorry about that!")
                await chain_responses.close_db_read_status(server,gamemode)
                fight_started = False
                await chain_responses.set_chain_battle_start(server, False)
                return
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
            await chain_responses.set_chain_battle_start(server, False)
            if 'RateLimitError' in error or 'server' in error:
                await interaction.channel.send("The server had an error while processing your request. Sorry about that!")
            else:
                await interaction.channel.send(e)
        await chain_responses.close_db_read_status(server,gamemode)

        #### Remove one player from each player token
        await chain_responses.deduct_token(p1_username)
        await chain_responses.deduct_token(p2_username)



    #2ND ROUND PLAYER 1 ACTION1
    @app_commands.command(name="actionp1", description="player 1 action")
    @app_commands.describe(action = "Input Fighter action")
    async def actionp1(self, interaction:discord.Interaction, *, action:str):
        gamemode = "Chain battle"
        p1_guild = self.bot.get_guild(interaction.guild_id)
        server = f"{p1_guild}-{p1_guild.id}"

        chain_battle_start = await chain_responses.check_chain_battle_start(server)

        if chain_battle_start == False:
            logger.warning(f"CHAIN BATTLE NOT STARTED.")
            await interaction.response.send_message("START CHAIN BATTLE WITH /CONTROL COMMANDS FIRST", ephemeral=True )
            return

        else:
            player1_data = await chain_responses.get_control_p1(server, gamemode)
            chain_counter = player1_data["action count"]
            control_player1 = player1_data['Fighter']
            chain_result = player1_data['fight_output']
            P1_username = player1_data['username']
            try:
                player2_data = await chain_responses.get_control_p2(server, gamemode)
                p2_played = player2_data["player_played"]
                control_player2 = player2_data['Fighter']
                action_player2 = player2_data['Player_action']
                P2_username = player2_data['username']
            except Exception as e:
                print(e)
            action_player1  = action
            p1_played = True
            player="Player 1"
            await chain_responses.input_action(player, action_player1, server, gamemode, p1_played)
            logger.info("PLAYER 1 ACTION1 ADDED TO DB")
            
            #Check if this is the first chain or 2nd chain
            if p1_played == True and p2_played==True:
                response = await interaction.response.send_message("ACTION REGISTERED.", delete_after=0)
                embed = discord.Embed(title=f"Player 1 {interaction.user} Action Registered", description="Creating chain battle", color=discord.Color.blue())
                await interaction.channel.send(embed=embed)
                if chain_counter == 0:
                    logger.info(f"Making 1st round:    control_player1: {control_player1}    control_player2: {control_player2}")
                    try:
                        chain_result2 = await chain_responses.gpt3_chain_fight2(control_player1,control_player2,action_player1,action_player2,chain_result)
                        logger.info("1st round done")
                    except Exception as e:
                        logger.info(f"ACTION P1 FAILED. ERROR: {e}")
                        chain_result2 = await chain_responses.gpt3_chain_fight2(control_player1,control_player2,action_player1,action_player2,chain_result)

                    logger.info(f"CHAIN RESULT 2:            {chain_result2}")
                    await interaction.channel.send(chain_result2)
                    await chain_responses.input_chain_battle(chain_result2, server, gamemode)
                    chain_check_sentence = '.'.join(chain_result2.split('.')[-5:])
                    chain_check = await chain_responses.gpt3_fight_completed(chain_check_sentence)
                    if "2" in chain_check or "completed" in chain_check:
                        logger.info(f'CHAIN COMPLETED SUCCESSFULLY = {chain_check}')
                        await interaction.channel.send("**CHAIN BATTLE COMPLETED**")
                        fight_started = False
                        fight_decider = await chain_responses.gpt3_decider(chain_check_sentence, control_player1, control_player2)
                        if '2' in fight_decider:
                            logger.info(f'Player 2 won the fight')
                            await interaction.channel.send('**PLAYER 2 WON THE FIGHT**')
                            await chain_responses.add_player_experience(gamemode,server, P2_username,P1_username,20,10)
                        else:
                            logger.info(f'Player 1 won the fight')
                            await interaction.channel.send('**PLAYER 1 WON THE FIGHT**')
                            await chain_responses.add_player_experience(gamemode,server, P1_username,P2_username,20,10)
                        await chain_responses.set_chain_battle_start(server, fight_started)

                    #Chain battle ongoing
                    else:
                        logger.info(f'CHAIN INCOMPLETED= {chain_check}')
                        await interaction.channel.send("**INPUT NEXT ACTION**")
                        await chain_responses.set_chain_counter(1,server,gamemode)
                    p1_played = False
                    await chain_responses.set_p1_played(p1_played,server,gamemode)
                    await chain_responses.set_p2_played(p1_played,server,gamemode)


                elif chain_counter == 1:
                    logger.info(f"Making 2nd round:    control_player1: {control_player1}    control_player2: {control_player2}")
                    try:
                        chain_result3 = await chain_responses.gpt3_chain_fight3(control_player1,control_player2,action_player1,action_player2,chain_result)
                        logger.info("2nd round done")
                    except Exception as e:
                        logger.info(f"ACTION P1 FAILED. ERROR: {e}")
                        chain_result3 = await chain_responses.gpt3_chain_fight3(control_player1,control_player2,action_player1,action_player2,chain_result)
                    await interaction.channel.send(chain_result3)
                    await interaction.channel.send("**CHAIN BATTLE COMPLETED**")
                    chain_check_sentence = '.'.join(chain_result3.split('.')[-5:])
                    fight_decider = await chain_responses.gpt3_decider(chain_check_sentence, control_player1, control_player2)
                    if '2' in fight_decider:
                        logger.info(f'Player 2 won the fight')
                        await interaction.channel.send('**PLAYER 2 WON THE FIGHT**')
                        await chain_responses.add_player_experience(gamemode,server, P2_username,P1_username,20,10)
                    else:
                        logger.info(f'Player 1 won the fight')
                        await interaction.channel.send('**PLAYER 1 WON THE FIGHT**')
                        await chain_responses.add_player_experience(gamemode,server, P1_username,P2_username,20,10)
                    fight_started = False
                    await chain_responses.set_chain_battle_start(server, fight_started)
                    await chain_responses.set_chain_counter(0,server,gamemode)

            else:
                await interaction.response.send_message("ACTION REGISTERED. WAITING FOR PLAYER 2", delete_after=0)
                embed = discord.Embed(title=f"Player 1 {interaction.user} Action Registered", description="Waiting for Player 2", color=discord.Color.blue())
                await interaction.channel.send(embed=embed)





            # elif chain_counter == 1 and p1_played==True: #Check if this is the first chain or 2nd chain
            #     action_player1  = action
            #     logger.info("FIRST CHAIN P1 REGISTERED. ADDING TO DB")
            #     p1_played = True
            #     await chain_responses.input_action(action_player1, server, gamemode, p1_played)
            #     logger.info("PLAYER 1 ACTION1 ADDED TO DB")
            #     response = await interaction.response.send_message("ACTION REGISTERED. WAITING FOR PLAYER 2", delete_after=0)
            #     embed = discord.Embed(title=f"Player 1 {interaction.user} Action Registered", description="Waiting for Player 2", color=discord.Color.blue())
            #     await interaction.channel.send(embed=embed)
            #     chain_counter = 1



            # #3RD ROUND PLAYER 1 ACTION2
            # elif chain_counter == 1:
            #     logger.info(f"CHAIN COUNTER = {chain_counter} ")
            #     second_action_player1  = action
            #     logger.info("SECOND CHAIN P1 REGISTERED. ADDING TO DB")
            #     p1_played = True
            #     player="Player 2"
            #     await chain_responses.input_action(player,second_action_player1, server, gamemode, p1_played)
            #     response = await interaction.response.send_message("SECOND ACTION REGISTERED. WAITING FOR PLAYER 2", delete_after=0)
            #     embed = discord.Embed(title=f"Player 1 {interaction.user} Action Registered", description="Waiting for Player 2", color=discord.Color.blue())
            #     await interaction.channel.send(embed=embed)
            #     chain_counter = 2




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
            try:
                player1_data = await chain_responses.get_control_p1(server, gamemode)
                chain_counter = player1_data['action count']
                control_player1 = player1_data['Fighter']
                action_player1 = player1_data['Player_action']
                chain_result = player1_data['fight_output']
                P1_username = player1_data['username']
                p1_played = player1_data['player_played']
            except Exception as e:
                print(e)
            player2_data = await chain_responses.get_control_p2(server, gamemode)
            control_player2 = player2_data["Fighter"]
            P2_username = player2_data["username"]
            action_player2 = action
            p2_played = True
            player="Player 2"
            await chain_responses.input_action(player, action_player2, server, gamemode, p2_played)
            logger.info("PLAYER 2 ACTION ADDED TO DB")
            
            #Check if this is the first chain or 2nd chain
            if p1_played == True and p2_played==True:
                response = await interaction.response.send_message("ACTION REGISTERED.", delete_after=0)
                embed = discord.Embed(title=f"Player 2 {interaction.user} Action Registered", description="Creating chain battle", color=discord.Color.blue())
                await interaction.channel.send(embed=embed)
                if chain_counter == 0:
                    logger.info(f"Making 1st round:    control_player1: {control_player1}    control_player2: {control_player2}")
                    try:
                        chain_result2 = await chain_responses.gpt3_chain_fight2(control_player1,control_player2,action_player1,action_player2,chain_result)
                        logger.info("1st round done")
                    except Exception as e:
                        logger.info(f"ACTION P2 FAILED. ERROR: {e}")
                        chain_result2 = await chain_responses.gpt3_chain_fight2(control_player1,control_player2,action_player1,action_player2,chain_result)

                    logger.info(f"CHAIN RESULT 2:            {chain_result2}")
                    await interaction.channel.send(chain_result2)
                    await chain_responses.input_chain_battle(chain_result2, server, gamemode)
                    chain_check_sentence = '.'.join(chain_result2.split('.')[-5:])
                    chain_check = await chain_responses.gpt3_fight_completed(chain_check_sentence)
                    if "2" in chain_check or "completed" in chain_check:
                        logger.info(f'CHAIN COMPLETED SUCCESSFULLY = {chain_check}')
                        await interaction.channel.send("**CHAIN BATTLE COMPLETED**")
                        fight_started = False
                        fight_decider = await chain_responses.gpt3_decider(chain_check_sentence, control_player1, control_player2)
                        if '2' in fight_decider:
                            logger.info(f'Player 2 won the fight')
                            await interaction.channel.send('**PLAYER 2 WON THE FIGHT**')
                            await chain_responses.add_player_experience(gamemode,server, P2_username,P1_username,20,10)
                        else:
                            logger.info(f'Player 1 won the fight')
                            await interaction.channel.send('**PLAYER 1 WON THE FIGHT**')
                            await chain_responses.add_player_experience(gamemode,server, P1_username,P2_username,20,10)
                        await chain_responses.set_chain_battle_start(server, fight_started)

                    #Chain battle ongoing
                    else:
                        logger.info(f'CHAIN INCOMPLETED= {chain_check}')
                        await interaction.channel.send("**INPUT NEXT ACTION**")
                        await chain_responses.set_chain_counter(1,server,gamemode)
                    p1_played = False
                    await chain_responses.set_p1_played(p1_played,server,gamemode)
                    await chain_responses.set_p2_played(p1_played,server,gamemode)


                elif chain_counter == 1:
                    logger.info(f"Making 2nd round:    control_player1: {control_player1}    control_player2: {control_player2}")
                    try:
                        chain_result3 = await chain_responses.gpt3_chain_fight3(control_player1,control_player2,action_player1,action_player2,chain_result)
                        logger.info("2nd round done")
                    except Exception as e:
                        logger.info(f"ACTION P2 FAILED. ERROR: {e}")
                        chain_result3 = await chain_responses.gpt3_chain_fight3(control_player1,control_player2,action_player1,action_player2,chain_result)
                    await interaction.channel.send(chain_result3)
                    await interaction.channel.send("**CHAIN BATTLE COMPLETED**")
                    chain_check_sentence = '.'.join(chain_result3.split('.')[-5:])
                    fight_decider = await chain_responses.gpt3_decider(chain_check_sentence, control_player1, control_player2)
                    if '2' in fight_decider:
                        logger.info(f'Player 2 won the fight')
                        await interaction.channel.send('**PLAYER 2 WON THE FIGHT**')
                        await chain_responses.add_player_experience(gamemode,server, P2_username,P1_username,20,10)
                    else:
                        logger.info(f'Player 1 won the fight')
                        await interaction.channel.send('**PLAYER 1 WON THE FIGHT**')
                        await chain_responses.add_player_experience(gamemode,server, P1_username,P2_username,20,10)
                    fight_started = False
                    await chain_responses.set_chain_battle_start(server, fight_started)
                    await chain_responses.set_chain_counter(0,server,gamemode)

            else:
                await interaction.response.send_message("ACTION REGISTERED. WAITING FOR PLAYER 2", delete_after=0)
                embed = discord.Embed(title=f"Player 2 {interaction.user} Action Registered", description="Waiting for Player 1", color=discord.Color.blue())
                await interaction.channel.send(embed=embed)
        return

    # async def chain_battle_fight():
    #     # logger.info(f"action_count: {action_count}")
    #     if action_count == 0:         #IF 0, that means action 1 player 1 missing
    #         await interaction.response.send_message("INPUT ACTION P1 FIRST")
    #         return
    #     elif action_count == 1:
    #         if p1_played == False:
    #             await interaction.response.send_message("INPUT ACTION P1 FIRST")
    #             return

    #         action_player2 = action
    #         logger.info("FIRST CHAIN P2 REGISTERED")
    #         try:
    #             logger.info(f"CHAIN BATTLE Player 1 {control_player1},{action_player1}") #Check if player 1 exists
    #             response = await interaction.response.send_message("ACTION REGISTERED.", delete_after=0)
    #             embed = discord.Embed(title=f"Player 2 {interaction.user} Action Registered", description="Creating chain battle", color=discord.Color.blue())
    #             await interaction.channel.send(embed=embed)
    #             p1_played = False
    #             await chain_responses.set_p1_played(p1_played,server,gamemode)
    #         except Exception as e:
    #             await interaction.response.send_message("WAITING FOR PLAYER 1")
    #             return

    #         try:
    #             logger.info("GETTING CONTROL P2")


    #             logger.info(f"Making 2nd round:    control_player1: {control_player1}    control_player2: {control_player2}")
    #             chain_result2 = await chain_responses.gpt3_chain_fight2(control_player1,control_player2,action_player1,action_player2,chain_result)
    #             logger.info("2nd round done")
    #             logger.info(f"CHAIN RESULT 2:            {chain_result2}")
    #             if chain_result2 == "NO NSFW OR PUBLIC FIGURES ALLOWED":
    #                 await interaction.channel.send("WARNING: NO NSFW OR PUBLIC FIGURES ALLOWED")
    #                 return
    #             await interaction.channel.send(chain_result2)
    #             await chain_responses.input_chain_battle(chain_result2, server, gamemode)

    #         #Check to see if chain battle is completed
    #             chain_result_check = chain_result2
    #             chain_result_list = chain_result_check.split('.')
    #             chain_result_list = chain_result_list[-5:]
    #             chain_check_sentence = '.'.join(chain_result_list)
    #             # logger.info("CHAIN CHECK SENTENCE\n",chain_check_sentence)
    #             chain_check = await chain_responses.gpt3_fight_completed(chain_check_sentence)
    #             chain_check = chain_check.lower()
    #             if "2" in chain_check or "completed" in chain_check:
    #                 logger.info(f'CHAIN COMPLETED SUCCESSFULLY = {chain_check}')
    #                 await interaction.channel.send("**CHAIN BATTLE COMPLETED**")

    #                 fight_started = False
    #                 # Decide fight winner
    #                 control_player1_text = re.sub('[^a-zA-Z ]+',' ', control_player1)
    #                 control_player2_text = re.sub('[^a-zA-Z ]+',' ', control_player2)
    #                 fight_decider = await chain_responses.gpt3_decider(chain_check_sentence, control_player1_text, control_player2_text)
    #                 # logger.info(fight_decider)
    #                 if '2' in fight_decider:
    #                     logger.info(f'Player 2 won the fight')
    #                     await interaction.channel.send('**PLAYER 2 WON THE FIGHT**')
    #                     await chain_responses.add_player_experience(gamemode,server, P2_username,P1_username,20,10)

    #                 else:
    #                     logger.info(f'Player 1 won the fight')
    #                     await interaction.channel.send('**PLAYER 1 WON THE FIGHT**')
    #                     await chain_responses.add_player_experience(gamemode,server, P1_username,P2_username,20,10)



    #                 await chain_responses.set_chain_battle_start(server, fight_started)
    #                 await chain_responses.set_chain_counter(0,server,gamemode)

    #             else:
    #                 logger.info(f'CHAIN INCOMPLETED= {chain_check}')
    #                 await interaction.channel.send("**INPUT NEXT ACTION**")
    #         except Exception as e:
    #             logger.error(e)
    #             await interaction.channel.send(e)


    # #3RD ROUND PLAYER 2 ACTION2
    #     elif action_count == 2:
    #         logger.info("round 2")
    #         second_action_player2 = action
    #         player2_data = await chain_responses.get_control_p2(server, gamemode)
    #         control_player2 = player2_data["Fighter"]
    #         P2_username = player2_data["username"]
    #         logger.info(f"Making 2nd round:    control_player1: {control_player1}    control_player2: {control_player2}")

    #         # logger.info(control_player2,second_action_player2 )
    #         logger.info("FIRST CHAIN P2 REGISTERED")
    #         response = await interaction.response.send_message("PLAYER 2 SECOND ACTION REGISTERED", delete_after=0)
    #         embed = discord.Embed(title=f"Player 2 {interaction.user} Action Registered", description="Creating chain battle", color=discord.Color.blue())
    #         await interaction.channel.send(embed=embed)
    #         try:
    #             logger.info(f"Check if player 1 second action exists: {control_player1}, {action_player1}") #Check if player 1 exists
    #         except Exception as e:
    #             await interaction.channel.send("WAITING FOR PLAYER 1")
    #             return

    #         try:
    #             # logger.info(chain_result)
    #             chain_result3 = await chain_responses.gpt3_chain_fight3(control_player1,control_player2,action_player1,second_action_player2,chain_result)
    #             if chain_result3 == "NO NSFW OR PUBLIC FIGURES ALLOWED":
    #                 await interaction.channel.send("WARNING: NO NSFW OR PUBLIC FIGURES ALLOWED")
    #                 return
    #             await interaction.channel.send(chain_result3)

    #             #Check to see if chain battle is completed
    #             chain_result_check = chain_result3
    #             chain_result_list = chain_result_check.split('.')
    #             chain_result_list = chain_result_list[-4:]
    #             chain_check_sentence = '.'.join(chain_result_list)
    #             # logger.info("CHAIN CHECK SENTENCE\n",chain_check_sentence)
    #             fight_started = False
    #             # logger.info(f'CHAIN COMPLETED SUCCESSFULLY = {chain_check_sentence}')
    #             await interaction.channel.send("**CHAIN BATTLE COMPLETED**")

    #             # Decide fight winner
    #             control_player1_text = re.sub('[^a-zA-Z ]+',' ', control_player1)
    #             control_player2_text = re.sub('[^a-zA-Z ]+',' ', control_player2)
    #             fight_decider2 = await chain_responses.gpt3_decider(chain_check_sentence, control_player1_text, control_player2_text)
    #             logger.info(fight_decider2)
    #             if '2' in fight_decider2:
    #                 logger.info(f'Player 2 won the fight')
    #                 await interaction.channel.send('**PLAYER 2 WON THE FIGHT**')
    #                 await chain_responses.add_player_experience(gamemode,server, P2_username,P1_username,20,10)
    #             else:
    #                 logger.info(f'Player 1 won the fight')
    #                 await interaction.channel.send('**PLAYER 1 WON THE FIGHT**')
    #                 await chain_responses.add_player_experience(gamemode,server, P1_username,P2_username,20,10)

    #             await chain_responses.set_chain_counter(0,server,gamemode)
    #             await chain_responses.set_chain_battle_start(server, fight_started)

    #         except Exception as e:
    #             logger.info(e)
    #             await interaction.channel.send(e)

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
            await chain_responses.set_p2_played(p1_played,server,gamemode)
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
