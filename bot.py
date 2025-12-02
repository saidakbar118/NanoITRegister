import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

# ========== KONFIGURATSIYA ==========
BASE_DIR = Path(__file__).parent
ENV_PATH = BASE_DIR / ".env"

if not ENV_PATH.exists():
    print("❌ .env fayli topilmadi!")
    print(f"📁 {ENV_PATH} faylini yarating va quyidagilarni yozing:")
    print("BOT_TOKEN=your_bot_token")
    print("ADMIN_ID=146900578")
    sys.exit(1)

load_dotenv(ENV_PATH)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "146900578"))

if not BOT_TOKEN:
    print("❌ BOT_TOKEN topilmadi!")
    sys.exit(1)

print(f"✅ Bot sozlandi")
print(f"✅ Admin ID: {ADMIN_ID}")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ========== STATES ==========
class Form(StatesGroup):
    group = State()
    name = State()
    phone = State()

# ========== HANDLERS ==========
@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="1-группа"), KeyboardButton(text="2-группа")],
            [KeyboardButton(text="3-группа"), KeyboardButton(text="4-группа")],
            [KeyboardButton(text="Ввести группу вручную")]
        ],
        resize_keyboard=True
    )
    await message.answer("Выберите группу или введите её номер:", reply_markup=kb)
    await state.set_state(Form.group)

@dp.message(Form.group)
async def get_group(message: types.Message, state: FSMContext):
    await state.update_data(group=message.text)
    await message.answer("Теперь введите Имя и Фамилию:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(Form.name)

@dp.message(Form.name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отправить номер", request_contact=True)]],
        resize_keyboard=True
    )
    await message.answer("Отправьте номер телефона или введите вручную:", reply_markup=kb)
    await state.set_state(Form.phone)

@dp.message(Form.phone)
async def get_phone(message: types.Message, state: FSMContext):
    data = await state.get_data()
    
    if message.contact:
        phone = message.contact.phone_number
    else:
        phone = message.text
    
    data["phone"] = phone
    
    text = (
        "📥 *НОВАЯ ЗАЯВКА*\n\n"
        f"📚 Группа: {data['group']}\n"
        f"👤 Имя: {data['name']}\n"
        f"📞 Телефон: {data['phone']}\n"
        f"🆔 Отправитель: {message.from_user.id}"
    )
    
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=text, parse_mode="Markdown")
    except Exception as e:
        print(f"❌ Adminga xabar yuborishda xato: {e}")
    
    await message.answer("Спасибо! Ваша заявка отправлена ✔️")
    await state.clear()

# ========== WEBHOOK HANDLER ==========
async def set_webhook():
    """Webhook ni sozlash"""
    webhook_url = "https://nanoregisterbot.pythonanywhere.com/webhook"
    
    try:
        await bot.set_webhook(webhook_url)
        print(f"✅ Webhook sozlandi: {webhook_url}")
    except Exception as e:
        print(f"❌ Webhook sozlashda xato: {e}")

# ========== AIOHTTP APP ==========
async def webhook_handler(request):
    """Webhook request'larini qayta ishlash"""
    try:
        request_data = await request.json()
        update = types.Update(**request_data)
        await dp.feed_update(bot=bot, update=update)
        return web.Response(text="OK")
    except Exception as e:
        print(f"❌ Webhook handler xato: {e}")
        return web.Response(text="Error", status=500)

async def on_startup(app):
    """Server ishga tushganda"""
    print("🚀 Bot server ishga tushdi")
    await set_webhook()

async def on_shutdown(app):
    """Server to'xtaganda"""
    print("🛑 Bot server to'xtadi")
    await bot.session.close()

def create_app():
    """Aiohttp application yaratish"""
    app = web.Application()
    
    # Webhook endpoint
    app.router.add_post('/webhook', webhook_handler)
    
    # Health check
    app.router.add_get('/', lambda request: web.Response(text="Bot ishlamoqda ✅"))
    
    # Startup/shutdown handlers
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    
    return app

# ========== ASOSIY FUNKSIYA ==========
if __name__ == "__main__":
    # Agar polling kerak bo'lsa (local test uchun)
    if len(sys.argv) > 1 and sys.argv[1] == "--polling":
        import asyncio
        async def polling_main():
            await bot.delete_webhook(drop_pending_updates=True)
            await dp.start_polling(bot)
        
        print("🔄 Polling rejimida ishlayapti...")
        asyncio.run(polling_main())
    
    else:
        # Production (webhook rejimi)
        print("🌐 Webhook rejimida ishlayapti...")
        app = create_app()
        web.run_app(app, host='0.0.0.0', port=8080)