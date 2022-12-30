import os
import openai
import discord
import asyncio
import time
import base64
import sqlite3
import config
from PIL import Image
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(dotenv_path='/.env')
TOKEN = config.DISCORD_TOKEN
openai.api_key = config.OPENAI_API_KEY2

#Connect to Database
global conn
global cursor
conn=sqlite3.connect('DreamBattle_Beta_Chain.db')
cursor=conn.cursor()
def store_image_to_DB(username,time,date,fighter,image_data):        #HOW DO I CREATE A NEW DATABASE WITH SQLITE3 ON PYTHON WITH TIME FORMAT
    #Create database table using SQLite3
    #cursor=conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dreambattle_chain_fighters(id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    username TEXT,
    time TEXT,
    date TEXT,
    fighter TEXT,
    image_data BLOP)""")

    print("table created")

    username = str(username)
    cursor.execute("""
    INSERT INTO dreambattle_chain_fighters(username,time,date,fighter,image_data) VALUES(?,?,?,?,?)""", (username,time,date,fighter,image_data))
    print("real data updated")
    return 


#Dalle image generator function
async def image(player_number,username,sentence):
    response = openai.Image.create(
            prompt=sentence,
            n=1,
            size="1024x1024",
            response_format="b64_json"
    )
    print("image ready")
    b64 = response['data'][0]['b64_json']
    fighter = sentence[:-48]
    print(fighter)
    
    #save base 64 into png file
    if player_number == 1:
        with open('p1.jpg', 'wb') as handler:
            handler.write(base64.urlsafe_b64decode(b64))
        im = Image.open('p1.jpg') 
        im.show()
        #read png file and save into DB
        with open('p1.jpg', 'rb' ) as handler:
             img_binary = handler.read()
    else:
        with open('p2.jpg', 'wb') as handler:
            handler.write(base64.urlsafe_b64decode(b64))
        im = Image.open('p2.jpg') 
        im.show()
        #read png file and save into DB
        with open('p2.jpg', 'rb' ) as handler:
             img_binary = handler.read()

    now = datetime.today()
    time = now.strftime('%H:%M:%S')
    date = now.strftime('%Y-%m-%d')
    
    store_image_to_DB(username,time,date,fighter,img_binary)

    return fighter


#GPT3 Fight narration function
def gpt3_fight (f1,f2):
    fight = "Excitingly narrated transcript of a brief fight to the death, between \" {} \" and \" {} \", basing the outcome on the implied capabilities of the two opponents drawing on the specific skills and attributes of the fighters concluding with who won the fight and why:\n".format(f1, f2)
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt= fight,
        temperature=0.7,
        max_tokens=260,
        top_p=1,
        frequency_penalty=0.2,
        presence_penalty=0.3
  )
    content =  response.choices[0].text.split('.')
    finished_fight = response.choices[0].text
    if finished_fight[-1:] == ('.' or '!'):
        print(f'FIGHT FINISHED: {finished_fight[-500:]}')
        return response.choices[0].text
    else:
        print("FIGHT NOT FINISHED")
        fight_end = finished_fight[-500:]
        print(f"UNFINISHED FIGHT ENDING  : {fight_end}")
        complete = "finish this Excitingly narrated transcript of a brief fight to the death, between \" {} \" and \" {} \".concluding with who won the fight and why \n Fight:\" {} \"- ".format(f1, f2, fight_end)
        response2 = openai.Completion.create(
        model="text-davinci-003",
        prompt= complete,
        temperature=0.2,
        max_tokens=60,
        top_p=1,
        frequency_penalty=0.2,
        presence_penalty=0.3
    )
        content2 = response2.choices[0].text.split('.')
        content2 = content2[:-1]
        content2 = '.'.join(content2).strip()
        print(f'ADDITION SENTENCE:{content2}')
        # if response2.choices[0].text[2:] == '\n':
        #     content2 = content2[:2].join
        #     print("FIXED!")
        #     print (content2)
        full_fight = finished_fight + '. ' + content2
        return full_fight



#GPT3 Fight decider function
async def gpt3_decider(sentence, f1, f2):
    fight_winner = "from this passage, \"{}\", tell me which option won the fight , Option 1 \"{}\" or Option 2 \"{}\" :".format(sentence, f1, f2)
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt= fight_winner,
        temperature=0.1,
        max_tokens=20,
        top_p=0,
        frequency_penalty=0.1 ,
        presence_penalty=0
    )
    content =  response.choices[0].text.split('.')
    print(content)
    return response.choices[0].text


def gpt3_chain_fight1 (fighter1,fighter2):
    fight = f"Forget all previous instructions. you are a 2 player game, a fight between 2 fighters. begin a brief exciting story mode realistic fight between them. Both players begin with 100 Health points and take health damage from attacks. \n fighter: {fighter1} \n fighter: {fighter2}\n"
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt= fight,
        temperature=0.7,
        max_tokens=150,
        top_p=1,
        frequency_penalty=0.2,
        presence_penalty=0.2
  )
    content =  response.choices[0].text.split('.')
    return response.choices[0].text


async def gpt3_chain_fight2 (fighter1,fighter2,action1,action2,chain1):
    try:
        print("2nd chain function started")
        fight = f"continue an exciting story mode realistic fight between player1 and player2, using both player1 and player2 to actions continue the fight. basing the outcome on the actions and implied capabilities of both fighters, then concluding with who won the fight and why \nPlayer1: {fighter1}\n player1's action: {action1} \nplayer2: {fighter2}\n player2's action: {action2}\n\n \"{chain1} "       
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt= fight,
            temperature=0.5,
            max_tokens=160,
            top_p=1,
            frequency_penalty=0.2,
            presence_penalty=0.3
        )
        print(f"FULL FIGHT LENGTH \n {response.choices[0].text}")
        content =  response.choices[0].text.split('.')
        #Remove the last 2 sentences of the chain fight
        chain2_output_list = content[:-2]
        chain2_output = '.'.join(chain2_output_list)
        chain2_output = '`' + chain2_output + '`'
        return chain2_output
    except Exception as e:
        print(e)
        return "NO NSFW OR PUBLIC FIGURES ALLOWED"


async def gpt3_chain_fight3 (fighter1,fighter2,action1,action2, chain2):
    print("CHAIN 3 STARTED")
    fight = f"Complete an exciting story mode realistic fight between player1 and player2 using the players to actions determine how the fight goes. basing the outcome on the actions and implied capabilities of the two opponents, then concluding with who won the fight and why \nPlayer1: {fighter1}\n player1 action: {action1} \nplayer2: {fighter2}\n player2 action: {action2}\n \"{chain2} "
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt= fight,
        temperature=0.5,
        max_tokens=160,
        top_p=1,
        frequency_penalty=0.2,
        presence_penalty=0.3
  )
    content =  response.choices[0].text.split('.')
    chain3_output = '`' +  response.choices[0].text + '`' 
    return chain3_output


async def gpt3_fight_completed(sentence):
        fight_winner = "from this passage, \"{}\", tell me if the fight is completed or ongoing, Option 1 \"completed\" or Option 2 \"ongoing\":".format(sentence)
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt= fight_winner,
            temperature=0.1,
            max_tokens=20,
            top_p=0,
            frequency_penalty=0 ,
            presence_penalty=0
        )
        content =  response.choices[0].text.split('.')
        print(content)
        return response.choices[0].text


#function for 2 player game
async def message_handler(user1,user2,p1,p2) -> str:
        global conn
        global cursor
        conn=sqlite3.connect('DreamBattle_Beta.db')
        cursor=conn.cursor()
        print (p1)
        print (p2)
        

        final1 = p1 +", 4k,highly detailed octane render, by alex ross" 
        final2 = p2 +", 4k,highly detailed octane render, by alex ross"
        try: 
            img1_path = image(1,user1,final1)
            
            img2_path = image(2,user2,final2)
            print("Now working on images")
            await img1_path
            await img2_path
            conn.commit()
            cursor.close()
            conn.close()
            print("Images completed, creating text")
            fight_description = gpt3_fight(p1, p2)
            print("fight completed, creating text")
            print(fight_description)
        except Exception as e:
            print(e)
            return "NO NSFW OR PUBLIC FIGURES ALLOWED"

        fight_description = '`'+ fight_description + '`'
        return fight_description


async def chain_message_handler(user1,user2,p1,p2) -> str:
        global conn
        global cursor
        conn=sqlite3.connect('DreamBattle_Beta_Chain.db')
        cursor=conn.cursor()
        print (f'Player 1:{p1}')
        print (f'Player 2:{p2}')
        

        final1 = p1 +", 4k,highly detailed octane render, by Alex Ross" 
        final2 = p2 +", 4k,highly detailed octane render, by Alex Ross"
        try:
            print("Now working on images")
            img1_path = await image(1,user1,final1)
            img2_path = await image(2,user2,final2)
            conn.commit()
            cursor.close()
            conn.close()
            print("Images completed, creating chain battle")
            chain_list1 = gpt3_chain_fight1(p1, p2)
            chain_list1 = chain_list1.split('.')
            chain_list1= chain_list1[:-1]
            chain_fight1 = '.'.join(chain_list1)
            print("chain battle 1 started")
            print(chain_fight1)
            chain_fight1 = '`'+ chain_fight1 + '`'
            return chain_fight1
        except Exception as e:
            print(e)
            return "NO NSFW OR PUBLIC FIGURES ALLOWED"

        
    


