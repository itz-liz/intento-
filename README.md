# IA Parlante con NPL - Sistema de Llamadas

Sistema de inteligencia artificial parlante que utiliza procesamiento de lenguaje natural (NLP) para analizar documentos PDF y responder preguntas por voz.

## 🚀 Características

- ✅ **Sin VAPI**: Sistema propio de procesamiento de voz
- 🎙️ **IA Parlante**: Escucha y responde con voz natural
- 🧠 **NPL Avanzado**: Usa NLP Cloud + Groq para análisis profundo
- 📱 **Interfaz Web Responsive**: Funciona en móviles y escritorio
- 🔊 **Text-to-Speech**: Respuestas en audio con gTTS
- 🎤 **Speech Recognition**: Reconocimiento de voz integrado
- 📝 **Análisis de PDFs**: Interpreta documentos y responde preguntas
- 🆔 **Sistema de IDs**: Cada llamada tiene un ID único

## 📋 Requisitos

```bash
Python 3.8+
ffmpeg (para procesamiento de audio)
```

## 🛠️ Instalación

1. **Clonar repositorio**
```bash
git clone <tu-repositorio>
cd intento-
```

2. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

3. **Instalar ffmpeg** (necesario para audio)
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Descargar de https://ffmpeg.org/download.html
```

4. **Configurar variables de entorno**
Copia el archivo `.env` y configura tus claves API:
- `TELEGRAM_BOT_TOKEN`: Token de tu bot de Telegram
- `GROQ_API_KEY`: API key de Groq
- `NLP_CLOUD_TOKEN`: Token de NLP Cloud

## 🚀 Uso

### Iniciar el bot

```bash
python llamadabot.py
```

Esto iniciará:
- Bot de Telegram
- Servidor web en http://localhost:5000

### Telegram

1. Inicia el bot: `/start`
2. Envía un PDF
3. Usa `/llamar` para obtener un ID de llamada
4. Pregunta por texto o audio de voz

### Interfaz Web

1. Abre http://localhost:5000 en tu navegador
2. Ingresa el ID de llamada que recibiste del bot
3. Escribe tu pregunta o usa el micrófono
4. Recibe respuesta en texto y audio

## 🎯 Flujo de Trabajo

```
Usuario → Bot Telegram
   ↓
Envía PDF
   ↓
Bot extrae texto y guarda en BD
   ↓
Usuario: /llamar
   ↓
Bot genera ID único (ej: a1b2c3d4)
   ↓
Usuario usa ID en interfaz web
   ↓
Hace pregunta (texto/voz)
   ↓
IA procesa con NLP + Groq
   ↓
Genera respuesta + audio
   ↓
Usuario recibe respuesta hablada
```

## 🧠 Tecnologías

- **NLP Cloud**: Procesamiento de lenguaje natural y transcripción de voz
- **Groq**: Modelo de IA para razonamiento y análisis
- **gTTS**: Síntesis de voz (Text-to-Speech)
- **SpeechRecognition**: Reconocimiento de voz
- **Flask**: Servidor web para interfaz
- **Telegram Bot API**: Interfaz de chat

## 📱 Interfaz Web Responsive

La interfaz está optimizada para:
- 📱 Teléfonos móviles
- 💻 Tablets
- 🖥️ Computadoras de escritorio

## 🔧 API REST

### GET /api/llamada/{call_id}
Consulta el estado de una llamada

**Respuesta:**
```json
{
  "id": "a1b2c3d4",
  "estado": "completada",
  "transcripcion": "¿De qué trata el libro?",
  "respuesta": "El libro trata sobre...",
  "audio_path": "respuesta_123.mp3",
  "created_at": "2026-01-29T10:30:00"
}
```

### POST /api/llamada/{call_id}/hablar
Envía una pregunta a la IA

**Body:**
```json
{
  "pregunta": "¿Cuál es la idea principal del capítulo 3?"
}
```

**Respuesta:**
```json
{
  "pregunta": "¿Cuál es la idea principal del capítulo 3?",
  "respuesta": "La idea principal del capítulo 3 es...",
  "audio_url": "/api/audio/respuesta_123.mp3"
}
```

## 📊 Base de Datos

SQLite con 2 tablas:

**usuarios**
- user_id (PK)
- pdf_text
- phone_number

**llamadas**
- id (PK, UUID corto)
- user_id (FK)
- estado (pendiente/completada)
- transcripcion
- respuesta
- audio_path
- created_at
- updated_at

## 🎤 Comandos del Bot

- `/start` - Iniciar el bot
- `/comandos` - Ver ayuda
- `/llamar` - Crear nueva llamada y obtener ID

## 🔒 Seguridad

- Las claves API se almacenan en `.env` (no commitear)
- SQLite local para datos de usuario
- CORS habilitado para interfaz web

## 🐛 Solución de Problemas

**Error de audio:**
```bash
# Verificar que ffmpeg esté instalado
ffmpeg -version
```

**Error de API:**
- Verifica que las claves en `.env` sean correctas
- Comprueba límites de uso de las APIs

**Puerto ocupado:**
```bash
# Cambiar puerto en llamadabot.py línea:
flask_app.run(host='0.0.0.0', port=5001)
```

## 📝 Licencia

Ver archivo LICENSE

## 👥 Contribuir

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/mejora`)
3. Commit cambios (`git commit -am 'Añade mejora'`)
4. Push a la rama (`git push origin feature/mejora`)
5. Abre un Pull Request

## 📧 Soporte

Para problemas o preguntas, abre un issue en GitHub.

---

Hecho con ❤️ usando NLP y IA
 
