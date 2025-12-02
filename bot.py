import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State

# ========== KONFIGURATSIYA ==========
# Papka manzilini aniqlash
BASE_DIR = Path(__file__).parent
ENV_PATH = BASE_DIR / ".env"

# .env fayli yo'q bo'lsa yaratish
if not ENV_PATH.exists():
    print(f"⚠️ .env fayli topilmadi: {ENV_PATH}")
    print("📝 Namuna .env fayli yaratilmoqda...")
    with open(ENV_PATH, "w") as f:
        f.write("# Telegram Bot Token\n")
        f.write("BOT_TOKEN=your_bot_token_here\n\n")
        f.write("# Admin Telegram ID\n")
        f.write("ADMIN_ID=146900578\n")
    print("✅ .env fayli yaratildi. Token qo'ying!")

# Environment yuklash
load_dotenv(ENV_PATH)

# Token va Admin ID olish
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN or BOT_TOKEN == "your_bot_token_here":
    print("❌ XATO: BOT_TOKEN topilmadi yoki default qiymat!")
    print(f"📁 {ENV_PATH} faylini oching va BOT_TOKEN ni yozing")
    print("🛠️ Bot token olish uchun: @BotFather > /newbot")
    sys.exit(1)

# Admin ID (agar bo'lmasa default)
ADMIN_ID = 146900578  # Default qiymat
admin_env = os.getenv("ADMIN_ID")
if admin_env:
    try:
        ADMIN_ID = int(admin_env)
    except ValueError:
        print(f"⚠️ ADMIN_ID noto'g'ri: {admin_env}, default ishlatilmoqda")

print(f"✅ Bot sozlandi")
print(f"✅ Admin ID: {ADMIN_ID}")

# Bot obyektlari
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ========== QOLGAN KOD O'ZGARMAS ==========
class Form(StatesGroup):
    group = State()
    name = State()
    phone = State()

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

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())