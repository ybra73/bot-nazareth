import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from groq import Groq

# ── CONFIGURACIÓN DE LLAVES (Insertadas directamente para evitar errores) ──────
TELEGRAM_TOKEN = "8602807198:AAHHitHYRqxQGKwQx9uIOtkas9TtN6kxFaY"
GROQ_API_KEY = "Gsk_MbSZpfsMcnw5iw5hIiEDWGdyb3FYzazoz9RQAd7PUqDzaMlblQlp"
GROQ_MODEL = "llama3-70b-8192"

# Datos de contacto
WHATSAPP_NUMBER = "584264014765" 
AULA_VIRTUAL = "https://academiajesusdenazareth.milaulas.com"

# Configuración de Logs para ver errores en la terminal
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ── PROMPT DEL SISTEMA (Personalidad de NAZARETH) ─────────────────────────────
SYSTEM_PROMPT = f"""Eres NAZARETH, la asistente virtual de la Academia Jesús de Nazareth (AVAJDN).
Ubicación: Venezuela. Modalidad: 100% Online.
Tu tono es cálido, motivador y profesional. 
IMPORTANTE: Resalta que usamos Inteligencia Artificial en TODOS los cursos.
Si preguntan por inscripciones o costos, diles que hablen con un asesor humano en WhatsApp: +{WHATSAPP_NUMBER}.
Enlace al Aula Virtual: {AULA_VIRTUAL}.
Sé concisa, responde en máximo 2 o 3 párrafos cortos."""

# ── CLIENTE GROQ ──────────────────────────────────────────────────────────────
client = Groq(api_key=GROQ_API_KEY)
conversations = {}

# ── TECLADO PRINCIPAL ─────────────────────────────────────────────────────────
def build_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("🛠️ Área Técnica", callback_data="area_tecnica")],
        [InlineKeyboardButton("📊 Área Administrativa", callback_data="area_admin")],
        [InlineKeyboardButton("🎨 Área Creativa", callback_data="area_creativa")],
        [InlineKeyboardButton("📲 ¡Inscribirme ahora!", url=f"https://wa.me/{WHATSAPP_NUMBER}")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ── MANEJADORES DE COMANDOS Y MENSAJES ────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde al comando /start"""
    user = update.effective_user
    conversations[user.id] = [] # Reiniciar memoria al empezar
    await update.message.reply_text(
        f"¡Hola {user.first_name}! 👋 Soy *NAZARETH*, tu guía de formación con IA.\n\n"
        "¿En qué área te gustaría especializarte hoy?",
        parse_mode="Markdown",
        reply_markup=build_main_keyboard()
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja los clics en los botones del teclado"""
    query = update.callback_query
    await query.answer()
    
    msg = (
        "¡Excelente elección! 🚀\n\n"
        "Pregúntame lo que quieras sobre esa área (ejemplo: '¿Qué enseñan en mecánica?') "
        "o escribe el nombre del curso que te interesa para darte detalles."
    )
    await query.edit_message_text(msg, reply_markup=build_main_keyboard())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el chat de texto usando la IA de Groq"""
    user_id = update.effective_user.id
    user_text = update.message.text

    # Mantener un historial básico para cada usuario
    if user_id not in conversations:
        conversations[user_id] = []
    
    conversations[user_id].append({"role": "user", "content": user_text})
    
    # Limitar historial para no saturar la API
    if len(conversations[user_id]) > 10:
        conversations[user_id] = conversations[user_id][-10:]

    try:
        # Llamada a la Inteligencia Artificial
        completion = client.chat.completions.create(
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + conversations[user_id],
            model=GROQ_MODEL,
            temperature=0.7,
        )
        
        reply = completion.choices[0].message.content
        conversations[user_id].append({"role": "assistant", "content": reply})
        
        await update.message.reply_text(reply, reply_markup=build_main_keyboard())

    except Exception as e:
        logger.error(f"Error en Groq: {e}")
        await update.message.reply_text(
            "Lo siento, mis circuitos están un poco ocupados. 😅\n"
            f"Por favor, contacta directamente a nuestros asesores aquí: https://wa.me/{WHATSAPP_NUMBER}"
        )

# ── EJECUCIÓN DEL BOT ──────────────────────────────────────────────────────────
def main():
    # Validar que existan las llaves
    if "Gsk_" not in GROQ_API_KEY:
        print("⚠️ ERROR: La API Key de Groq parece inválida.")
        return

    print("🤖 Iniciando bot NAZARETH...")
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Rutas de comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ ¡Bot en línea! Presiona Ctrl+C para detener.")
    app.run_polling()

if __name__ == "__main__":
    main()
