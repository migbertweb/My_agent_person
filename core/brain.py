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

_FS_SEARCH_TRIGGERS = re.compile(
    r"\b(busca|buscar|encuentra|listame|muestrame|donde está|donde esta)\b.*\b(archivo|"
    r"carpeta|directorio|fichero|pdf|documento|imagen|foto|musica|video)\b",
    re.IGNORECASE
)

_FS_OPEN_TRIGGERS = re.compile(
    r"\b(abre|abrir|ejecuta|inicia|lanza)\b",
    re.IGNORECASE
)

_FS_INFO_TRIGGERS = re.compile(
    r"\b(que pesa|tamaño|info|información|propiedades|permisos)\b.*\b(de|del)\b",
    re.IGNORECASE
)

_FS_READ_TRIGGERS = re.compile(
    r"\b(lee|leeme|muestra|contenido|contenido de|abre archivo)\b",
    re.IGNORECASE
)

_FS_COPY_TRIGGERS = re.compile(
    r"\b(copia|copiar|duplica|duplicar)\b",
    re.IGNORECASE
)

_FS_MOVE_TRIGGERS = re.compile(
    r"\b(mueve|mover|traslada|trasladar|renombra|renombrar)\b",
    re.IGNORECASE
)

_FS_DELETE_TRIGGERS = re.compile(
    r"\b(borra|borrar|elimina|eliminar|suprime|suprimir|tira|tirar)\b",
    re.IGNORECASE
)

_APP_TRIGGERS = {
    "vscodium": re.compile(r"\b(vscodium|vscode|codium|code)\b", re.IGNORECASE),
    "brave": re.compile(r"\b(brave)\b", re.IGNORECASE),
    "nautilus": re.compile(r"\b(nautilus|archivos|carpetas)\b", re.IGNORECASE),
    "steam": re.compile(r"\b(steam)\b", re.IGNORECASE),
    "kitty": re.compile(r"\b(kitty|terminal)\b", re.IGNORECASE),
    "firefox": re.compile(r"\b(firefox|navegador)\b", re.IGNORECASE),
    "libreoffice": re.compile(r"\b(libreoffice|office|writer|calc)\b", re.IGNORECASE),
    "vlc": re.compile(r"\b(vlc|reproductor|video)\b", re.IGNORECASE),
    "mpv": re.compile(r"\b(mpv)\b", re.IGNORECASE),
    "gimp": re.compile(r"\b(gimp)\b", re.IGNORECASE),
    "discord": re.compile(r"\b(discord)\b", re.IGNORECASE),
    "spotify": re.compile(r"\b(spotify|musica)\b", re.IGNORECASE),
    "signal": re.compile(r"\b(signal)\b", re.IGNORECASE),
    "telegram": re.compile(r"\b(telegram)\b", re.IGNORECASE),
    "thunderbird": re.compile(r"\b(thunderbird)\b", re.IGNORECASE),
}


class _GogRouter:
    """Routes natural language to the correct Google tool + injection logic."""

    def __init__(self, run_tool):
        self._run_tool = run_tool

    # ── Intent definitions: (domain, action, patterns, inject_fn) ──
    # inject_fn: receives (user_input, run_tool) → str | None
    #   Return str to inject data, None/"" to skip injection (LLM handles via tool calling)

    _INTENTS = None

    @classmethod
    def _build_intents(cls):
        if cls._INTENTS is not None:
            return cls._INTENTS

        import re
        I = re.IGNORECASE

        def _date_range(days=7):
            from datetime import datetime, timedelta
            today = datetime.now()
            return today.strftime("%Y-%m-%d"), (today + timedelta(days=days)).strftime("%Y-%m-%d")

        cls._INTENTS = [
            # ── GMAIL ──────────────────────────────────
            # Send → skip injection (LLM handles with tool calling)
            ("gmail", "send", [
                r"\b(enviar|envía|envíar|manda|mandar|remitir)\b.*\b(correo|email|mail|mensaje)\b",
                r"\b(correo|email)\b.*\b(enviar|envía|mandar|manda)\b",
            ], lambda text, rt: None),

            # Read last email(s)
            ("gmail", "read", [
                r"\b(leeme|lee)\b.*\b(correo|email|mail|mensaje)\b",
                r"\b(último|últimos?)\b.*\b(correo|correos?|email|mensajes?)\b",
                r"\b(muestra|muestrame|enséñame|enseñame)\b.*\b(correo|email|bandeja|inbox)\b",
            ], lambda text, rt: rt("gog_gmail_search", query="in:inbox newer_than:30d",
                                    max_results=1 if not re.search(r"\b(últimos?\s*\d+|varios|todos|lista|listame)\b", text, I) else 10)),

            # Search / list emails
            ("gmail", "search", [
                r"\b(busca|buscar|búsqueda)\b.*\b(correos?|email|mensajes?|gmail)\b",
                r"\b(correos?|mensajes?)\b.*\b(no\s+leídos?|no\s+leídas?|sin\s+leer|nuevos?)\b",
                r"\b(lista|listame)\b.*\b(correos?|mensajes?|email)\b",
                r"\b(tengo|hay)\b.*\b(correos?|mensajes?)\b.*\b(nuevos?|sin\s+leer)\b",
                r"\binbox\b|\bbandeja\b",
                r"\b(no\s+leídos?|no\s+leídas?)\b",
            ], lambda text, rt: rt("gog_gmail_search", query="in:inbox newer_than:30d",
                                    max_results=10 if re.search(r"\b(lista|listame|varios|todos|tres|cinco)\b", text, I) else 5)),

            # ── CALENDAR ───────────────────────────────
            # List calendars
            ("calendar", "list_calendars", [
                r"\b(lista|listame|listar|muestra|muestrame|mostrar|ver)\b.*\b(calendarios?)\b",
                r"\b(calendarios?)\b.*\b(disponibles?|tengo|hay|lista|listar)\b",
            ], lambda text, rt: rt("gog_calendar_list")),

            # Events today
            ("calendar", "events_today", [
                r"\b(hoy|el\s+día\s+de\s+hoy|de\s+hoy)\b.*\b(eventos?|citas?|reuniones?|agenda|programado)\b",
                r"\b(qué|que)\b.*\b(tengo|hay|agendado|programado)\b.*\b(hoy)\b",
            ], lambda text, rt: rt("gog_calendar_events", calendar_id=None,
                                    date_from=_date_range(0)[0], date_to=_date_range(0)[0])),

            # Events tomorrow
            ("calendar", "events_tomorrow", [
                r"\b(mañana|manana)\b.*\b(eventos?|citas?|reuniones?|agenda)\b",
            ], lambda text, rt: rt("gog_calendar_events", calendar_id=None,
                                    date_from=_date_range(1)[0], date_to=_date_range(1)[0])),

            # Events this week
            ("calendar", "events_week", [
                r"\b(esta\s+semana|ésta\s+semana|próximos?\s+días?|próximas?\s+semana|próximo)\b.*\b(eventos?|citas?|reuniones?|agenda)\b",
                r"\b(qué|que)\b.*\b(tengo|hay)\b.*\b(esta\s+semana|semana)\b",
                r"\b(eventos?|citas?|reuniones?)\b.*\b(de\s+la\s+semana|semanal)\b",
                r"\b(mis)\b.*\b(eventos?|citas?|reuniones?)\b",
                r"\b(calendario|agenda)\b(?!.*\b(lista|listar|calendarios?|disponibles|crear|crea|guarda|guardar|registra|registrar|nuevo|nueva|agrega|agregar|añade)\b)",
            ], lambda text, rt: rt("gog_calendar_events", calendar_id=None,
                                    date_from=_date_range(0)[0], date_to=_date_range(7)[0])),

            # Events specific day
            ("calendar", "events_day", [
                r"\b(eventos?|citas?|reuniones?)\b.*\b(del?\s+)?(lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)\b",
                r"\b(el\s+)?(lunes|martes|miércoles|miercoles|jueves|viernes|sábado|sabado|domingo)\b.*\b(eventos?|citas?|reuniones?|tengo|hay)\b",
            ], lambda text, rt: rt("gog_calendar_events", calendar_id=None,
                                    date_from=_date_range(0)[0], date_to=_date_range(7)[0])),

            # Create event → skip injection
            ("calendar", "create", [
                r"\b(crea|crear|agenda|agendar|programa|programar)\b.*\b(evento|cita|reunión|reunion)\b",
                r"\b(guarda|guardar|registra|registrar|marca|apunta)\b.*\b(evento|cita|reunión|reunion|calendario)\b",
                r"\b(evento|cita|reunión|reunion)\b.*\b(crear|nuevo|nueva|agendar|programar|guardar|registrar)\b",
                r"\b(añade|agrega|agregar)\b.*\b(evento|cita|reunión|reunion|calendario)\b",
            ], lambda text, rt: None),

            # ── CONTACTS ───────────────────────────────
            ("contacts", "list", [
                r"\b(lista|listame|listar|muestra|muestrame|mostrar|ver|todos)\b.*\b(contactos?)\b",
                r"\b(contactos?)\b.*\b(lista|listar|todos|disponibles)\b",
            ], lambda text, rt: rt("gog_contacts_list", max_results=50)),

            ("contacts", "search", [
                r"\b(busca|buscar|encuentra|búsca|búscame)\b.*\b(contacto|persona|gente)\b",
                r"\b(contacto)\b.*\b(de|llamado?|llamada?)\b",
            ], lambda text, rt: rt("gog_contacts_search",
                                    query=_extract_search(text) or text, max_results=10)),

            # ── DRIVE ──────────────────────────────────
            ("drive", "search", [
                r"\b(busca|buscar|encuentra|lista|listame|muestra|muestrame)\b.*\b(drive|archivos?|documentos?|pdfs?)\b",
                r"\b(drive)\b.*\b(archivos?|documentos?|buscar|tengo|hay)\b",
                r"\b(archivos?|documentos?)\b.*\b(drive)\b",
            ], lambda text, rt: rt("gog_drive_search", query=_extract_search(text) or text, max_results=10)),

            # Drive download → skip injection
            ("drive", "download", [
                r"\b(descarga|descargar|baja|bajar)\b.*\b(drive|archivo|documento)\b",
            ], lambda text, rt: None),

            # ── DOCS ───────────────────────────────────
            ("docs", "read", [
                r"\b(lee|leeme|muestra|abre|contenido)\b.*\b(documento|doc|docs)\b",
                r"\b(documento|doc|docs)\b.*\b(leer|mostrar|contenido)\b",
            ], lambda text, rt: None),  # Requires doc ID → LLM handles

            ("docs", "create", [
                r"\b(crea|crear|nuevo|nueva|haz|hacer)\b.*\b(documento|doc|docs)\b",
                r"\b(documento|doc|docs)\b.*\b(crear|nuevo|nueva)\b",
            ], lambda text, rt: None),

            # ── SHEETS ─────────────────────────────────
            ("sheets", "read", [
                r"\b(lee|leeme|muestra|muestrame|leer|mostrar)\b.*\b(hoja|sheet|sheets|tabla|planilla)\b",
            ], lambda text, rt: None),

            ("sheets", "create", [
                r"\b(crea|crear|nuevo|nueva|haz|hacer)\b.*\b(hoja|sheet|sheets|tabla|planilla|calculo)\b",
            ], lambda text, rt: None),

            # ── TASKS ──────────────────────────────────
            ("tasks", "list_lists", [
                r"\b(lista|listame|muestra|muestrame|ver)\b.*\b(listas?\s*de\s*tareas?|tareas?)\b",
            ], lambda text, rt: rt("gog_tasks_lists")),

            ("tasks", "list", [
                r"\b(mis)\b.*\b(tareas?|pendientes)\b",
                r"\b(tareas?)\b.*\b(pendientes?|listar|lista|ver)\b",
            ], lambda text, rt: rt("gog_tasks_list", tasklist_id="@default", max_results=20)),

            ("tasks", "add", [
                r"\b(agrega|agregar|añade|crea|crear|nueva|nuevo)\b.*\b(tarea)\b",
                r"\b(tarea)\b.*\b(agregar|crear|nueva)\b",
            ], lambda text, rt: None),

            # ── YOUTUBE ────────────────────────────────
            ("youtube", "search", [
                r"\b(busca|buscar|busca|encuentra|buscar)\b.*\b(videos?|tutorial)\b.*\b(youtube)\b",
                r"\b(youtube)\b.*\b(videos?|buscar|canal)\b",
                r"\b(videos?)\b.*\b(de|en)\b.*\b(youtube)\b",
            ], lambda text, rt: rt("gog_youtube_search",
                                    query=_extract_search(text) or text, max_results=5)),

            # ── PHOTOS ─────────────────────────────────
            ("photos", "list", [
                r"\b(fotos?|imágenes?|fotos?)\b.*\b(recientes?|últimas?|lista|listar|ver|mostrar)\b",
                r"\b(muestra|muestrame|lista|listame|ver)\b.*\b(fotos?|imágenes?)\b",
            ], lambda text, rt: rt("gog_photos_list", max_results=10)),

            # ── FORMS ──────────────────────────────────
            ("forms", "get", [
                r"\b(obtén|obtener|recupera|recuperar|ver|muestra)\b.*\b(formulario|form|forms)\b",
            ], lambda text, rt: None),

            # ── SLIDES ─────────────────────────────────
            ("slides", "info", [
                r"\b(info|información|detalles?|datos)\b.*\b(presentación|presentacion|slides?)\b",
            ], lambda text, rt: None),

            # ── TELEGRAM ───────────────────────────────
            ("telegram", "me", [
                r"\b(quién soy|quien soy|mi perfil|mis datos)\b.*\b(telegram)\b",
                r"\b(telegram)\b.*\b(quién soy|quien soy|perfil|cuenta)\b",
            ], lambda text, rt: rt("telegram_get_me")),

            ("telegram", "dialogs", [
                r"\b(mis?|lista|listame|muestra|ver)\b.*\b(chats?|conversaciones?|dialogos?|mensajes)\b.*\b(telegram)\b",
                r"\b(telegram)\b.*\b(chats?|conversaciones?|dialogos?|mensajes)\b.*\b(lista|ver|muestra|recientes)\b",
                r"\b(telegram)\b.*\b(que hay|que tal|novedades?)\b",
            ], lambda text, rt: rt("telegram_get_dialogs", limit=15)),

            ("telegram", "messages", [
                r"\b(leeme|lee|leer|muestra|ver|últimos?|ultimos?)\b.*\b(mensajes?|msgs?)\b.*\b(de|del)\b.*(.+?)(?:\b(?:en telegram|telegram)\b|$)",
                r"\b(telegram)\b.*\b(mensajes?)\b.*\b(de|del)\b.*(.+?)$",
                r"\b(del|de)\b.*(.+?)\b.*\b(telegram)\b",
            ], lambda text, rt: rt("telegram_get_messages", entity=_extract_telegram_entity(text), limit=5)),

            ("telegram", "send", [
                r"\b(envía|envia|enviale|enviar|manda|mandale|dile|decile)\b.*\b(telegram)\b.*\b(.+?)\b.*\b(diciendo|que|:)\b(.+)",
                r"\b(telegram)\b.*\b(envía|envia|manda|dile)\b.*\b(a|al|para)\b.*(.+?)\b.*\b(diciendo|que|:)\b(.+)",
            ], lambda text, rt: None),  # tool calling
        ]
        return cls._INTENTS

    def route(self, user_input: str):
        """Find best-matching intent and return injection data, or None."""
        intents = self._build_intents()
        I = re.IGNORECASE

        best = None
        best_len = 0

        for domain, action, patterns, inject_fn in intents:
            for p in patterns:
                m = re.search(p, user_input, I)
                if m:
                    span_len = m.end() - m.start()
                    if span_len > best_len:
                        best_len = span_len
                        best = (domain, action, inject_fn)
                    break

        if best:
            domain, action, inject_fn = best
            logger.agent_action("GOG_ROUTER", f"{domain}/{action}")
            result = inject_fn(user_input, self._run_tool)
            if result:
                label = f"{domain.capitalize()}"
                return f"\n[{label}: {domain}/{action}]\n{result}\n"
            return None

        return None


def _extract_telegram_entity(text: str) -> str:
    m = re.search(r"(?:del|de|a|al|para)\s+(@?\w[\w\s]+?)(?:\s+en telegram|\s+telegram|\s+diciendo|\s+que\s*:|\s*$)", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    m = re.search(r"@\w+", text)
    if m:
        return m.group(0)
    return ""


def _extract_search(text: str) -> str:
    """Extract search terms after trigger words."""
    m = re.search(r"(?:busca|buscar|encuentra|sobre|de|acerca de|llamado|llamada)\s+(.+?)$", text, re.IGNORECASE)
    if m:
        q = m.group(1).strip().rstrip(".?!")
        if len(q) > 2 and not re.match(r"^(un|una|el|la|los|las|mis|tus|del|para)\b", q, re.IGNORECASE):
            return q
    return ""


class AgentPiro:
    def __init__(self, memory: Memory, toolkit: Toolkit, llm_manager: OllamaManager = None):
        self.memory = memory
        self.toolkit = toolkit
        self.llm = llm_manager or OllamaManager()
        self.last_source = "local"
        self.last_model = ""
        self._gog_router = _GogRouter(self._run_tool)

    def _run_tool(self, name: str, **kwargs) -> str:
        tool = self.toolkit.get(name)
        if not tool:
            return ""
        logger.agent_action("FORCE_TOOL", f"{name} | args: {kwargs}")
        return tool.execute(**kwargs)

    def _inject_web_search(self, query: str) -> str:
        return self._run_tool("web_search", query=query)

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

        google_data = self._gog_router.route(user_input)
        if google_data:
            injected_data += google_data

        filesystem_result = ""
        if _FS_SEARCH_TRIGGERS.search(user_input):
            m = re.search(r"(?:\.\w+|\*\.\w+)", user_input)
            pattern = m.group(0) if m else "*"
            fs_result = self._run_tool("search_files", pattern=pattern, max_results=15)
            if fs_result:
                injected_data += f"\n[Files encontrados:\n{fs_result}]\n"

        if _FS_OPEN_TRIGGERS.search(user_input):
            app_found = None
            for app_name, app_re in _APP_TRIGGERS.items():
                if app_re.search(user_input):
                    app_found = app_name
                    break
            if app_found:
                fs_result = self._run_tool("run_app", app=app_found)
                if fs_result:
                    injected_data += f"\n[App: {fs_result}]\n"

        if _FS_INFO_TRIGGERS.search(user_input):
            injected_data += "\n[Tip: usa file_info con la ruta completa]\n"

        history = self.memory.get_conversation_history(limit=10)

        if injected_data:
            user_content = f"{user_input}\n\n---\n{injected_data}"
            iter_extra = " (con datos inyectados)"
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
