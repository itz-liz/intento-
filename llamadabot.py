import os
import sqlite3
import fitz
import requests
import nlpcloud
import json
import uuid
from datetime import datetime
from groq import Groq
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from gtts import gTTS
from pydub.utils import mediainfo
import speech_recognition as sr
from pydub import AudioSegment
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import threading
from PIL import Image
import pytesseract
import io

load_dotenv()

# Cliente de IA
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
nlp_client = nlpcloud.Client("fast-wav2vec2-xlsr-53-spanish", os.getenv("NLP_CLOUD_TOKEN"), gpu=True)

# Flask app para servidor web
flask_app = Flask(__name__)
CORS(flask_app)

# System prompt del experto en análisis documental
SYSTEM_PROMPT = """Eres un ASISTENTE ESPECIALIZADO en LECTURA E INTERPRETACIÓN DE LIBROS.

TU MISIÓN:
- Analizar profundamente el contenido del libro
- Explicar ideas complejas de forma clara
- Conectar conceptos entre diferentes partes
- Conversar de manera natural sobre el libro

HABILIDADES:
- Análisis textual avanzado
- Interpretación de significados profundos
- Síntesis de ideas principales
- Contextualización de conceptos
- Respuestas breves en audio (máx 40 segundos)
- Respuestas directas y conversacionales

REGLAS DE RESPUESTA:
- BASARSE EN EL LIBRO: Solo responde con información del documento
- CLARIDAD: Explica conceptos complejos de forma sencilla
- BREVEDAD: En audio/llamadas, máximo 40 segundos
- DIRECTO: Responde sin encabezados, listas ni secciones
- OPINIÓN INFORMADA: Puedes dar una opinión breve y razonada si el libro lo permite
- PRECISIÓN: Si falta info, di "Esa información no aparece en el libro"
- HONESTIDAD: Admite cuando no sabes algo

ESTILO:
- Conversacional y cercano
- Una sola respuesta continua, sin estructura tipo “Idea principal / Puntos clave / Conclusión”

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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS llamadas (
            id TEXT PRIMARY KEY,
            user_id INTEGER,
            estado TEXT,
            transcripcion TEXT,
            respuesta TEXT,
            audio_path TEXT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES usuarios(user_id)
        )
    ''')
    conn.commit()
    conn.close()

def extract_text_from_pdf(file_path):
    """
    Extrae texto de un PDF. Si el PDF es escaneado (solo imágenes),
    usa OCR para extraer el texto de las imágenes.
    """
    try:
        doc = fitz.open(file_path)
        text = ""
        
        # Primer intento: extracción directa de texto
        print(f"[PDF] Extrayendo texto de {len(doc)} páginas...")
        for page_num, page in enumerate(doc):
            page_text = page.get_text()
            text += page_text
            if page_num == 0:
                print(f"[PDF] Página 1: {len(page_text)} caracteres")
        
        # Si no hay texto, es un PDF escaneado - usar OCR
        if len(text.strip()) == 0:
            print(f"[PDF] PDF escaneado detectado. Usando OCR...")
            text = ""
            
            for page_num, page in enumerate(doc):
                print(f"[OCR] Procesando página {page_num + 1}/{len(doc)}...")
                
                # Convertir página a imagen
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom para mejor calidad
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                
                # Aplicar OCR con Tesseract
                try:
                    page_text = pytesseract.image_to_string(img, lang='spa')  # español
                    text += page_text + "\n"
                    print(f"[OCR] Página {page_num + 1}: {len(page_text)} caracteres extraídos")
                except Exception as e_ocr:
                    print(f"[OCR] Error en página {page_num + 1}: {str(e_ocr)}")
                    continue
                
                # Limitar a las primeras 20 páginas para evitar timeout
                if page_num >= 19:
                    print(f"[OCR] Limitado a 20 páginas para optimizar velocidad")
                    break
        
        doc.close()
        
        if len(text.strip()) > 0:
            print(f"[PDF] Texto extraído exitosamente: {len(text)} caracteres totales")
            return text
        else:
            print(f"[PDF] No se pudo extraer texto del PDF")
            return None
            
    except Exception as e:
        print(f"[ERROR] Error extrayendo PDF: {str(e)}")
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
        
        # Guardar en base de datos - USAR INSERT OR REPLACE para crear/actualizar usuario
        conn = sqlite3.connect('ia_servicio.db')
        cursor = conn.cursor()
        
        # Verificar si el usuario existe
        existe = cursor.execute("SELECT user_id FROM usuarios WHERE user_id = ?", (user_id,)).fetchone()
        
        if existe:
            # Actualizar
            cursor.execute("UPDATE usuarios SET pdf_text = ? WHERE user_id = ?", (texto_extraido, user_id))
            print(f"[DB] Usuario {user_id} actualizado con nuevo PDF")
        else:
            # Insertar nuevo usuario
            cursor.execute("INSERT INTO usuarios (user_id, pdf_text) VALUES (?, ?)", (user_id, texto_extraido))
            print(f"[DB] Nuevo usuario {user_id} creado con PDF")
        
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

    print(f"[CHAT] Usuario {user_id} pregunta: {pregunta[:50]}...")
    print(f"[CHAT] PDF encontrado en BD: {resultado is not None}")

    if not resultado or not resultado[0]:
        print(f"[CHAT] ERROR: Usuario {user_id} no tiene PDF en la base de datos")
        await update.message.reply_text("Primero envíame un PDF.")
        return

    pdf_texto = resultado[0]
    print(f"[CHAT] Usando PDF de {len(pdf_texto)} caracteres para responder")
    
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
                print(f"[CHAT] Audio enviado al usuario {user_id}")
            else:
                print(f"[CHAT] No se pudo generar audio para usuario {user_id}")
        except Exception as e_audio:
            print(f"[CHAT] Error con audio: {str(e_audio)}")
            
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
    
    print(f"[LLAMAR] Usuario {user_id} ejecutó /llamar")
    print(f"[LLAMAR] Resultado de BD: {resultado is not None}")
    
    if not resultado or not resultado[0]:
        conn.close()
        print(f"[LLAMAR] ERROR: Usuario {user_id} no tiene PDF cargado")
        await update.message.reply_text("Primero envíame un PDF.")
        return

    # Crear ID único para la llamada
    call_id = str(uuid.uuid4())[:8]
    pdf_texto = resultado[0]
    
    print(f"[LLAMAR] PDF encontrado: {len(pdf_texto)} caracteres")
    print(f"[LLAMAR] Creando llamada {call_id}")
    
    # Guardar llamada en base de datos
    conn.execute('''
        INSERT INTO llamadas (id, user_id, estado, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (call_id, user_id, 'pendiente', datetime.now(), datetime.now()))
    conn.commit()
    conn.close()
    
    mensaje = f"""🎙️ LLAMADA ACTIVADA

ID de llamada: {call_id}

Puedes usar este ID para:
1. Probar la llamada en la interfaz web: http://localhost:5000
2. Enviar preguntas por voz
3. Recibir respuestas habladas de la IA

Ahora puedes:
- Escribir tu pregunta aquí
- Enviar un audio (nota de voz)
- Usar la interfaz web con el ID: {call_id}

¿Cuál es tu pregunta sobre el PDF?"""
    
    await update.message.reply_text(mensaje)
    print(f"[LLAMAR] Llamada {call_id} creada exitosamente para usuario {user_id}")

# Función para procesar audio del usuario
async def procesar_audio_usuario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    
    try:
        # Descargar archivo de audio
        file = await context.bot.get_file(update.message.voice.file_id)
        audio_path = f"audio_usuario_{user_id}.ogg"
        await file.download_to_drive(audio_path)
        
        await update.message.reply_text("🎧 Escuchando tu audio...")
        
        # Convertir OGG a WAV para reconocimiento
        audio = AudioSegment.from_ogg(audio_path)
        wav_path = f"audio_usuario_{user_id}.wav"
        audio.export(wav_path, format="wav")
        
        # Reconocer voz con SpeechRecognition
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            try:
                # Intentar con Google Speech Recognition (gratis)
                texto = recognizer.recognize_google(audio_data, language="es-ES")
                print(f"[VOZ] Transcripción: {texto}")
            except sr.UnknownValueError:
                await update.message.reply_text("No pude entender el audio. ¿Puedes repetir?")
                return
            except sr.RequestError as e:
                # Si Google falla, usar NLP Cloud
                print(f"[VOZ] Google no disponible, usando NLP Cloud...")
                try:
                    with open(wav_path, 'rb') as f:
                        transcription = nlp_client.speech_recognition(f)
                        texto = transcription.get('text', '')
                except Exception as e2:
                    await update.message.reply_text(f"Error al procesar audio: {str(e2)}")
                    return
        
        # Limpiar archivos temporales
        os.remove(audio_path)
        os.remove(wav_path)
        
        await update.message.reply_text(f"📝 Entendí: {texto}\n\nProcesando respuesta...")
        
        # Procesar la pregunta como texto normal
        update.message.text = texto
        await chat_with_groq(update, context)
        
    except Exception as e:
        await update.message.reply_text(f"Error procesando audio: {str(e)}")

# API REST para interfaz web
@flask_app.route('/')
def index():
    return send_from_directory('.', 'interfaz_llamada.html')

@flask_app.route('/api/llamada/<call_id>', methods=['GET'])
def obtener_llamada(call_id):
    try:
        conn = sqlite3.connect('ia_servicio.db')
        cursor = conn.cursor()
        resultado = cursor.execute('''
            SELECT id, estado, transcripcion, respuesta, audio_path, created_at
            FROM llamadas WHERE id = ?
        ''', (call_id,)).fetchone()
        conn.close()
        
        if not resultado:
            return jsonify({'error': 'Llamada no encontrada'}), 404
        
        return jsonify({
            'id': resultado[0],
            'estado': resultado[1],
            'transcripcion': resultado[2],
            'respuesta': resultado[3],
            'audio_path': resultado[4],
            'created_at': resultado[5]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@flask_app.route('/api/llamada/<call_id>/procesar-audio', methods=['POST'])
def procesar_audio_llamada(call_id):
    try:
        # Verificar que se envió un archivo de audio
        if 'audio' not in request.files:
            return jsonify({'error': 'No se envió archivo de audio'}), 400
        
        audio_file = request.files['audio']
        
        if audio_file.filename == '':
            return jsonify({'error': 'Archivo de audio vacío'}), 400
        
        # Obtener información de la llamada
        conn = sqlite3.connect('ia_servicio.db')
        cursor = conn.cursor()
        llamada = cursor.execute('SELECT user_id FROM llamadas WHERE id = ?', (call_id,)).fetchone()
        
        if not llamada:
            conn.close()
            return jsonify({'error': 'Llamada no encontrada'}), 404
        
        user_id = llamada[0]
        pdf = cursor.execute('SELECT pdf_text FROM usuarios WHERE user_id = ?', (user_id,)).fetchone()
        
        if not pdf or not pdf[0]:
            conn.close()
            return jsonify({'error': 'No hay PDF cargado'}), 400
        
        pdf_texto = pdf[0]
        
        # Guardar audio temporal con extensión correcta
        temp_audio_path = f"audio_temp_{call_id}"
        audio_file.save(temp_audio_path)
        
        # Convertir a WAV usando pydub
        print(f"[AUDIO] Convirtiendo audio para llamada {call_id}...")
        try:
            # Intentar detectar y convertir el formato
            audio = AudioSegment.from_file(temp_audio_path)
            wav_path = f"audio_temp_{call_id}.wav"
            audio.export(wav_path, format="wav")
            os.remove(temp_audio_path)
            temp_audio_path = wav_path
        except Exception as e:
            print(f"[AUDIO] Error en conversión: {str(e)}, intentando como WAV directo")
            # Si falla, asumir que ya es WAV
            wav_path = f"audio_temp_{call_id}.wav"
            os.rename(temp_audio_path, wav_path)
            temp_audio_path = wav_path
        
        # Transcribir audio
        print(f"[AUDIO] Transcribiendo audio para llamada {call_id}...")
        recognizer = sr.Recognizer()
        pregunta = None
        
        try:
            with sr.AudioFile(temp_audio_path) as source:
                audio_data = recognizer.record(source)
                # Intentar con Google Speech Recognition primero
                try:
                    pregunta = recognizer.recognize_google(audio_data, language="es-ES")
                    print(f"[VOZ] Transcripción exitosa: {pregunta}")
                except sr.UnknownValueError:
                    print(f"[VOZ] Google no entiende, intentando NLP Cloud...")
                    # Fallback a NLP Cloud
                    try:
                        with open(temp_audio_path, 'rb') as f:
                            transcription = nlp_client.speech_recognition(f)
                            pregunta = transcription.get('text', '')
                            if pregunta:
                                print(f"[VOZ] Transcripción NLP Cloud: {pregunta}")
                    except Exception as e2:
                        print(f"[ERROR] NLP Cloud también falló: {str(e2)}")
                except sr.RequestError as e:
                    print(f"[VOZ] Error en Google Recognition: {str(e)}")
                    # Fallback a NLP Cloud
                    try:
                        with open(temp_audio_path, 'rb') as f:
                            transcription = nlp_client.speech_recognition(f)
                            pregunta = transcription.get('text', '')
                            if pregunta:
                                print(f"[VOZ] Transcripción NLP Cloud: {pregunta}")
                    except Exception as e2:
                        print(f"[ERROR] NLP Cloud también falló: {str(e2)}")
        except Exception as e:
            print(f"[ERROR] Error leyendo archivo de audio: {str(e)}")
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
            return jsonify({'error': f'Error al procesar audio: {str(e)}'}), 400
        
        if not pregunta:
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)
            return jsonify({'error': 'No se pudo transcribir el audio. Intenta hablar más claro.'}), 400
        
        # Limpiar archivo temporal
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
        
        # Procesar pregunta con IA
        import asyncio
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            respuesta = loop.run_until_complete(procesar_pregunta_con_nlp(pregunta, pdf_texto, user_id))
            
            # Generar audio de respuesta
            audio_file_path = loop.run_until_complete(generar_audio_desde_texto(respuesta, user_id))
            
        except Exception as e:
            return jsonify({'error': f'Error procesando pregunta: {str(e)}'}), 500
        
        # Actualizar llamada en BD
        try:
            cursor.execute('''
                UPDATE llamadas 
                SET transcripcion = ?, respuesta = ?, audio_path = ?, estado = ?, updated_at = ?
                WHERE id = ?
            ''', (pregunta, respuesta, audio_file_path, 'completada', datetime.now(), call_id))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[ERROR] Error actualizando BD: {str(e)}")
        
        return jsonify({
            'exito': True,
            'pregunta': pregunta,
            'respuesta': respuesta,
            'audio_url': f'/api/audio/{audio_file_path}' if audio_file_path else None
        })
        
    except Exception as e:
        print(f"[ERROR] Error en procesar_audio_llamada: {str(e)}")
        return jsonify({'error': str(e)}), 500

@flask_app.route('/api/audio/<filename>')
def servir_audio(filename):
    return send_from_directory('.', filename)

def run_flask():
    flask_app.run(host='0.0.0.0', port=5001, debug=False)

# Iniciar bot
if __name__ == '__main__':
    init_db()
    
    # Iniciar servidor Flask en thread separado
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print("Servidor web iniciado en http://localhost:5001")
    
    # Iniciar bot de Telegram
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("comandos", comandos))
    app.add_handler(CommandHandler("llamar", llamar))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_document))
    app.add_handler(MessageHandler(filters.VOICE, procesar_audio_usuario))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_with_groq))

    print("Bot encendido...")
    app.run_polling()