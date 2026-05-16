import sys
import time
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                                QTextEdit, QLineEdit, QPushButton, QLabel,
                                QMenuBar, QMenu, QMessageBox, QScrollBar)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QAction, QTextCursor

from core.brain import AgentPiro
from core.memory import Memory
from core.llm_manager import OllamaManager
from core.tts import create_tts_provider, strip_markdown
from tools.system_tools import create_system_tools
from utils.config import (AGENT_NAME, OLLAMA_MODEL, OLLAMA_CLOUD_MODEL,
                           TTS_ENABLED, TTS_PROVIDER, TTS_VOICE,
                           TTS_RATE, TTS_PITCH, TTS_AUTO_PLAY)
from utils.logger import logger

from gui.theme import DARK_THEME, USER_BUBBLE, AGENT_BUBBLE, ERROR_BUBBLE, SYSTEM_BUBBLE


class AgentWorker(QThread):
    finished = Signal(str, float)  # respuesta, tiempo_elapsed
    error = Signal(str)

    def __init__(self, agent: AgentPiro, message: str):
        super().__init__()
        self.agent = agent
        self.message = message

    def run(self):
        try:
            start_time = time.time()
            response = self.agent.process(self.message)
            elapsed = time.time() - start_time
            self.finished.emit(response, elapsed)
        except Exception as e:
            logger.error(f"Error en worker: {e}")
            self.error.emit(str(e))


class TTSWorker(QThread):
    finished = Signal()
    error = Signal(str)

    def __init__(self, text: str, voice: str = "es-ES-AlvaroNeural",
                 rate: str = "0%", pitch: str = "0%"):
        super().__init__()
        self.text = text
        self.tts = create_tts_provider("edge", voice, rate, pitch)

    def run(self):
        try:
            self.tts.speak(self.text)
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))


class AgentPiroGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.agent = None
        self.worker = None
        self.tts_worker = None
        self._typing_timer = QTimer()
        self._typing_timer.setSingleShot(True)
        self._typing_timer.timeout.connect(self._on_typing_stopped)
        self._last_text = ""
        self._last_change_time = 0
        self._char_count = 0
        self._tts_enabled = TTS_ENABLED and TTS_AUTO_PLAY
        self.init_agent()
        self.init_ui()

    def init_agent(self):
        logger.info("Inicializando AgentPiro...")
        memory = Memory()
        toolkit = create_system_tools()
        llm = OllamaManager()
        self.agent = AgentPiro(memory, toolkit, llm)
        logger.info("AgentPiro listo")

    def init_ui(self):
        self.setWindowTitle(f"{AGENT_NAME} - Asistente Personal")
        self.setMinimumSize(600, 500)
        self.resize(800, 600)

        self.setStyleSheet(DARK_THEME)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        title_bar = QWidget()
        title_bar.setStyleSheet("background-color: #181825; padding: 10px;")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(15, 5, 15, 5)

        self.title_label = QLabel(f"🤖 {AGENT_NAME}")
        self.title_label.setObjectName("titleLabel")
        title_layout.addWidget(self.title_label)

        title_layout.addStretch()

        self.status_label = QLabel(f"Model: {OLLAMA_MODEL}")
        self.status_label.setObjectName("statusLabel")
        title_layout.addWidget(self.status_label)

        main_layout.addWidget(title_bar)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setObjectName("chatDisplay")
        self.chat_display.setAlignment(Qt.AlignLeft)
        self.chat_display.document().setDefaultStyleSheet("body, p, div { text-align: left; }")
        main_layout.addWidget(self.chat_display)

        input_container = QWidget()
        input_container.setStyleSheet("background-color: #1e1e2e; padding: 15px;")
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(15, 10, 15, 10)

        self.input_field = QLineEdit()
        self.input_field.setObjectName("inputField")
        self.input_field.setPlaceholderText("Escribe tu mensaje o usa voz...")
        self.input_field.returnPressed.connect(self.send_message)
        self.input_field.textChanged.connect(self._on_text_changed)
        input_layout.addWidget(self.input_field, 1)

        self.send_button = QPushButton("Enviar")
        self.send_button.setObjectName("sendButton")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)

        main_layout.addWidget(input_container)

        self.create_menu()
        self.append_message("system", f"Hola, soy {AGENT_NAME}. ¿En qué puedo ayudarte?")
        self.input_field.setFocus()

    def create_menu(self):
        menu_bar = self.menuBar()

        archivo_menu = menu_bar.addMenu("Archivo")

        clear_action = QAction("Limpiar Chat", self)
        clear_action.triggered.connect(self.clear_chat)
        archivo_menu.addAction(clear_action)

        archivo_menu.addSeparator()

        exit_action = QAction("Salir", self)
        exit_action.triggered.connect(self.close)
        archivo_menu.addAction(exit_action)

        help_menu = menu_bar.addMenu("Ayuda")

        about_action = QAction("Acerca de", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def send_message(self):
        message = self.input_field.text().strip()
        if not message:
            return

        self.input_field.clear()
        self.input_field.setEnabled(False)
        self.send_button.setEnabled(False)

        self.append_message("user", message)
        self.update_status("Pensando...")

        self.worker = AgentWorker(self.agent, message)
        self.worker.finished.connect(self.on_response)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_response(self, response: str, elapsed: float):
        source = self.agent.last_source
        source_icon = "☁️" if source == "cloud" else "💻"
        model_name = OLLAMA_CLOUD_MODEL if source == "cloud" else OLLAMA_MODEL

        self.append_message("agent", response)
        self.input_field.setEnabled(True)
        self.send_button.setEnabled(True)
        self.input_field.setFocus()
        self.update_status(f"{source_icon} {model_name} | ⏱ {elapsed:.1f}s")

        if self._tts_enabled:
            self.speak_response(response)

    def speak_response(self, text: str):
        self.update_status("🔊 Speaking...")
        clean = strip_markdown(text)
        self.tts_worker = TTSWorker(clean, TTS_VOICE, TTS_RATE, TTS_PITCH)
        self.tts_worker.finished.connect(self._on_speak_finished)
        self.tts_worker.error.connect(self._on_speak_error)
        self.tts_worker.start()

    def _on_speak_finished(self):
        self.tts_worker = None
        source = self.agent.last_source
        source_icon = "☁️" if source == "cloud" else "💻"
        model_name = OLLAMA_CLOUD_MODEL if source == "cloud" else OLLAMA_MODEL
        self.update_status(f"{source_icon} {model_name}")

    def _on_speak_error(self, error: str):
        self.tts_worker = None
        logger.error(f"Error en TTS: {error}")
        self.update_status("Error TTS")

    def on_error(self, error: str):
        self.append_message("error", error)
        self.input_field.setEnabled(True)
        self.send_button.setEnabled(True)
        self.update_status("Error - Intenta de nuevo")

    def _on_text_changed(self, text: str):
        if not text.strip():
            return
        now = time.time()
        elapsed = now - self._last_change_time if self._last_change_time else 999

        # Si recibi múltiples caracteres muy rápido (< 50ms entre cambios), es wtype/Handy
        if elapsed < 0.05:
            self._char_count += 1
        else:
            self._char_count = 1

        self._last_change_time = now
        self._last_text = text

        # Si parece dictado (>5 chars en ráfaga) o texto ya largo, esperar a que termine
        if self._char_count >= 3 or len(text) > 20:
            self._typing_timer.start(200)  # 200ms de silencio = dictado terminado

    def _on_typing_stopped(self):
        text = self.input_field.text().strip()
        if text and self.input_field.isEnabled():
            self.send_message()

    def append_message(self, sender: str, content: str):
        if sender == "user":
            bubble = USER_BUBBLE.format(content=self.escape_html(content))
        elif sender == "agent":
            bubble = AGENT_BUBBLE.format(content=self.escape_html(content))
        elif sender == "system":
            bubble = SYSTEM_BUBBLE.format(content=self.escape_html(content))
        else:
            bubble = ERROR_BUBBLE.format(content=self.escape_html(content))

        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertBlock()
        cursor.insertHtml(bubble)
        cursor.insertHtml('<div style="height: 16px;"></div>')
        self.chat_display.setTextCursor(cursor)
        self.chat_display.ensureCursorVisible()

    def escape_html(self, text: str):
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("\n", "<br>"))

    def clear_chat(self):
        self.chat_display.clear()
        self.agent.clear_history()
        self.append_message("system", "Chat limpiado. ¿En qué puedo ayudarte?")

    def update_status(self, text: str):
        self.status_label.setText(text)

    def show_about(self):
        QMessageBox.about(self, f"Acerca de {AGENT_NAME}",
                          f"<b>{AGENT_NAME}</b><br><br>"
                          "Asistente personal de IA<br>"
                          f"Modelo: {OLLAMA_MODEL}<br><br>"
                          "Ejecutándose localmente con Ollama")

    def closeEvent(self, event):
        logger.info("Cerrando AgentPiro...")
        if self.tts_worker and self.tts_worker.isRunning():
            self.tts_worker.tts.stop()
            self.tts_worker.wait(2000)
        event.accept()