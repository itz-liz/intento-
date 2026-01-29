# 🎙️ Cómo Usar la IA Parlante

## 📱 Pasos para Usar en Web

### 1️⃣ Obtener ID de Llamada (Telegram)
```
Bot de Telegram → /llamar
↓
Recibes: ID de llamada (ej: aa979dd6)
```

### 2️⃣ Abrir Interfaz Web
- Abre en tu navegador: `http://localhost:5001`
- O en celular: `http://[tu-ip]:5001`

### 3️⃣ Pegar el ID de Llamada
- Campo: "ID de Llamada"
- Pega el ID que recibiste del bot

### 4️⃣ Presionar el Micrófono 🎤
- Botón grande con ícono de micrófono
- Verás que empieza a grabar
- El texto cambiará a "Grabando... Habla ahora"
- Las ondas se animan

### 5️⃣ Hablar tu Pregunta
- Habla claro y natural
- Puedes preguntar sobre el PDF que enviaste
- El contador de tiempo va aumentando

### 6️⃣ Detener & Enviar
- Presiona el botón rojo **"⏹️ Detener & Enviar"** que aparece
- El audio se envía automáticamente
- Verás un loading "Procesando tu voz..."

### 7️⃣ Recibir Respuesta
- La IA procesa tu pregunta
- Genera una respuesta por voz
- Se reproduce automáticamente
- Ves la transcripción y la respuesta en texto

---

## 📋 Flujo Completo

```
1. Presionar 🎤              → Empieza grabación
                             (El botón rojo aparece)

2. Hablar pregunta          → Grabando con contador
                             (Ondas animadas)

3. Presionar ⏹️ Enviar      → Se detiene y envía
                             (Loading: "Procesando")

4. La IA procesa            → Transcribe + Piensa + Responde
                             (Lleva 2-5 segundos)

5. Respuesta + Audio        → Se reproduce automáticamente
                             (Ves texto y escuchas)

6. Presionar 🎤 de nuevo    → Nueva pregunta
                             (Vuelve al inicio)
```

---

## 💡 Tips

✅ **Habla claro** - La transcripción mejora si pronuncias bien
✅ **Pausas naturales** - No hables todo de corrido
✅ **En español** - Asegúrate de hablar en español
✅ **Preguntas sobre el PDF** - Solo responde sobre el documento
✅ **Presiona "Detener & Enviar"** - No se envía automáticamente

❌ **No olvides:** Presionar el botón rojo para enviar
❌ **No esperes:** La respuesta no sale si no presionas "Enviar"

---

## 🐛 Problemas Comunes

### ❌ "No se grabó audio"
**Causa:** Presionaste "Detener & Enviar" sin haber grabado nada

**Solución:**
1. Presiona el botón 🎤 (debe cambiar a 🔴 Grabando)
2. Habla tu pregunta (espera al menos 1 segundo)
3. Presiona el botón rojo "⏹️ Detener & Enviar"
4. Debe mostrar un loading "Procesando tu voz..."

**Checklist:**
- ✅ ¿Presionaste el micrófono? (debe decir "🔴 Grabando...")
- ✅ ¿Hablaste al menos 1 segundo?
- ✅ ¿Aparece el botón rojo "⏹️ Detener & Enviar"?
- ✅ ¿Presionaste el botón rojo?

### ❌ "No se pudo transcribir el audio"
- Intenta hablar más claro
- Reduce el ruido de fondo
- Asegúrate de tener internet

### ❌ "Llamada no encontrada"
- Verifica el ID de llamada
- Cópialo exactamente del bot
- No agregues espacios

### ❌ "No hay PDF cargado"
- En Telegram primero envía un PDF
- Luego usa `/llamar`
- Después abre la web

---

## 🌐 Acceso Remoto

Si quieres acceder desde otro dispositivo:

1. En la terminal donde corre el bot:
   ```
   Servidor web iniciado en http://localhost:5001
   Running on http://10.0.0.54:5001  ← Copia esta IP
   ```

2. Desde tu celular:
   ```
   http://10.0.0.54:5001
   ```

3. Pega el ID de llamada y comienza

---

¡Disfruta conversando con la IA! 🚀
