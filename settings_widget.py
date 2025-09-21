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
    shadowDefaultsChanged = pyqtSignal(dict)
    fillDefaultsChanged = pyqtSignal(dict)
    
    BACKGROUND_TYPES = {
        'solid': 'Düz Renk',
        'grid': 'Çizgili',
        'dots': 'Kareli'
    }
    
    CANVAS_SIZES = {
        'small': 'Küçük (827x1169)',
        'medium': 'Orta (1240x1754)',
        'large': 'Büyük (2480x3508)',
        'custom': 'Özel...',
        'screen': 'Ekran'
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
        from PyQt6.QtWidgets import QScrollArea, QWidget as QtWidget
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(0)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        scroll_widget = QtWidget()
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

        # Varsayılan Gölge Ayarları
        shadow_group = QGroupBox("Varsayılan Gölge")
        sh_layout = QVBoxLayout()

        # Araç seçimi (global veya araç bazlı)
        tool_row = QHBoxLayout()
        tool_row.addWidget(QLabel("Araç:"))
        self.shadow_tool_combo = QComboBox()
        # key -> etiket
        self.shadow_tool_combo.addItem("Genel", "")
        self.shadow_tool_combo.addItem("Line", "Line")
        self.shadow_tool_combo.addItem("Rectangle", "Rectangle")
        self.shadow_tool_combo.addItem("Circle", "Circle")
        self.shadow_tool_combo.addItem("B‑Spline", "BSpline")
        self.shadow_tool_combo.addItem("Freehand", "Freehand")
        tool_row.addWidget(self.shadow_tool_combo)
        tool_row.addStretch()
        sh_layout.addLayout(tool_row)

        # Etkin
        sh_enabled_layout = QHBoxLayout()
        self.shadow_enabled_checkbox = QCheckBox("Gölge Kullan")
        sh_enabled_layout.addWidget(self.shadow_enabled_checkbox)
        sh_enabled_layout.addStretch()
        sh_layout.addLayout(sh_enabled_layout)

        # Renk
        sh_color_layout = QHBoxLayout()
        sh_color_layout.addWidget(QLabel("Renk:"))
        self.shadow_color_button = QPushButton()
        self.shadow_color_button.setFixedSize(30, 25)
        self.shadow_color_button.clicked.connect(self.choose_shadow_default_color)
        sh_color_layout.addWidget(self.shadow_color_button)
        sh_color_layout.addStretch()
        sh_layout.addLayout(sh_color_layout)

        # Offset
        sh_off_layout = QHBoxLayout()
        sh_off_layout.addWidget(QLabel("Offset:"))
        self.shadow_off_x = QSpinBox()
        self.shadow_off_x.setRange(-50, 50)
        self.shadow_off_y = QSpinBox()
        self.shadow_off_y.setRange(-50, 50)
        sh_off_layout.addWidget(self.shadow_off_x)
        sh_off_layout.addWidget(self.shadow_off_y)
        sh_off_layout.addStretch()
        sh_layout.addLayout(sh_off_layout)

        # Blur / Size
        sh_blur_layout = QHBoxLayout()
        sh_blur_layout.addWidget(QLabel("Bulanıklık:"))
        self.shadow_blur_spin = QSpinBox()
        self.shadow_blur_spin.setRange(0, 50)
        sh_blur_layout.addWidget(self.shadow_blur_spin)
        sh_blur_layout.addWidget(QLabel("Boyut:"))
        self.shadow_size_spin = QSpinBox()
        self.shadow_size_spin.setRange(0, 50)
        sh_blur_layout.addWidget(self.shadow_size_spin)
        sh_blur_layout.addStretch()
        sh_layout.addLayout(sh_blur_layout)

        # Opacity
        sh_op_layout = QHBoxLayout()
        sh_op_layout.addWidget(QLabel("Şeffaflık:"))
        self.shadow_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.shadow_opacity_slider.setRange(0, 100)
        self.shadow_opacity_label = QLabel("70%")
        self.shadow_opacity_label.setMinimumWidth(35)
        sh_op_layout.addWidget(self.shadow_opacity_slider)
        sh_op_layout.addWidget(self.shadow_opacity_label)
        sh_layout.addLayout(sh_op_layout)

        # İç/Dış ve kalite
        sh_type_layout = QHBoxLayout()
        self.shadow_inner_checkbox = QCheckBox("İç Gölge")
        sh_type_layout.addWidget(self.shadow_inner_checkbox)
        sh_type_layout.addWidget(QLabel("Kalite:"))
        self.shadow_quality_combo = QComboBox()
        self.shadow_quality_combo.addItem("Düşük", "low")
        self.shadow_quality_combo.addItem("Orta", "medium")
        self.shadow_quality_combo.addItem("Yüksek", "high")
        sh_type_layout.addWidget(self.shadow_quality_combo)
        sh_type_layout.addStretch()
        sh_layout.addLayout(sh_type_layout)

        shadow_group.setLayout(sh_layout)
        layout.addWidget(shadow_group)

        # Başlangıç değerleri
        self.load_shadow_defaults_from_settings()
        # Araç değişince mevcut ayarları yükleyelim
        def on_tool_combo_changed(_):
            self.load_shadow_defaults_from_settings()
            self.emit_shadow_defaults()
        self.shadow_tool_combo.currentIndexChanged.connect(on_tool_combo_changed)

        # Değişiklikleri dinle
        self.shadow_enabled_checkbox.toggled.connect(self.emit_shadow_defaults)
        self.shadow_off_x.valueChanged.connect(self.emit_shadow_defaults)
        self.shadow_off_y.valueChanged.connect(self.emit_shadow_defaults)
        self.shadow_blur_spin.valueChanged.connect(self.emit_shadow_defaults)
        self.shadow_size_spin.valueChanged.connect(self.emit_shadow_defaults)
        self.shadow_opacity_slider.valueChanged.connect(self.on_shadow_opacity_slider)
        self.shadow_inner_checkbox.toggled.connect(self.emit_shadow_defaults)
        self.shadow_quality_combo.currentIndexChanged.connect(self.emit_shadow_defaults)
        
        # Fill defaults section
        self.add_fill_defaults_section(layout)
        
        layout.addStretch()
        scroll_widget.setLayout(layout)
        self.scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(self.scroll_area)
        self.setLayout(main_layout)
        
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
        if not current_data:
            return
        self.canvas_size = current_data
        if current_data == 'custom':
            from PyQt6.QtWidgets import QInputDialog
            width, ok_w = QInputDialog.getInt(self, "Özel Genişlik", "Genişlik (px)", 1200, 100, 10000, 10)
            if not ok_w:
                return
            height, ok_h = QInputDialog.getInt(self, "Özel Yükseklik", "Yükseklik (px)", 800, 100, 10000, 10)
            if not ok_h:
                return
            self.canvasSizeChanged.emit(f"custom:{width}x{height}")
        elif current_data == 'screen':
            self.canvasSizeChanged.emit('screen')
        else:
            self.canvasSizeChanged.emit(current_data)

    # ---------- Varsayılan Gölge Yardımcıları ----------
    def load_shadow_defaults_from_settings(self):
        try:
            from settings_manager import SettingsManager
            mgr = SettingsManager()
            tool_key = self.shadow_tool_combo.currentData()
            defaults = mgr.get_shadow_defaults(tool_key)
        except Exception:
            from PyQt6.QtGui import QColor
            defaults = {
                'has_shadow': False,
                'shadow_color': QColor('#000000'),
                'shadow_offset_x': 5,
                'shadow_offset_y': 5,
                'shadow_blur': 10,
                'shadow_size': 0,
                'shadow_opacity': 0.7,
                'inner_shadow': False,
                'shadow_quality': 'medium'
            }
        self.shadow_enabled_checkbox.setChecked(defaults['has_shadow'])
        self.set_shadow_color_button(defaults['shadow_color'])
        self.shadow_off_x.setValue(defaults['shadow_offset_x'])
        self.shadow_off_y.setValue(defaults['shadow_offset_y'])
        self.shadow_blur_spin.setValue(defaults['shadow_blur'])
        self.shadow_size_spin.setValue(defaults['shadow_size'])
        self.shadow_opacity_slider.setValue(int(defaults['shadow_opacity'] * 100))
        self.shadow_opacity_label.setText(f"{int(defaults['shadow_opacity']*100)}%")
        self.shadow_inner_checkbox.setChecked(defaults['inner_shadow'])
        for i in range(self.shadow_quality_combo.count()):
            if self.shadow_quality_combo.itemData(i) == defaults['shadow_quality']:
                self.shadow_quality_combo.setCurrentIndex(i)
                break

    def set_shadow_color_button(self, color: QColor):
        color_hex = color.name()
        self.shadow_color_button.setStyleSheet(f"background-color: {color_hex}; border:1px solid #999; border-radius:3px;")

    def choose_shadow_default_color(self):
        color = QColorDialog.getColor(QColor('#000000'), self)
        if color.isValid():
            self.set_shadow_color_button(color)
            self.emit_shadow_defaults()

    def on_shadow_opacity_slider(self, value):
        self.shadow_opacity_label.setText(f"{value}%")
        self.emit_shadow_defaults()

    def emit_shadow_defaults(self):
        # Renk butonundaki rengi palette üzerinden al
        color = self.shadow_color_button.palette().button().color()
        payload = {
            'has_shadow': self.shadow_enabled_checkbox.isChecked(),
            'shadow_color': color,
            'shadow_offset_x': self.shadow_off_x.value(),
            'shadow_offset_y': self.shadow_off_y.value(),
            'shadow_blur': self.shadow_blur_spin.value(),
            'shadow_size': self.shadow_size_spin.value(),
            'shadow_opacity': self.shadow_opacity_slider.value()/100.0,
            'inner_shadow': self.shadow_inner_checkbox.isChecked(),
            'shadow_quality': self.shadow_quality_combo.currentData(),
        }
        tool_key = self.shadow_tool_combo.currentData()
        payload['tool_key'] = tool_key
        self.shadowDefaultsChanged.emit(payload)

        # --- Varsayılan Dolgu ---
        # (Bu fonksiyon içinde değil; aşağıda ayrı bölümde sinyallenecek)

        
        
            
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

    def add_fill_defaults_section(self, parent_layout: QVBoxLayout):
        group = QGroupBox("Varsayılan Dolgu")
        lay = QVBoxLayout()
        row1 = QHBoxLayout()
        self.fill_enabled_checkbox = QCheckBox("Dolgu Kullan")
        row1.addWidget(self.fill_enabled_checkbox)
        row1.addStretch()
        lay.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Renk:"))
        self.fill_color_button = QPushButton()
        self.fill_color_button.setFixedSize(30,25)
        self.fill_color_button.clicked.connect(self.choose_fill_default_color)
        row2.addWidget(self.fill_color_button)
        row2.addStretch()
        lay.addLayout(row2)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Şeffaflık:"))
        self.fill_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.fill_opacity_slider.setRange(0,100)
        self.fill_opacity_label = QLabel("100%")
        self.fill_opacity_label.setMinimumWidth(35)
        row3.addWidget(self.fill_opacity_slider)
        row3.addWidget(self.fill_opacity_label)
        lay.addLayout(row3)

        group.setLayout(lay)
        parent_layout.addWidget(group)

        # Başlangıç değerleri yükle
        self.load_fill_defaults_from_settings()
        # Eventler
        self.fill_enabled_checkbox.toggled.connect(self.emit_fill_defaults)
        self.fill_opacity_slider.valueChanged.connect(self.on_fill_opacity_slider)

    def load_fill_defaults_from_settings(self):
        try:
            from settings_manager import SettingsManager
            mgr = SettingsManager()
            d = mgr.get_fill_defaults()
        except Exception:
            from PyQt6.QtGui import QColor
            d = {'enabled': False, 'color': QColor('#FFFFFF'), 'opacity': 1.0}
        self.fill_enabled_checkbox.setChecked(d['enabled'])
        color_hex = d['color'].name()
        self.fill_color_button.setStyleSheet(f"background-color: {color_hex}; border:1px solid #999; border-radius:3px;")
        self.fill_opacity_slider.setValue(int(d['opacity']*100))
        self.fill_opacity_label.setText(f"{int(d['opacity']*100)}%")

    def choose_fill_default_color(self):
        color = QColorDialog.getColor(QColor('#FFFFFF'), self)
        if color.isValid():
            self.fill_color_button.setStyleSheet(f"background-color: {color.name()}; border:1px solid #999; border-radius:3px;")
            self.emit_fill_defaults()

    def on_fill_opacity_slider(self, value):
        self.fill_opacity_label.setText(f"{value}%")
        self.emit_fill_defaults()

    def emit_fill_defaults(self):
        # Rengi butondan oku
        color = self.fill_color_button.palette().button().color()
        payload = {'enabled': self.fill_enabled_checkbox.isChecked(), 'color': color, 'opacity': self.fill_opacity_slider.value()/100.0}
        self.fillDefaultsChanged.emit(payload) 