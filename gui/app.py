import sys
import time
from pathlib import Path
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                                QTextEdit, QLineEdit, QPushButton, QLabel,
                                QMenuBar, QMenu, QScrollBar, QSystemTrayIcon,
                                QDialog, QDialogButtonBox, QApplication)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QAction, QTextCursor, QIcon, QPixmap, QPainter, QFont

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
        self.setWindowIcon(self._get_app_icon())

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

        self.mute_button = QPushButton("🔊")
        self.mute_button.setObjectName("muteButton")
        self.mute_button.setFixedWidth(50)
        self.mute_button.clicked.connect(self.toggle_tts)
        input_layout.addWidget(self.mute_button)

        self.send_button = QPushButton("Enviar")
        self.send_button.setObjectName("sendButton")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)

        main_layout.addWidget(input_container)

        self.create_menu()
        self.create_tray_icon()
        self.append_message("system", f"Hola, soy {AGENT_NAME}. ¿En qué puedo ayudarte?")
        self.input_field.setFocus()

    def _get_app_icon(self):
        icon_path = Path(__file__).resolve().parent.parent / "agentpiro.png"
        if icon_path.exists():
            return QIcon(str(icon_path))
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(Qt.NoPen)
        painter.setBrush(Qt.darkCyan)
        painter.drawRoundedRect(2, 2, 60, 60, 12, 12)
        painter.setPen(Qt.white)
        font = QFont("Segoe UI", 28, QFont.Bold)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "AP")
        painter.end()
        return QIcon(pixmap)

    def create_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self._get_app_icon(), self)
        self.tray_icon.setToolTip(AGENT_NAME)

        tray_menu = QMenu()
        show_action = tray_menu.addAction("Mostrar/Ocultar")
        show_action.triggered.connect(self.toggle_visibility)
        tray_menu.addSeparator()
        quit_action = tray_menu.addAction("Salir")
        quit_action.triggered.connect(self.quit_app)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.toggle_visibility()

    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()

    def create_menu(self):
        menu_bar = self.menuBar()

        archivo_menu = menu_bar.addMenu("Archivo")

        clear_action = QAction("Limpiar Chat", self)
        clear_action.triggered.connect(self.clear_chat)
        archivo_menu.addAction(clear_action)

        self.tts_menu_action = QAction("Desactivar Voz", self)
        self.tts_menu_action.triggered.connect(self.toggle_tts)
        archivo_menu.addAction(self.tts_menu_action)

        archivo_menu.addSeparator()

        tray_action = QAction("Minimizar a Bandeja", self)
        tray_action.triggered.connect(self.hide)
        archivo_menu.addAction(tray_action)

        archivo_menu.addSeparator()

        exit_action = QAction("Salir", self)
        exit_action.triggered.connect(self.quit_app)
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

        # Solo auto-envía si detecta ráfaga rápida (Handy/dictado)
        if self._char_count >= 3:
            self._typing_timer.start(300)  # 0.3s de silencio = dictado terminado

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

    def toggle_tts(self):
        self._tts_enabled = not self._tts_enabled
        icon = "🔊" if self._tts_enabled else "🔇"
        self.mute_button.setText(icon)
        self.tts_menu_action.setText("Desactivar Voz" if self._tts_enabled else "Activar Voz")
        self.mute_button.setObjectName("muteButton" if self._tts_enabled else "muteButtonMuted")
        self.mute_button.style().unpolish(self.mute_button)
        self.mute_button.style().polish(self.mute_button)
        logger.info(f"TTS {'activado' if self._tts_enabled else 'desactivado'}")

    def clear_chat(self):
        self.chat_display.clear()
        self.agent.clear_history()
        self.append_message("system", "Chat limpiado. ¿En qué puedo ayudarte?")

    def update_status(self, text: str):
        self.status_label.setText(text)

    def show_about(self):
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Acerca de {AGENT_NAME}")
        dlg.setFixedSize(400, 250)
        dlg.setStyleSheet("""
            QDialog {
                background-color: #1e1e2e;
                color: #cdd6f4;
            }
            QLabel {
                color: #cdd6f4;
                font-size: 14px;
            }
        """)
        layout = QVBoxLayout(dlg)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel(f"<b style='font-size: 22px; color: #89b4fa;'>{AGENT_NAME}</b>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        desc = QLabel("Asistente personal de IA")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)

        info = QLabel(
            f"<b>Modelo local:</b> {OLLAMA_MODEL}<br>"
            f"<b>Modelo cloud:</b> {OLLAMA_CLOUD_MODEL}<br><br>"
            "Ejecutándose localmente con Ollama"
        )
        info.setAlignment(Qt.AlignCenter)
        info.setWordWrap(True)
        layout.addWidget(info)

        layout.addStretch()

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok)
        btn_box.setStyleSheet("""
            QPushButton {
                background-color: #89b4fa;
                color: #1e1e2e;
                border: none;
                border-radius: 8px;
                padding: 8px 24px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #b4befe;
            }
        """)
        btn_box.accepted.connect(dlg.accept)
        layout.addWidget(btn_box, alignment=Qt.AlignCenter)

        dlg.exec()

    def closeEvent(self, event):
        if self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            logger.info("Cerrando AgentPiro...")
            if self.tts_worker and self.tts_worker.isRunning():
                self.tts_worker.tts.stop()
                self.tts_worker.wait(2000)
            event.accept()

    def quit_app(self):
        logger.info("Cerrando AgentPiro...")
        self.tray_icon.hide()
        if self.tts_worker and self.tts_worker.isRunning():
            self.tts_worker.tts.stop()
            self.tts_worker.wait(2000)
        QApplication.quit()