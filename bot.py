# /var/www/nanoregisterbot_pythonanywhere_com_wsgi.py

import sys
import os

# Path qo'shish
path = '/home/nanoregisterbot/NanoITRegister'
if path not in sys.path:
    sys.path.append(path)

# Environment variables
os.environ['BOT_TOKEN'] = 'ВАШ_BOT_TOKEN'
os.environ['ADMIN_ID'] = '146900578'

# Flask app yaratish (ENGL OSON YO'L)
from flask import Flask, request, jsonify
import asyncio
import threading

app = Flask(__name__)

# Bot obyektini global qilish
from bot import bot, dp, Form
from aiogram import types
from aiogram.fsm.context import FSMContext
import json

async def process_update(update_data):
    """Async update processing"""
    update = types.Update(**update_data)
    await dp.feed_update(bot=bot, update=update)

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.json
        
        # Async funksiyani sync qilish
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(process_update(data))
        loop.close()
        
        return jsonify({"status": "ok"})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    return "Telegram Bot ishlamoqda ✅"

@app.route('/setwebhook')
def set_webhook():
    """Webhook ni sozlash uchun (bir marta chaqirish kerak)"""
    try:
        import asyncio
        
        async def set_wh():
            webhook_url = "https://nanoregisterbot.pythonanywhere.com/webhook"
            await bot.set_webhook(webhook_url)
            return f"Webhook sozlandi: {webhook_url}"
        
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(set_wh())
        loop.close()
        
        return result
    
    except Exception as e:
        return f"Xato: {e}"

@app.route('/deletewebhook')
def delete_webhook():
    """Webhook ni o'chirish"""
    try:
        import asyncio
        
        async def del_wh():
            await bot.delete_webhook()
            return "Webhook o'chirildi"
        
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(del_wh())
        loop.close()
        
        return result
    
    except Exception as e:
        return f"Xato: {e}"

# Flask app ni export qilish
application = app