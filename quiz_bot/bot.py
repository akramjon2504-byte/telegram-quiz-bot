# bot.py

import asyncio
import logging
import random
import os
import threading  # Ko'p oqimli ishlash uchun qo'shildi
from flask import Flask  # Veb-server uchun Flask qo'shildi
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, PollAnswerHandler, filters

# --- Veb-server qismi (Render uchun hiyla) ---
# Bu qism Render "port" talabini qondirish uchun kerak
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is alive!"

def run_flask():
    # Render odatda PORT o'zgaruvchisini o'zi belgilaydi
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# -------------------------------------------------


# --- SOZLAMALAR ---
TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN muhit o'zgaruvchisi topilmadi!")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


# --- VIKTORINA MA'LUMOTLARI ---
# Bu qism o'zgarishsiz qoldi
QUESTIONS = [
    {
        "question": "Python'da ro'yxat (list) yaratish uchun qaysi qavslardan foydalaniladi?",
        "options": ["( )", "{ }", "[ ]", "< >"],
        "correct_answer_index": 2,
    },
    {
        "question": "O'zgaruvchi nomida qaysi belgi bo'lishi mumkin EMAS?",
        "options": ["_", "1 (boshida bo'lmasa)", "-", "A"],
        "correct_answer_index": 2,
    },
] # ... va boshqa savollar


# --- BOT FUNKSIYALARI ---
# Bu qismdagi funksiyalar (start, quiz, receive_poll_answer, score) o'zgarishsiz qoldi
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    keyboard = [["Viktorinani boshlash"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    await update.message.reply_html(
        f"Salom, {user.mention_html()}! Boshlash uchun tugmani bosing.",
        reply_markup=reply_markup
    )

async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    random_question = random.choice(QUESTIONS)
    message = await context.bot.send_poll(
        chat_id=update.effective_chat.id,
        question=random_question["question"],
        options=random_question["options"],
        is_anonymous=False,
        type="quiz",
        correct_option_id=random_question["correct_answer_index"],
        explanation=f"To'g'ri javob: {random_question['options'][random_question['correct_answer_index']]}"
    )
    context.bot_data[message.poll.id] = {"correct_answer_index": random_question["correct_answer_index"]}

async def receive_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    answer = update.poll_answer
    poll_id = answer.poll_id
    try:
        saved_poll_data = context.bot_data[poll_id]
        if saved_poll_data["correct_answer_index"] == answer.option_ids[0]:
            current_score = context.user_data.get('score', 0)
            context.user_data['score'] = current_score + 1
    except KeyError:
        logger.warning(f"Poll with ID {poll_id} not found.")

async def score(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    current_score = context.user_data.get('score', 0)
    await update.message.reply_text(f"Sizning joriy balingiz: {current_score} ✨")


# --- ASOSIY FUNKSIYA ---
def main() -> None:
    # Veb-serverni alohida oqimda (thread) ishga tushirish
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    # Botni ishga tushirish
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("quiz", quiz))
    application.add_handler(CommandHandler("score", score))
    application.add_handler(MessageHandler(filters.Regex('^Viktorinani boshlash$'), quiz))
    application.add_handler(PollAnswerHandler(receive_poll_answer))

    print("Bot ishga tushdi...")
    application.run_polling()

if __name__ == "__main__":
    main()
