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


class AgentPiro:
    def __init__(self, memory: Memory, toolkit: Toolkit, llm_manager: OllamaManager = None):
        self.memory = memory
        self.toolkit = toolkit
        self.llm = llm_manager or OllamaManager()
        self.last_source = "local"
        self.last_model = ""

    def _inject_web_search(self, query: str) -> str:
        tool = self.toolkit.get("web_search")
        if not tool:
            return ""
        logger.agent_action("AUTO_WEB_SEARCH", query[:100])
        return tool.execute(query=query)

    def process(self, user_input: str) -> str:
        logger.agent_action("USER_INPUT", user_input[:100])

        facts = self.memory.get_all_facts()
        system_prompt = AgentPrompt.get_system_prompt(facts)

        search_result = ""
        if _SEARCH_TRIGGERS.search(user_input):
            search_result = self._inject_web_search(user_input)

        history = self.memory.get_conversation_history(limit=10)

        # API Cloud requiere alternancia user/assistant. No soporta rol 'system'.
        messages = []
        if not history:
            messages.append({
                "role": "user",
                "content": f"{system_prompt}\n\n{user_input}"
            })
        else:
            messages.extend(history)
            messages.append({"role": "user", "content": user_input})

        if search_result:
            messages.append({"role": "assistant", "content": f"Resultados de búsqueda para '{user_input}':\n{search_result}"})
            iter_extra = " (con búsqueda automática)"
        else:
            iter_extra = ""

        tools_schema = self.toolkit.get_all_tools()

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