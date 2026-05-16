#!/usr/bin/env python3
import sys
from PySide6.QtWidgets import QApplication

from gui.app import AgentPiroGUI
from utils.logger import logger


def main():
    logger.info("=" * 50)
    logger.info("Iniciando AgentPiro")
    logger.info("=" * 50)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("AgentPiro")

    window = AgentPiroGUI()
    window.show()

    from core.telegram_bot import TelegramBot
    telegram_bot = TelegramBot(window.agent)
    telegram_bot.start()
    app.aboutToQuit.connect(telegram_bot.stop)

    logger.info("Interfaz iniciada correctamente")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()