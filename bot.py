import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile

TOKEN = "ТОКЕН_ОТ_BOTFATHER"  # вставь свой токен

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
    unique_started.add(user_id)   # считаем уникальных начавших
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

@dp.message(~Command())   # ⚠️ общий обработчик только для НЕ команд
async def handle_message(message: types.Message):
    user_id = message.from_user.id
    idx = user_state.get(user_id, -1)

    # если ждём имя
    if idx == -1:
        user_name[user_id] = message.text
        user_state[user_id] = 0
        user_score[user_id] = 0
        await message.answer(f"Отлично, {message.text}! Начнём викторину 🎲")
        await send_question(user_id)
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
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text=opt)] for opt in q["options"]],
            resize_keyboard=True
        )
        await bot.send_message(user_id, q["question"], reply_markup=keyboard)
    else:
        score = user_score[user_id]
        name = user_name.get(user_id, "Участник")

        await bot.send_message(
            user_id,
            f"🎉 Викторина закончена!\n{name}, ты набрал {score} из {len(questions)}.",
            reply_markup=types.ReplyKeyboardRemove()
        )

        # добавляем в список закончивших
        unique_finished.add(user_id)
        save_stats()

        # отправляем сертификат через FSInputFile
        certificate = FSInputFile("certificate.png")
        await bot.send_photo(
            user_id,
            photo=certificate,
            caption=f"🎓 Сертификат участника\n{name}\nРезультат: {score}/{len(questions)}"
        )

        user_state[user_id] = -1

# ------------------- Запуск -------------------

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
