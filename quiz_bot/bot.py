# bot.py

import asyncio
import logging
import random
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, PollAnswerHandler, filters

# --- SOZLAMALAR ---
# BotFather'dan olgan tokeningizni shu yerga qo'ying
TOKEN = "7883812870:AAGzrEUv33rj_yHSccGFGfJrgXoFnHBb6JE"

# Konsolda botning ishlashi haqida ma'lumotlarni ko'rsatish uchun
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


# --- VIKTORINA MA'LUMOTLARI ---
# Savollar ro'yxati kengaytirildi
QUESTIONS = [
    {
        "question": "Python'da ro'yxat (list) yaratish uchun qaysi qavslardan foydalaniladi?",
        "options": ["( ) - Oddiy qavslar", "{ } - Figurali qavslar", "[ ] - Kvadrat qavslar", "< > - Burchakli qavslar"],
        "correct_answer_index": 2,
    },
    {
        "question": "O'zgaruvchi nomida qaysi belgi bo'lishi mumkin EMAS?",
        "options": ["_ (pastki chiziq)", "1 (raqam, boshida bo'lmasa)", "- (defis/chiziqcha)", "A (katta harf)"],
        "correct_answer_index": 2,
    },
    {
        "question": "Koddagi bir qatorni izoh (comment) holatiga o'tkazish uchun qaysi belgidan foydalaniladi?",
        "options": ["//", "/* */", "#", "---"],
        "correct_answer_index": 2,
    },
    {
        "question": "`len()` funksiyasi nima vazifani bajaradi?",
        "options": ["Matnni katta harfga o'tkazadi", "Elementlar sonini (uzunligini) qaytaradi", "Ro'yxatni tartiblaydi", "Matnni kichik harfga o'tkazadi"],
        "correct_answer_index": 1,
    },
    {
        "question": "Python'da qaysi kalit so'z funksiya e'lon qilish uchun ishlatiladi?",
        "options": ["fun", "function", "def", "create"],
        "correct_answer_index": 2,
    },
    {
        "question": "Qaysi ma'lumot turi o'zgarmas (immutable) hisoblanadi?",
        "options": ["list (ro'yxat)", "dictionary (lug'at)", "set (to'plam)", "tuple (kortezh)"],
        "correct_answer_index": 3,
    },
    {
        "question": "`'Hello'.upper()` kodi qanday natija qaytaradi?",
        "options": ["hello", "hELLO", "HELLO", "HeLlO"],
        "correct_answer_index": 2,
    },
    {
        "question": "Faylni o'qish uchun ochishda qaysi rejim (mode) ishlatiladi?",
        "options": ["'r'", "'w'", "'a'", "'x'"],
        "correct_answer_index": 0,
    },
    {
        "question": "Sinf (class) asosida yaratilgan ob'ekt nima deb ataladi?",
        "options": ["Instance (nusxa)", "Variable (o'zgaruvchi)", "Module (modul)", "Function (funksiya)"],
        "correct_answer_index": 0,
    }
]


# --- BOT FUNKSIYALARI (COMMAND HANDLERS) ---

# /start buyrug'i uchun funksiya
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Foydalanuvchini kutib oladi va interaktiv tugma yuboradi."""
    user = update.effective_user
    # Tugma yaratish
    keyboard = [["Viktorinani boshlash"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    
    await update.message.reply_html(
        f"Salom, {user.mention_html()}!\n\n"
        f"Men Python asoslari bo'yicha bilimingizni sinovchi botman.\n\n"
        f"Boshlash uchun quyidagi tugmani bosing yoki /quiz buyrug'ini yuboring.",
        reply_markup=reply_markup
    )

# /quiz buyrug'i yoki "Viktorinani boshlash" tugmasi uchun funksiya
async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Foydalanuvchiga tasodifiy viktorina yuboradi."""
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
    # To'g'ri javobni context.bot_data da saqlab qo'yish
    context.bot_data[message.poll.id] = {"correct_answer_index": random_question["correct_answer_index"]}


# Foydalanuvchi javobini qabul qilish va ballni hisoblash
async def receive_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Foydalanuvchi javobini tekshiradi va to'g'ri bo'lsa, ball qo'shadi."""
    answer = update.poll_answer
    poll_id = answer.poll_id
    
    try:
        # Saqlangan to'g'ri javobni olish
        saved_poll_data = context.bot_data[poll_id]
    except KeyError:
        # Agar so'rovnoma topilmasa (eski bo'lsa), hech narsa qilmaymiz
        logger.warning(f"Poll with ID {poll_id} not found in bot_data")
        return

    # Foydalanuvchi tanlagan javob bilan to'g'ri javobni solishtirish
    if saved_poll_data["correct_answer_index"] == answer.option_ids[0]:
        # Agar to'g'ri bo'lsa, ballni 1 ga oshirish
        current_score = context.user_data.get('score', 0)
        context.user_data['score'] = current_score + 1


# /score buyrug'i uchun funksiya
async def score(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Foydalanuvchining to'plagan ballini ko'rsatadi."""
    current_score = context.user_data.get('score', 0)
    await update.message.reply_text(f"Sizning joriy balingiz: {current_score} ✨")


# --- ASOSIY FUNKSIYA ---

def main() -> None:
    """Botni ishga tushiruvchi asosiy funksiya."""
    application = Application.builder().token(TOKEN).build()

    # Buyruqlar va xabarlarni ro'yxatdan o'tkazish
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("quiz", quiz))
    application.add_handler(CommandHandler("score", score))
    # "Viktorinani boshlash" tugmasi uchun handler
    application.add_handler(MessageHandler(filters.Regex('^Viktorinani boshlash$'), quiz))
    # Javoblarni qabul qilish uchun handler
    application.add_handler(PollAnswerHandler(receive_poll_answer))

    print("Bot ishga tushdi... To'xtatish uchun CTRL+C bosing.")
    application.run_polling()


if __name__ == "__main__":
    main()
