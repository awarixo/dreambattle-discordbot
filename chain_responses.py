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
from PIL import Image
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
  "serviceAccount": "./dreambattlebeta-firebase-adminsdk-3qx63-979ca29af4.json",
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
    username = str(re.sub(r"#", "-", username))
    data = {"username":f"{username}","Fighter":f"{fighter}", "Gamemode":f"{gamemode}"}
    database.child("servers").child(server).child(gamemode).child("Player 2").update(data,)
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
    username = str(re.sub(r"#", "-", username))
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
    data = {"Time":time, "Date":date, "Fighter":f"{fighter}", "Gamemode":f"{gamemode}", "image_URL":imgURL}
    username = re.sub(r"#", "-", username)
    #logger.info(f"STORING {username}'S FIGHTER TO {server}")

    database.child("servers").child(server).child(gamemode).child(username).child(fighter).set(data)
    logger.info(F"{username}---->{fighter}  DATA STORED IN DB")
    return 


#Dalle image generator function
def image(player_number,username,server,sentence):
    try:
        now = datetime.today()
        time = now.strftime('%H:%M:%S')
        date = now.strftime('%Y-%m-%d')
        username = str(username)
        username = re.sub(r"#", "-", username)

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
            cloudfilename1 = f"{server}/{username}/{fighter}.png"
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
            cloudfilename2 = f"{server}/{username}/{fighter}.png"
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
            cloudfilename3 = f"{server}/{username}/{fighter}.png"
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
            cloudfilename4 = f"{server}/{username}/{fighter}.png"
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
    url = f"https://firebasestorage.googleapis.com/v0/b/dreambattlebeta.appspot.com/o/{cloudfilename}"
    headers = {
        "Content-Type": "image/png",
        "Authorization": f"Bearer {access_token}"
    }
    with open(files, 'rb') as f:
        response = requests.post(url, headers=headers, data=f)
    return


#GPT3 Fight narration function
def gpt3_fight (f1,f2):
    try:
        fight = "Under 5 paragraphs,create an Excitingly narrated transcript of a brief engaging realistic fight to the death, between \" {} \" VS \" {} \", basing the outcome on the implied capabilities of the two opponents drawing on the specific skills and attributes of the fighters concluding with who won the fight and why:\n".format(f1, f2)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role":"system", "content": f"{fight}"}
            ],
            temperature=0.7,
            max_tokens=220,
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
            complete = "Bring this fight to an end under 60 word tokens, finish this Excitingly narrated transcript of a brief fight to the death, between \" {} \" VS \" {} \".concluding with who won the fight and why \n Continue from the last word:\" {} \"- ".format(f1, f2, fight_end)
            response2 = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role":"system", "content": f"{complete}"}
            ],
            temperature=0.2,
            max_tokens=60,
            top_p=1,
            frequency_penalty=0.2,
            presence_penalty=0.3
        )
            content2 = response2["choices"][0]["message"]["content"].split('.')
            content2 = content2[:-1]
            content2 = '.'.join(content2).strip()
            logger.info(f'ADDITION SENTENCE:{content2}')
            # if response2.choices[0].text[2:] == '\n':
            #     content2 = content2[:2].join
            #     logger.info("FIXED!")
            #     logger.info (content2)
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
        fight = f"""continue an excitingly narrated transcript of realistic fight between {fighter1} and {fighter2}, using the actions of both players to advance the battle. Each player should input one action per turn,which should be based on the skills and attributes of their fighter. 
        Remember that both fighters start with 100 health points, and take damage from attacks. In your response, include the actions taken by both players, describing in detail the impact of each action on the fight. Tell the narration from a 3rd party's point of view to avoid bias &
         Make sure to give equal attention to both fighters and their actions to ensure a fair and engaging battle. The outcome should be determined by the actions and implied capabilities of both fighters, concluding with who won the fight and why. \nPlayer1: {fighter1}\n player1's action: {action1} \nplayer2: {fighter2}\n player2's action: {action2}\n\nContinue from here:\"{chain1}\" """      
        response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role":"system", "content": f"{fight}"}
        ],
            temperature=0.5,
            max_tokens=160,
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
    fight = f"""finish an exciting story mode realistic fight between {fighter1} and {fighter2}, using the actions of both players to advance the battle. Remember that both fighters started with 100 health points, and take damage from attacks. 
        In your response, include the actions taken by both players, describing in detail the impact of each action on the fight. Tell the narration from a 3rd party's point of view to avoid bias & Make sure to give equal attention to both fighters and their actions to ensure a fair and engaging battle.
         The outcome should be determined by the actions and implied capabilities of both fighters,make sure to conclude with who won the fight and why. \nPlayer1: {fighter1}\n player1's action: {action1} \nplayer2: {fighter2}\n player2's action: {action2}\n Finish the fight:\"{chain2} """
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role":"system", "content": f"{fight}"}
        ],
        temperature=0.5,
        max_tokens=160,
        top_p=1,
        frequency_penalty=0.2,
        presence_penalty=0.3
  )
    chain_fight_end =  response["choices"][0]["message"]["content"]
    if chain_fight_end[-1:] in ('.','!',"\""):
            logger.info(f'FIGHT FINISHED: {chain_fight_end[-500:]}')
            return response["choices"][0]["message"]["content"]
    else:
        logger.info("FIGHT NOT FINISHED")
        fight_end = chain_fight_end[-500:]
        logger.info(f"UNFINISHED FIGHT ENDING  : {fight_end}")
        complete = "Bring this fight to an end under 60 word tokens, finish this Excitingly narrated transcript of a brief fight to the death, between \" {} \" VS \" {} \".concluding with who won the fight and why \n Continue from the last word:\" {} \"- ".format(fighter1, fighter2, fight_end)
        response2 = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role":"system", "content": f"{complete}"}
        ],
        temperature=0.2,
        max_tokens=60,
        top_p=1,
        frequency_penalty=0.2,
        presence_penalty=0.3
    )
    content2 = response2["choices"][0]["message"]["content"].split('.')
    content2 = content2[:-1]
    content2 = '.'.join(content2).strip()
    logger.info(f'CHAIN ADDITION SENTENCE:{content2}')

    chain3_output = '`' +  chain_fight_end + content2 + '`' 
    return chain3_output


async def gpt3_fight_completed(sentence):
        fight_winner = "from this passage, \"{}\", tell me if the fight is completed or ongoing, Option 1 \"ongoing\" or Option 2 \"completed\". if it is unclear, return Option 1 \"ongoing\":".format(sentence)
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
            if "server" in error:
                logger.info("SERVER ERRORRRRRR")
                return(e)
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
            if "server" in error:
                logger.info("SERVER ERRORRRRRR")
                return(e)
            else:
                return "NO NSFW OR PUBLIC FIGURES ALLOWED"
        return chain_fight1

        
    


