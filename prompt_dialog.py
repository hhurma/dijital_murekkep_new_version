from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QComboBox, QPushButton, QProgressBar
from PyQt6.QtCore import Qt, pyqtSignal


class PromptDialog(QDialog):
    sendRequested = pyqtSignal()
    drawRequested = pyqtSignal()
    def __init__(self, parent=None, models=None):
        super().__init__(parent)
        self.setWindowTitle("Prompt ile çiz")
        self.resize(520, 360)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Model seçimi
        row = QHBoxLayout()
        row.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.setEditable(False)
        for m in (models or []):
            self.model_combo.addItem(m)
        row.addWidget(self.model_combo, 1)
        layout.addLayout(row)

        # Prompt metni
        layout.addWidget(QLabel("İstek:"))
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Örn: Sadece JSON ver. axes/series/points şemasını kullan.")
        layout.addWidget(self.text_edit, 1)

        # Durum / ilerleme
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        layout.addWidget(self.progress)

        # Log alanı
        layout.addWidget(QLabel("Günlük:"))
        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setMaximumHeight(120)
        layout.addWidget(self.log_edit)

        # Butonlar
        btns = QHBoxLayout()
        btns.addStretch(1)
        self.cancel_btn = QPushButton("Kapat")
        self.send_btn = QPushButton("Gönder")
        self.draw_btn = QPushButton("Çiz")
        self.draw_btn.setEnabled(False)
        btns.addWidget(self.cancel_btn)
        btns.addWidget(self.send_btn)
        btns.addWidget(self.draw_btn)
        layout.addLayout(btns)

        self.cancel_btn.clicked.connect(self.reject)
        self.send_btn.clicked.connect(self._on_send)
        self.draw_btn.clicked.connect(self._on_draw)

    def set_busy(self, busy: bool):
        self.progress.setVisible(busy)
        self.send_btn.setEnabled(not busy)
        self.draw_btn.setEnabled(not busy and self.draw_btn.isEnabled())
        self.cancel_btn.setEnabled(not busy)

    def get_prompt(self):
        return self.text_edit.toPlainText().strip()

    def get_selected_model(self):
        return self.model_combo.currentText().strip()

    def append_log(self, text: str):
        try:
            self.log_edit.append(text)
        except Exception:
            pass

    def set_draw_enabled(self, enabled: bool):
        self.draw_btn.setEnabled(bool(enabled))

    def _on_send(self):
        self.sendRequested.emit()

    def _on_draw(self):
        self.drawRequested.emit()

    # Yardımcı: açılışta önerilen şablonu doldur
    def set_default_prompt(self, text: str):
        try:
            if self.text_edit.toPlainText().strip() == "":
                self.text_edit.setPlainText(text)
        except Exception:
            pass


