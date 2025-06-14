from PyQt6.QtWidgets import QWidget, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPen
import qtawesome as qta

class LineStyleWidget(QWidget):
    """Çizgi stili seçici widget'ı"""
    styleChanged = pyqtSignal(Qt.PenStyle)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_style = Qt.PenStyle.SolidLine
        self.styles = [
            (Qt.PenStyle.SolidLine, "Düz Çizgi", 'fa5s.minus'),
            (Qt.PenStyle.DashLine, "Kesikli Çizgi", 'fa5s.minus'),
            (Qt.PenStyle.DotLine, "Noktalı Çizgi", 'fa5s.ellipsis-h'),
            (Qt.PenStyle.DashDotLine, "Çizgi-Nokta", 'fa5s.minus'),
            (Qt.PenStyle.DashDotDotLine, "Çizgi-Nokta-Nokta", 'fa5s.minus')
        ]
        self.current_index = 0
        self.setup_ui()
        
    def setup_ui(self):
        """UI bileşenlerini oluştur"""
        self.style_button = QPushButton()
        self.style_button.setFixedSize(32, 32)
        self.style_button.clicked.connect(self.cycle_style)
        self.update_button()
        
        # Layout
        from PyQt6.QtWidgets import QHBoxLayout
        layout = QHBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.addWidget(self.style_button)
        self.setLayout(layout)
        
    def update_button(self):
        """Butonu güncelle"""
        style, name, icon_name = self.styles[self.current_index]
        
        # Icon color based on style
        if style == Qt.PenStyle.SolidLine:
            color = '#2196F3'
        elif style == Qt.PenStyle.DashLine:
            color = '#FF9800'
        elif style == Qt.PenStyle.DotLine:
            color = '#4CAF50'
        elif style == Qt.PenStyle.DashDotLine:
            color = '#9C27B0'
        else:  # DashDotDotLine
            color = '#F44336'
            
        self.style_button.setIcon(qta.icon(icon_name, color=color))
        self.style_button.setToolTip(f"Çizgi Stili: {name}\nTıkla: Sonraki stil")
        
        self.style_button.setStyleSheet(f"""
            QPushButton {{
                border: 2px solid #ddd;
                border-radius: 16px;
                background: white;
            }}
            QPushButton:hover {{
                border: 2px solid {color};
                background: {color}15;
            }}
            QPushButton:pressed {{
                background: {color}25;
            }}
        """)
        
    def cycle_style(self):
        """Sonraki stile geç"""
        self.current_index = (self.current_index + 1) % len(self.styles)
        self.current_style = self.styles[self.current_index][0]
        self.update_button()
        self.styleChanged.emit(self.current_style)
        
    def get_current_style(self):
        """Mevcut stili al"""
        return self.current_style
        
    def set_style(self, style):
        """Stili ayarla"""
        for i, (s, _, _) in enumerate(self.styles):
            if s == style:
                self.current_index = i
                self.current_style = style
                self.update_button()
                break 