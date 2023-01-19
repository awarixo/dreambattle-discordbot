import requests
import asyncio
import os
import chain_responses
import discord
from discord import app_commands
from discord.ext import commands



class Chain(commands.Cog):
    def __init__(self, bot: commands.Bot):        #Initialize your chain class instance
        self.bot = bot


    @commands.command()
    async def sync(self,ctx):
        synced = await ctx.bot.tree.sync(guild = ctx.guild)
        print(f'Synced {len(synced)} commands')


    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            synced = await self.bot.tree.sync(guild = guild)
            print(f'Synced {len(synced)} commands for guild {guild.name}')
            print(f'Chain Cog is loaded')
    

    global chain_counter
    global fight_started
    fight_started = False
    chain_counter = 0 #Check if this is the first chain or 2nd chain


    # #Check to see if chain battle is completed
    # async def fight_completed(output):
    #     chain_result_check = output 
    #     chain_result_list = chain_result_check.split('.')
    #     chain_result_list = chain_result_list[-4:]
    #     chain_check_sentence = '.'.join(chain_result2_list)
    #     print("CHAIN CHECK SENTENCE\n",chain_check_sentence)
    #     chain_check = await chain_responses.gpt3_fight_completed(chain_check_sentence)
    #     chain_check = chain_check.lower()
    #     if ("completed" or "2") in chain_check:
    #         chain_counter = 0
    #         control_player1 = 0
    #         control_player2 = 0
    #         print(f'CHAIN COMPLETED SUCCESSFULLY = {chain_check}')
    #         await interaction.channel.send("CHAIN BATTLE COMPLETED")
    #         fight_started = False
    #         fight_decider = await chain_responses.gpt3_decider(chain_check_sentence, control_player1, control_player2)
    #         print(fight_decider)
    #         if '2' in fight_decider:
    #             print(f'Player 2 won the fight')
    #             await interaction.channel.send('PLAYER 2 WON THE FIGHT')
    #         else:
    #             print(f'Player 1 won the fight')
    #             await interaction.channel.send('PLAYER 1 WON THE FIGHT')

    #     else:
    #         chain_counter = 1
    #         print(f'CHAIN INCOMPLETED= {chain_check}')
    #         await interaction.channel.send("INPUT NEXT ACTION")
    #     return chain_counter


    #1ST ROUND CREATE PLAYER 1
    @app_commands.command(name="controlp1", description="Control player 1")
    @app_commands.describe(fighter = "Create your fighter")
    async def controlp1(self, interaction: discord.Interaction, *, fighter:str):
        global control_player1, p1_username, fight_started

        if fight_started == True:
            await interaction.response.send_message("CHAIN BATTLE ONGOING. USE /ACTION TO INPUT ACTIONS")
            return
        control_player1 = fighter
        p1_username = interaction.user
        print(f'Control mode P1: {p1_username} , {control_player1}')
        await interaction.response.send_message("CONTROL GAMEMODE STARTED. WAITING FOR PLAYER 2")


    #1ST ROUND CREATE PLAYER 2
    @app_commands.command(name="controlp2", description="Control player 2")
    @app_commands.describe(fighter = "Create your fighter")
    async def controlp2(self, interaction:discord.Interaction , *, fighter:str):
        global control_player1, control_player2, p2_username, chain_result, fight_started
        if fight_started == True:
            await interaction.response.send_message("CHAIN BATTLE ONGOING. USE /ACTION TO INPUT ACTIONS")
            return
        try:
            print(control_player1)
            if control_player1 == 0:
                await interaction.response.send_message("CREATE PLAYER 1 FIRST")
                return
        except Exception as e:
            await interaction.response.send_message("CREATE PLAYER 1 FIRST")
            return
       
        control_player2 = fighter
        p2_username = interaction.user
        print(f'Control mode P2: {p2_username} , {control_player2}')
        await interaction.response.send_message(f"FIGHTER REGISTERED")
        await interaction.channel.send(f"CREATING FIGHTERS")
        fight_started = True

        try:
            chain_result = await chain_responses.chain_message_handler(p1_username,p2_username,control_player1,control_player2)
            if chain_result == "NO NSFW OR PUBLIC FIGURES ALLOWED":
                await interaction.followup.send("WARNING: NO NSFW OR PUBLIC FIGURES ALLOWED")
                return
            await interaction.channel.send(f"`PLAYER 1:{control_player1}`")
            await interaction.channel.send(file=discord.File('chain_p1.jpg'))
            await interaction.channel.send(f"`PLAYER 2:{control_player2}`")
            await interaction.channel.send(file=discord.File('chain_p2.jpg'))
            await interaction.channel.send(chain_result)
        except Exception as e:
            print(e)

    #2ND ROUND PLAYER 1 ACTION1
    @app_commands.command(name="actionp1", description="player 1 action")
    @app_commands.describe(action = "Input Fighter action")
    async def actionp1(self, interaction:discord.Interaction, *, action:str):
        global control_player1, control_player2, chain_counter, action_player1, second_action_player1, chain_result
        try:
            print("check if player 1 exists: ",control_player1) #check if player 1 exists
        except Exception as e:
            await interaction.response.send_message("CREATE PLAYER 1 FIRST", ephemeral=True )
            return
        if chain_counter == 0: #Check if this is the first chain or 2nd chain
            action_player1  = action
            print("FIRST CHAIN P1 REGISTERED")
            await interaction.response.send_message("ACTION REGISTERED. WAITING FOR PLAYER 2")

        #3RD ROUND PLAYER 1 ACTION2
        else:
            print("CHAIN COUNTER = ",chain_counter)
            second_action_player1  = action
            print(f'3RD ROUND PLAYER 1 ACTION2:{control_player1}, {second_action_player1}')
            await interaction.response.send_message("SECOND ACTION REGISTERED. WAITING FOR PLAYER 2")


    #2ND ROUND PLAYER 2 ACTION1
    @app_commands.command(name = "actionp2", description="player 2 action")
    @app_commands.describe(action = "Input Fighter action")
    async def actionp2(self, interaction:discord.Interaction, *, action:str):
        global control_player1, control_player2, chain_counter, action_player1, second_action_player1, action_player2, chain_result,chain_result2, fight_started
        try:
            print("Check if player 2 exists: ",control_player2) #Check if player 2 exists
        except Exception as e:
            await interaction.response.send_message("CREATE PLAYER 2 FIRST")
            return
        try: 
            print("Check if action 1 exists: ", action_player1) #Check if action 1 exists
            if action_player1 == 0:
                return
        except Exception as e:
            await interaction.response.send_message("INPUT ACTION P1 FIRST")
            return
        if chain_counter == 0: #Check if this is the first chain or 2nd chain
            action_player2 = action
            print("FIRST CHAIN P2 REGISTERED")
            try:
                print("Player 1",control_player1,action_player1) #Check if player 1 exists
                await interaction.response.send_message("ACTION REGISTERED.")
            except Exception as e:
                await interaction.response.send_message("WAITING FOR PLAYER 1")
                return

            try:
                print("CHAIN COUNTER = ",chain_counter)
                print("Making 2nd round")
                chain_result2 = await chain_responses.gpt3_chain_fight2(control_player1,control_player2,action_player1,action_player2,chain_result)
                print("2nd round done")
                print("CHAIN RESULT 2",chain_result2)
                if chain_result2 == "NO NSFW OR PUBLIC FIGURES ALLOWED":
                    await interaction.channel.send("WARNING: NO NSFW OR PUBLIC FIGURES ALLOWED")
                    return
                await interaction.channel.send(chain_result2)
                # action_player1 = 0 #To reset player 1 action

                #Check to see if chain battle is completed
                chain_result_check = chain_result2 
                chain_result_list = chain_result_check.split('.')
                chain_result_list = chain_result_list[-4:]
                chain_check_sentence = '.'.join(chain_result_list)
                print("CHAIN CHECK SENTENCE\n",chain_check_sentence)
                chain_check = await chain_responses.gpt3_fight_completed(chain_check_sentence)
                chain_check = chain_check.lower()
                if ("completed" or "2") in chain_check:
                    chain_counter = 0
                    control_player1 = 0
                    control_player2 = 0
                    print(f'CHAIN COMPLETED SUCCESSFULLY = {chain_check}')
                    await interaction.channel.send("CHAIN BATTLE COMPLETED")
                    fight_started = False
                    fight_decider = await chain_responses.gpt3_decider(chain_check_sentence, control_player1, control_player2)
                    print(fight_decider)
                    if '2' in fight_decider:
                        print(f'Player 2 won the fight')
                        await interaction.channel.send('PLAYER 2 WON THE FIGHT')
                    else:
                        print(f'Player 1 won the fight')
                        await interaction.channel.send('PLAYER 1 WON THE FIGHT')

                else:
                    chain_counter = 1
                    print(f'CHAIN INCOMPLETED= {chain_check}')
                    await interaction.channel.send("INPUT NEXT ACTION")
            except Exception as e:
                print(e)
                await interaction.channel.send(e)


        #3RD ROUND PLAYER 2 ACTION2
        else:       
            print("round 2")
            second_action_player2 = action
            print(control_player2,second_action_player2 )
            print("FIRST CHAIN P2 REGISTERED")
            await interaction.response.send_message("PLAYER 2 SECOND ACTION REGISTERED")
            await interaction.channel.send("CREATING CHAIN BATTLE.")
            try:
                print("Check if player 1 second action exists: ",control_player1,second_action_player1) #Check if player 1 exists
            except Exception as e:
                await interaction.channel.send("WAITING FOR PLAYER 1")
                return
            
            try:
                print(chain_result2)
                chain_result3 = await chain_responses.gpt3_chain_fight3(control_player1,control_player2,second_action_player1,second_action_player2,chain_result2)
                if chain_result3 == "NO NSFW OR PUBLIC FIGURES ALLOWED":
                    await interaction.channel.send("WARNING: NO NSFW OR PUBLIC FIGURES ALLOWED")
                    return
                await interaction.channel.send(chain_result3)

                #Check to see if chain battle is completed
                chain_result_check = chain_result3 
                chain_result_list = chain_result_check.split('.')
                chain_result_list = chain_result_list[-4:]
                chain_check_sentence = '.'.join(chain_result_list)
                print("CHAIN CHECK SENTENCE\n",chain_check_sentence)
                fight_started = False
                chain_counter = 0
                control_player1 = 0
                control_player2 = 0
                print(f'CHAIN COMPLETED SUCCESSFULLY = {chain_check_sentence}')
                await interaction.channel.send("CHAIN BATTLE COMPLETED")
                fight_decider = await chain_responses.gpt3_decider(chain_check_sentence, control_player1, control_player2)
                print(fight_decider)
                if '2' in fight_decider:
                    print(f'Player 2 won the fight')
                    await interaction.channel.send('PLAYER 2 WON THE FIGHT')
                else:
                    print(f'Player 1 won the fight')
                    await interaction.channel.send('PLAYER 1 WON THE FIGHT')
            except Exception as e:
                print(e)
                await interaction.channel.send(e)
            return

    

async def setup(bot):       #Command to add cog to bot
    await bot.add_cog(Chain(bot), guilds=[discord.Object(id=1047862232987484190)])
