from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QSlider, QLabel)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor

class OpacityWidget(QWidget):
    """Şeffaflık kontrolü için slider widget'ı"""
    opacityChanged = pyqtSignal(float)  # 0.0 - 1.0 arası değer
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_opacity = 1.0  # Varsayılan tam opak
        self.setup_ui()
        
    def setup_ui(self):
        """UI bileşenlerini oluştur"""
        layout = QHBoxLayout()
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(3)
        
        # Opacity slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setFixedWidth(60)  # Daha küçük
        self.slider.setFixedHeight(20)
        self.slider.setMinimum(10)  # %10 minimum (tamamen şeffaf olmasın)
        self.slider.setMaximum(100)  # %100 maksimum
        self.slider.setValue(100)  # Varsayılan %100
        self.slider.valueChanged.connect(self.on_opacity_changed)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #ccc;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2196F3, stop:1 rgba(33,150,243,0.3));
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #2196F3;
                border: 2px solid #fff;
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
                border: 1px solid rgba(0,0,0,0.3);
            }
            QSlider::handle:horizontal:hover {
                background: #1976D2;
                transform: scale(1.1);
            }
            QSlider::handle:horizontal:pressed {
                background: #0D47A1;
            }
        """)
        self.slider.setToolTip("Şeffaflık: %100")
        
        # Yüzde etiketi
        self.label = QLabel("100%")
        self.label.setFixedWidth(25)  # Daha küçük
        self.label.setStyleSheet("""
            QLabel {
                font-size: 10px;
                color: #666;
            }
        """)
        
        # Önizleme widget'ı
        self.preview = OpacityPreview(self.current_opacity)
        
        layout.addWidget(self.preview)
        layout.addWidget(self.slider)
        layout.addWidget(self.label)
        self.setLayout(layout)
        
    def on_opacity_changed(self, value):
        """Slider değeri değiştiğinde"""
        self.current_opacity = value / 100.0  # 0.0 - 1.0 arası
        self.label.setText(f"{value}%")
        self.slider.setToolTip(f"Şeffaflık: %{value}")
        self.preview.set_opacity(self.current_opacity)
        self.opacityChanged.emit(self.current_opacity)
        
    def get_opacity(self):
        """Şu anki opacity değerini al"""
        return self.current_opacity
        
    def set_opacity(self, opacity):
        """Opacity değerini ayarla (0.0 - 1.0)"""
        opacity = max(0.1, min(1.0, opacity))  # Sınırları kontrol et
        self.current_opacity = opacity
        value = int(opacity * 100)
        self.slider.setValue(value)
        self.label.setText(f"{value}%")
        self.preview.set_opacity(opacity)

class OpacityPreview(QWidget):
    """Opacity önizleme widget'ı"""
    def __init__(self, opacity=1.0, parent=None):
        super().__init__(parent)
        self.opacity = opacity
        self.setFixedSize(20, 20)
        
    def set_opacity(self, opacity):
        """Opacity değerini ayarla"""
        self.opacity = opacity
        self.update()
        
    def paintEvent(self, event):
        """Opacity önizlemesini çiz"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Satranç tahtası pattern (şeffaflık göstergesi)
        square_size = 4
        for y in range(0, self.height(), square_size):
            for x in range(0, self.width(), square_size):
                if (x // square_size + y // square_size) % 2:
                    painter.fillRect(x, y, square_size, square_size, QColor(220, 220, 220))
                else:
                    painter.fillRect(x, y, square_size, square_size, QColor(255, 255, 255))
        
        # Opacity ile renkli katman
        color = QColor(50, 150, 255)
        color.setAlphaF(self.opacity)
        brush = QBrush(color)
        painter.setBrush(brush)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(self.rect())
        
        # Çerçeve
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor(150, 150, 150), 1))
        painter.drawRect(self.rect().adjusted(0, 0, -1, -1)) 