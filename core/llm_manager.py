from typing import Optional
from datetime import datetime
import requests
from utils.config import (
    ALLOWED_COMMANDS,
    OLLAMA_HOST,
    OLLAMA_MODEL,
    OLLAMA_FALLBACK_MODEL,
    OLLAMA_CLOUD_ENABLED,
    OLLAMA_CLOUD_URL,
    OLLAMA_CLOUD_MODEL,
    OLLAMA_CLOUD_API_KEY
)
from utils.logger import logger


class LLMResponse:
    """Respuesta del LLM con soporte para tool calls"""
    def __init__(self, content: str, tool_calls: Optional[list] = None, source: str = "local"):
        self.content = content.strip() if content else ""
        self.tool_calls = tool_calls or []
        self.source = source  # "cloud" o "local"

    def has_tool_call(self) -> bool:
        return len(self.tool_calls) > 0


class OllamaManager:
    """Gestor de Ollama con soporte para Cloud > Local > Fallback"""
    
    def __init__(self):
        self.local_host = OLLAMA_HOST
        self.local_model = OLLAMA_MODEL
        self.fallback_model = OLLAMA_FALLBACK_MODEL
        self.cloud_enabled = OLLAMA_CLOUD_ENABLED
        self.cloud_url = OLLAMA_CLOUD_URL
        self.cloud_model = OLLAMA_CLOUD_MODEL
        self.cloud_api_key = OLLAMA_CLOUD_API_KEY
        self._local_available = None

    def is_local_available(self) -> bool:
        if self._local_available is not None:
            return self._local_available
        try:
            response = requests.get(f"{self.local_host}/api/tags", timeout=5)
            self._local_available = response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama Local no disponible: {e}")
            self._local_available = False
        return self._local_available

    def _build_tools_schema(self, tools: list) -> list:
        if not tools:
            return []
        schema = []
        for tool in tools:
            schema.append({
                "type": "function",
                "function": {
                    "name": tool.get("name", ""),
                    "description": tool.get("description", ""),
                    "parameters": tool.get("parameters", {})
                }
            })
        return schema

    def _call_api(self, url: str, model: str, messages: list,
                  tools: Optional[list] = None,
                  headers: Optional[dict] = None,
                  timeout: int = 120) -> Optional[LLMResponse]:
        payload = {
            "model": model,
            "messages": messages,
            "stream": False
        }
        if tools:
            payload["tools"] = self._build_tools_schema(tools)

        try:
            logger.debug(f"Llamando a {url} con modelo: {model}")
            logger.debug(f"Payload tools: {payload.get('tools', 'ninguno')}")
            response = requests.post(url, json=payload, headers=headers, timeout=timeout)
            if response.status_code == 200:
                data = response.json()
                message = data.get("message", {})
                content = message.get("content", "")
                tool_calls_data = message.get("tool_calls", [])
                logger.debug(f"Respuesta API - tool_calls raw: {tool_calls_data}")
                tool_calls = []
                for tc in tool_calls_data:
                    func = tc.get("function", {})
                    tool_calls.append({
                        "name": func.get("name", ""),
                        "arguments": func.get("arguments", {})
                    })
                logger.debug(f"Tool_calls parseadas: {tool_calls}")
                return LLMResponse(content, tool_calls)
            else:
                logger.error(f"Error {response.status_code}: {response.text[:200]}")
                return None
        except Exception as e:
            logger.error(f"Error llamando a Ollama: {e}")
            return None

    def chat(self, messages: list, tools: Optional[list] = None) -> Optional[LLMResponse]:
        """Cloud > Local > Fallback"""

        # 1. Intentar Cloud primero
        if self.cloud_enabled and self.cloud_api_key:
            logger.debug(f"Intentando Ollama Cloud: {self.cloud_model}")
            url = f"{self.cloud_url}/api/chat"
            headers = {
                "Authorization": f"Bearer {self.cloud_api_key}",
                "Content-Type": "application/json"
            }
            result = self._call_api(url, self.cloud_model, messages, tools, headers)
            if result is not None:
                result.source = "cloud"
                logger.info(f"Respuesta obtenida de Ollama Cloud: {self.cloud_model}")
                return result
            logger.warning("Ollama Cloud no disponible, intentando local...")

        # 2. Fallback a local primario
        if self.is_local_available():
            logger.debug(f"Intentando modelo local: {self.local_model}")
            url = f"{self.local_host}/api/chat"
            result = self._call_api(url, self.local_model, messages, tools)
            if result is not None:
                result.source = "local"
                logger.info(f"Respuesta obtenida de modelo local: {self.local_model}")
                return result
            logger.warning("Error con modelo local primario...")

            # 3. Fallback local secundario
            logger.debug(f"Intentando fallback local: {self.fallback_model}")
            result = self._call_api(url, self.fallback_model, messages, tools)
            if result is not None:
                result.source = "local"
                logger.info(f"Respuesta obtenida de fallback local: {self.fallback_model}")
                return result

        logger.error("Ningún modelo disponible")
        return None


class AgentPrompt:
    @staticmethod
    def get_system_prompt(facts: dict) -> str:
        now = datetime.now()
        date_str = now.strftime("%A %d de %B de %Y")
        time_str = now.strftime("%H:%M:%S")
        weekday = now.weekday()  # 0=lunes, 6=domingo
        dias = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
        context_summary = facts.get("context_summary")
        other_facts = {k: v for k, v in facts.items() if k != "context_summary"}
        facts_text = "\n".join([f"- {k}: {v}" for k, v in other_facts.items()]) if other_facts else "Sin datos personales guardados."
        summary_section = f"\nCONTEXTO PREVIO (resumido):\n{context_summary}\n" if context_summary else ""
        return f"""
Eres AgentPiro, un asistente personal de IA con acceso completo a Google Workspace mediante herramientas 'gog' para Gmail, Calendar, Drive, Docs, Sheets, Slides, Forms, Contacts, Tasks, YouTube, Photos, Chat, Classroom, People, Admin, Keep, Meet, Groups, Sites, Apps Script, Maps, Analytics y Search Console. Si la petición se puede cumplir usando estas herramientas, ÚSALAS SIEMPRE.

INFORMACIÓN DEL SISTEMA:
- Fecha actual: {date_str}
- Hora actual: {time_str}
- Día de la semana: {dias[weekday]}
- Esto es lo que significa "hoy", "mañana", "esta semana", "ayer" en el contexto de la conversación.
- Modelo local: {OLLAMA_MODEL}
- Modelo cloud: {OLLAMA_CLOUD_MODEL}
- Modelo activo: determinado por disponibilidad (cloud > local > fallback)

PERFIL DEL USUARIO:
{facts_text}
{summary_section}
HERRAMIENTAS GOOGLE DISPONIBLES:
Correo: gog_gmail_search, gog_gmail_send
Calendario: gog_calendar_events, gog_calendar_list, gog_calendar_create_event
Contactos: gog_contacts_list, gog_contacts_search
Drive: gog_drive_search, gog_drive_download
Sheets: gog_sheets_get, gog_sheets_update, gog_sheets_append, gog_sheets_create
Docs: gog_docs_cat, gog_docs_export, gog_docs_create
Tasks: gog_tasks_lists, gog_tasks_list, gog_tasks_add
YouTube: gog_youtube_search
Photos: gog_photos_list
Forms: gog_forms_get, gog_forms_responses
Slides: gog_slides_info, gog_slides_export
Genérica: gog_raw (cualquier comando gog no cubierto arriba: admin, classroom, chat, groups, keep, people, maps, analytics, appscript, sites, search console, etc.)

TELEGRAM (Telethon User API):
- telegram_get_me: Mi perfil de Telegram
- telegram_get_dialogs: Listar chats/conversaciones
- telegram_get_messages: Leer mensajes de un chat
- telegram_send_message: Enviar mensaje de texto
- telegram_send_file: Enviar archivo
- telegram_search_messages: Buscar en un chat
- telegram_read_all: Marcar como leídos
- telegram_download_media: Descargar multimedia
- telegram_export_chat: Exportar chat a archivo

HERRAMIENTAS DEL SISTEMA:
- get_current_time: Hora actual del sistema
- get_current_date: Fecha actual
- get_datetime_full: Fecha y hora
- execute_command: Ejecuta comandos Unix permitidos
- web_search: Busca en la web

DATOS INYECTADOS AUTOMÁTICAMENTE:
- Verás bloques entre --- con etiquetas como [Calendar: calendar/events_today], [Gmail: gmail/search], [Drive: drive/search], etc. Esos son DATOS REALES recién recuperados de las cuentas de Google del usuario. PRESENTA los datos de forma natural y conversacional. NO digas "no tengo acceso", "no puedo ver", ni similares.
- Cuando veas [Calendar: calendar/list_calendars] con una lista de calendarios, PRESENTA los calendarios disponibles.
- Cuando veas [Calendar: calendar/events_*] con eventos, PRESENTA los eventos al usuario.
- Cuando veas [Gmail: gmail/read] con datos de correos, LÉE los correos al usuario.
- Cuando veas [Web: ...] con resultados de búsqueda, PRESENTA la información.

ACCIONES QUE DEBES REALIZAR TÚ (tool calling):
- Enviar/responder correos (gog_gmail_send)
- Crear/modificar/eliminar eventos de calendario (gog_calendar_create_event, gog_calendar_update_event, gog_calendar_delete_event)
- Escribir en Sheets (gog_sheets_update, gog_sheets_append, gog_sheets_clear)
- Crear documentos/hojas (gog_docs_create, gog_sheets_create)
- Agregar tareas (gog_tasks_add)
- Operaciones con IDs específicos (gog_docs_cat, gog_docs_export, gog_sheets_get, gog_forms_get, gog_slides_info)
- **Cualquier otro comando gog** usa gog_raw con la sintaxis exacta del CLI. Ej: gog_raw(command="calendar colors"), gog_raw(command="people me"), gog_raw(command="chat spaces list"), gog_raw(command="classroom courses list")

EJEMPLOS DE INTERPRETACIÓN DE LENGUAJE NATURAL:
- "listame los calendarios" → datos inyectados con [Calendar: calendar/list_calendars]
- "que eventos tengo esta semana" → datos inyectados con [Calendar: calendar/events_week]
- "mis eventos de hoy" → datos inyectados con [Calendar: calendar/events_today]
- "leeme el ultimo correo" → datos inyectados con [Gmail: gmail/read]
- "tengo correos nuevos" → datos inyectados con [Gmail: gmail/search]
- "busca archivos en drive llamados reporte" → datos inyectados con [Drive: drive/search]
- "envía un correo a miguel diciendo hola" → USA tool calling gog_gmail_send
- "crea un evento mañana a las 10" → USA tool calling gog_calendar_create_event
- "agrega una tarea: comprar leche" → USA tool calling gog_tasks_add
- NUNCA respondas diciendo que "no tengo acceso". Usa las herramientas o datos inyectados proactivamente.
- Si el usuario solicita info general, responde normalmente.

TONE: Amigable y eficiente.
"""

    @staticmethod
    def get_tool_prompt(tools: list) -> list:
        return [
            {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"]
                }
            }
            for tool in tools
        ]
