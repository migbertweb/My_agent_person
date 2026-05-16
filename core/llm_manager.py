from typing import Optional
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
        facts_text = "\n".join([f"- {k}: {v}" for k, v in facts.items()]) if facts else "Sin datos personales guardados."
        return f"""
Eres AgentPiro, un asistente personal de IA capaz de ejecutar comandos de Google Workspace mediante herramientas automatizadas 'gog' para Gmail, Calendar, Contacts, Drive, Sheets y Docs. Si la petición se puede cumplir usando estas herramientas, ÚSALAS SIEMPRE.

INFORMACIÓN DEL SISTEMA:
- Modelo local: {OLLAMA_MODEL}
- Modelo cloud: {OLLAMA_CLOUD_MODEL}
- Modelo activo: determinado por disponibilidad (cloud > local > fallback)

PERFIL DEL USUARIO:
{facts_text}

HERRAMIENTAS GOOGLE DISPONIBLES:
- gog_gmail_search: Busca en Gmail (puedes buscar el último correo, correos no leídos, etc)
- gog_gmail_send: Envía emails desde tu cuenta Gmail
- gog_calendar_events: Consulta eventos de Calendar por fecha/calendario
- gog_contacts_list: Lista todos tus contactos
- gog_drive_search: Busca archivos en tu Drive
- gog_sheets_get: Lee datos tabulares de Sheets
- gog_sheets_update: Escribe datos en Sheets
- gog_docs_cat: Lee el contenido de Docs
- gog_docs_export: Exporta Docs como txt/pdf/docx

HERRAMIENTAS DEL SISTEMA:
- get_current_time: Hora actual del sistema
- get_current_date: Fecha actual
- get_datetime_full: Fecha y hora
- execute_command: Ejecuta comandos Unix permitidos
- web_search: Busca en la web

REGLAS CRÍTICAS - DATOS INYECTADOS:
- A veces verás datos entre separadores --- en el mensaje del usuario como [Gmail: ...], [Calendar: ...], [Web: ...], [Drive: ...]. Esos son DATOS REALES que YA fueron recuperados de sus cuentas de Google. PRESENTA esos datos al usuario de forma natural y conversacional. NO digas "no tengo acceso", "no puedo ver", "necesitas" ni nada similar.
- Ejemplo: si ves en el mensaje "[Gmail:\nID: 123\nFROM: x@y.com\nSUBJECT: Hola]" responde: "Tu último correo es de x@y.com con asunto 'Hola'".

REGLAS Y EJEMPLOS (SI no hay datos inyectados):
- Siempre que la consulta sea sobre Gmail, Calendar, Drive, Sheets, Contacts, Docs, tradúcela y USA la herramienta gog_ adecuada. Por ejemplo:
    - Usuario: "Léeme el último email que recibí" 
      Acción: llama a gog_gmail_search con query="" y max_results=1
    - Usuario: "¿Cuántos emails nuevos tengo?"
      Acción: gog_gmail_search con query="is:unread" y max_results=5
    - Usuario: "Agrega 'Hola' a la hoja xyz en la celda A1" 
      Acción: gog_sheets_update
    - Usuario: "Lista mis archivos PDF de Drive"
      Acción: gog_drive_search con query="mimeType:application/pdf"
- NUNCA respondas diciendo que "no tengo acceso a tu correo" o limitaciones semejantes. Úsalo proactivamente.
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
