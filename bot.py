import os
import ast
import json
import random
import string
import requests
import telebot
from dotenv import load_dotenv
from flask import Flask, request
from twilio.rest import Client
from telebot import types
from requests.auth import HTTPBasicAuth
from datetime import datetime, date, timedelta  

# 1. Safely load secrets from environment variables
load_dotenv()

bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
ngrok = os.getenv('NGROK_URL')
phone_numz = os.getenv('TWILIO_PHONE_NUMBER')

# 2. Initialize API Clients
client = Client(account_sid, auth_token)
bot = telebot.TeleBot(bot_token)  

def check_subscription(idkey):
    try:
        with open('./conf/'+idkey+'/subs.txt', 'r') as f:
            subscription = f.read().strip()
        idmember = datetime.strptime(subscription, '%d/%m/%Y')
        if idmember < datetime.now():
            return "EXPIRED"
        else:
            return "ACTIVE"
    except FileNotFoundError:
        return "EXPIRED"

def generate_ai(iduser, text, page):
    headers = {
        'accept': 'audio/mpeg',
        'xi-api-key': 'f343277da36e000924585730b1a3f91e', # ElevenLabs key (consider moving this to .env too!)
        'Content-Type': 'application/json',
    }

    json_data = {
        'text': text,
        'voice_settings': {
            'stability': 1,
            'similarity_boost': 1,
        },
    }
    botai = requests.post('https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM', headers=headers, json=json_data)
    
    os.makedirs(f"./conf/{iduser}", exist_ok=True)
    with open(f"./conf/{iduser}/{page}.mp3", 'wb') as f:
        f.write(botai.content)


@bot.message_handler(commands=['help'])
def help_command(pm):
    help_text = """
🤖 **OTP-Boss Bot User Guide**:  
Below are the basic commands of the bot and their descriptions:  

🔑 /check: Check your subscription status.  
📞 /call [Phone Number] [Name] [Code] [Company Name]: Initiate a call with the specified details.  
🔄 /add_subs [User ID] [Number of Days]: Add a subscription to the specified user (Admin only).  
⚙️ /clearset: Reset the current settings of the bot.  
🎙️ /start: Start the bot and create your subscription information.  

💡 For more information, please contact @YOUR_TG_NAME.  
"""
    safe_text = help_text.replace("_", "\\_").replace("*", "\\*").replace("[", "\\[").replace("]", "\\]").replace("(", "\\(").replace(")", "\\ ").replace(".", "\\.").replace("-", "\\-")
    bot.send_message(pm.chat.id, safe_text, parse_mode="MarkdownV2")


@bot.message_handler(commands=['subscription_info'])
def subscription_info(pm):
    iduser = pm.from_user.id
    if check_subscription(str(iduser)) == "ACTIVE":
        try:
            with open(f'./conf/{iduser}/subs.txt', 'r') as f:
                expiry_date = f.read().strip()
            bot.send_message(
                pm.chat.id,
                f"✅ **Subscription Status**: Active\n📅 **Exp Date**: {expiry_date}\n\nWe wish you a pleasant use!",
                parse_mode="Markdown"
            )
        except FileNotFoundError:
            bot.send_message(pm.chat.id, "❌ Error retrieving subscription file.")
    else:
        bot.send_message(
            pm.chat.id,
            "❌ Subscription Status: Passive\n\nPlease contact @YOUR_TG_NAME to purchase a subscription.",
            parse_mode="Markdown"
        )


@bot.message_handler(commands=['manage_subscription'])
def manage_subscription(pm):
    iduser = pm.from_user.id
    buttons = types.InlineKeyboardMarkup(row_width=2)
    btn_extend = types.InlineKeyboardButton("📅 Extend Subscription", callback_data="extend_subscription")
    btn_info = types.InlineKeyboardButton("ℹ️ Subscription Info", callback_data="subscription_info")
    buttons.add(btn_extend, btn_info)
    bot.send_message(
        pm.chat.id,
        "🔑 Subscription Management\n\nPlease select the action you want to take.",
        reply_markup=buttons,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data == "extend_subscription")
def extend_subscription(call):
    bot.send_message(
        call.message.chat.id,
        "📞 Please contact @YOUR_TG_NAME to extend your subscription."
    )

# Cleaned up the broken callback handler syntax at the end
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data == "subscription_info":
        subscription_info(call.message)

if __name__ == "__main__":
    print("Bot is polling cleanly and safely...")
    bot.infinity_polling()
