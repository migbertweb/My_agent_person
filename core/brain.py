import re
from typing import Optional
from core.llm_manager import OllamaManager, AgentPrompt
from core.memory import Memory
from tools.toolkit import Toolkit
from utils.config import MAX_ITERATIONS
from utils.logger import logger

_SEARCH_TRIGGERS = re.compile(
    r"\b(busca|buscar|búscame|búsqueda|search|"
    r"encuentra información|"
    r"qué hay de nuevo|últimas noticias|noticias de|"
    r"dónde está|dónde queda|"
    r"precio de|cuánto cuesta|"
    r"qué pasó|última hora)\b",
    re.IGNORECASE
)

_GMAIL_TRIGGERS = re.compile(
    r"\b(correo|email|mail|gmail|mensaje|"
    r"leeme|lee(me)?|último(s)? correo(s)?|"
    r"no leído|no leídos|no leidas|inbox|bandeja|"
    r"enviar|envía|manda(me)?)\b",
    re.IGNORECASE
)

_CALENDAR_TRIGGERS = re.compile(
    r"\b(calendario|calendar|eventos|citas|reunión|reunion|"
    r"agenda|agendado|programado|schedule)\b",
    re.IGNORECASE
)

_DRIVE_TRIGGERS = re.compile(
    r"\b(drive|archivo(s)?|documento(s)?|fichero(s)?|"
    r"pdf|word|excel|hoja(s)?)\b",
    re.IGNORECASE
)


class AgentPiro:
    def __init__(self, memory: Memory, toolkit: Toolkit, llm_manager: OllamaManager = None):
        self.memory = memory
        self.toolkit = toolkit
        self.llm = llm_manager or OllamaManager()
        self.last_source = "local"
        self.last_model = ""

    def _run_tool(self, name: str, **kwargs) -> str:
        tool = self.toolkit.get(name)
        if not tool:
            return ""
        logger.agent_action("FORCE_TOOL", f"{name} | args: {kwargs}")
        return tool.execute(**kwargs)

    def _inject_web_search(self, query: str) -> str:
        return self._run_tool("web_search", query=query)

    def _inject_gmail_search(self, user_input: str) -> str:
        max_results = 1
        m = re.search(r"últimos?\s+(\d+)|ultimos?\s+(\d+)", user_input, re.IGNORECASE)
        if m:
            max_results = int((m.group(1) or m.group(2)))
        if "no leído" in user_input or "no leidos" in user_input or "no leidas" in user_input:
            max_results = 5
        if "enviar" in user_input or "envía" in user_input or "manda" in user_input:
            return None
        return self._run_tool("gog_gmail_search", query="in:inbox newer_than:30d", max_results=max_results)

    def process(self, user_input: str) -> str:
        logger.agent_action("USER_INPUT", user_input[:100])

        facts = self.memory.get_all_facts()
        system_prompt = AgentPrompt.get_system_prompt(facts)

        injected_data = ""

        search_result = ""
        if _SEARCH_TRIGGERS.search(user_input):
            search_result = self._inject_web_search(user_input)
            if search_result:
                injected_data += f"\n[Web: {search_result}]\n"

        gmail_result = ""
        if _GMAIL_TRIGGERS.search(user_input):
            gmail_result = self._inject_gmail_search(user_input)
            if gmail_result:
                injected_data += f"\n[Gmail:\n{gmail_result}]\n"

        calendar_result = ""
        if _CALENDAR_TRIGGERS.search(user_input):
            from datetime import datetime, timedelta
            today = datetime.now()
            next_week = today + timedelta(days=7)
            date_from = today.strftime("%Y-%m-%d")
            date_to = next_week.strftime("%Y-%m-%d")
            calendar_result = self._run_tool("gog_calendar_events", calendar_id="default", date_from=date_from, date_to=date_to)
            if calendar_result:
                injected_data += f"\n[Calendar:\n{calendar_result}]\n"

        drive_result = ""
        if _DRIVE_TRIGGERS.search(user_input):
            drive_result = self._run_tool("gog_drive_search", query=user_input, max_results=5)
            if drive_result:
                injected_data += f"\n[Drive:\n{drive_result}]\n"

        history = self.memory.get_conversation_history(limit=10)

        if injected_data:
            user_content = f"{user_input}\n\n---\n{injected_data}"
            iter_extra = " (con datos Google inyectados)"
        else:
            user_content = user_input
            iter_extra = ""

        messages = []
        if not history:
            messages.append({
                "role": "user",
                "content": f"{system_prompt}\n\n{user_content}"
            })
        else:
            messages.extend(history)
            messages.append({"role": "user", "content": user_content})

        tools_schema = self.toolkit.get_all_tools()
        logger.debug(f"Tools schema enviado al modelo ({len(tools_schema)} tools): {[t['name'] for t in tools_schema]}")

        iteration = 0
        max_iter = MAX_ITERATIONS

        while iteration < max_iter:
            iteration += 1
            logger.debug(f"Iteración {iteration}/{max_iter}{iter_extra}")

            response = self.llm.chat(messages, tools=tools_schema if tools_schema else None)

            if not response:
                return "Lo siento, tuve un problema al procesar tu solicitud. ¿Podrías intentarlo de nuevo?"

            self.last_source = response.source

            if response.has_tool_call():
                tool_call = response.tool_calls[0]
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("arguments", {})

                logger.agent_action("TOOL_EXECUTING", f"{tool_name} | iter {iteration}")
                tool_result = self.toolkit.execute(tool_name, **tool_args)

                messages.append({
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [tool_call]
                })
                messages.append({
                    "role": "tool",
                    "content": tool_result
                })

                continue

            if response.content:
                self.memory.add_message("user", user_input)
                self.memory.add_message("assistant", response.content)
                logger.agent_action("RESPONSE", response.content[:100])
                return response.content

        self.memory.add_message("assistant", "Alcancé el límite de iteraciones.")
        return "Necesito más tiempo para procesar tu solicitud. ¿Podrías reformularla?"

    def clear_history(self):
        self.memory.clear_conversation()
        logger.agent_action("HISTORY_CLEAR", "Historial de conversación limpiado")

    def save_fact(self, key: str, value: str):
        self.memory.save_fact(key, value)
