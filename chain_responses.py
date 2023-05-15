import os
import openai
import discord
import asyncio
import time
import base64
import json
import pyrebase
import re
import requests
import loggerSettings
import concurrent.futures
from threading import Thread
from PIL import Image, ImageFont, ImageDraw, ImageEnhance

from datetime import datetime
from dotenv import load_dotenv

#Environment variables
load_dotenv(dotenv_path='/.env')
FIREBASE_APIKEY = os.getenv("FIREBASE_APIKEY")


logger = loggerSettings.logging.getLogger("discord")

# logging.basicConfig(filename='battlebot.log',format='%(asctime)s %(levelname)s: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logger.info)
TOKEN = os.getenv("DISCORD_TOKEN")
openai.api_key = os.getenv("OPENAI_YUSUF_KEY")
FIREBASE_AUTH_EMAIL = os.getenv("FIREBASE_AUTH_EMAIL")
FIREBASE_AUTH_PASSWORD = os.getenv("FIREBASE_AUTH_PASSWORD")
FIREBASE_SERVICE_ACCOUNT = os.getenv("FIREBASE_SERVICE_ACCOUNT")
FIREBASE_PRIVATE_KEY = os.getenv("FIREBASE_PRIVATE_KEY")


# #Firestore configuration
# FIRESTORE_PRIVATE_KEY = os.getenv("FIRESTORE_PRIVATE_KEY")
# FIRESTORE_KEY_ID = os.getenv("FIRESTORE_KEY_ID")

# firestore_config = {
#   "type": "service_account",
#   "project_id": "dreambattlebeta",
#   "private_key_id": FIRESTORE_KEY_ID,
#   "private_key": FIRESTORE_PRIVATE_KEY,
#   "client_email": "firebase-adminsdk-3qx63@dreambattlebeta.iam.gserviceaccount.com",
#   "client_id": "117095672579436770582",
#   "auth_uri": "https://accounts.google.com/o/oauth2/auth",
#   "token_uri": "https://oauth2.googleapis.com/token",
#   "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
#   "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-3qx63%40dreambattlebeta.iam.gserviceaccount.com"

# }

# #Firebase admin setup
# cred = credentials.Certificate(firestore_config)
# firebase_admin.initialize_app(cred)
# #db = firestore.client()


#Firebase database configuration
firebaseConfig = {
  "apiKey": FIREBASE_APIKEY,
  "authDomain": "dreambattlebeta.firebaseapp.com",
  "projectId": "dreambattlebeta",
  "databaseURL": "https://dreambattlebeta-default-rtdb.asia-southeast1.firebasedatabase.app",
  "storageBucket": "dreambattlebeta.appspot.com",
  "messagingSenderId": "1019723627495",
  "appId": "1:1019723627495:web:f4cd87c1a5b5f4095fdb42",
  "measurementId": "G-3NH8RLQV7V",
  "serviceAccount": "dreambattlebeta-firebase-adminsdk-3qx63-979ca29af4.json",
}

#Connect to Database
firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()
database = firebase.database()
storage = firebase.storage()
user = auth.sign_in_with_email_and_password(FIREBASE_AUTH_EMAIL, FIREBASE_AUTH_PASSWORD)
access_token = user['idToken']


#-----------------CHAIN BATTLE--------------------------------
async def set_chain_battle_start(server, setting):
    read_status = {f"Chain Battle Started": setting}
    database.child("servers").child(server).child("status").update(read_status)
    return

async def check_chain_battle_start(server):
    read_status = database.child("servers").child(server).child("status").get().val()
    # status =list(read_status)[0]
    logger.info(f"READ STATUS:    {read_status}")
    check_status = read_status["Chain Battle Started"]
    logger.info(f"fight_started: {check_status}")
    return check_status

async def set_chain_counter(fight_number,server,gamemode):
    logger.info("Setting player action 1 in DB")
    data = {"action count":fight_number}
    player1_data = database.child("servers").child(server).child(gamemode).child("Player 1").update(data)

async def check_chain_counter(server,gamemode):
    read_status = database.child("servers").child(server).child(gamemode).child("Player 1").get().val()
    # status =list(read_status)[0]                                                                                                                              
    logger.info(f"READ STATUS:    {read_status}")
    action_count = read_status["action count"]
    logger.info(f"action count: {action_count}")
    return action_count

# async def check_p1_played(server,gamemode):
#     read_status = database.child("servers").child(server).child(gamemode).child("Player 1").get(user['idToken']).val()
#     # status =list(read_status)[0]                                                                                                                              
#     logger.info(f"READ STATUS:    {read_status}")
#     p1_played = read_status["p1_played"]
#     logger.info(f"p1_played: {p1_played}")
#     return p1_played
async def set_p1_played(p1_played,server,gamemode):
    # logger.info("Setting p1_played in DB")
    data = {"p1_played":p1_played}
    player1_data = database.child("servers").child(server).child(gamemode).child("Player 1").update(data)

async def input_action(fight_number, P1_action, server, gamemode,p1_played):
    data = {"P1_action":P1_action, "action count":fight_number, "p1_played": p1_played}
    player1_data = database.child("servers").child(server).child(gamemode).child("Player 1").update(data)

async def input_chain_battle(fight_output, server, gamemode):
    data = {"fight_output":fight_output}
    player1_data = database.child("servers").child(server).child(gamemode).child("Player 1").update(data)


async def get_control_p1(server,gamemode):
    logger.info("Getting control player 1 from DB")
    player1_data = database.child("servers").child(server).child(gamemode).child("Player 1").get().val()    
    return player1_data

async def get_control_p2(server,gamemode):
    logger.info("Getting control player 2 from DB")
    player2_data = database.child("servers").child(server).child(gamemode).child("Player 2").get().val()    
    return player2_data

    # player2_fighters = list(player2_data.keys())
    # logger.info(f"player2_data:       {player2_fighters}")
    # logger.info(player2_fighters)
    # control_p2 = player2_fighters[0]
    # return control_p2

async def set_control_p2(server,username,gamemode,fighter):
    logger.info("Storing player 2 in DB")
    # username = str(re.sub(r"#", "-", username))
    data = {"username":f"{username}","Fighter":f"{fighter}", "Gamemode":f"{gamemode}"}
    database.child("servers").child(server).child(gamemode).child("Player 2").update(data)
    return


#########################Adding Timestamps#####################

# async def update_fighters_timestamps(username, gamemode):
#     fighters_data = database.child("fighters").child(username).child(gamemode).get().val()
#     print("updating timestamps")
#     if fighters_data is None:
#         print("No data found for fighters")
#         return
    
#     for fighter_id, fighter_data in fighters_data.items():
#         # Get the date and time strings from the fighter data
#         date_str = fighter_data.get("Date")
#         time_str = fighter_data.get("Time")
        
#         # If either of the date or time strings are missing, skip this fighter
#         if not date_str or not time_str:
#             print(f"Skipping fighter {fighter_id} due to missing date or time data")
#             continue
        
#         # Parse the date and time strings into datetime objects
#         date_obj = datetime.strptime(date_str, "%Y-%m-%d")
#         time_obj = datetime.strptime(time_str, "%H:%M:%S")
        
#         # Combine the date and time objects into a single datetime object
#         timestamp_obj = datetime.combine(date_obj.date(), time_obj.time())
        
#         # Convert the timestamp datetime object into a string for storage in the database
#         timestamp_str = timestamp_obj.isoformat()
        
#         # Update the fighter data in the database with the new timestamp value
#         database.child("fighters").child(username).child(gamemode).child(fighter_id).update({"timestamp": timestamp_str})
        
#         print(f"Updated fighter {fighter_id} with timestamp {timestamp_str}")

#----------------------LEVELING SYSTEM--------------------------------------
async def add_player_experience(winner,loser,xp1,xp2):
    winner_data = dict(database.child("users").child(winner).get().val().items())
    loser_data = dict(database.child("users").child(loser).get().val().items())

    winner_xp = winner_data ["experience"]
    loser_xp = loser_data ["experience"]

    winner_xp += xp1
    winner_level_counter, winner_player_xp, winner_new_level_xp  = add_player_level(winner_xp)
    loser_xp += xp2
    loser_level_counter, loser_player_xp, loser_new_level_xp  = add_player_level(loser_xp)

    loser_updated = {"experience": loser_xp, "level": loser_level_counter}
    winner_updated = {"experience": winner_xp, "level": winner_level_counter}
    database.child("users").child(loser).update(loser_updated)
    database.child("users").child(winner).update(winner_updated)



def add_player_level(player_xp):
    #Level requirements increase by 25XP. lvl1 = 50. lvl2 = 75. lvl3 = 100
    level_counter = 0
    new_level_xp = 50
    first_level_xp = 50
    while player_xp >= new_level_xp:
        print(f"Level: {level_counter}.playerXP: {player_xp}.required next level xp: {new_level_xp}")
        player_xp -= new_level_xp
        level_counter +=1
        new_level_xp = first_level_xp + (level_counter)*25
    print(f"Final Level: {level_counter}.playerXP: {player_xp}.required next level xp: {new_level_xp}")

    return level_counter, player_xp, new_level_xp 
    
    


#----------------------USER STATS CHECKS------------------------------------
async def get_user_stats(username):
    users = database.child("users").get().val()
    users_list = dict(users.items())
    user_data = users_list[username]
    user_experience, user_level, user_token, user_status = user_data["experience"], user_data["level"], user_data["tokens"], user_data["status"]
    return user_data["experience"], user_data["level"], user_data["tokens"], user_data["status"]

async def get_player_list(username,gamemode):
    fighters = database.child("fighters").child(username).child(gamemode).order_by_child("timestamp").get().val()
    game_data = dict(fighters.items())
    game_fighters = list(game_data.keys())
    game_fighters.reverse()

    print(f"{username} {gamemode} fighters: {game_fighters}")
    return game_fighters

def create_fighter_list(chain_list, current_page):
            fighters_str = ""
            start_index = (current_page - 1) * 10
            end_index = current_page * 10 

            for i, fighter in enumerate(chain_list[start_index:end_index], start=start_index+1):
                fighters_str += f"{i}. {fighter}\n"
            return fighters_str

# async def drawProgressBar(x, y, w, h, progress, bg="black", fg="green"):
#     out = Image.new("RGB", (125, 25), (255, 255, 255))
#     d = ImageDraw.Draw(out)


#     # draw background
#     d.ellipse((x+w, y, x+h+w, y+h), fill=bg)
#     d.ellipse((x, y, x+h, y+h), fill=bg)
#     d.rectangle((x+(h/2), y, x+w+(h/2), y+h), fill=bg)

#     # draw progress bar
#     w *= progress
#     d.ellipse((x+w, y, x+h+w, y+h),fill=fg)
#     d.ellipse((x, y, x+h, y+h),fill=fg)
#     d.rectangle((x+(h/2), y, x+w+(h/2), y+h),fill=fg)
#     out.save("progressbar.jpg")


#     return d


##################################TOKENS & USERS CHECKS#######################################################
async def get_users_list():
    users = database.child("users").get().val()
    return users

async def check_player_exist(username,users):

    #Convert firebase users Odict response to a normal dict so we can get key value pairs
    users_keys = dict(users.items()).keys()

    # print(f"users: {users_keys}")
    # for user in users_keys:
    #     print(user)
    if username in users_keys:
        logger.info(f"{username} already registered in db")
        return True
    else:
        logger.info(f"{username} not registered in db")
        return False 

async def set_new_player(username, server):
    now = datetime.today()
    time = now.strftime('%H:%M:%S')
    date = now.strftime('%Y-%m-%d')
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    time_obj = datetime.strptime(time, "%H:%M:%S")
    
    # Combine the date and time objects into a single datetime object
    timestamp_obj = datetime.combine(date_obj.date(), time_obj.time())
    
    # Convert the timestamp datetime object into a string for storage in the database
    timestamp = timestamp_obj.isoformat()
    data = {"level":0, "experience":0,"tokens":5, "status":"Starter","server_created":server, "date_created":timestamp}
    database.child("users").child(username).update(data)

async def check_user_tokens(username,users):
    #Convert firebase users Odict response to a normal dict so we can get key value pairs
    users_data = dict(users.items())
    
    users_stats = users_data[username]
    logger.info(f"{username}'s stats: {users_stats}")
    user_tokens = users_stats["tokens"]
    # print(f"user_tokens: {user_tokens}")

    return user_tokens

async def deduct_token(username):
    user_data = database.child("users").child(username).get().val()
    user_token = user_data["tokens"] 
    updated_token = user_token - 1
    data = {"tokens": updated_token}
    database.child("users").child(username).update(data)
    return
   




#----------------------------GENERAL----------------------------------
async def get_p1_from_DB(server,gamemode):
    # logger.info("Getting player 1 in DB")
    player1_data = database.child("servers").child(server).child(gamemode).child("Player 1").get().val()    
    p1_username = player1_data["username"]
    p1_fighter = player1_data["Fighter"]
    logger.info(f"PLAYER 1 USERNAME:{p1_username} FIGHTER: {p1_fighter}")
    return p1_username, p1_fighter


async def store_p1_to_DB(server,username,gamemode,fighter):
    logger.info("Storing player 1 in DB")
    # username = str(re.sub(r"#", "-", username))
    data = {"username":f"{username}","Fighter":f"{fighter}", "Gamemode":f"{gamemode}"}

    database.child("servers").child(server).child(gamemode).child("Player 1").update(data)
    # logger.info(f"Setting Database {gamemode} read_status to true")
    read_status = {f"{gamemode}": True}
    database.child("servers").child(server).child("status").update(read_status)
    return


async def check_db_read_status(server,gamemode):
    data = database.child("servers").child(server).child("status").get()
    status_check = data.val()
    #logger.info("Status check data:   ",status_check)
    if gamemode == "Quick game":
        read_status= status_check['Quick game']
    else:
        read_status= status_check['Chain battle']
    return read_status


async def close_db_read_status(server,gamemode):
    if gamemode == "Quick game":
        read_status = {"Quick game": False}
        database.child("servers").child(server).child("status").update(read_status)
    else:
        read_status = {"Chain battle": False}
        database.child("servers").child(server).child("status").update(read_status)
    logger.info(f"{gamemode} READ STATUS CLOSED")
    return 


def store_image_to_DB(server,username,gamemode,time,date,fighter,imgURL):        #HOW DO I CREATE A NEW DATABASE WITH SQLITE3 ON PYTHON WITH TIME FORMAT
    # Parse the date and time strings into datetime objects
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    time_obj = datetime.strptime(time, "%H:%M:%S")
    
    # Combine the date and time objects into a single datetime object
    timestamp_obj = datetime.combine(date_obj.date(), time_obj.time())
    
    # Convert the timestamp datetime object into a string for storage in the database
    timestamp_str = timestamp_obj.isoformat()
    data = {"Time":time, "Date":date,"Server":f"{server}", "Fighter":f"{fighter}", "Gamemode":f"{gamemode}", "image_URL":imgURL, "timestamp": timestamp_str}

    # username = re.sub(r"#", "-", username)
    #logger.info(f"STORING {username}'S FIGHTER TO {server}")

    database.child("fighters").child(username).child(gamemode).child(fighter).update(data)
    logger.info(F"{username}---->{fighter}  DATA STORED IN DB")
    return 


#Dalle image generator function
def image(player_number,username,server,sentence):
    try:
        now = datetime.today()
        time = now.strftime('%H:%M:%S')
        date = now.strftime('%Y-%m-%d')
        username = str(username)
            # username = re.sub(r"#", "-", username)

        logger.info("IMAGE FUNCTION STARTED")
        response = openai.Image.create(
                prompt=sentence,
                n=1,
                size="1024x1024",
                response_format="b64_json"
        )
        b64 = response['data'][0]['b64_json']
        fighter = sentence[:-48]
        logger.info(f"image ready: {fighter}")
        

        #save base 64 into png file
        if player_number == 1:
            gamemode = "Quick game"
            with open('quick_p1.jpg', 'wb') as handler1:
                handler1.write(base64.urlsafe_b64decode(b64))
            im = Image.open('quick_p1.jpg') 

            # save image into firebase storage
            file1 = "quick_p1.jpg"
            # cloudfilename1 = f"{server}/{username}/{fighter}.png"
            cloudfilename1 = f"{username}/{gamemode}/{fighter}.png"
            logger.info(f"CLOUDFILENAME1:  {cloudfilename1}")
            try:
                store_image(cloudfilename1, file1)
            except Exception as e:
                logger.error(f"CLOUDFILENAME1 PUT FAILED, {e}")
            logger.info(f"CLOUDFILENAME1 STORED {cloudfilename1}")
            #get image url
            imgURL = storage.child(cloudfilename1).get_url(None)

        elif player_number == 2:
            gamemode = "Quick game"
            with open('quick_p2.jpg', 'wb') as handler2:
                handler2.write(base64.urlsafe_b64decode(b64))
            im = Image.open('quick_p2.jpg') 

            # save image into firebase storage
            file2 = "quick_p2.jpg"
            cloudfilename2 = f"{username}/{gamemode}/{fighter}.png"
            logger.info(f"CLOUDFILENAME2:  {cloudfilename2}")
            try:
                store_image(cloudfilename2, file2)
            except Exception as e:
                logger.error(f"CLOUDFILENAME2 PUT FAILED, {e}")
            logger.info(f"CLOUDFILENAME2 STORED {cloudfilename2}")
            #get image url
            imgURL = storage.child(cloudfilename2).get_url(None)


        elif player_number == 3:
            gamemode = "Chain battle"
            with open('chain_p1.jpg', 'wb') as handler3:
                handler3.write(base64.urlsafe_b64decode(b64))
            im = Image.open('chain_p1.jpg') 
            # save image into firebase storage
            file3 = 'chain_p1.jpg'
            cloudfilename3 = f"{username}/{gamemode}/{fighter}.png"
            logger.info(f"CLOUDFILENAME3:  {cloudfilename3}")
            try:
                store_image(cloudfilename3, file3)
            except Exception as e:
                logger.error(f"CLOUDFILENAME3 PUT FAILED, {e}")
            logger.info(f"CLOUDFILENAME3 STORED {cloudfilename3}")
            #get image url
            imgURL = storage.child(cloudfilename3).get_url(None)

        
        elif player_number == 4:
            gamemode = "Chain battle"
            with open('chain_p2.jpg', 'wb') as handler4:
                handler4.write(base64.urlsafe_b64decode(b64))
            im = Image.open('chain_p2.jpg') 
            # save image into firebase storage
            file4 = "chain_p2.jpg"
            cloudfilename4 = f"{username}/{gamemode}/{fighter}.png"
            logger.info(f"CLOUDFILENAME4:  {cloudfilename4}")
            try:
                store_image(cloudfilename4, file4)
            except Exception as e:
                logger.error(f"CLOUDFILENAME4 PUT FAILED, {e}")
            logger.info(f"CLOUDFILENAME4 STORED {cloudfilename4}")
            #get image url
            imgURL = storage.child(cloudfilename4).get_url(None)

        
        store_image_to_DB(server,username,gamemode,time,date,fighter,imgURL)

        return fighter
    except Exception as e:
        return e

#Firebase Store image
def store_image(cloudfilename, files):
    global access_token
    url = f"https://storage.googleapis.com/dreambattlebeta.appspot.com/o/?uploadType=multipart&name={cloudfilename}"
    headers = {
        "Content-Type": "image/png",
        "Authorization": f"Bearer {access_token}"
    }
    with open(files, "rb") as f:
        storage.child(cloudfilename).put(f)
    # with open(files, 'rb') as f:
    #     try:
    #         response = requests.post(url, headers=headers, data=f)
    #         response.raise_for_status()  # Check for HTTP errors
    #         print("Image stored successfully")
    #     except requests.exceptions.HTTPError as e:
    #         print(f"HTTP error occurred while storing image: {e}")
    #         print(response.text)
    #     except Exception as e:
    #         print(f"An error occurred while storing image: {e}")
    return


#GPT3 Fight narration function
def gpt3_fight (f1,f2):
    try:
        logger.info("Fight text started")
        fight = "create a brief Excitingly narrated transcript of an engaging realistic fight to the death, between \" {} \" VS \" {} \", highlighting the actions of both fighters, basing the outcome on the implied capabilities of the two opponents drawing on the specific skills and attributes of the fighters concluding with who won the fight and why:\n".format(f1, f2)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role":"system", "content": f"{fight}"}
            ],
            temperature=0.7,
            max_tokens=240,
            top_p=1,
            frequency_penalty=0.5,
            presence_penalty=0.8
    )
        logger.info(f'RESPONSE: {response}')
        content =  response["choices"][0]["message"]["content"].split('.')
        finished_fight = response["choices"][0]["message"]["content"]
        if finished_fight[-1:] in ('.','!',"\""):
            logger.info(f'FIGHT FINISHED: {finished_fight[-500:]}')
            return response["choices"][0]["message"]["content"]
        else:
            logger.info("FIGHT NOT FINISHED")
            fight_end = finished_fight[-500:]
            logger.info(f"UNFINISHED FIGHT ENDING  : {fight_end}")
            complete = "Bring this fight to an end under 60 word tokens, finish this Excitingly narrated transcript of a brief fight to the death, between \" {} \" VS \" {} \".concluding with who won the fight and why. \n Continue from the story from the last sentence:\" {} \"- ".format(f1, f2, fight_end)
            response2 = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role":"system", "content": f"{complete}"}
            ],
            temperature=0.2,
            max_tokens=90,
            top_p=1,
            frequency_penalty=0.2,
            presence_penalty=0.3
        )
            content2 = response2["choices"][0]["message"]["content"].split('.')
            content2 = content2[:-1]
            content2 = '.'.join(content2).strip()
            logger.info(f'ADDITION SENTENCE:{content2}')
            content2 = re.sub('\"', " ", content2)


            full_fight = finished_fight + ' ' + content2
            return full_fight
    except Exception as e:
        return e


#GPT3 Fight decider function
async def gpt3_decider(sentence, f1, f2):
    fight_winner = "from this passage, \"{}\", tell me which option won the fight , Option 1: \"{}\" \n or Option 2: \"{}\" :".format(sentence, f1, f2)
    logger.info(f"fight_winner:           {fight_winner}")
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role":"system", "content": f"{fight_winner}"}
        ],
        temperature=0.1,
        max_tokens=20,
        top_p=0,
        frequency_penalty=0.1 ,
        presence_penalty=0
    )
    content =  response["choices"][0]["message"]["content"].split('.')
    logger.info(content)
    return response["choices"][0]["message"]["content"]


def gpt3_chain_fight1 (fighter1,fighter2):
    logger.info("Fight text started")
    fight = f"begin a brief excitingly narrated transcript of realistic fight between '{fighter1}' AND '{fighter2}' . Both players begin with 100 Health points and take health point damage from attacks.\n"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role":"system", "content": f"{fight}"}
        ],
        temperature=0.7,
        max_tokens=160,
        top_p=1,
        frequency_penalty=0.2,
        presence_penalty=0.2
  )
    content =  response["choices"][0]["message"]["content"].split('.')
    chain_list1 = content[:-1]
    chain_fight1 = '.'.join(chain_list1)
    chain_fight1 = '`'+ chain_fight1 + '`'
    return chain_fight1


async def gpt3_chain_fight2 (fighter1,fighter2,action1,action2,chain1):
    try:
        logger.info("2nd chain function started")
        chain1_end = chain1.split('.')
        chain1_end = chain1_end[-3:]
        script = '.'.join(chain1_end)
        print(f'SCRIPT 1 {script}')

        fight = f""" finish the narrated transcript in 200 words based on the actions of both fighters.
        \n Fighter1: {fighter1}\n Fighter1's action: {action1} \n Fighter2: {fighter2}\n Fighter2's action: {action2}.\n my transcript ends here: {script}
        bring the fight to an end based on the actions of both players, describing in detail the impact of each action on the fight.
        Avoid bias & Make sure to give equal attention to both fighters' actions to ensure a fair and engaging end. continue the narration highlighting the actions of both players:"""      
        response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role":"system", "content": f"{fight}"}
        ],
            temperature=0.2,
            max_tokens=210,
            top_p=1,
            frequency_penalty=0.2,
            presence_penalty=0.3
        )
        #logger.info(f"FULL FIGHT LENGTH \n {response["choices"][0]["message"]["content"]}")
        content =  response["choices"][0]["message"]["content"].split('.')
        #Remove the last 2 sentences of the chain fight
        chain2_output_list = content[:-1]
        chain2_output = '.'.join(chain2_output_list)
        chain2_output = '`' + chain2_output + '`'
        return chain2_output
    except Exception as e:
        logger.info(e)
        return "NO NSFW OR PUBLIC FIGURES ALLOWED"


async def gpt3_chain_fight3 (fighter1,fighter2,action1,action2, chain2):
    logger.info("CHAIN 3 STARTED")
    chain2_end = chain2.split('.')
    chain2_end = chain2_end[-5:]
    script = '.'.join(chain2_end)
    print(f'SCRIPT 2 {script}')
    fight = f"""finish the narrated transcript in 200 words based on the actions of both fighters.
    \n Fighter1: {fighter1}\n Fighter1's action: {action1} \n Fighter2: {fighter2}\n Fighter2's action: {action2}.\n\n my transcript ends here: {script}-
    Bring the fight to an end solely based on the actions of both players describing in detail the impact of each action on the fight, concluding with who won the fight and why.
    Avoid bias & Make sure to give equal attention to both fighters' actions to ensure a fair and engaging end: """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role":"system", "content": f"{fight}"}
        ],
        temperature=0.3,
        max_tokens=240,
        top_p=1,
        frequency_penalty=0.2,
        presence_penalty=0.3
  )
    chain_fight =  response["choices"][0]["message"]["content"].split('.')
    chain_fight = chain_fight[:-1]
    chain3_output = '.'.join(chain_fight)
    chain3_output = '`' + chain3_output + '`' 
    return chain3_output


async def gpt3_fight_completed(sentence):
        fight_winner = "from this passage, \"{}\", tell me if the fight is ongoing or completed. Please read the passage carefully, Option 1 \"ongoing\" or Option 2 \"completed\". if it is unclear, return Option 1 \"ongoing\":".format(sentence)
        response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role":"system", "content": f"{fight_winner}"}
        ],
            temperature=0.1,
            max_tokens=20,
            top_p=0,
            frequency_penalty=0 ,
            presence_penalty=0
        )
        content =  response["choices"][0]["message"]["content"].split('.')
        logger.info(content)
        return response["choices"][0]["message"]["content"]


#function for 2 player game
async def message_handler(user1,user2,server,p1,p2) -> str:
        
        final1 = p1 +", 4k,highly detailed octane render, by alex ross" 
        final2 = p2 +", 4k,highly detailed octane render, by alex ross"
        server1, server2 = server,server

        try:
            
            logger.info("Now working on images")
            with concurrent.futures.ThreadPoolExecutor() as executor:
                thread1 = executor.submit(image, 1,user1,server1,final1)
                thread2 = executor.submit(image, 2,user2,server2,final2)
                thread3 = executor.submit(gpt3_fight,p1, p2)
            results = [thread1,thread2,thread3]

            # image1 = thread1.result()
            # image2 = thread2.result()
            fight_description = thread3.result() 
            result_list=[]
            for f in concurrent.futures.as_completed(results):
                result = f.result()
                result_list.append(result)

                if isinstance(result, Exception):   #Check if the result returned is an exception
                    raise result
            # #list of futures that completed and futures that failed
            # done, not_done = concurrent.futures.wait([thread1, thread2, thread3], timeout=None, return_when=concurrent.futures.ALL_COMPLETED)

            # for future in done:
            #     result = future.result()
            #     if isinstance(result, Exception):   #Check if the result returned is an exception
            #         raise result

            logger.info("THREADS FINISHED")
            
        except Exception as e:
            logger.info(e)
            error = str(e).lower()
            if "error" in error:
                logger.info("SERVER ERRORRRRRR")
                return "The server had an error while processing your request. Sorry about that!"
            else:
                return "NO NSFW OR PUBLIC FIGURES ALLOWED"

        fight_description = '`'+ fight_description + '`'
        return fight_description


async def chain_message_handler(user1,user2,server,p1,p2) -> str:

        final1 = p1 +", 4k,highly detailed octane render, by Alex Ross" 
        final2 = p2 +", 4k,highly detailed octane render, by Alex Ross"
        server1, server2 = server,server
        try:
            logger.info("Now working on images")
            with concurrent.futures.ThreadPoolExecutor() as executor:
                thread1 = executor.submit(image, 3,user1,server1,final1)
                thread2 = executor.submit(image, 4,user2,server2,final2)
                thread3 = executor.submit(gpt3_chain_fight1, p1,p2)
            image1 = thread1.result()
            image2 = thread2.result()
            chain_fight1 = thread3.result()
            
            #list of futures that completed and futures that failed
            done, not_done = concurrent.futures.wait([thread1, thread2, thread3], timeout=None, return_when=concurrent.futures.ALL_COMPLETED)

            for future in done:
                result = future.result()
                if isinstance(result, Exception):   #Check if the result returned is an exception
                    raise result
            logger.info("THREADS FINISHED")

        except Exception as e:
            logger.info(e)
            error = str(e).lower()
            if "error" in error:
                logger.info("SERVER ERRORRRRRR")
                return "The server had an error while processing your request. Sorry about that!"
            else:
                return "NO NSFW OR PUBLIC FIGURES ALLOWED"
        return chain_fight1

        
    


