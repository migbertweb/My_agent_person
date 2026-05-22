#!/usr/bin/env python3
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QLockFile
from PySide6.QtNetwork import QLocalServer, QLocalSocket

from gui.app import AgentPiroGUI
from utils.logger import logger

LOCK_FILE = Path("/tmp/agentpiro.lock")
SERVER_NAME = "agentpiro-single-instance"


def _send_toggle():
    socket = QLocalSocket()
    socket.connectToServer(SERVER_NAME)
    if socket.waitForConnected(1000):
        socket.write(b"toggle")
        socket.waitForBytesWritten(1000)
        socket.waitForDisconnected(1000)
        return True
    return False


def main():
    logger.info("=" * 50)
    logger.info("Iniciando AgentPiro")
    logger.info("=" * 50)

    lock = QLockFile(str(LOCK_FILE))
    if not lock.tryLock(100):
        logger.info("Instancia ya activa, enviando toggle...")
        if _send_toggle():
            logger.info("Toggle enviado a la instancia existente.")
        else:
            logger.warning("No se pudo comunicar con la instancia existente.")
        return

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("AgentPiro")

    QLocalServer.removeServer(SERVER_NAME)
    server = QLocalServer()
    server.listen(SERVER_NAME)

    window = AgentPiroGUI()

    def _handle_connection():
        conn = server.nextPendingConnection()
        if conn and conn.waitForReadyRead(1000):
            data = bytes(conn.readAll()).decode().strip()
            if data == "toggle":
                window.toggle_visibility()
        if conn:
            conn.disconnectFromServer()

    server.newConnection.connect(_handle_connection)

    wants_visible = "--hidden" not in sys.argv[1:]
    if wants_visible:
        window.show()

    from core.telegram_bot import TelegramBot
    telegram_bot = TelegramBot(window.agent)
    telegram_bot.start()
    app.aboutToQuit.connect(telegram_bot.stop)
    app.aboutToQuit.connect(lambda: (lock.unlock(),
                                     QLocalServer.removeServer(SERVER_NAME)))

    logger.info("Interfaz iniciada correctamente")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()