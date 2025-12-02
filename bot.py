import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, WebhookInfo
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
    print(f"⚠️ .env fayli topilmadi")
    sys.exit(1)

load_dotenv(ENV_PATH)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("❌ BOT_TOKEN topilmadi")
    sys.exit(1)

ADMIN_ID = 146900578  # Sizning ID'ingiz

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
    
    await bot.send_message(chat_id=ADMIN_ID, text=text, parse_mode="Markdown")
    await message.answer("Спасибо! Ваша заявка отправлена ✔️")
    await state.clear()

# ========== WEBHOOK SOZLASH ==========
async def on_startup(bot: Bot):
    # Webhook sozlash
    webhook_url = f"https://{YOUR_PYTHONANYWHERE_USERNAME}.pythonanywhere.com/webhook"
    await bot.set_webhook(webhook_url)
    print(f"✅ Webhook sozlandi: {webhook_url}")

# ========== AIOHTTP SERVER ==========
async def aiohttp_app():
    app = web.Application()
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    
    webhook_requests_handler.register(app, path="/webhook")
    
    # Startup handler
    app.on_startup.append(on_startup)
    
    return app

if __name__ == "__main__":
    # PythonAnywhere'da web server sifatida ishlash
    app = asyncio.run(aiohttp_app())
    
    # Agar kommand satridan ishga tushirilsa
    if len(sys.argv) > 1 and sys.argv[1] == "--local":
        # Local test uchun polling
        async def local_main():
            await dp.start_polling(bot)
        asyncio.run(local_main())
    else:
        # Production uchun
        web.run_app(app, host="0.0.0.0", port=8080)