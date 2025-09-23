from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QColorDialog, QSpinBox, QButtonGroup,
                            QGroupBox, QRadioButton, QCheckBox, QSlider)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen
import qtawesome as qta

class GridSettingsWidget(QWidget):
    """Grid ayarları widget'ı - arka plan ayarlarından ayrı"""
    gridSettingsChanged = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Grid ayarları (snap için)
        self.snap_grid_enabled = False
        self.snap_grid_color = QColor(100, 100, 255)  # Mavi ton
        self.snap_major_grid_color = QColor(50, 50, 200)  # Koyu mavi 
        self.snap_grid_size = 20
        self.snap_grid_width = 1
        self.snap_major_grid_width = 2
        self.snap_major_grid_interval = 5
        self.snap_grid_opacity = 0.5  # Yarı şeffaf
        self.snap_to_grid = False
        self.setup_ui()
        
    def setup_ui(self):
        """UI bileşenlerini oluştur"""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)
        
        # Grid görünürlüğü
        self.grid_enabled_checkbox = QCheckBox("Snap Grid'i Göster")
        self.grid_enabled_checkbox.setChecked(self.snap_grid_enabled)
        self.grid_enabled_checkbox.toggled.connect(self.on_grid_enabled_changed)
        layout.addWidget(self.grid_enabled_checkbox)
        
        # Grid ayarları grubu
        self.grid_group = QGroupBox("Snap Grid Ayarları")
        grid_layout = QVBoxLayout()
        
        # Grid rengi
        grid_color_layout = QHBoxLayout()
        grid_color_layout.addWidget(QLabel("Grid Rengi:"))
        
        self.grid_color_button = QPushButton()
        self.grid_color_button.setFixedSize(30, 25)
        self.grid_color_button.clicked.connect(self.choose_grid_color)
        self.update_grid_color_button()
        grid_color_layout.addWidget(self.grid_color_button)
        grid_color_layout.addStretch()
        
        grid_layout.addLayout(grid_color_layout)
        
        # Major grid rengi
        major_color_layout = QHBoxLayout()
        major_color_layout.addWidget(QLabel("Kalın Grid Rengi:"))
        
        self.major_grid_color_button = QPushButton()
        self.major_grid_color_button.setFixedSize(30, 25)
        self.major_grid_color_button.clicked.connect(self.choose_major_grid_color)
        self.update_major_grid_color_button()
        major_color_layout.addWidget(self.major_grid_color_button)
        major_color_layout.addStretch()
        
        grid_layout.addLayout(major_color_layout)
        
        # Grid boyutu
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Grid Aralığı:"))
        
        self.size_spinbox = QSpinBox()
        self.size_spinbox.setRange(5, 100)
        self.size_spinbox.setValue(self.snap_grid_size)
        self.size_spinbox.setSuffix(" px")
        self.size_spinbox.valueChanged.connect(self.on_grid_size_changed)
        size_layout.addWidget(self.size_spinbox)
        size_layout.addStretch()
        
        grid_layout.addLayout(size_layout)
        
        # Grid kalınlığı
        width_layout = QHBoxLayout()
        width_layout.addWidget(QLabel("Grid Kalınlığı:"))
        
        self.width_spinbox = QSpinBox()
        self.width_spinbox.setRange(1, 5)
        self.width_spinbox.setValue(self.snap_grid_width)
        self.width_spinbox.setSuffix(" px")
        self.width_spinbox.valueChanged.connect(self.on_grid_width_changed)
        width_layout.addWidget(self.width_spinbox)
        width_layout.addStretch()
        
        grid_layout.addLayout(width_layout)
        
        # Major grid kalınlığı
        major_width_layout = QHBoxLayout()
        major_width_layout.addWidget(QLabel("Kalın Grid Kalınlığı:"))
        
        self.major_width_spinbox = QSpinBox()
        self.major_width_spinbox.setRange(1, 8)
        self.major_width_spinbox.setValue(self.snap_major_grid_width)
        self.major_width_spinbox.setSuffix(" px")
        self.major_width_spinbox.valueChanged.connect(self.on_major_grid_width_changed)
        major_width_layout.addWidget(self.major_width_spinbox)
        major_width_layout.addStretch()
        
        grid_layout.addLayout(major_width_layout)
        
        # Major grid aralığı
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Kalın Grid Aralığı:"))
        
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setRange(2, 20)
        self.interval_spinbox.setValue(self.snap_major_grid_interval)
        self.interval_spinbox.setSuffix(" çizgi")
        self.interval_spinbox.valueChanged.connect(self.on_major_grid_interval_changed)
        interval_layout.addWidget(self.interval_spinbox)
        interval_layout.addStretch()
        
        grid_layout.addLayout(interval_layout)
        
        # Grid şeffaflığı
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("Grid Şeffaflığı:"))
        
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(10, 100)  # %10 ile %100 arası
        self.opacity_slider.setValue(int(self.snap_grid_opacity * 100))
        self.opacity_slider.valueChanged.connect(self.on_grid_opacity_changed)
        opacity_layout.addWidget(self.opacity_slider)
        
        self.opacity_label = QLabel(f"{int(self.snap_grid_opacity * 100)}%")
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
        self.grid_group.setEnabled(self.snap_grid_enabled)
        layout.addWidget(self.grid_group)
        
        layout.addStretch()
        self.setLayout(layout)
        
    def update_grid_color_button(self):
        """Grid renk butonunu güncelle"""
        color_hex = self.snap_grid_color.name()
        self.grid_color_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color_hex};
                border: 1px solid #999;
                border-radius: 3px;
            }}
        """)
        self.grid_color_button.setToolTip(f"Grid rengi: {color_hex}")
        
    def update_major_grid_color_button(self):
        """Major grid renk butonunu güncelle"""
        color_hex = self.snap_major_grid_color.name()
        self.major_grid_color_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color_hex};
                border: 1px solid #999;
                border-radius: 3px;
            }}
        """)
        self.major_grid_color_button.setToolTip(f"Kalın grid rengi: {color_hex}")
        
    def on_grid_enabled_changed(self, checked):
        """Grid görünürlüğü değiştiğinde"""
        self.snap_grid_enabled = checked
        self.grid_group.setEnabled(checked)
        self.emit_grid_settings_changed()
        
    def choose_grid_color(self):
        """Grid rengi seç"""
        color = QColorDialog.getColor(self.snap_grid_color, self, "Grid Rengi Seçin")
        if color.isValid():
            self.snap_grid_color = color
            self.update_grid_color_button()
            self.emit_grid_settings_changed()
            
    def choose_major_grid_color(self):
        """Major grid rengi seç"""
        color = QColorDialog.getColor(self.snap_major_grid_color, self, "Kalın Grid Rengi Seçin")
        if color.isValid():
            self.snap_major_grid_color = color
            self.update_major_grid_color_button()
            self.emit_grid_settings_changed()
            
    def on_grid_size_changed(self, value):
        """Grid boyutu değiştiğinde"""
        self.snap_grid_size = value
        self.emit_grid_settings_changed()
        
    def on_grid_width_changed(self, value):
        """Grid kalınlığı değiştiğinde"""
        self.snap_grid_width = value
        self.emit_grid_settings_changed()
        
    def on_major_grid_width_changed(self, value):
        """Major grid kalınlığı değiştiğinde"""
        self.snap_major_grid_width = value
        self.emit_grid_settings_changed()
        
    def on_major_grid_interval_changed(self, value):
        """Major grid aralığı değiştiğinde"""
        self.snap_major_grid_interval = value
        self.emit_grid_settings_changed()
        
    def on_snap_changed(self, checked):
        """Snap to grid durumu değiştiğinde"""
        self.snap_to_grid = checked
        self.emit_grid_settings_changed()
        
    def on_grid_opacity_changed(self, value):
        """Grid şeffaflığı değiştiğinde"""
        self.snap_grid_opacity = value / 100.0  # 0.1 ile 1.0 arasına çevir
        self.opacity_label.setText(f"{value}%")
        self.emit_grid_settings_changed()
        
    def emit_grid_settings_changed(self):
        """Grid ayarları değişikliği sinyali gönder"""
        data = {
            'enabled': self.snap_grid_enabled,
            'snap_grid_color': self.snap_grid_color,
            'snap_major_grid_color': self.snap_major_grid_color,
            'snap_grid_size': self.snap_grid_size,
            'snap_grid_width': self.snap_grid_width,
            'snap_major_grid_width': self.snap_major_grid_width,
            'snap_major_grid_interval': self.snap_major_grid_interval,
            'snap_grid_opacity': self.snap_grid_opacity,
            'snap_to_grid': self.snap_to_grid
        }
        self.gridSettingsChanged.emit(data)
        
    def get_grid_settings(self):
        """Mevcut grid ayarlarını al"""
        return {
            'enabled': self.snap_grid_enabled,
            'snap_grid_color': self.snap_grid_color,
            'snap_major_grid_color': self.snap_major_grid_color,
            'snap_grid_size': self.snap_grid_size,
            'snap_grid_width': self.snap_grid_width,
            'snap_major_grid_width': self.snap_major_grid_width,
            'snap_major_grid_interval': self.snap_major_grid_interval,
            'snap_grid_opacity': self.snap_grid_opacity,
            'snap_to_grid': self.snap_to_grid
        }
        
    def set_grid_settings(self, settings):
        """Grid ayarlarını güncelle"""
        self.snap_grid_enabled = settings.get('enabled', False)
        self.snap_grid_color = settings.get('snap_grid_color', QColor(100, 100, 255))
        self.snap_major_grid_color = settings.get('snap_major_grid_color', QColor(50, 50, 200))
        self.snap_grid_size = settings.get('snap_grid_size', 20)
        self.snap_grid_width = settings.get('snap_grid_width', 1)
        self.snap_major_grid_width = settings.get('snap_major_grid_width', 2)
        self.snap_major_grid_interval = settings.get('snap_major_grid_interval', 5)
        self.snap_grid_opacity = settings.get('snap_grid_opacity', 0.5)
        self.snap_to_grid = settings.get('snap_to_grid', False)
        
        # UI'yi güncelle
        self.grid_enabled_checkbox.setChecked(self.snap_grid_enabled)
        self.update_grid_color_button()
        self.update_major_grid_color_button()
        self.size_spinbox.setValue(self.snap_grid_size)
        self.width_spinbox.setValue(self.snap_grid_width)
        self.major_width_spinbox.setValue(self.snap_major_grid_width)
        self.interval_spinbox.setValue(self.snap_major_grid_interval)
        self.opacity_slider.setValue(int(self.snap_grid_opacity * 100))
        self.opacity_label.setText(f"{int(self.snap_grid_opacity * 100)}%")
        self.snap_checkbox.setChecked(self.snap_to_grid)
        self.grid_group.setEnabled(self.snap_grid_enabled)
