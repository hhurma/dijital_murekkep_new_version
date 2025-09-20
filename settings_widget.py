from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QColorDialog, QSpinBox, QDoubleSpinBox, QButtonGroup,
                            QGroupBox, QRadioButton, QCheckBox, QSlider, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen
import qtawesome as qta

class SettingsWidget(QWidget):
    """Uygulama ayarları widget'ı - arka plan, PDF ve canvas ayarları"""
    backgroundChanged = pyqtSignal(dict)
    pdfOrientationChanged = pyqtSignal(str)
    canvasOrientationChanged = pyqtSignal(str)
    canvasSizeChanged = pyqtSignal(str)
    
    BACKGROUND_TYPES = {
        'solid': 'Düz Renk',
        'grid': 'Çizgili',
        'dots': 'Kareli'
    }
    
    CANVAS_SIZES = {
        'small': 'Küçük (827x1169)',
        'medium': 'Orta (1240x1754)',
        'large': 'Büyük (2480x3508)'
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        # Arka plan ayarları
        self.background_type = 'solid'
        self.background_color = QColor(255, 255, 255)
        self.grid_color = QColor(200, 200, 200)
        self.major_grid_color = QColor(150, 150, 150)
        self.grid_size = 20
        self.grid_width = 1
        self.major_grid_width = 2
        self.major_grid_interval = 5
        self.minor_grid_interval = 1.0
        self.grid_opacity = 1.0
        self.snap_to_grid = False
        
        # PDF ve Canvas ayarları
        self.pdf_orientation = 'landscape'
        self.canvas_orientation = 'landscape'
        self.canvas_size = 'small'
        
        self.setup_ui()
        
    def setup_ui(self):
        """UI bileşenlerini oluştur"""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)
        
        # Canvas Ayarları
        canvas_group = QGroupBox("Canvas Ayarları")
        canvas_layout = QVBoxLayout()
        
        # Canvas boyutu
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Canvas Boyutu:"))
        
        self.canvas_size_combo = QComboBox()
        for key, label in self.CANVAS_SIZES.items():
            self.canvas_size_combo.addItem(label, key)
        self.canvas_size_combo.setCurrentText(self.CANVAS_SIZES[self.canvas_size])
        self.canvas_size_combo.currentTextChanged.connect(self.on_canvas_size_changed)
        size_layout.addWidget(self.canvas_size_combo)
        size_layout.addStretch()
        
        canvas_layout.addLayout(size_layout)
        
        # Canvas yönü
        canvas_orientation_layout = QHBoxLayout()
        canvas_orientation_layout.addWidget(QLabel("Canvas Yönü:"))
        
        self.canvas_orientation_group = QButtonGroup()
        self.canvas_portrait_radio = QRadioButton("Dikey")
        self.canvas_landscape_radio = QRadioButton("Yatay")
        
        if self.canvas_orientation == 'landscape':
            self.canvas_landscape_radio.setChecked(True)
        else:
            self.canvas_portrait_radio.setChecked(True)
            
        self.canvas_portrait_radio.toggled.connect(self.on_canvas_orientation_changed)
        self.canvas_landscape_radio.toggled.connect(self.on_canvas_orientation_changed)
        
        self.canvas_orientation_group.addButton(self.canvas_portrait_radio)
        self.canvas_orientation_group.addButton(self.canvas_landscape_radio)
        
        canvas_orientation_layout.addWidget(self.canvas_portrait_radio)
        canvas_orientation_layout.addWidget(self.canvas_landscape_radio)
        canvas_orientation_layout.addStretch()
        
        canvas_layout.addLayout(canvas_orientation_layout)
        canvas_group.setLayout(canvas_layout)
        layout.addWidget(canvas_group)
        
        # PDF Ayarları
        pdf_group = QGroupBox("PDF Export Ayarları")
        pdf_layout = QVBoxLayout()
        
        # PDF yönü
        pdf_orientation_layout = QHBoxLayout()
        pdf_orientation_layout.addWidget(QLabel("PDF Yönü:"))
        
        self.pdf_orientation_group = QButtonGroup()
        self.pdf_portrait_radio = QRadioButton("Dikey")
        self.pdf_landscape_radio = QRadioButton("Yatay")
        
        if self.pdf_orientation == 'landscape':
            self.pdf_landscape_radio.setChecked(True)
        else:
            self.pdf_portrait_radio.setChecked(True)
            
        self.pdf_portrait_radio.toggled.connect(self.on_pdf_orientation_changed)
        self.pdf_landscape_radio.toggled.connect(self.on_pdf_orientation_changed)
        
        self.pdf_orientation_group.addButton(self.pdf_portrait_radio)
        self.pdf_orientation_group.addButton(self.pdf_landscape_radio)
        
        pdf_orientation_layout.addWidget(self.pdf_portrait_radio)
        pdf_orientation_layout.addWidget(self.pdf_landscape_radio)
        pdf_orientation_layout.addStretch()
        
        pdf_layout.addLayout(pdf_orientation_layout)
        pdf_group.setLayout(pdf_layout)
        layout.addWidget(pdf_group)
        
        # Arka Plan Ayarları
        bg_group = QGroupBox("Arka Plan Ayarları")
        bg_layout = QVBoxLayout()
        
        # Arka plan tipi seçimi
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
            
        bg_layout.addLayout(type_layout)
        
        # Arka plan rengi
        bg_color_layout = QHBoxLayout()
        bg_color_layout.addWidget(QLabel("Arka Plan Rengi:"))
        
        self.bg_color_button = QPushButton()
        self.bg_color_button.setFixedSize(30, 25)
        self.bg_color_button.clicked.connect(self.choose_background_color)
        self.update_bg_color_button()
        bg_color_layout.addWidget(self.bg_color_button)
        bg_color_layout.addStretch()
        
        bg_layout.addLayout(bg_color_layout)
        
        # Grid ayarları
        self.grid_group = QGroupBox("Çizgi/Kare Ayarları")
        grid_layout = QVBoxLayout()
        
        # İnce çizgi rengi
        grid_color_layout = QHBoxLayout()
        grid_color_layout.addWidget(QLabel("İnce Çizgi Rengi:"))
        
        self.grid_color_button = QPushButton()
        self.grid_color_button.setFixedSize(30, 25)
        self.grid_color_button.clicked.connect(self.choose_grid_color)
        self.update_grid_color_button()
        grid_color_layout.addWidget(self.grid_color_button)
        grid_color_layout.addStretch()
        
        grid_layout.addLayout(grid_color_layout)
        
        # Kalın çizgi rengi
        major_color_layout = QHBoxLayout()
        major_color_layout.addWidget(QLabel("Kalın Çizgi Rengi:"))
        
        self.major_grid_color_button = QPushButton()
        self.major_grid_color_button.setFixedSize(30, 25)
        self.major_grid_color_button.clicked.connect(self.choose_major_grid_color)
        self.update_major_grid_color_button()
        major_color_layout.addWidget(self.major_grid_color_button)
        major_color_layout.addStretch()
        
        grid_layout.addLayout(major_color_layout)
        
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
        
        # İnce çizgi kalınlığı
        width_layout = QHBoxLayout()
        width_layout.addWidget(QLabel("İnce Çizgi Kalınlığı:"))
        
        self.width_spinbox = QSpinBox()
        self.width_spinbox.setRange(1, 5)
        self.width_spinbox.setValue(self.grid_width)
        self.width_spinbox.setSuffix(" px")
        self.width_spinbox.valueChanged.connect(self.on_grid_width_changed)
        width_layout.addWidget(self.width_spinbox)
        width_layout.addStretch()
        
        grid_layout.addLayout(width_layout)

        # İnce çizgi aralığı
        minor_interval_layout = QHBoxLayout()
        minor_interval_layout.addWidget(QLabel("İnce Çizgi Aralığı:"))
        
        self.minor_interval_spinbox = QDoubleSpinBox()
        self.minor_interval_spinbox.setDecimals(1)
        self.minor_interval_spinbox.setSingleStep(0.1)
        self.minor_interval_spinbox.setRange(0.1, 10.0)
        self.minor_interval_spinbox.setValue(self.minor_grid_interval)
        self.minor_interval_spinbox.setSuffix(" çizgi")
        self.minor_interval_spinbox.valueChanged.connect(self.on_minor_grid_interval_changed)
        minor_interval_layout.addWidget(self.minor_interval_spinbox)
        minor_interval_layout.addStretch()
        
        grid_layout.addLayout(minor_interval_layout)
        
        # Kalın çizgi kalınlığı
        major_width_layout = QHBoxLayout()
        major_width_layout.addWidget(QLabel("Kalın Çizgi Kalınlığı:"))
        
        self.major_width_spinbox = QSpinBox()
        self.major_width_spinbox.setRange(1, 8)
        self.major_width_spinbox.setValue(self.major_grid_width)
        self.major_width_spinbox.setSuffix(" px")
        self.major_width_spinbox.valueChanged.connect(self.on_major_grid_width_changed)
        major_width_layout.addWidget(self.major_width_spinbox)
        major_width_layout.addStretch()
        
        grid_layout.addLayout(major_width_layout)
        
        # Kalın çizgi aralığı
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Kalın Çizgi Aralığı:"))
        
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setRange(2, 20)
        self.interval_spinbox.setValue(self.major_grid_interval)
        self.interval_spinbox.setSuffix(" çizgi")
        self.interval_spinbox.valueChanged.connect(self.on_major_grid_interval_changed)
        interval_layout.addWidget(self.interval_spinbox)
        interval_layout.addStretch()
        
        grid_layout.addLayout(interval_layout)
        
        # Grid saydamlığı
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("Saydamlık:"))
        
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(10, 100)  # %10 ile %100 arası
        self.opacity_slider.setValue(int(self.grid_opacity * 100))
        self.opacity_slider.valueChanged.connect(self.on_grid_opacity_changed)
        opacity_layout.addWidget(self.opacity_slider)
        
        self.opacity_label = QLabel(f"{int(self.grid_opacity * 100)}%")
        self.opacity_label.setMinimumWidth(35)
        opacity_layout.addWidget(self.opacity_label)
        
        grid_layout.addLayout(opacity_layout)
        
        # Snap to grid seçeneği
        self.snap_checkbox = QCheckBox("Grid'e Yapıştır (Snap to Grid)")
        self.snap_checkbox.setChecked(self.snap_to_grid)
        self.snap_checkbox.toggled.connect(self.on_snap_changed)
        grid_layout.addWidget(self.snap_checkbox)
        
        self.grid_group.setLayout(grid_layout)
        self.grid_group.setEnabled(True)
        bg_layout.addWidget(self.grid_group)
        
        bg_group.setLayout(bg_layout)
        layout.addWidget(bg_group)
        
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
        
    def update_major_grid_color_button(self):
        """Kalın grid renk butonunu güncelle"""
        color_hex = self.major_grid_color.name()
        self.major_grid_color_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color_hex};
                border: 1px solid #999;
                border-radius: 3px;
            }}
        """)
        
    def on_canvas_size_changed(self):
        """Canvas boyutu değiştiğinde"""
        current_data = self.canvas_size_combo.currentData()
        if current_data:
            self.canvas_size = current_data
            self.canvasSizeChanged.emit(current_data)
            
    def on_canvas_orientation_changed(self):
        """Canvas yönü değiştiğinde"""
        if self.canvas_portrait_radio.isChecked():
            self.canvas_orientation = 'portrait'
        else:
            self.canvas_orientation = 'landscape'
        self.canvasOrientationChanged.emit(self.canvas_orientation)
        
    def on_pdf_orientation_changed(self):
        """PDF yönü değiştiğinde"""
        if self.pdf_portrait_radio.isChecked():
            self.pdf_orientation = 'portrait'
        else:
            self.pdf_orientation = 'landscape'
        self.pdfOrientationChanged.emit(self.pdf_orientation)
        
    def on_type_changed(self):
        """Arka plan tipi değiştiğinde"""
        for button in self.type_group.buttons():
            if button.isChecked():
                self.background_type = button.objectName()
                break
        self.emit_background_changed()
        
    def choose_background_color(self):
        """Arka plan rengi seç"""
        color = QColorDialog.getColor(self.background_color, self)
        if color.isValid():
            self.background_color = color
            self.update_bg_color_button()
            self.emit_background_changed()
            
    def choose_grid_color(self):
        """Grid rengi seç"""
        color = QColorDialog.getColor(self.grid_color, self)
        if color.isValid():
            self.grid_color = color
            self.update_grid_color_button()
            self.emit_background_changed()
            
    def choose_major_grid_color(self):
        """Kalın grid rengi seç"""
        color = QColorDialog.getColor(self.major_grid_color, self)
        if color.isValid():
            self.major_grid_color = color
            self.update_major_grid_color_button()
            self.emit_background_changed()
            
    def on_grid_size_changed(self, value):
        """Grid boyutu değiştiğinde"""
        self.grid_size = value
        self.emit_background_changed()
        
    def on_grid_width_changed(self, value):
        """İnce grid kalınlığı değiştiğinde"""
        self.grid_width = value
        self.emit_background_changed()
        
    def on_major_grid_width_changed(self, value):
        """Kalın grid kalınlığı değiştiğinde"""
        self.major_grid_width = value
        self.emit_background_changed()
        
    def on_major_grid_interval_changed(self, value):
        """Kalın grid aralığı değiştiğinde"""
        self.major_grid_interval = value
        self.emit_background_changed()
        
    def on_minor_grid_interval_changed(self, value):
        """İnce grid aralığı değiştiğinde"""
        self.minor_grid_interval = float(value)
        self.emit_background_changed()
        
    def on_grid_opacity_changed(self, value):
        """Grid saydamlığı değiştiğinde"""
        self.grid_opacity = value / 100.0
        self.opacity_label.setText(f"{value}%")
        self.emit_background_changed()
        
    def on_snap_changed(self, checked):
        """Snap to grid değiştiğinde"""
        self.snap_to_grid = checked
        self.emit_background_changed()
        
    def emit_background_changed(self):
        """Arka plan değişikliği sinyali gönder"""
        settings = {
            'type': self.background_type,
            'background_color': self.background_color,
            'grid_color': self.grid_color,
            'major_grid_color': self.major_grid_color,
            'grid_size': self.grid_size,
            'grid_width': self.grid_width,
            'major_grid_width': self.major_grid_width,
            'major_grid_interval': self.major_grid_interval,
            'minor_grid_interval': self.minor_grid_interval,
            'grid_opacity': self.grid_opacity,
            'snap_to_grid': self.snap_to_grid
        }
        self.backgroundChanged.emit(settings)
        
    def get_background_settings(self):
        """Arka plan ayarlarını döndür"""
        return {
            'type': self.background_type,
            'background_color': self.background_color,
            'grid_color': self.grid_color,
            'major_grid_color': self.major_grid_color,
            'grid_size': self.grid_size,
            'grid_width': self.grid_width,
            'major_grid_width': self.major_grid_width,
            'major_grid_interval': self.major_grid_interval,
            'minor_grid_interval': self.minor_grid_interval,
            'grid_opacity': self.grid_opacity,
            'snap_to_grid': self.snap_to_grid
        }
        
    def set_background_settings(self, settings):
        """Arka plan ayarlarını uygula"""
        self.background_type = settings.get('type', 'solid')
        self.background_color = settings.get('background_color', QColor(255, 255, 255))
        self.grid_color = settings.get('grid_color', QColor(200, 200, 200))
        self.major_grid_color = settings.get('major_grid_color', QColor(150, 150, 150))
        self.grid_size = settings.get('grid_size', 20)
        self.grid_width = settings.get('grid_width', 1)
        self.major_grid_width = settings.get('major_grid_width', 2)
        self.major_grid_interval = settings.get('major_grid_interval', 5)
        self.minor_grid_interval = float(settings.get('minor_grid_interval', 1.0))
        self.grid_opacity = settings.get('grid_opacity', 1.0)
        self.snap_to_grid = settings.get('snap_to_grid', False)
        
        # UI'ı güncelle
        for button in self.type_group.buttons():
            if button.objectName() == self.background_type:
                button.setChecked(True)
                break
                
        self.update_bg_color_button()
        self.update_grid_color_button()
        self.update_major_grid_color_button()
        self.size_spinbox.setValue(self.grid_size)
        self.width_spinbox.setValue(self.grid_width)
        self.major_width_spinbox.setValue(self.major_grid_width)
        self.interval_spinbox.setValue(self.major_grid_interval)
        self.minor_interval_spinbox.setValue(self.minor_grid_interval)
        self.opacity_slider.setValue(int(self.grid_opacity * 100))
        self.opacity_label.setText(f"{int(self.grid_opacity * 100)}%")
        self.snap_checkbox.setChecked(self.snap_to_grid)
        
    def set_pdf_orientation(self, orientation):
        """PDF yönünü ayarla"""
        self.pdf_orientation = orientation
        if orientation == 'portrait':
            self.pdf_portrait_radio.setChecked(True)
        else:
            self.pdf_landscape_radio.setChecked(True)
            
    def set_canvas_orientation(self, orientation):
        """Canvas yönünü ayarla"""
        self.canvas_orientation = orientation
        if orientation == 'portrait':
            self.canvas_portrait_radio.setChecked(True)
        else:
            self.canvas_landscape_radio.setChecked(True)
            
    def set_canvas_size(self, size):
        """Canvas boyutunu ayarla"""
        self.canvas_size = size
        for i in range(self.canvas_size_combo.count()):
            if self.canvas_size_combo.itemData(i) == size:
                self.canvas_size_combo.setCurrentIndex(i)
                break 