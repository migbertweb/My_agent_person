# AgentPiro - Asistente Personal de IA

Asistente de IA personal, modular y seguro que se ejecuta completamente en local.

## 🚀 Inicio Rápido

```bash
cd agent-piro
./run.sh
```

## 📋 Requisitos

- Python 3.10+
- Ollama instalado (local)
- Conexión a internet (opcional, para Ollama Cloud)

## ⚙️ Configuración

### Variables de Entorno (`.env`)

```env
# Ollama Local
OLLAMA_HOST="http://localhost:11434"
OLLAMA_MODEL="gemma3:1b"
OLLAMA_FALLBACK_MODEL="gemma3:4b"

# Ollama Cloud (Opcional - prioridad sobre local)
OLLAMA_CLOUD_ENABLED="true"
OLLAMA_CLOUD_URL="https://api.ollama.com"
OLLAMA_CLOUD_MODEL="gemma3:12b"
OLLAMA_CLOUD_API_KEY="tu_api_key_aqui"

# Memoria
DB_PATH="./memory.db"

# Agente
MAX_ITERATIONS=5
AGENT_NAME="AgentPiro"
DEBUG_MODE=false

# Seguridad
ALLOWED_COMMANDS="date,time,cal,echo,ls,pwd,whoami,uname,cat"

# Texto a Voz (TTS)
TTS_ENABLED="true"
TTS_PROVIDER="edge"
TTS_VOICE="es-ES-AlvaroNeural"
TTS_RATE="0%"
TTS_PITCH="0%"
TTS_AUTO_PLAY="true"
```

## 🌐 Configurar Ollama Cloud

### 1. Obtener API Key

1. Accede a [Ollama Cloud](https://ollama.com/cloud)
2. Crea una cuenta si no la tienes
3. Genera una API Key en tu panel de usuario
4. Copia la clave

### 2. Habilitar en AgentPiro

Edita `.env`:

```env
OLLAMA_CLOUD_ENABLED="true"
OLLAMA_CLOUD_API_KEY="tu_api_key_aqui"
```

### 3. Estrategia de Fallback

AgentPiro intenta usar modelos en este orden:

1. **Ollama Cloud** (`gemma3:12b`) — si está habilitado y hay API key
2. **Modelo Local Primario** (`gemma3:1b`)
3. **Modelo Local Fallback** (`gemma3:4b`)

Si el modelo cloud falla, automáticamente cae a local.

## 📊 Características

- ✅ GUI minimalista con PySide6 (tema oscuro Catppuccin)
- ✅ Medición automática de tiempo de respuesta
- ✅ **Texto a Voz (TTS)** con edge-tts — voces naturales en español
- ✅ **Entrada por dictado** compatible con wtype/Handy — auto-detecta y envía automáticamente
- ✅ **Botón Mute** para silenciar/activar la voz en un clic
- ✅ **Bandeja del sistema** — minimiza a tray con icono personalizable
- ✅ Memoria persistente con SQLite
- ✅ Herramientas del sistema (hora, fecha, comandos)
- ✅ Soporte para Ollama Local y Cloud
- ✅ Fallback automático Cloud → Local
- ✅ Agent Loop con límite de iteraciones
- ✅ Logs de seguridad y auditoría

## 🛠️ Arquitectura

```
agent-piro/
├── core/           # Lógica del agente
│   ├── brain.py    # Agent Loop
│   ├── llm_manager.py  # Gestor de LLM
│   └── memory.py   # Base de datos
├── tools/          # Herramientas disponibles
├── gui/            # Interfaz gráfica
├── utils/          # Configuración y logging
└── main.py         # Entry point
```

## 📝 Herramientas Disponibles

- `get_current_time` - Obtiene la hora actual
- `get_current_date` - Obtiene la fecha actual
- `get_datetime_full` - Obtiene fecha y hora completa
- `execute_command` - Ejecuta comandos permitidos (whitelist)

## 🎤 Texto a Voz (TTS)

AgentPiro puede leer las respuestas en voz alta usando voces neurales de Microsoft Edge (edge-tts).

### Configuración

En `.env`:

```env
TTS_ENABLED="true"
TTS_PROVIDER="edge"
TTS_VOICE="es-ES-AlvaroNeural"   # Voz en español
TTS_RATE="+30%"                   # Velocidad
TTS_PITCH="-15Hz"                 # Tono
TTS_AUTO_PLAY="true"              # Reproducir automáticamente
```

### Controles

- **Botón 🔊/🔇** en la barra de entrada — silencia o activa la voz
- **Menú Archivo → Activar/Desactivar Voz** — mismo control

## ⌨️ Entrada por Dictado (Handy/wtype)

AgentPiro detecta automáticamente cuando el texto se ingresa mediante herramientas de dictado o automatización (wtype, Handy Desktop).

### Funcionamiento

- Si los caracteres llegan en **ráfagas rápidas** (< 50ms entre caracteres), se considera dictado/Handy
- Al detectar **3 segundos de silencio** tras la ráfaga, el mensaje se envía automáticamente
- La escritura manual nunca activa el envío automático

### Uso con Handy Desktop

```bash
# Handy envía el texto a la ventana de AgentPiro
handy "Escribe tu consulta aquí"
# AgentPiro lo detecta y envía automáticamente al detectar pausa
```

## 🔒 Seguridad

- **Whitelist de comandos**: Solo comandos autorizados pueden ejecutarse
- **Logs de auditoría**: Todas las acciones se registran
- **Aislamiento**: No hay acceso a APIs externas no autorizadas
- **Límite de iteraciones**: Máximo 5 vueltas del agent loop

## 📖 Documentación

- [Ollama API](https://docs.ollama.com/api)
- [Ollama Cloud](https://docs.ollama.com/cloud)

## 🎯 Próximos Pasos

- [ ] Más herramientas del sistema
- [ ] Exportación de conversaciones
- [ ] Transcripción de audio con Whisper
- [ ] Más voces y proveedores TTS
