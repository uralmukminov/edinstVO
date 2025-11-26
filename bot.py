import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile

TOKEN = "8239212075:AAG9lZCatLghF9bHddO5xCZejlHFykBLStY"  # вставь свой токен

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Загружаем вопросы
with open("questions.json", "r", encoding="utf-8") as f:
    questions = json.load(f)

user_state = {}
user_score = {}
user_name = {}

# Файл для статистики
STATS_FILE = "stats.json"

# Загружаем статистику из файла (если есть)
if os.path.exists(STATS_FILE):
    with open(STATS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        unique_started = set(data.get("started", []))
        unique_finished = set(data.get("finished", []))
else:
    unique_started = set()
    unique_finished = set()

def save_stats():
    """Сохраняем статистику в файл"""
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "started": list(unique_started),
            "finished": list(unique_finished)
        }, f, ensure_ascii=False, indent=2)

# ------------------- Команды -------------------

@dp.message(Command("start"))
async def ask_name(message: types.Message):
    user_id = message.from_user.id
    unique_started.add(user_id)
    save_stats()
    await message.answer("Привет! Напиши, как тебя зовут 👇")
    user_state[user_id] = -1

@dp.message(Command("stats"))
async def show_stats(message: types.Message):
    await message.answer(
        f"📊 Статистика:\n"
        f"Начали: {len(unique_started)} участников\n"
        f"Закончили: {len(unique_finished)} участников"
    )

@dp.message(Command("export"))
async def export_stats(message: types.Message):
    if os.path.exists(STATS_FILE):
        await bot.send_document(
            message.from_user.id,
            document=FSInputFile(STATS_FILE),
            caption="📊 Файл статистики участников"
        )
    else:
        await message.answer("Файл статистики пока не создан.")

# ------------------- Викторина -------------------

@dp.message()
async def handle_message(message: types.Message):
    if message.text.startswith("/"):
        return

    user_id = message.from_user.id
    idx = user_state.get(user_id, None)

    if idx is None:
        await message.answer("Сначала напиши /start")
        return

    # если ждём имя
    if idx == -1:
        if user_id not in user_name:
            user_name[user_id] = message.text
            user_state[user_id] = 0
            user_score[user_id] = 0
            await message.answer(f"Отлично, {message.text}! Начнём викторину 🎲")
            await send_question(user_id)
        else:
            await message.answer("Ты уже ввёл имя, продолжай викторину 👇")
        return

    # если ждём решение о перезапуске
    if idx == -2:
        if message.text.lower() == "да":
            user_state[user_id] = 0
            user_score[user_id] = 0
            await message.answer("🚀 Начинаем заново!")
            await send_question(user_id)
        else:
            await message.answer("Хорошо 👍 Викторина завершена.")
            user_state[user_id] = None
        return

    # если идёт викторина
    if idx < len(questions):
        q = questions[idx]
        correct_option = q["options"][q["answer"][0]]

        if message.text == correct_option:
            await message.answer("✅ Верно!")
            user_score[user_id] += 1
        else:
            await message.answer(f"❌ Неправильно. Правильный ответ: {correct_option}")

        user_state[user_id] = idx + 1
        await send_question(user_id)

async def send_question(user_id: int):
    idx = user_state[user_id]
    if idx < len(questions):
        q = questions[idx]
        options = q.get("options", [])

        keyboard = types.ReplyKeyboardMarkup(
            resize_keyboard=True,
            one_time_keyboard=True,
            input_field_placeholder="Выбери вариант 👇"
        )
        for opt in options:
            keyboard.add(types.KeyboardButton(text=opt))

        await bot.send_message(user_id, q["question"], reply_markup=keyboard)
    else:
        score = user_score[user_id]
        name = user_name.get(user_id, "Участник")

        await bot.send_message(
            user_id,
            f"🎉 Викторина закончена!\n{name}, ты набрал {score} из {len(questions)}.",
            reply_markup=types.ReplyKeyboardRemove()
        )

        unique_finished.add(user_id)
        save_stats()

        certificate = FSInputFile("certificate_v2.png")  # или certificate.png
        await bot.send_photo(
            user_id,
            photo=certificate,
            caption=f"🎓 Сертификат участника\n{name}\nРезультат: {score}/{len(questions)}"
        )

        # 👉 предлагаем пройти заново
        restart_keyboard = types.ReplyKeyboardMarkup(
            resize_keyboard=True,
            one_time_keyboard=True
        )
        restart_keyboard.add("Да", "Нет")

        await bot.send_message(
            user_id,
            "Хочешь пройти викторину заново?",
            reply_markup=restart_keyboard
        )

        user_state[user_id] = -2  # спец. состояние "ожидание ответа на перезапуск"

# ------------------- Запуск -------------------

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
