import asyncio
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State

# Загружаем переменные окружения
load_dotenv()

BOT_TOKEN = os.getenv("8576072030:AAGLkatiFFeFfqpwfYwCn2nMx1zrLi4go7k")
ADMIN_ID = int(os.getenv("146900578"))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Состояния
class Form(StatesGroup):
    group = State()
    name = State()
    phone = State()

# Команда /start
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

# Получаем группу
@dp.message(Form.group)
async def get_group(message: types.Message, state: FSMContext):
    await state.update_data(group=message.text)
    await message.answer("Теперь введите Имя и Фамилию:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(Form.name)

# Получаем имя
@dp.message(Form.name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отправить номер", request_contact=True)]],
        resize_keyboard=True
    )

    await message.answer("Отправьте номер телефона или введите вручную:", reply_markup=kb)
    await state.set_state(Form.phone)

# Получаем телефон + отправляем админу
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

    # Отправляем админу
    await bot.send_message(chat_id=ADMIN_ID, text=text, parse_mode="Markdown")

    await message.answer("Спасибо! Ваша заявка отправлена ✔️")
    await state.clear()

# Запуск
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
