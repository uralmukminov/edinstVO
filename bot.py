import asyncio
import json
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

TOKEN = "8239212075:AAG9lZCatLghF9bHddO5xCZejlHFykBLStY"  # вставь свой токен

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Загружаем вопросы
with open("questions.json", "r", encoding="utf-8") as f:
    questions = json.load(f)

user_state = {}
user_score = {}
user_name = {}

@dp.message(Command("start"))
async def ask_name(message: types.Message):
    await message.answer("Привет! Напиши, как тебя зовут 👇")
    user_state[message.from_user.id] = -1  # ждём имя

@dp.message()
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

        # Убираем клавиатуру
        await bot.send_message(
            user_id,
            f"🎉 Викторина закончена!\n{name}, ты набрал {score} из {len(questions)}.",
            reply_markup=types.ReplyKeyboardRemove()
        )

        # Отправляем сертификат-картинку
        await bot.send_photo(
            user_id,
            photo=open("certificate.png", "rb"),
            caption=f"🎓 Сертификат участника\n{name}\nРезультат: {score}/{len(questions)}"
        )

        # Сброс состояния
        user_state[user_id] = -1

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
