from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QColorDialog, QSpinBox, QButtonGroup,
                            QGroupBox, QRadioButton, QCheckBox, QSlider)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen
import qtawesome as qta

class BackgroundWidget(QWidget):
    """Canvas arka plan ayarları widget'ı"""
    backgroundChanged = pyqtSignal(dict)  # background_type, color, grid_size, grid_color
    
    BACKGROUND_TYPES = {
        'solid': 'Düz Renk',
        'grid': 'Çizgili',
        'dots': 'Kareli'
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.background_type = 'solid'
        self.background_color = QColor(255, 255, 255)
        self.grid_color = QColor(200, 200, 200)
        self.grid_size = 20
        self.grid_width = 1
        self.grid_opacity = 1.0
        self.snap_to_grid = False
        self.setup_ui()
        
    def setup_ui(self):
        """UI bileşenlerini oluştur"""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)
        
        # Arka plan tipi seçimi
        type_group = QGroupBox("Arka Plan Tipi")
        type_layout = QVBoxLayout()
        
        self.type_group = QButtonGroup()
        for key, label in self.BACKGROUND_TYPES.items():
            radio = QRadioButton(label)
            radio.setObjectName(key)
            if key == 'solid':
                radio.setChecked(True)
            radio.toggled.connect(self.on_type_changed)
            self.type_group.addButton(radio)
            type_layout.addWidget(radio)
            
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)
        
        # Arka plan rengi
        bg_color_layout = QHBoxLayout()
        bg_color_layout.addWidget(QLabel("Arka Plan Rengi:"))
        
        self.bg_color_button = QPushButton()
        self.bg_color_button.setFixedSize(30, 25)
        self.bg_color_button.clicked.connect(self.choose_background_color)
        self.update_bg_color_button()
        bg_color_layout.addWidget(self.bg_color_button)
        bg_color_layout.addStretch()
        
        layout.addLayout(bg_color_layout)
        
        # Grid/Çizgi ayarları
        self.grid_group = QGroupBox("Çizgi/Kare Ayarları")
        grid_layout = QVBoxLayout()
        
        # Grid rengi
        grid_color_layout = QHBoxLayout()
        grid_color_layout.addWidget(QLabel("Çizgi Rengi:"))
        
        self.grid_color_button = QPushButton()
        self.grid_color_button.setFixedSize(30, 25)
        self.grid_color_button.clicked.connect(self.choose_grid_color)
        self.update_grid_color_button()
        grid_color_layout.addWidget(self.grid_color_button)
        grid_color_layout.addStretch()
        
        grid_layout.addLayout(grid_color_layout)
        
        # Grid boyutu
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Aralık:"))
        
        self.size_spinbox = QSpinBox()
        self.size_spinbox.setRange(5, 100)
        self.size_spinbox.setValue(self.grid_size)
        self.size_spinbox.setSuffix(" px")
        self.size_spinbox.valueChanged.connect(self.on_grid_size_changed)
        size_layout.addWidget(self.size_spinbox)
        size_layout.addStretch()
        
        grid_layout.addLayout(size_layout)
        
        # Grid kalınlığı
        width_layout = QHBoxLayout()
        width_layout.addWidget(QLabel("Kalınlık:"))
        
        self.width_spinbox = QSpinBox()
        self.width_spinbox.setRange(1, 5)
        self.width_spinbox.setValue(self.grid_width)
        self.width_spinbox.setSuffix(" px")
        self.width_spinbox.valueChanged.connect(self.on_grid_width_changed)
        width_layout.addWidget(self.width_spinbox)
        width_layout.addStretch()
        
        grid_layout.addLayout(width_layout)
        
        # Grid şeffaflığı
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("Şeffaflık:"))
        
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(10, 100)  # %10 ile %100 arası
        self.opacity_slider.setValue(int(self.grid_opacity * 100))
        self.opacity_slider.valueChanged.connect(self.on_grid_opacity_changed)
        opacity_layout.addWidget(self.opacity_slider)
        
        self.opacity_label = QLabel(f"{int(self.grid_opacity * 100)}%")
        self.opacity_label.setMinimumWidth(35)
        opacity_layout.addWidget(self.opacity_label)
        opacity_layout.addStretch()
        
        grid_layout.addLayout(opacity_layout)
        
        # Snap to grid seçeneği
        self.snap_checkbox = QCheckBox("Grid'e Yapıştır (Snap to Grid)")
        self.snap_checkbox.setChecked(self.snap_to_grid)
        self.snap_checkbox.toggled.connect(self.on_snap_changed)
        grid_layout.addWidget(self.snap_checkbox)
        
        self.grid_group.setLayout(grid_layout)
        self.grid_group.setEnabled(True)  # Başlangıçta aktif (snap için)
        layout.addWidget(self.grid_group)
        
        layout.addStretch()
        self.setLayout(layout)
        
    def update_bg_color_button(self):
        """Arka plan renk butonunu güncelle"""
        color_hex = self.background_color.name()
        self.bg_color_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color_hex};
                border: 1px solid #999;
                border-radius: 3px;
            }}
        """)
        self.bg_color_button.setToolTip(f"Arka plan rengi: {color_hex}")
        
    def update_grid_color_button(self):
        """Grid renk butonunu güncelle"""
        color_hex = self.grid_color.name()
        self.grid_color_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color_hex};
                border: 1px solid #999;
                border-radius: 3px;
            }}
        """)
        self.grid_color_button.setToolTip(f"Çizgi rengi: {color_hex}")
        
    def on_type_changed(self):
        """Arka plan tipi değiştiğinde"""
        checked_button = self.type_group.checkedButton()
        if checked_button:
            self.background_type = checked_button.objectName()
            # Grid ayarları her zaman aktif (solid'de snap için gerekli)
            self.grid_group.setEnabled(True)
            self.emit_background_changed()
            
    def choose_background_color(self):
        """Arka plan rengi seç"""
        color = QColorDialog.getColor(self.background_color, self, "Arka Plan Rengi Seçin")
        if color.isValid():
            self.background_color = color
            self.update_bg_color_button()
            self.emit_background_changed()
            
    def choose_grid_color(self):
        """Grid rengi seç"""
        color = QColorDialog.getColor(self.grid_color, self, "Çizgi Rengi Seçin")
        if color.isValid():
            self.grid_color = color
            self.update_grid_color_button()
            self.emit_background_changed()
            
    def on_grid_size_changed(self, value):
        """Grid boyutu değiştiğinde"""
        self.grid_size = value
        self.emit_background_changed()
        
    def on_grid_width_changed(self, value):
        """Grid kalınlığı değiştiğinde"""
        self.grid_width = value
        self.emit_background_changed()
        
    def on_snap_changed(self, checked):
        """Snap to grid durumu değiştiğinde"""
        self.snap_to_grid = checked
        self.emit_background_changed()
        
    def on_grid_opacity_changed(self, value):
        """Grid şeffaflığı değiştiğinde"""
        self.grid_opacity = value / 100.0  # 0.1 ile 1.0 arasına çevir
        self.opacity_label.setText(f"{value}%")
        self.emit_background_changed()
        
    def emit_background_changed(self):
        """Arka plan değişikliği sinyali gönder"""
        data = {
            'type': self.background_type,
            'background_color': self.background_color,
            'grid_color': self.grid_color,
            'grid_size': self.grid_size,
            'grid_width': self.grid_width,
            'grid_opacity': self.grid_opacity,
            'snap_to_grid': self.snap_to_grid
        }
        self.backgroundChanged.emit(data)
        
    def get_background_settings(self):
        """Mevcut arka plan ayarlarını al"""
        return {
            'type': self.background_type,
            'background_color': self.background_color,
            'grid_color': self.grid_color,
            'grid_size': self.grid_size,
            'grid_width': self.grid_width,
            'grid_opacity': self.grid_opacity,
            'snap_to_grid': self.snap_to_grid
        }
        
    def set_background_settings(self, settings):
        """Arka plan ayarlarını güncelle"""
        self.background_type = settings.get('type', 'solid')
        self.background_color = settings.get('background_color', QColor(255, 255, 255))
        self.grid_color = settings.get('grid_color', QColor(200, 200, 200))
        self.grid_size = settings.get('grid_size', 20)
        self.grid_width = settings.get('grid_width', 1)
        self.grid_opacity = settings.get('grid_opacity', 1.0)
        self.snap_to_grid = settings.get('snap_to_grid', False)
        
        # UI'yi güncelle
        for button in self.type_group.buttons():
            if button.objectName() == self.background_type:
                button.setChecked(True)
                break
                
        self.update_bg_color_button()
        self.update_grid_color_button()
        self.size_spinbox.setValue(self.grid_size)
        self.width_spinbox.setValue(self.grid_width)
        self.opacity_slider.setValue(int(self.grid_opacity * 100))
        self.opacity_label.setText(f"{int(self.grid_opacity * 100)}%")
        self.snap_checkbox.setChecked(self.snap_to_grid)
        self.grid_group.setEnabled(self.background_type in ['grid', 'dots']) 