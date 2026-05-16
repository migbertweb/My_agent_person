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
OLLAMA_MODEL="llama3.2"
OLLAMA_FALLBACK_MODEL="gemma4:31b-cloud"

# Ollama Cloud (Opcional)
OLLAMA_CLOUD_ENABLED="false"
OLLAMA_CLOUD_URL="https://api.ollama.com"
OLLAMA_CLOUD_API_KEY=""

# Otros
MAX_ITERATIONS=5
AGENT_NAME="AgentPiro"
DEBUG_MODE=false
ALLOWED_COMMANDS="date,time,cal,echo,ls,pwd,whoami,uname,cat"
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

1. **Modelo Primario Local** (`llama3.2`)
2. **Modelo Fallback Local** (`gemma4:31b-cloud`)
3. **Ollama Cloud** (si está habilitado)

Si el modelo local falla, automáticamente usa el siguiente en la lista.

## 📊 Características

- ✅ GUI minimalista con PySide6
- ✅ Medición automática de tiempo de respuesta
- ✅ Memoria persistente con SQLite
- ✅ Herramientas del sistema (hora, fecha, comandos)
- ✅ Soporte para Ollama Local y Cloud
- ✅ Fallback automático entre modelos
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

## 🔒 Seguridad

- **Whitelist de comandos**: Solo comandos autorizados pueden ejecutarse
- **Logs de auditoría**: Todas las acciones se registran
- **Aislamiento**: No hay acceso a APIs externas no autorizadas
- **Límite de iteraciones**: Máximo 5 vueltas del agent loop

## 📖 Documentación

- [Ollama API](https://docs.ollama.com/api)
- [Ollama Cloud](https://docs.ollama.com/cloud)

## 🎯 Próximos Pasos

- [ ] Integración con ElevenLabs para texto a voz
- [ ] Transcripción de audio con Whisper
- [ ] Más herramientas del sistema
- [ ] Exportación de conversaciones
- [ ] Despliegue en la nube (Firebase)
