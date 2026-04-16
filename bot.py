import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from groq import Groq
from dotenv import load_dotenv

# Cargar variables de entorno (Opcional si las pones directas abajo)
load_dotenv()

# ── CONFIGURACIÓN DE SEGURIDAD ────────────────────────────────────────────────
# RECOMENDACIÓN: Pega tus llaves aquí directamente para evitar errores de lectura
TELEGRAM_TOKEN = "8602807198:AAHHitHYRqxQGKwQx9uIOtkas9TtN6kxFaY"
GROQ_API_KEY = "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"

# Modelo recomendado en la documentación oficial de Groq
GROQ_MODEL = "llama-3.3-70b-versatile" 
WHATSAPP_NUMBER = "584264014765"
AULA_VIRTUAL = "https://academiajesusdenazareth.milaulas.com"

# Configuración de Logs para ver qué pasa en la terminal
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ── PROMPT DEL SISTEMA (LA PERSONALIDAD) ──────────────────────────────────────
SYSTEM_PROMPT = f"""Eres NAZARETH, la asistente virtual de la Academia Jesús de Nazareth en Venezuela.
Tu objetivo es ayudar a los alumnos a conocer nuestros cursos 100% Online con IA.
Tono: Muy amable, profesional y motivador. 
Datos clave: WhatsApp +{WHATSAPP_NUMBER}, Aula Virtual: {AULA_VIRTUAL}.
REGLA: Si preguntan por precios o inscripción, diles que pulsen el botón de WhatsApp."""

# ── CLIENTE GROQ ──────────────────────────────────────────────────────────────
client = Groq(api_key=GROQ_API_KEY)
# Diccionario para mantener una memoria corta de la conversación
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
    user_memory[user_id] = [] # Limpiar memoria al iniciar
    await update.message.reply_text(
        f"¡Hola {update.effective_user.first_name}! 👋 Soy NAZARETH.\n"
        "¿En qué área te gustaría especializarte hoy?",
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

    # Mantener historial corto (últimos 5 mensajes) para no saturar tokens
    if user_id not in user_memory:
        user_memory[user_id] = []
    
    user_memory[user_id].append({"role": "user", "content": user_input})
    user_memory[user_id] = user_memory[user_id][-5:] 

    try:
        # Petición a la API de Groq siguiendo la documentación Chat-Create
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + user_memory[user_id],
            temperature=0.7, # Creatividad balanceada
            max_tokens=500,  # Respuestas concisas
            top_p=1,
            stream=False
        )
        
        response_text = completion.choices[0].message.content
        user_memory[user_id].append({"role": "assistant", "content": response_text})
        
        await update.message.reply_text(response_text, reply_markup=main_keyboard())

    except Exception as e:
        logger.error(f"Error en Groq: {e}")
        await update.message.reply_text(
            "Lo siento, estamos recibiendo muchas consultas. Por favor, contacta directamente a nuestro "
            "WhatsApp para una atención inmediata.",
            reply_markup=main_keyboard()
        )

# ── EJECUCIÓN PRINCIPAL ───────────────────────────────────────────────────────
def main():
    if not TELEGRAM_TOKEN or not GROQ_API_KEY:
        print("❌ ERROR: No se encontraron las llaves API.")
        return

    # Construir la aplicación de Telegram
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Comandos y Mensajes
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 NAZARETH está en línea y escuchando...")
    app.run_polling()

if __name__ == "__main__":
    main()
