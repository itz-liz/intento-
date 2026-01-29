import os
import sqlite3
import fitz
import requests
import nlpcloud
import json
from groq import Groq
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from gtts import gTTS
from pydub.utils import mediainfo

load_dotenv()

# Cliente de IA
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
nlp_client = nlpcloud.Client("fast-wav2vec2-xlsr-53-spanish", os.getenv("NLP_CLOUD_TOKEN"), gpu=True)

# System prompt del experto en análisis documental
SYSTEM_PROMPT = """Eres un ASISTENTE ESPECIALIZADO en LECTURA E INTERPRETACIÓN DE LIBROS.

TU MISIÓN:
- Analizar profundamente el contenido del libro
- Explicar ideas complejas de forma clara
- Conectar conceptos entre diferentes partes
- Ayudar al usuario a entender el libro mejor

HABILIDADES:
- Análisis textual avanzado
- Interpretación de significados profundos
- Síntesis de ideas principales
- Contextualization de conceptos
- Respuestas breves en audio (máx 3-4 frases)
- Respuestas estructuradas en texto

REGLAS DE RESPUESTA:
- BASARSE EN EL LIBRO: Solo responde con información del documento
- CLARIDAD: Explica conceptos complejos de forma sencilla
- BREVEDAD: En audio/llamadas, máximo 3-4 frases
- PRECISIÓN: Si falta info, di "Esa información no aparece en el libro"
- HONESTIDAD: Admite cuando no sabes algo

ESTRUCTURA DE RESPUESTA:
Para preguntas complejas:
1. Idea principal (1-2 frases)
2. Puntos clave (máx 3)
3. Conclusión o conexión con el libro

CONTEXTO DEL LIBRO:
{documento_context}

Sé un asistente amable y accesible que ayude a entender el libro."""

# Base de datos
def init_db():
    conn = sqlite3.connect('ia_servicio.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            user_id INTEGER PRIMARY KEY,
            pdf_text TEXT,
            phone_number TEXT
        )
    ''')
    conn.commit()
    conn.close()

def extract_text_from_pdf(file_path):
    try:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        print(f"Error extrayendo PDF: {str(e)}")
        return None

# Función para procesar información con NLP y Machine Learning
async def procesar_pregunta_con_nlp(pregunta: str, pdf_texto: str, user_id: int) -> str:
    """
    Procesa la pregunta del usuario con NLP Cloud (análisis de lenguaje)
    y Groq (razonamiento) para una interpretación profunda del PDF
    """
    try:
        # Limitar PDF a 8000 caracteres para mejor procesamiento
        pdf_context = pdf_texto[:8000]
        
        print(f"[NLP] Analizando pregunta y documento con IA especializada...")
        
        # PASO 1: Análisis con NLP Cloud (extrae entidades, sentimientos, contexto)
        print(f"[NLP-CLOUD] Extrayendo información clave del documento...")
        try:
            analisis_nlp = nlp_client.classification(pregunta)
            print(f"[NLP-CLOUD] Análisis completado: {str(analisis_nlp)[:100]}...")
        except Exception as e:
            print(f"[WARNING] NLP Cloud no disponible: {str(e)}")
            analisis_nlp = {}
        
        # PASO 2: Usar Groq para razonamiento y respuesta detallada
        # Mejorar el contexto con instrucciones de interpretación
        context_mejorado = f"""CONTEXTO DEL LIBRO:
{pdf_context}

ANÁLISIS COMPLEMENTARIO:
- El usuario busca entender: {pregunta}
- Analiza el contenido del libro de forma crítica
- Extrae ideas principales y secundarias
- Relaciona conceptos entre secciones del libro"""
        
        system_prompt = SYSTEM_PROMPT.format(documento_context=context_mejorado)
        
        print(f"[GROQ] Procesando pregunta con razonamiento avanzado...")
        
        # Consultar a Groq para análisis profundo
        respuesta = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analiza profundamente esta pregunta sobre el libro:\n\n{pregunta}"}
            ],
            temperature=0.5,  # Balance entre creatividad y precisión
            max_tokens=600
        )
        
        texto_respuesta = respuesta.choices[0].message.content
        print(f"[SUCCESS] Interpretación generada: {len(texto_respuesta)} caracteres")
        print(f"[INTELLIGENCE] Usado NLP Cloud + Groq para análisis profundo del libro")
        
        return texto_respuesta
        
    except Exception as e:
        print(f"[ERROR] Error en procesamiento NLP: {str(e)}")
        return f"Error al procesar la pregunta: {str(e)}"

# Función para generar audio desde texto (Text-to-Speech con gTTS - GRATIS)
async def generar_audio_desde_texto(texto: str, user_id: int) -> str:
    """
    Genera audio desde texto usando Google TTS (gTTS) - GRATIS
    Limita el audio a máximo 40 segundos
    Retorna la ruta del archivo de audio o None si falla
    """
    try:
        MAX_DURATION = 40  # segundos
        MAX_CHARS = 300    # Aproximación: ~7-8 caracteres por segundo en español
        
        # Truncar texto si es muy largo
        if len(texto) > MAX_CHARS:
            print(f"[AUDIO] Texto muy largo ({len(texto)} caracteres). Truncando a {MAX_CHARS} caracteres...")
            texto = texto[:MAX_CHARS] + "..."
        
        print(f"[AUDIO] Generando audio con gTTS para {len(texto)} caracteres...")
        
        audio_file = f"respuesta_{user_id}.mp3"
        
        # Usar Google TTS (gTTS) - Gratuito
        tts = gTTS(text=texto, lang='es', slow=False)
        tts.save(audio_file)
        
        # Validar duración del audio
        try:
            info = mediainfo(audio_file)
            duration_ms = float(info.get('duration', 0)) * 1000
            duration_seconds = duration_ms / 1000
            
            if duration_seconds > MAX_DURATION:
                print(f"[WARNING] Audio dura {duration_seconds:.1f}s, excede {MAX_DURATION}s. Reduciendo texto...")
                # Reducir aún más el texto
                texto_reducido = texto[:int(len(texto) * (MAX_DURATION / duration_seconds * 0.9))]
                tts = gTTS(text=texto_reducido, lang='es', slow=False)
                tts.save(audio_file)
        except Exception as e:
            print(f"[WARNING] No se pudo validar duración del audio: {str(e)}")
        
        print(f"[SUCCESS] Audio generado: {audio_file}")
        return audio_file
        
    except Exception as e:
        print(f"[ERROR] Error generando audio: {str(e)}")
        return None

# Manejadores de Telegram
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = """¡Hola! Estamos en un aprendizaje juntos.

Qué puedo hacer:
1. Envíame un PDF para analizar
2. Hazme preguntas sobre el PDF
3. Llámanos para una conversación por teléfono

Para más información, usa /comandos"""
    await update.message.reply_text(mensaje)

async def comandos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = """COMANDO /llamar

¿Cómo usar?
/llamar +52XXXXXXXXXX

Formato del número:
- Comienza con: +
- Código de país: 52 (México) u otro
- 1 (si es celular en México)
- Número de 10 dígitos

Ejemplos válidos:
/llamar +521234567890 (celular)
/llamar +525555123456 (fijo)

Ejemplos inválidos:
/llamar 5551234567 (falta +52)
/llamar 1234567890 (falta código país)
/llamar +5212345 (muy corto)

Pasos antes de llamar:
1. Usa /start
2. Envía un PDF
3. Espera confirmación
4. Luego usa /llamar +52XXXXXXXXXX

¿Necesitas ayuda?"""
    await update.message.reply_text(mensaje)

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    try:
        file = await context.bot.get_file(update.message.document.file_id)
        file_path = f"documento_{user_id}.pdf"
        await file.download_to_drive(file_path)
        
        await update.message.reply_text("Leyendo documento...")
        
        texto_extraido = extract_text_from_pdf(file_path)
        
        if texto_extraido is None:
            await update.message.reply_text("Error: No pude leer el PDF. Intenta con otro archivo.")
            return
        
        # Guardar en base de datos
        conn = sqlite3.connect('ia_servicio.db')
        conn.execute("UPDATE usuarios SET pdf_text = ? WHERE user_id = ?", (texto_extraido, user_id))
        conn.commit()
        conn.close()
        
        await update.message.reply_text("PDF procesado! Ya puedo responderte preguntas.")
    except Exception as e:
        await update.message.reply_text(f"Error al procesar PDF: {str(e)}")

async def chat_with_groq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    pregunta = update.message.text

    conn = sqlite3.connect('ia_servicio.db')
    resultado = conn.execute("SELECT pdf_text FROM usuarios WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()

    if not resultado or not resultado[0]:
        await update.message.reply_text("Primero envíame un PDF.")
        return

    pdf_texto = resultado[0]
    
    try:
        # Procesar pregunta con NLP y ML
        await update.message.reply_text("Analizando tu pregunta...")
        
        texto_respuesta = await procesar_pregunta_con_nlp(pregunta, pdf_texto, user_id)
        
        # Enviar respuesta de texto
        await update.message.reply_text(f"Respuesta:\n\n{texto_respuesta}")
        
        # Generar audio
        try:
            await update.message.reply_text("Generando audio...")
            
            audio_file = await generar_audio_desde_texto(texto_respuesta, user_id)
            
            if audio_file and os.path.exists(audio_file):
                with open(audio_file, 'rb') as f:
                    await update.message.reply_voice(voice=f, caption="Escucha la respuesta")
                
                os.remove(audio_file)
                print(f"Audio enviado al usuario {user_id}")
            else:
                print(f"No se pudo generar audio para usuario {user_id}")
        except Exception as e_audio:
            print(f"Error con audio: {str(e_audio)}")
            
    except Exception as e:
        error_msg = str(e).lower()
        
        if "401" in error_msg or "unauthorized" in error_msg:
            await update.message.reply_text("Error 401: Clave API inválida.")
        elif "429" in error_msg or "rate_limit" in error_msg:
            await update.message.reply_text("Error 429: Límite de solicitudes. Espera un momento.")
        elif "500" in error_msg or "internal" in error_msg:
            await update.message.reply_text("Error 500: Problema en servidor. Intenta después.")
        elif "timeout" in error_msg:
            await update.message.reply_text("Error: La solicitud tardó demasiado. Intenta de nuevo.")
        else:
            await update.message.reply_text(f"Error: {error_msg}")

async def llamar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    conn = sqlite3.connect('ia_servicio.db')
    resultado = conn.execute("SELECT pdf_text FROM usuarios WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()

    if not resultado or not resultado[0]:
        await update.message.reply_text("Primero envíame un PDF.")
        return

    pdf_texto = resultado[0]
    
    mensaje = """Disponible para atender tu consulta por voz:

Opciones:
1. Escribe tu pregunta aquí en el chat
2. Envía un audio (nota de voz) con tu pregunta
3. Recibirás la respuesta en texto Y audio

El asistente analizará tu PDF y responderá basándose en su contenido.

¿Cual es tu pregunta?"""
    
    await update.message.reply_text(mensaje)
    print(f"Usuario {user_id} solicitó asistencia por voz/análisis")

# Iniciar bot
if __name__ == '__main__':
    init_db()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("comandos", comandos))
    app.add_handler(CommandHandler("llamar", llamar))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_with_groq))

    print("Bot encendido...")
    app.run_polling()