import os
import logging
import urllib.parse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from groq import Groq
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# ── Configuración ──────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama3-70b-8192"
WHATSAPP_NUMBER = "584264014765"  # Formato internacional corregido
AULA_VIRTUAL = "https://academiajesusdenazareth.milaulas.com"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ── Catálogo de cursos ─────────────────────────────────────────────────────────
CURSOS = {
    "🛠️ Técnica e Industrial": [
        "Mecánica Automotriz con IA", "Mecánica de Motos con IA",
        "Reparación de Cajas Automáticas", "Electrónica y Robótica con IA",
        "Reparación de Celulares", "Refrigeración Avanzada"
    ],
    "📊 Administrativa y Comercial": [
        "Inglés con IA", "Marketing Digital y Ventas",
        "Asistente de Contabilidad con IA", "Excel (Básico a Avanzado)",
        "Asistente de Farmacia", "Computación y Ofimática"
    ],
    "🎨 Creativa y Artesanal": [
        "Peluquería y Estilo", "Barbería Profesional",
        "Diseño de Cejas y Pestañas", "Sistemas de Uñas",
        "Corte y Confección"
    ],
}

# ── Prompt del sistema ─────────────────────────────────────────────────────────
SYSTEM_PROMPT = f"""Eres NAZARETH, la asistente virtual de la Academia Jesús de Nazareth (AVAJDN).
Ubicación: Venezuela. Modalidad: 100% Online.
Tu tono es cálido, motivador y profesional. Resalta que usamos IA en todos los cursos.
WhatsApp: +{WHATSAPP_NUMBER}. Aula: {AULA_VIRTUAL}.
Instrucción: Sé concisa (máximo 3 párrafos). Si preguntan por inscripción o precios, invítalos al WhatsApp."""

# ── Cliente Groq ──────────────────────────────────────────────────────────────
client = Groq(api_key=GROQ_API_KEY)
conversations = {}

# ── Funciones de Teclado ───────────────────────────────────────────────────────
def build_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("🛠️ Área Técnica", callback_data="area_tecnica")],
        [InlineKeyboardButton("📊 Área Administrativa", callback_data="area_admin")],
        [InlineKeyboardButton("🎨 Área Creativa", callback_data="area_creativa")],
        [InlineKeyboardButton("📲 ¡Inscribirme ahora!", url=f"https://wa.me/{WHATSAPP_NUMBER}")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ── Handlers ───────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    conversations[user.id] = []
    await update.message.reply_text(
        f"¡Hola {user.first_name}! 👋 Soy *NAZARETH*.\n¿En qué área te gustaría formarte hoy?",
        parse_mode="Markdown",
        reply_markup=build_main_keyboard()
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if "area" in query.data:
        msg = "Has seleccionado un área. ¿Qué curso te interesa? Escríbemelo y te daré detalles."
        await query.edit_message_text(msg, reply_markup=build_main_keyboard())

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    if user_id not in conversations: conversations[user_id] = []
    conversations[user_id].append({"role": "user", "content": user_text})

    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + conversations[user_id],
            model=GROQ_MODEL,
        )
        reply = chat_completion.choices[0].message.content
        await update.message.reply_text(reply, reply_markup=build_main_keyboard())
    except Exception as e:
        logger.error(e)
        await update.message.reply_text("Lo siento, tengo mucha demanda. Escríbenos al WhatsApp.")

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    if not TELEGRAM_TOKEN or not GROQ_API_KEY:
        print("ERROR: Falta el Token o la API Key en el entorno.")
        return

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 Bot NAZARETH en línea...")
    app.run_polling()

if __name__ == "__main__":
    main()
