from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QPushButton, QMenu)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QAction

class LineWidthPreview(QWidget):
    """Çizgi kalınlığı önizleme widget'ı"""
    def __init__(self, width, parent=None):
        super().__init__(parent)
        self.line_width = width
        self.setFixedSize(120, 30)
        self.setToolTip(f"{width}px")
        
    def paintEvent(self, event):
        """Çizgi kalınlığını çiz"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Çizgi kalınlığını göster
        pen = QPen(QColor(Qt.GlobalColor.black), self.line_width, Qt.PenStyle.SolidLine, 
                  Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        
        # Yatay çizgi çiz
        y = self.height() // 2
        margin = 10
        painter.drawLine(margin, y, self.width() - margin, y)
        
        # Kalınlık metnini çiz
        painter.setPen(QPen(Qt.GlobalColor.gray, 1))
        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)
        painter.drawText(self.width() - margin - 20, y + 10, f"{self.line_width}px")

class LineWidthWidget(QWidget):
    """Speed button tarzında çizgi kalınlığı seçici"""
    widthChanged = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_width = 2
        self.widths = [1, 2, 4, 6, 8]
        self.setup_ui()
        
    def setup_ui(self):
        """UI bileşenlerini oluştur"""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Ana buton
        self.main_button = QPushButton()
        self.main_button.setFixedSize(50, 32)
        self.main_button.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 1px solid #ccc;
                border-right: none;
                border-top-left-radius: 4px;
                border-bottom-left-radius: 4px;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
            }
            QPushButton:pressed {
                background-color: #e0e0e0;
            }
        """)
        self.main_button.clicked.connect(self.show_menu)
        
        # Dropdown ok butonu
        self.arrow_button = QPushButton("⌄")
        self.arrow_button.setFixedSize(16, 32)
        self.arrow_button.setStyleSheet("""
            QPushButton {
                background-color: white;
                border: 1px solid #ccc;
                border-left: none;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
                font-size: 8px;
                font-weight: bold;
                color: #666;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
            }
            QPushButton:pressed {
                background-color: #e0e0e0;
            }
        """)
        self.arrow_button.clicked.connect(self.show_menu)
        
        # Menu oluştur
        self.create_menu()
        
        # Ana butonun içeriğini güncelle
        self.update_main_button()
        
        layout.addWidget(self.main_button)
        layout.addWidget(self.arrow_button)
        self.setLayout(layout)
        
    def create_menu(self):
        """Dropdown menüyü oluştur"""
        self.menu = QMenu(self)
        
        for width in self.widths:
            # Normal QAction kullan
            action = QAction(f"{width}px", self)
            action.width = width
            action.triggered.connect(lambda checked, w=width: self.set_width(w))
            self.menu.addAction(action)
            
    def show_menu(self):
        """Menüyü göster"""
        # Menüyü butonun altında göster
        button_pos = self.main_button.mapToGlobal(self.main_button.rect().bottomLeft())
        self.menu.exec(button_pos)
        
    def set_width(self, width):
        """Kalınlığı ayarla"""
        if self.current_width != width:
            self.current_width = width
            self.update_main_button()
            self.widthChanged.emit(width)
            
    def update_main_button(self):
        """Ana butonun görünümünü güncelle"""
        # Ana butonu özel paint ile çiz
        self.main_button.setText("")
        self.main_button.setToolTip(f"Çizgi kalınlığı: {self.current_width}px")
        
        # Custom paint için override
        def paint_event(event):
            painter = QPainter(self.main_button)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Arka plan
            painter.fillRect(self.main_button.rect(), QColor("white"))
            
            # Çizgi kalınlığını göster
            pen = QPen(QColor(Qt.GlobalColor.black), self.current_width, Qt.PenStyle.SolidLine, 
                      Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            
            # Yatay çizgi çiz
            rect = self.main_button.rect()
            y = rect.height() // 2
            margin = 8
            painter.drawLine(margin, y, rect.width() - margin, y)
            
            # Kalınlık değerini sağ altta göster
            painter.setPen(QPen(Qt.GlobalColor.gray, 1))
            font = QFont()
            font.setPointSize(7)
            painter.setFont(font)
            painter.drawText(rect.width() - 15, rect.height() - 3, str(self.current_width))
            
        self.main_button.paintEvent = paint_event
        self.main_button.update()
        
    def get_current_width(self):
        """Şu anki seçili kalınlığı al"""
        return self.current_width
        
    def set_current_width(self, width):
        """Aktif kalınlığı ayarla"""
        self.set_width(width) 