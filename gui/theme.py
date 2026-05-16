DARK_THEME = """
QMainWindow {
    background-color: #1e1e2e;
}

QWidget {
    color: #cdd6f4;
    font-family: 'Segoe UI', 'Ubuntu', sans-serif;
    font-size: 16px;
}

QTextEdit#chatDisplay {
    background-color: #181825;
    border: none;
    padding: 15px;
    color: #cdd6f4;
    selection-background-color: #89b4fa;
    font-size: 16px;
}

QLineEdit#inputField {
    background-color: #313244;
    border: 2px solid #45475a;
    border-radius: 12px;
    padding: 12px 16px;
    color: #cdd6f4;
    font-size: 16px;
    selection-background-color: #89b4fa;
}

QLineEdit#inputField:focus {
    border-color: #89b4fa;
    background-color: #383a4e;
}

QPushButton#sendButton {
    background-color: #89b4fa;
    color: #ffffff;
    border: 2px solid #b4befe;
    border-radius: 10px;
    padding: 12px 24px;
    font-weight: bold;
    font-size: 15px;
    min-width: 100px;
}

QPushButton#sendButton:hover {
    background-color: #b4befe;
    border-color: #cdd6f4;
}

QPushButton#sendButton:pressed {
    background-color: #74c7ec;
}

QPushButton#clearButton {
    background-color: #45475a;
    color: #cdd6f4;
    border: none;
    border-radius: 8px;
    padding: 10px 18px;
}

QPushButton#clearButton:hover {
    background-color: #585b70;
}

QScrollBar:vertical {
    background: #181825;
    width: 10px;
    border: none;
}

QScrollBar::handle:vertical {
    background: #45475a;
    border-radius: 5px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: #585b70;
}

QLabel#titleLabel {
    color: #89b4fa;
    font-size: 22px;
    font-weight: bold;
}

QLabel#statusLabel {
    color: #a6adc8;
    font-size: 14px;
}

QPushButton#muteButton {
    background-color: #a6e3a1;
    color: #11111b;
    border: 2px solid #94e2d5;
    border-radius: 10px;
    font-size: 18px;
    padding: 10px;
    min-width: 50px;
}

QPushButton#muteButton:hover {
    background-color: #94e2d5;
    border-color: #a6e3a1;
}

QPushButton#muteButtonMuted {
    background-color: #585b70;
    color: #cdd6f4;
    border: 2px solid #6c7086;
    border-radius: 10px;
    font-size: 18px;
    padding: 10px;
    min-width: 50px;
}

QPushButton#muteButtonMuted:hover {
    background-color: #6c7086;
    border-color: #7f849c;
}

QMenuBar {
    background-color: #181825;
    color: #cdd6f4;
    border-bottom: 1px solid #313244;
    font-size: 15px;
}

QMenuBar::item:selected {
    background-color: #313244;
}

QMenu {
    background-color: #181825;
    color: #cdd6f4;
    border: 1px solid #313244;
    font-size: 15px;
}

QMenu::item:selected {
    background-color: #313244;
}
"""

USER_BUBBLE = """
<div style="text-align: left; margin-bottom: 10px;">
    <p style="color: #cdd6f4; background-color: #45475a; padding: 12px; border-radius: 12px; display: inline-block; max-width: 80%; font-size: 16px;">
        <b style="color: #89b4fa; font-size: 16px;">Tú:</b> {content}
    </p>
</div>
"""

AGENT_BUBBLE = """
<div style="text-align: left; margin-bottom: 10px;">
    <p style="color: #ffffff; background-color: #89b4fa; padding: 12px; border-radius: 12px; display: inline-block; max-width: 80%; font-size: 16px;">
        <b style="color: #ffffff; font-weight: bold; font-size: 16px;">AgentPiro:</b> {content}
    </p>
</div>
"""

ERROR_BUBBLE = """
<div style="text-align: left; margin-bottom: 10px;">
    <p style="color: #f38ba8; background-color: #181825; padding: 12px; border-radius: 8px; border-left: 3px solid #f38ba8; display: inline-block; max-width: 80%; font-size: 16px;">
        <b style="color: #f38ba8; font-size: 16px;">Error:</b> {content}
    </p>
</div>
"""

SYSTEM_BUBBLE = """
<div style="text-align: center; margin: 10px 0;">
    <p style="color: #a6adc8; font-style: italic; font-size: 14px;">
        {content}
    </p>
</div>
"""