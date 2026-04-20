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

# ── SERVIDOR WEB PARA EVITAR EL SUEÑO (Keep-Alive) ─────────────────────────
app = Flask(__name__)

@app.route('/')
def home():
    return "NAZARETH ONLINE: Academia Internacional activa."

def run_flask():
    # Render asigna un puerto automáticamente
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

# ── CONFIGURACIÓN DE SEGURIDAD (Lectura desde Render) ─────────────────────
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GROQ_MODEL = "llama-3.3-70b-versatile" 
WHATSAPP_NUMBER = "584264014765"
AULA_VIRTUAL = "https://academiajesusdenazareth.milaulas.com"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ── PROMPT DEL SISTEMA ──────────────────────────────────────────────────────
SYSTEM_PROMPT = f"""Eres NAZARETH, la asistente virtual de la Academia Internacional Jesús de Nazareth.
Responde en el idioma del usuario. Somos una academia global.
Datos clave: WhatsApp +{WHATSAPP_NUMBER}, Aula Virtual: {AULA_VIRTUAL}.
REGLA: Si preguntan por precios o inscripción, diles que pulsen el botón de WhatsApp."""

# Inicialización del cliente Groq
client = Groq(api_key=GROQ_API_KEY)
user_memory = {}

# ── TECLADO PRINCIPAL ─────────────────────────────────────────────────────────
def main_keyboard():
    keyboard = [
        [InlineKeyboardButton("🛠️ Área Técnica", callback_data="area_tecnica")],
        [InlineKeyboardButton("📊 Área Administrativa", callback_data="area_admin")],
        [InlineKeyboardButton("🎨 Área Creativa", callback_data="area_creativa")],
        [InlineKeyboardButton("📲 Contactar WhatsApp", url=f"https://wa.me/{WHATSAPP_NUMBER}")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ── FUNCIONES DEL BOT ─────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_memory[user_id] = [] 
    await update.message.reply_text(
        f"¡Hola {update.effective_user.first_name}! 👋 Soy NAZARETH.\n"
        "Bienvenido a nuestra Academia Internacional. ¿En qué área te gustaría especializarte hoy?",
        reply_markup=main_keyboard()
    )

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "¡Excelente elección! Cuéntame qué curso buscas o hazme cualquier duda sobre esa área.",
        reply_markup=main_keyboard()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_input = update.message.text

    if user_id not in user_memory:
        user_memory[user_id] = []
    
    # Mantener memoria corta de 5 mensajes
    user_memory[user_id].append({"role": "user", "content": user_input})
    user_memory[user_id] = user_memory[user_id][-5:] 

    try:
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + user_memory[user_id],
            temperature=0.7,
            max_tokens=500
        )
        
        response_text = completion.choices[0].message.content
        user_memory[user_id].append({"role": "assistant", "content": response_text})
        await update.message.reply_text(response_text, reply_markup=main_keyboard())

    except Exception as e:
        logger.error(f"Error real detectado: {e}")
        # Este mensaje te dirá exactamente qué falla (ej: si la API Key es inválida)
        await update.message.reply_text(
            f"Lo siento, tengo un inconveniente técnico: {e}. Por favor, usa el botón de WhatsApp mientras lo soluciono.",
            reply_markup=main_keyboard()
        )

# ── EJECUCIÓN PRINCIPAL ───────────────────────────────────────────────────────
def main():
    # 1. Iniciar Flask para Keep-Alive
    threading.Thread(target=run_flask, daemon=True).start()

    # 2. Iniciar el bot de Telegram
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_buttons))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 NAZARETH está lista y escuchando...")
    application.run_polling()

if __name__ == "__main__":
    main()
