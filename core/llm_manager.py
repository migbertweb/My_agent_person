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
            response = requests.post(url, json=payload, headers=headers, timeout=timeout)
            if response.status_code == 200:
                data = response.json()
                message = data.get("message", {})
                content = message.get("content", "")
                tool_calls_data = message.get("tool_calls", [])
                tool_calls = []
                for tc in tool_calls_data:
                    func = tc.get("function", {})
                    tool_calls.append({
                        "name": func.get("name", ""),
                        "arguments": func.get("arguments", {})
                    })
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
        return f"""Eres AgentPiro, un asistente personal de IA conciso y útil.

INFORMACIÓN DEL SISTEMA:
- Modelo local: {OLLAMA_MODEL}
- Modelo cloud: {OLLAMA_CLOUD_MODEL}
- Modelo activo: determinado por disponibilidad (cloud > local > fallback)

PERFIL DEL USUARIO:
{facts_text}

HERRAMIENTAS DISPONIBLES:
- get_current_time: Hora actual del sistema
- get_current_date: Fecha actual del sistema
- get_datetime_full: Fecha y hora completa
- execute_command: Ejecuta comandos del sistema ({', '.join(ALLOWED_COMMANDS)})
- web_search: Busca información actualizada en internet

REGLAS PARA USAR HERRAMIENTAS:
- Si necesitas hora/fecha, USA get_current_time/get_current_date. No la inventes.
- Si el usuario dice "busca", "busca en la web", "busca en internet", "búscame", "search", o pide info actualizada/recién pasada, USA web_search.
- Si preguntan conocimiento general que ya sabes (historia, definiciones, conceptos), responde directamente SIN usar herramientas.
- No uses herramientas si no es necesario.

TONE: Amigable pero profesional."""

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
