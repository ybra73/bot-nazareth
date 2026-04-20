import os
import logging
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from groq import Groq

app = Flask(__name__)

@app.route('/')
def home():
    return "NAZARETH ONLINE"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile" 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = Groq(api_key=GROQ_API_KEY)
user_memory = {}

def main_keyboard():
    keyboard = [
        [InlineKeyboardButton("🛠️ Área Técnica", callback_data="area_tecnica")],
        [InlineKeyboardButton("📊 Área Administrativa", callback_data="area_admin")],
        [InlineKeyboardButton("🎨 Área Creativa", callback_data="area_creativa")],
        [InlineKeyboardButton("📲 Contactar WhatsApp", url="https://wa.me/584264014765")],
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"¡Hola {update.effective_user.first_name}! 👋 Soy NAZARETH.\n¿En qué área te gustaría especializarte?",
        reply_markup=main_keyboard()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_input = update.message.text
    if user_id not in user_memory: user_memory[user_id] = []
    user_memory[user_id].append({"role": "user", "content": user_input})
    user_memory[user_id] = user_memory[user_id][-5:] 

    try:
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "system", "content": "Eres NAZARETH, asistente de la Academia J. de Nazareth."}] + user_memory[user_id]
        )
        response = completion.choices[0].message.content
        await update.message.reply_text(response, reply_markup=main_keyboard())
    except Exception as e:
        # ESTA LÍNEA ES LA QUE NOS DIRÁ QUÉ PASA
        await update.message.reply_text(f"Error técnico real: {e}", reply_markup=main_keyboard())

def main():
    threading.Thread(target=run_flask, daemon=True).start()
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == "__main__":
    main()
