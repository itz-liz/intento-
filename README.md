# Llamada Bot Telegram V1

Asistente conversacional que analiza documentos PDF y responde preguntas por texto y voz a través de Telegram y una interfaz web.

## Resumen

Este proyecto combina:

- Bot de Telegram para carga de PDF y conversación.
- API Flask para procesamiento de audio desde la web.
- Transcripción de voz y síntesis de audio.
- Razonamiento sobre contenido documental con IA.

## Video de Introducción
[![Miniatura video de introducción](https://img.youtube.com/vi/w8wFlB879XM/hqdefault.jpg)](https://youtu.be/w8wFlB879XM)

[Ver video de introducción](https://youtu.be/w8wFlB879XM)

Video generado con: Google Flow, Google IA Studio.

## Video de funcionamiento
[![Miniatura video de funcionamiento](https://img.youtube.com/vi/WUltsIs_YrE/hqdefault.jpg)](https://youtu.be/WUltsIs_YrE)

[Ver video de funcionamiento](https://youtu.be/WUltsIs_YrE)

## Funcionalidades principales

- Carga y lectura de PDFs (incluyendo OCR con Tesseract para PDFs escaneados).
- Consulta del contenido del documento con respuestas contextuales.
- Flujo por voz: grabación → transcripción → respuesta IA → audio de salida.
- Generación de IDs de llamada para sesiones desde la interfaz web.
- Persistencia local en SQLite (`usuarios` y `llamadas`).

## Arquitectura

- `llamadabot.py`: orquestador principal (Telegram + Flask + IA + BD).
- `interfaz_llamada.html`: cliente web para grabación y reproducción de respuestas.
- `ia_servicio.db`: base SQLite generada automáticamente en ejecución.

## Requisitos

### Software

- Python 3.10+
- ffmpeg + ffprobe (obligatorio para convertir audio webm/ogg)
- Tesseract OCR (recomendado para PDFs escaneados)

### Dependencias Python

Instaladas desde `requirements.txt`.

## Instalación

1) Clona el repositorio:

```bash
git clone https://github.com/itz-liz/Llamada_Bot_TelegramV1.git
cd Llamada_Bot_TelegramV1
```

2) Crea y activa entorno virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3) Instala dependencias Python:

```bash
pip install -r requirements.txt
```

4) Instala binarios del sistema:

```bash
# Ubuntu / Debian
sudo apt-get install -y ffmpeg tesseract-ocr tesseract-ocr-spa

# macOS
brew install ffmpeg tesseract
```

## Configuración (`.env`)

Define las variables en formato `CLAVE=valor`:

```env
TELEGRAM_BOT_TOKEN=tu_token_de_telegram
GROQ_API_KEY=tu_api_key_de_groq
NLP_CLOUD_TOKEN=tu_token_de_nlp_cloud
```

## Ejecución

```bash
python3 llamadabot.py
```

Al iniciar:

- Bot de Telegram en modo polling.
- Servidor Flask en `http://localhost:5001`.

## Flujo de uso

1. En Telegram ejecuta `/start`.
2. Envía un PDF.
3. Ejecuta `/llamar` para obtener un `call_id`.
4. Abre la interfaz web y pega el `call_id`.
5. Graba tu pregunta de voz.
6. Recibe transcripción, respuesta textual y audio.

