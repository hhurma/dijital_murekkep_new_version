from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QCheckBox, QLabel)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor
import qtawesome as qta

class FillWidget(QWidget):
    """Şekil dolgusu için checkbox widget'ı"""
    fillChanged = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_filled = False
        self.setup_ui()
        
    def setup_ui(self):
        """UI bileşenlerini oluştur"""
        layout = QHBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(3)
        
        # Checkbox
        self.checkbox = QCheckBox()
        self.checkbox.setFixedSize(16, 16)
        self.checkbox.setStyleSheet("""
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
                border: 1px solid #ccc;
                border-radius: 2px;
                background-color: white;
            }
            QCheckBox::indicator:hover {
                border: 1px solid #999;
            }
            QCheckBox::indicator:checked {
                background-color: #2196F3;
                border: 1px solid #1976D2;
            }
            QCheckBox::indicator:checked:hover {
                background-color: #1976D2;
            }
        """)
        self.checkbox.stateChanged.connect(self.on_fill_changed)
        self.checkbox.setToolTip("Şekillerin içini doldur")
        
        # Boya kutusu ikonu
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(16, 16)
        self.update_icon()
        
        layout.addWidget(self.checkbox)
        layout.addWidget(self.icon_label)
        self.setLayout(layout)
        
    def on_fill_changed(self, state):
        """Fill durumu değiştiğinde"""
        self.is_filled = state == Qt.CheckState.Checked.value
        self.update_icon()
        self.fillChanged.emit(self.is_filled)
        
    def get_is_filled(self):
        """Fill durumunu al"""
        return self.is_filled
        
    def set_filled(self, filled):
        """Fill durumunu ayarla"""
        self.is_filled = filled
        self.checkbox.setChecked(filled)
        self.update_icon()
        
    def update_icon(self):
        """İkonu güncelle"""
        if self.is_filled:
            # Dolu boya kutusu
            icon = qta.icon('fa5s.fill-drip', color='#2196F3')
        else:
            # Boş boya kutusu
            icon = qta.icon('fa5s.fill', color='#666')
        
        pixmap = icon.pixmap(16, 16)
        self.icon_label.setPixmap(pixmap)

 