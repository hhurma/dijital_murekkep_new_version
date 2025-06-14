from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QPushButton, QColorDialog, 
                            QLabel, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPixmap
import qtawesome as qta

class FillColorWidget(QWidget):
    """Dolgu rengi seçici widget'ı"""
    fillColorChanged = pyqtSignal(QColor)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.fill_color = QColor(255, 255, 255, 0)  # Başlangıçta şeffaf
        self.setup_ui()
        
    def setup_ui(self):
        """UI bileşenlerini oluştur"""
        layout = QHBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(4)
        
        # Label
        label = QLabel("Dolgu:")
        label.setStyleSheet("font-size: 11px; color: #666;")
        layout.addWidget(label)
        
        # Renk butonu
        self.color_button = QPushButton()
        self.color_button.setFixedSize(28, 28)
        self.color_button.clicked.connect(self.choose_color)
        self.update_color_button()
        layout.addWidget(self.color_button)
        
        # Temizle butonu
        self.clear_button = QPushButton()
        self.clear_button.setIcon(qta.icon('fa5s.times', color='#666'))
        self.clear_button.setFixedSize(20, 20)
        self.clear_button.clicked.connect(self.clear_fill)
        self.clear_button.setToolTip("Dolgu rengini temizle")
        self.clear_button.setStyleSheet("""
            QPushButton {
                border: 1px solid #ccc;
                border-radius: 10px;
                background: white;
            }
            QPushButton:hover {
                background: #f0f0f0;
            }
        """)
        layout.addWidget(self.clear_button)
        
        self.setLayout(layout)
        
    def update_color_button(self):
        """Renk butonunu güncelle"""
        if self.fill_color.alpha() == 0:
            # Şeffaf - çizgili pattern göster
            pixmap = QPixmap(24, 24)
            pixmap.fill(Qt.GlobalColor.white)
            painter = QPainter(pixmap)
            painter.setPen(Qt.GlobalColor.red)
            painter.drawLine(0, 0, 24, 24)
            painter.drawLine(0, 24, 24, 0)
            painter.end()
            
            self.color_button.setIcon(qta.icon('fa5s.fill-drip', color='#999'))
            self.color_button.setStyleSheet("""
                QPushButton {
                    background: white;
                    border: 2px solid #ddd;
                    border-radius: 14px;
                }
                QPushButton:hover {
                    border: 2px solid #999;
                }
            """)
            self.color_button.setToolTip("Dolgu rengi seç (şu an şeffaf)")
        else:
            # Renkli
            color_hex = self.fill_color.name()
            self.color_button.setIcon(qta.icon('fa5s.fill-drip', color=color_hex))
            self.color_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color_hex};
                    border: 2px solid #ddd;
                    border-radius: 14px;
                }}
                QPushButton:hover {{
                    border: 2px solid #999;
                }}
            """)
            self.color_button.setToolTip(f"Dolgu rengi: {color_hex}")
            
    def choose_color(self):
        """Renk seçim dialogu aç"""
        initial_color = self.fill_color if self.fill_color.alpha() > 0 else QColor(255, 255, 255)
        color = QColorDialog.getColor(initial_color, self, "Dolgu Rengi Seçin")
        if color.isValid():
            self.fill_color = color
            self.update_color_button()
            self.fillColorChanged.emit(self.fill_color)
            
    def clear_fill(self):
        """Dolgu rengini temizle (şeffaf yap)"""
        self.fill_color = QColor(255, 255, 255, 0)
        self.update_color_button()
        self.fillColorChanged.emit(self.fill_color)
        
    def get_fill_color(self):
        """Mevcut dolgu rengini al"""
        return self.fill_color
        
    def set_fill_color(self, color):
        """Dolgu rengini ayarla"""
        self.fill_color = QColor(color)
        self.update_color_button() 