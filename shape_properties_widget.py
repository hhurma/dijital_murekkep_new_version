from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QColorDialog, QSpinBox, QButtonGroup,
                            QGroupBox, QRadioButton, QCheckBox, QSlider, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen
import qtawesome as qta

class ShapePropertiesWidget(QWidget):
    """Seçilen şekillerin özelliklerini düzenlemek için widget"""
    
    # Özellik değişiklik sinyalleri
    colorChanged = pyqtSignal(QColor)  # Çizgi rengi değişti
    widthChanged = pyqtSignal(int)     # Çizgi kalınlığı değişti
    lineStyleChanged = pyqtSignal(Qt.PenStyle) # Çizgi stili değişti
    fillColorChanged = pyqtSignal(QColor)  # Dolgu rengi değişti
    fillEnabledChanged = pyqtSignal(bool)  # Dolgu etkin/pasif
    fillOpacityChanged = pyqtSignal(float)  # Dolgu şeffaflığı değişti
    
    # Resim özellikleri sinyalleri
    imageOpacityChanged = pyqtSignal(float)  # Resim şeffaflığı değişti
    imageBorderEnabledChanged = pyqtSignal(bool)  # Resim kenarlığı etkin/pasif
    imageBorderColorChanged = pyqtSignal(QColor)  # Resim kenarlık rengi değişti
    imageBorderWidthChanged = pyqtSignal(int)  # Resim kenarlık kalınlığı değişti
    imageBorderStyleChanged = pyqtSignal(Qt.PenStyle)  # Resim kenarlık stili değişti
    imageShadowEnabledChanged = pyqtSignal(bool)  # Resim gölgesi etkin/pasif
    imageShadowColorChanged = pyqtSignal(QColor)  # Resim gölge rengi değişti
    imageShadowOffsetChanged = pyqtSignal(int, int)  # Resim gölge offseti değişti
    imageShadowBlurChanged = pyqtSignal(int)  # Resim gölge bulanıklığı değişti
    imageShadowSizeChanged = pyqtSignal(int)  # Resim gölge boyutu değişti
    imageShadowInnerChanged = pyqtSignal(bool)  # İç/dış gölge değişti
    imageShadowQualityChanged = pyqtSignal(str)  # Gölge kalitesi değişti
    imageFilterChanged = pyqtSignal(str, float)  # Resim filtresi değişti (tip, intensity)
    imageTransparencyChanged = pyqtSignal(float)  # Resim şeffaflığı değişti (ekstra)
    imageBlurChanged = pyqtSignal(int)  # Resim bulanıklığı değişti
    imageCornerRadiusChanged = pyqtSignal(int)  # Kenar yuvarlama değişti
    imageShadowOpacityChanged = pyqtSignal(float)  # Gölge şeffaflığı değişti
    
    # Dikdörtgen özellikleri sinyalleri
    rectangleCornerRadiusChanged = pyqtSignal(int)  # Dikdörtgen kenar yuvarlama değişti
    rectangleShadowEnabledChanged = pyqtSignal(bool)  # Dikdörtgen gölgesi etkin/pasif
    rectangleShadowColorChanged = pyqtSignal(QColor)  # Dikdörtgen gölge rengi değişti
    rectangleShadowOffsetChanged = pyqtSignal(int, int)  # Dikdörtgen gölge offseti değişti
    rectangleShadowBlurChanged = pyqtSignal(int)  # Dikdörtgen gölge bulanıklığı değişti
    rectangleShadowSizeChanged = pyqtSignal(int)  # Dikdörtgen gölge boyutu değişti
    rectangleShadowOpacityChanged = pyqtSignal(float)  # Dikdörtgen gölge şeffaflığı değişti
    rectangleShadowInnerChanged = pyqtSignal(bool)  # Dikdörtgen iç/dış gölge değişti
    rectangleShadowQualityChanged = pyqtSignal(str)  # Dikdörtgen gölge kalitesi değişti
    
    # Çember özellikleri sinyalleri
    circleShadowEnabledChanged = pyqtSignal(bool)  # Çember gölgesi etkin/pasif
    circleShadowColorChanged = pyqtSignal(QColor)  # Çember gölge rengi değişti
    circleShadowOffsetChanged = pyqtSignal(int, int)  # Çember gölge offseti değişti
    circleShadowBlurChanged = pyqtSignal(int)  # Çember gölge bulanıklığı değişti
    circleShadowSizeChanged = pyqtSignal(int)  # Çember gölge boyutu değişti
    circleShadowOpacityChanged = pyqtSignal(float)  # Çember gölge şeffaflığı değişti
    circleShadowInnerChanged = pyqtSignal(bool)  # Çember iç/dış gölge değişti
    circleShadowQualityChanged = pyqtSignal(str)  # Çember gölge kalitesi değişti

    # Çizgi gölge özellikleri sinyalleri
    strokeShadowEnabledChanged = pyqtSignal(bool)
    strokeShadowColorChanged = pyqtSignal(QColor)
    strokeShadowOffsetChanged = pyqtSignal(int, int)
    strokeShadowBlurChanged = pyqtSignal(int)
    strokeShadowSizeChanged = pyqtSignal(int)
    strokeShadowOpacityChanged = pyqtSignal(float)
    strokeShadowInnerChanged = pyqtSignal(bool)
    strokeShadowQualityChanged = pyqtSignal(str)
    
    # Grup işlemi sinyalleri
    groupShapes = pyqtSignal()  # Şekilleri grupla
    ungroupShapes = pyqtSignal()  # Grubu çöz
    
    # Hizalama sinyalleri
    alignLeft = pyqtSignal()  # Sola hizala
    alignRight = pyqtSignal()  # Sağa hizala
    alignTop = pyqtSignal()  # Yukarı hizala
    alignBottom = pyqtSignal()  # Aşağı hizala
    alignCenterH = pyqtSignal()  # Yatay ortala
    alignCenterV = pyqtSignal()  # Dikey ortala
    distributeH = pyqtSignal()  # Yatay dağıt
    distributeV = pyqtSignal()  # Dikey dağıt
    
    # Şekil havuzu sinyali
    addToShapeLibrary = pyqtSignal()  # Seçili şekilleri şekil havuzuna ekle
    
    # B-spline kontrol noktaları sinyali
    toggleControlPoints = pyqtSignal()  # B-spline kontrol noktalarını göster/gizle
    
    LINE_STYLES = {
        Qt.PenStyle.SolidLine: 'Düz',
        Qt.PenStyle.DashLine: 'Kesikli',
        Qt.PenStyle.DotLine: 'Noktalı',
        Qt.PenStyle.DashDotLine: 'Çizgi-Nokta'
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Mevcut değerler
        self.current_color = QColor(0, 0, 0)  # Siyah
        self.current_width = 2
        self.current_line_style = Qt.PenStyle.SolidLine
        self.current_fill_color = QColor(255, 255, 255)  # Beyaz
        self.current_fill_enabled = False
        self.current_fill_opacity = 1.0  # Tam opak
        
        # Resim özellikleri değerleri
        self.current_image_opacity = 1.0
        self.current_border_enabled = False
        self.current_border_color = QColor(0, 0, 0)  # Siyah
        self.current_border_width = 2
        self.current_border_style = Qt.PenStyle.SolidLine
        self.current_shadow_enabled = False
        self.current_shadow_color = QColor(0, 0, 0, 128)  # Yarı şeffaf siyah
        self.current_shadow_offset_x = 3
        self.current_shadow_offset_y = 3
        self.current_shadow_blur = 5
        self.current_shadow_size = 0
        self.current_inner_shadow = False
        self.current_shadow_quality = "medium"
        self.current_filter_type = "none"
        self.current_filter_intensity = 1.0
        self.current_transparency = 1.0
        self.current_blur_radius = 0
        self.current_corner_radius = 0
        self.current_shadow_opacity = 1.0
        
        # Dikdörtgen özellikleri değerleri
        self.current_rect_corner_radius = 0
        self.current_rect_shadow_enabled = False
        self.current_rect_shadow_color = QColor(0, 0, 0, 128)  # Yarı şeffaf siyah
        self.current_rect_shadow_offset_x = 5
        self.current_rect_shadow_offset_y = 5
        self.current_rect_shadow_blur = 10
        self.current_rect_shadow_size = 0
        self.current_rect_shadow_opacity = 0.7
        self.current_rect_inner_shadow = False
        self.current_rect_shadow_quality = "medium"
        
        # Çember özellikleri değerleri
        self.current_circle_shadow_enabled = False
        self.current_circle_shadow_color = QColor(0, 0, 0, 128)  # Yarı şeffaf siyah
        self.current_circle_shadow_offset_x = 5
        self.current_circle_shadow_offset_y = 5
        self.current_circle_shadow_blur = 10
        self.current_circle_shadow_size = 0
        self.current_circle_shadow_opacity = 0.7
        self.current_circle_inner_shadow = False
        self.current_circle_shadow_quality = "medium"

        # Çizgi gölge özellikleri değerleri
        self.current_stroke_shadow_enabled = False
        self.current_stroke_shadow_color = QColor(0, 0, 0, 128)
        self.current_stroke_shadow_offset_x = 5
        self.current_stroke_shadow_offset_y = 5
        self.current_stroke_shadow_blur = 10
        self.current_stroke_shadow_size = 0
        self.current_stroke_shadow_opacity = 0.7
        self.current_stroke_inner_shadow = False
        self.current_stroke_shadow_quality = "medium"

        # Seçilen şekil bilgileri
        self.selected_strokes = []
        self.stroke_data = []
        self.has_fillable_shapes = False  # Dikdörtgen/daire var mı
        self.has_bspline_shapes = False   # B-spline şekilleri var mı
        self.has_image_shapes = False     # Resim var mı
        self.has_rectangle_shapes = False # Dikdörtgen var mı (gölge/kenar için)
        self.has_circle_shapes = False    # Çember var mı (gölge için)
        self.has_stroke_shadow_shapes = False  # Çizgi gölgesi olan stroke var mı
        
        self.setup_ui()
        
    def setup_ui(self):
        """UI bileşenlerini oluştur"""
        from PyQt6.QtWidgets import QScrollArea
        
        # Ana layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Scroll area oluştur
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Scroll widget oluştur
        scroll_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(8)
        
        # Başlık
        title_label = QLabel("Şekil Özellikleri")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)
        
        # Çizgi özellikleri grubu
        line_group = QGroupBox("Çizgi Özellikleri")
        line_layout = QVBoxLayout()
        
        # Çizgi rengi
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Renk:"))
        
        self.color_button = QPushButton()
        self.color_button.setFixedSize(40, 25)
        self.color_button.clicked.connect(self.choose_color)
        self.update_color_button()
        color_layout.addWidget(self.color_button)
        color_layout.addStretch()
        
        line_layout.addLayout(color_layout)
        
        # Çizgi kalınlığı
        width_layout = QHBoxLayout()
        width_layout.addWidget(QLabel("Kalınlık:"))
        
        self.width_spinbox = QSpinBox()
        self.width_spinbox.setRange(1, 50)
        self.width_spinbox.setValue(self.current_width)
        self.width_spinbox.setSuffix(" px")
        self.width_spinbox.valueChanged.connect(self.on_width_changed)
        width_layout.addWidget(self.width_spinbox)
        width_layout.addStretch()
        
        line_layout.addLayout(width_layout)
        
        # Çizgi stili
        style_layout = QHBoxLayout()
        style_layout.addWidget(QLabel("Stil:"))
        
        self.style_combo = QComboBox()
        for style, name in self.LINE_STYLES.items():
            self.style_combo.addItem(name, style)
        self.style_combo.currentIndexChanged.connect(self.on_style_changed)
        style_layout.addWidget(self.style_combo)
        style_layout.addStretch()
        
        line_layout.addLayout(style_layout)
        
        line_group.setLayout(line_layout)
        layout.addWidget(line_group)
        
        # B-spline özellikleri grubu
        self.bspline_group = QGroupBox("B-Spline Özellikleri")
        bspline_layout = QVBoxLayout()
        
        # Kontrol noktaları butonu
        self.toggle_control_points_button = QPushButton("Noktaları Göster")
        self.toggle_control_points_button.clicked.connect(self.on_toggle_control_points)
        bspline_layout.addWidget(self.toggle_control_points_button)
        
        self.bspline_group.setLayout(bspline_layout)
        layout.addWidget(self.bspline_group)
        self.bspline_group.setVisible(False)  # Başlangıçta gizli

        # Çizgi gölge özellikleri grubu
        self.stroke_shadow_group = QGroupBox("Çizgi Gölgesi")
        stroke_shadow_layout = QVBoxLayout()

        self.stroke_shadow_checkbox = QCheckBox("Gölge Kullan")
        self.stroke_shadow_checkbox.setChecked(self.current_stroke_shadow_enabled)
        self.stroke_shadow_checkbox.toggled.connect(self.on_stroke_shadow_enabled_changed)
        stroke_shadow_layout.addWidget(self.stroke_shadow_checkbox)

        stroke_shadow_type_layout = QHBoxLayout()
        self.stroke_shadow_outer_radio = QRadioButton("Dış Gölge")
        self.stroke_shadow_inner_radio = QRadioButton("İç Gölge")
        self.stroke_shadow_outer_radio.setChecked(not self.current_stroke_inner_shadow)
        self.stroke_shadow_inner_radio.setChecked(self.current_stroke_inner_shadow)

        self.stroke_shadow_type_group = QButtonGroup()
        self.stroke_shadow_type_group.addButton(self.stroke_shadow_outer_radio, 0)
        self.stroke_shadow_type_group.addButton(self.stroke_shadow_inner_radio, 1)
        self.stroke_shadow_type_group.buttonClicked.connect(self.on_stroke_shadow_type_changed)

        stroke_shadow_type_layout.addWidget(self.stroke_shadow_outer_radio)
        stroke_shadow_type_layout.addWidget(self.stroke_shadow_inner_radio)
        stroke_shadow_layout.addLayout(stroke_shadow_type_layout)

        stroke_shadow_color_layout = QHBoxLayout()
        stroke_shadow_color_layout.addWidget(QLabel("Gölge Rengi:"))
        self.stroke_shadow_color_button = QPushButton()
        self.stroke_shadow_color_button.setFixedSize(40, 25)
        self.stroke_shadow_color_button.clicked.connect(self.choose_stroke_shadow_color)
        self.update_stroke_shadow_color_button()
        stroke_shadow_color_layout.addWidget(self.stroke_shadow_color_button)
        stroke_shadow_color_layout.addStretch()
        stroke_shadow_layout.addLayout(stroke_shadow_color_layout)

        stroke_shadow_offset_layout = QHBoxLayout()
        stroke_shadow_offset_layout.addWidget(QLabel("Gölge Offseti:"))
        self.stroke_shadow_x_spinbox = QSpinBox()
        self.stroke_shadow_x_spinbox.setRange(-50, 50)
        self.stroke_shadow_x_spinbox.setValue(self.current_stroke_shadow_offset_x)
        self.stroke_shadow_x_spinbox.setSuffix(" px")
        self.stroke_shadow_x_spinbox.valueChanged.connect(self.on_stroke_shadow_offset_changed)
        stroke_shadow_offset_layout.addWidget(self.stroke_shadow_x_spinbox)

        self.stroke_shadow_y_spinbox = QSpinBox()
        self.stroke_shadow_y_spinbox.setRange(-50, 50)
        self.stroke_shadow_y_spinbox.setValue(self.current_stroke_shadow_offset_y)
        self.stroke_shadow_y_spinbox.setSuffix(" px")
        self.stroke_shadow_y_spinbox.valueChanged.connect(self.on_stroke_shadow_offset_changed)
        stroke_shadow_offset_layout.addWidget(self.stroke_shadow_y_spinbox)
        stroke_shadow_offset_layout.addStretch()
        stroke_shadow_layout.addLayout(stroke_shadow_offset_layout)

        stroke_shadow_blur_layout = QHBoxLayout()
        stroke_shadow_blur_layout.addWidget(QLabel("Gölge Bulanıklığı:"))
        self.stroke_shadow_blur_spinbox = QSpinBox()
        self.stroke_shadow_blur_spinbox.setRange(0, 50)
        self.stroke_shadow_blur_spinbox.setValue(self.current_stroke_shadow_blur)
        self.stroke_shadow_blur_spinbox.setSuffix(" px")
        self.stroke_shadow_blur_spinbox.valueChanged.connect(self.on_stroke_shadow_blur_changed)
        stroke_shadow_blur_layout.addWidget(self.stroke_shadow_blur_spinbox)
        stroke_shadow_blur_layout.addStretch()
        stroke_shadow_layout.addLayout(stroke_shadow_blur_layout)

        stroke_shadow_size_layout = QHBoxLayout()
        stroke_shadow_size_layout.addWidget(QLabel("Gölge Boyutu:"))
        self.stroke_shadow_size_spinbox = QSpinBox()
        self.stroke_shadow_size_spinbox.setRange(0, 50)
        self.stroke_shadow_size_spinbox.setValue(self.current_stroke_shadow_size)
        self.stroke_shadow_size_spinbox.setSuffix(" px")
        self.stroke_shadow_size_spinbox.valueChanged.connect(self.on_stroke_shadow_size_changed)
        stroke_shadow_size_layout.addWidget(self.stroke_shadow_size_spinbox)
        stroke_shadow_size_layout.addStretch()
        stroke_shadow_layout.addLayout(stroke_shadow_size_layout)

        stroke_shadow_quality_layout = QHBoxLayout()
        stroke_shadow_quality_layout.addWidget(QLabel("Gölge Kalitesi:"))
        self.stroke_shadow_quality_combo = QComboBox()
        self.stroke_shadow_quality_combo.addItem("Düşük", "low")
        self.stroke_shadow_quality_combo.addItem("Orta", "medium")
        self.stroke_shadow_quality_combo.addItem("Yüksek", "high")
        for i in range(self.stroke_shadow_quality_combo.count()):
            if self.stroke_shadow_quality_combo.itemData(i) == self.current_stroke_shadow_quality:
                self.stroke_shadow_quality_combo.setCurrentIndex(i)
                break
        self.stroke_shadow_quality_combo.currentIndexChanged.connect(self.on_stroke_shadow_quality_changed)
        stroke_shadow_quality_layout.addWidget(self.stroke_shadow_quality_combo)
        stroke_shadow_quality_layout.addStretch()
        stroke_shadow_layout.addLayout(stroke_shadow_quality_layout)

        stroke_shadow_opacity_layout = QHBoxLayout()
        stroke_shadow_opacity_layout.addWidget(QLabel("Gölge Şeffaflığı:"))
        self.stroke_shadow_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.stroke_shadow_opacity_slider.setRange(0, 100)
        self.stroke_shadow_opacity_slider.setValue(int(self.current_stroke_shadow_opacity * 100))
        self.stroke_shadow_opacity_slider.valueChanged.connect(self.on_stroke_shadow_opacity_changed)
        stroke_shadow_opacity_layout.addWidget(self.stroke_shadow_opacity_slider)
        self.stroke_shadow_opacity_label = QLabel(f"{int(self.current_stroke_shadow_opacity * 100)}%")
        self.stroke_shadow_opacity_label.setMinimumWidth(35)
        stroke_shadow_opacity_layout.addWidget(self.stroke_shadow_opacity_label)
        stroke_shadow_layout.addLayout(stroke_shadow_opacity_layout)

        self.stroke_shadow_group.setLayout(stroke_shadow_layout)
        layout.addWidget(self.stroke_shadow_group)
        self.stroke_shadow_group.setVisible(False)
        
        # Dolgu özellikleri grubu (sadece dikdörtgen/daire için)
        self.fill_group = QGroupBox("Dolgu Özellikleri")
        fill_layout = QVBoxLayout()
        
        # Dolgu etkin/pasif
        self.fill_checkbox = QCheckBox("Dolgu Kullan")
        self.fill_checkbox.setChecked(self.current_fill_enabled)
        self.fill_checkbox.toggled.connect(self.on_fill_enabled_changed)
        fill_layout.addWidget(self.fill_checkbox)
        
        # Dolgu rengi
        fill_color_layout = QHBoxLayout()
        fill_color_layout.addWidget(QLabel("Dolgu Rengi:"))
        
        self.fill_color_button = QPushButton()
        self.fill_color_button.setFixedSize(40, 25)
        self.fill_color_button.clicked.connect(self.choose_fill_color)
        self.update_fill_color_button()
        fill_color_layout.addWidget(self.fill_color_button)
        fill_color_layout.addStretch()
        
        fill_layout.addLayout(fill_color_layout)
        
        # Dolgu şeffaflığı
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("Şeffaflık:"))
        
        self.fill_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.fill_opacity_slider.setRange(0, 100)  # 0-100 aralığı
        self.fill_opacity_slider.setValue(int(self.current_fill_opacity * 100))
        self.fill_opacity_slider.valueChanged.connect(self.on_fill_opacity_changed)
        opacity_layout.addWidget(self.fill_opacity_slider)
        
        self.fill_opacity_label = QLabel("100%")
        self.fill_opacity_label.setMinimumWidth(35)
        opacity_layout.addWidget(self.fill_opacity_label)
        
        fill_layout.addLayout(opacity_layout)
        
        self.fill_group.setLayout(fill_layout)
        layout.addWidget(self.fill_group)
        
        # Resim özellikleri grubu (sadece resimler için)
        self.image_group = QGroupBox("Resim Özellikleri")
        image_layout = QVBoxLayout()
        
        # Resim şeffaflığı
        image_opacity_layout = QHBoxLayout()
        image_opacity_layout.addWidget(QLabel("Şeffaflık:"))
        
        self.image_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.image_opacity_slider.setRange(0, 100)  # 0-100 aralığı
        self.image_opacity_slider.setValue(int(self.current_image_opacity * 100))
        self.image_opacity_slider.valueChanged.connect(self.on_image_opacity_changed)
        image_opacity_layout.addWidget(self.image_opacity_slider)
        
        self.image_opacity_label = QLabel("100%")
        self.image_opacity_label.setMinimumWidth(35)
        image_opacity_layout.addWidget(self.image_opacity_label)
        
        image_layout.addLayout(image_opacity_layout)
        
        # Kenarlık özellikleri
        self.border_checkbox = QCheckBox("Kenarlık")
        self.border_checkbox.setChecked(self.current_border_enabled)
        self.border_checkbox.toggled.connect(self.on_border_enabled_changed)
        image_layout.addWidget(self.border_checkbox)
        
        # Kenarlık rengi
        border_color_layout = QHBoxLayout()
        border_color_layout.addWidget(QLabel("Kenarlık Rengi:"))
        
        self.border_color_button = QPushButton()
        self.border_color_button.setFixedSize(40, 25)
        self.border_color_button.clicked.connect(self.choose_border_color)
        self.update_border_color_button()
        border_color_layout.addWidget(self.border_color_button)
        border_color_layout.addStretch()
        
        image_layout.addLayout(border_color_layout)
        
        # Kenarlık kalınlığı
        border_width_layout = QHBoxLayout()
        border_width_layout.addWidget(QLabel("Kenarlık Kalınlığı:"))
        
        self.border_width_spinbox = QSpinBox()
        self.border_width_spinbox.setRange(1, 20)
        self.border_width_spinbox.setValue(self.current_border_width)
        self.border_width_spinbox.setSuffix(" px")
        self.border_width_spinbox.valueChanged.connect(self.on_border_width_changed)
        border_width_layout.addWidget(self.border_width_spinbox)
        border_width_layout.addStretch()
        
        image_layout.addLayout(border_width_layout)
        
        # Kenarlık stili
        border_style_layout = QHBoxLayout()
        border_style_layout.addWidget(QLabel("Kenarlık Stili:"))
        
        self.border_style_combo = QComboBox()
        for style, name in self.LINE_STYLES.items():
            self.border_style_combo.addItem(name, style)
        self.border_style_combo.currentIndexChanged.connect(self.on_border_style_changed)
        border_style_layout.addWidget(self.border_style_combo)
        border_style_layout.addStretch()
        
        image_layout.addLayout(border_style_layout)
        
        # Gölge özellikleri
        self.shadow_checkbox = QCheckBox("Gölge Kullan")
        self.shadow_checkbox.setChecked(self.current_shadow_enabled)
        self.shadow_checkbox.toggled.connect(self.on_shadow_enabled_changed)
        image_layout.addWidget(self.shadow_checkbox)
        
        # Gölge tipi seçimi
        shadow_type_layout = QVBoxLayout()
        shadow_type_layout.setContentsMargins(20, 0, 0, 0)  # Sol taraftan girinti
        
        self.shadow_type_group = QButtonGroup()

        self.outer_shadow_radio = QRadioButton("Dış Gölge")
        self.inner_shadow_radio = QRadioButton("İç Gölge")
        
        self.outer_shadow_radio.setChecked(not self.current_inner_shadow)
        self.inner_shadow_radio.setChecked(self.current_inner_shadow)
        
        self.shadow_type_group.addButton(self.outer_shadow_radio, 0)
        self.shadow_type_group.addButton(self.inner_shadow_radio, 1)
        self.shadow_type_group.buttonClicked.connect(self.on_shadow_type_changed)
        
        shadow_type_layout.addWidget(self.outer_shadow_radio)
        shadow_type_layout.addWidget(self.inner_shadow_radio)
        
        image_layout.addLayout(shadow_type_layout)
        
        # Gölge rengi
        shadow_color_layout = QHBoxLayout()
        shadow_color_layout.addWidget(QLabel("Gölge Rengi:"))
        
        self.shadow_color_button = QPushButton()
        self.shadow_color_button.setFixedSize(40, 25)
        self.shadow_color_button.clicked.connect(self.choose_shadow_color)
        self.update_shadow_color_button()
        shadow_color_layout.addWidget(self.shadow_color_button)
        shadow_color_layout.addStretch()
        
        image_layout.addLayout(shadow_color_layout)
        
        # Gölge offseti
        shadow_offset_layout = QHBoxLayout()
        shadow_offset_layout.addWidget(QLabel("Gölge Offseti:"))
        
        self.shadow_x_spinbox = QSpinBox()
        self.shadow_x_spinbox.setRange(-20, 20)
        self.shadow_x_spinbox.setValue(self.current_shadow_offset_x)
        self.shadow_x_spinbox.setSuffix(" px")
        self.shadow_x_spinbox.valueChanged.connect(self.on_shadow_offset_changed)
        shadow_offset_layout.addWidget(self.shadow_x_spinbox)
        
        self.shadow_y_spinbox = QSpinBox()
        self.shadow_y_spinbox.setRange(-20, 20)
        self.shadow_y_spinbox.setValue(self.current_shadow_offset_y)
        self.shadow_y_spinbox.setSuffix(" px")
        self.shadow_y_spinbox.valueChanged.connect(self.on_shadow_offset_changed)
        shadow_offset_layout.addWidget(self.shadow_y_spinbox)
        shadow_offset_layout.addStretch()
        
        image_layout.addLayout(shadow_offset_layout)
        
        # Gölge bulanıklığı
        shadow_blur_layout = QHBoxLayout()
        shadow_blur_layout.addWidget(QLabel("Gölge Bulanıklığı:"))
        
        self.shadow_blur_spinbox = QSpinBox()
        self.shadow_blur_spinbox.setRange(0, 20)
        self.shadow_blur_spinbox.setValue(self.current_shadow_blur)
        self.shadow_blur_spinbox.setSuffix(" px")
        self.shadow_blur_spinbox.valueChanged.connect(self.on_shadow_blur_changed)
        shadow_blur_layout.addWidget(self.shadow_blur_spinbox)
        shadow_blur_layout.addStretch()
        
        image_layout.addLayout(shadow_blur_layout)
        
        # Gölge boyutu
        shadow_size_layout = QHBoxLayout()
        shadow_size_layout.addWidget(QLabel("Gölge Boyutu:"))
        
        self.shadow_size_spinbox = QSpinBox()
        self.shadow_size_spinbox.setRange(0, 50)
        self.shadow_size_spinbox.setValue(self.current_shadow_size)
        self.shadow_size_spinbox.setSuffix(" px")
        self.shadow_size_spinbox.valueChanged.connect(self.on_shadow_size_changed)
        shadow_size_layout.addWidget(self.shadow_size_spinbox)
        shadow_size_layout.addStretch()
        
        image_layout.addLayout(shadow_size_layout)
        
        # Gölge kalitesi
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Gölge Kalitesi:"))
        
        self.quality_combo = QComboBox()
        self.quality_combo.addItem("Düşük", "low")
        self.quality_combo.addItem("Orta", "medium") 
        self.quality_combo.addItem("Yüksek", "high")
        
        for i in range(self.quality_combo.count()):
            if self.quality_combo.itemData(i) == self.current_shadow_quality:
                self.quality_combo.setCurrentIndex(i)
                break
                
        self.quality_combo.currentIndexChanged.connect(self.on_quality_changed)
        quality_layout.addWidget(self.quality_combo)
        quality_layout.addStretch()
        
        image_layout.addLayout(quality_layout)
        
        # Gölge şeffaflığı
        shadow_opacity_layout = QHBoxLayout()
        shadow_opacity_layout.addWidget(QLabel("Gölge Şeffaflığı:"))
        
        self.shadow_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.shadow_opacity_slider.setRange(0, 100)  # 0-100 aralığı
        self.shadow_opacity_slider.setValue(int(self.current_shadow_opacity * 100))
        self.shadow_opacity_slider.valueChanged.connect(self.on_shadow_opacity_changed)
        shadow_opacity_layout.addWidget(self.shadow_opacity_slider)
        
        self.shadow_opacity_label = QLabel("100%")
        self.shadow_opacity_label.setMinimumWidth(35)
        shadow_opacity_layout.addWidget(self.shadow_opacity_label)
        
        image_layout.addLayout(shadow_opacity_layout)
        
        # Filtre özellikleri
        filter_label = QLabel("Filtre:")
        filter_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        image_layout.addWidget(filter_label)
        
        # Filtre tipi
        filter_type_layout = QHBoxLayout()
        filter_type_layout.addWidget(QLabel("Filtre Tipi:"))
        
        self.filter_type_combo = QComboBox()
        self.filter_type_combo.addItem("Yok", "none")
        self.filter_type_combo.addItem("Gri Tonlama", "grayscale")
        self.filter_type_combo.addItem("Sepia", "sepia")
        self.filter_type_combo.addItem("Renk Tersçevirme", "invert")
        self.filter_type_combo.currentIndexChanged.connect(self.on_filter_type_changed)
        filter_type_layout.addWidget(self.filter_type_combo)
        filter_type_layout.addStretch()
        
        image_layout.addLayout(filter_type_layout)
        
        # Filtre yoğunluğu
        filter_intensity_layout = QHBoxLayout()
        filter_intensity_layout.addWidget(QLabel("Filtre Yoğunluğu:"))
        
        self.filter_intensity_slider = QSlider(Qt.Orientation.Horizontal)
        self.filter_intensity_slider.setRange(0, 100)  # 0-100 aralığı
        self.filter_intensity_slider.setValue(int(self.current_filter_intensity * 100))
        self.filter_intensity_slider.valueChanged.connect(self.on_filter_intensity_changed)
        filter_intensity_layout.addWidget(self.filter_intensity_slider)
        
        self.filter_intensity_label = QLabel("100%")
        self.filter_intensity_label.setMinimumWidth(35)
        filter_intensity_layout.addWidget(self.filter_intensity_label)
        
        image_layout.addLayout(filter_intensity_layout)
        
        # Ekstra şeffaflık
        transparency_layout = QHBoxLayout()
        transparency_layout.addWidget(QLabel("Ekstra Şeffaflık:"))
        
        self.transparency_slider = QSlider(Qt.Orientation.Horizontal)
        self.transparency_slider.setRange(0, 100)  # 0-100 aralığı
        self.transparency_slider.setValue(int(self.current_transparency * 100))
        self.transparency_slider.valueChanged.connect(self.on_transparency_changed)
        transparency_layout.addWidget(self.transparency_slider)
        
        self.transparency_label = QLabel("100%")
        self.transparency_label.setMinimumWidth(35)
        transparency_layout.addWidget(self.transparency_label)
        
        image_layout.addLayout(transparency_layout)
        
        # Bulanıklık
        blur_layout = QHBoxLayout()
        blur_layout.addWidget(QLabel("Bulanıklık:"))
        
        self.blur_spinbox = QSpinBox()
        self.blur_spinbox.setRange(0, 20)
        self.blur_spinbox.setValue(self.current_blur_radius)
        self.blur_spinbox.setSuffix(" px")
        self.blur_spinbox.valueChanged.connect(self.on_blur_changed)
        blur_layout.addWidget(self.blur_spinbox)
        blur_layout.addStretch()
        
        image_layout.addLayout(blur_layout)
        
        # Kenar yuvarlama
        corner_layout = QHBoxLayout()
        corner_layout.addWidget(QLabel("Kenar Yuvarlama:"))
        
        self.corner_radius_spinbox = QSpinBox()
        self.corner_radius_spinbox.setRange(0, 50)
        self.corner_radius_spinbox.setValue(self.current_corner_radius)
        self.corner_radius_spinbox.setSuffix(" px")
        self.corner_radius_spinbox.valueChanged.connect(self.on_corner_radius_changed)
        corner_layout.addWidget(self.corner_radius_spinbox)
        corner_layout.addStretch()
        
        image_layout.addLayout(corner_layout)
        
        self.image_group.setLayout(image_layout)
        layout.addWidget(self.image_group)
        # Test için başlangıçta görünür yapalım
        self.image_group.setVisible(False)
        
        # Dikdörtgen özellikleri grubu (sadece dikdörtgen için)
        self.rectangle_group = QGroupBox("Dikdörtgen Özellikleri")
        rect_layout = QVBoxLayout()
        
        # Yuvarlak kenar
        rect_corner_layout = QHBoxLayout()
        rect_corner_layout.addWidget(QLabel("Kenar Yuvarlaklığı:"))
        
        self.rect_corner_radius_spinbox = QSpinBox()
        self.rect_corner_radius_spinbox.setRange(0, 50)
        self.rect_corner_radius_spinbox.setValue(self.current_rect_corner_radius)
        self.rect_corner_radius_spinbox.setSuffix(" px")
        self.rect_corner_radius_spinbox.valueChanged.connect(self.on_rect_corner_radius_changed)
        rect_corner_layout.addWidget(self.rect_corner_radius_spinbox)
        rect_corner_layout.addStretch()
        
        rect_layout.addLayout(rect_corner_layout)
        
        # Gölge etkin/pasif
        self.rect_shadow_checkbox = QCheckBox("Gölge Kullan")
        self.rect_shadow_checkbox.setChecked(self.current_rect_shadow_enabled)
        self.rect_shadow_checkbox.toggled.connect(self.on_rect_shadow_enabled_changed)
        rect_layout.addWidget(self.rect_shadow_checkbox)
        
        # Gölge türü (dış/iç)
        rect_shadow_type_layout = QHBoxLayout()
        self.rect_shadow_outer_radio = QRadioButton("Dış Gölge")
        self.rect_shadow_inner_radio = QRadioButton("İç Gölge")
        self.rect_shadow_outer_radio.setChecked(not self.current_rect_inner_shadow)
        self.rect_shadow_inner_radio.setChecked(self.current_rect_inner_shadow)
        
        self.rect_shadow_type_group = QButtonGroup()
        self.rect_shadow_type_group.addButton(self.rect_shadow_outer_radio)
        self.rect_shadow_type_group.addButton(self.rect_shadow_inner_radio)
        self.rect_shadow_type_group.buttonClicked.connect(self.on_rect_shadow_type_changed)
        
        rect_shadow_type_layout.addWidget(self.rect_shadow_outer_radio)
        rect_shadow_type_layout.addWidget(self.rect_shadow_inner_radio)
        rect_layout.addLayout(rect_shadow_type_layout)
        
        # Gölge rengi
        rect_shadow_color_layout = QHBoxLayout()
        rect_shadow_color_layout.addWidget(QLabel("Gölge Rengi:"))
        
        self.rect_shadow_color_button = QPushButton()
        self.rect_shadow_color_button.setFixedSize(40, 25)
        self.rect_shadow_color_button.clicked.connect(self.choose_rect_shadow_color)
        self.update_rect_shadow_color_button()
        rect_shadow_color_layout.addWidget(self.rect_shadow_color_button)
        rect_shadow_color_layout.addStretch()
        
        rect_layout.addLayout(rect_shadow_color_layout)
        
        # Gölge X offseti
        rect_shadow_x_layout = QHBoxLayout()
        rect_shadow_x_layout.addWidget(QLabel("Gölge X:"))
        
        self.rect_shadow_x_spinbox = QSpinBox()
        self.rect_shadow_x_spinbox.setRange(-20, 20)
        self.rect_shadow_x_spinbox.setValue(self.current_rect_shadow_offset_x)
        self.rect_shadow_x_spinbox.setSuffix(" px")
        self.rect_shadow_x_spinbox.valueChanged.connect(self.on_rect_shadow_offset_changed)
        rect_shadow_x_layout.addWidget(self.rect_shadow_x_spinbox)
        rect_shadow_x_layout.addStretch()
        
        rect_layout.addLayout(rect_shadow_x_layout)
        
        # Gölge Y offseti
        rect_shadow_y_layout = QHBoxLayout()
        rect_shadow_y_layout.addWidget(QLabel("Gölge Y:"))
        
        self.rect_shadow_y_spinbox = QSpinBox()
        self.rect_shadow_y_spinbox.setRange(-20, 20)
        self.rect_shadow_y_spinbox.setValue(self.current_rect_shadow_offset_y)
        self.rect_shadow_y_spinbox.setSuffix(" px")
        self.rect_shadow_y_spinbox.valueChanged.connect(self.on_rect_shadow_offset_changed)
        rect_shadow_y_layout.addWidget(self.rect_shadow_y_spinbox)
        rect_shadow_y_layout.addStretch()
        
        rect_layout.addLayout(rect_shadow_y_layout)
        
        # Gölge bulanıklık
        rect_blur_layout = QHBoxLayout()
        rect_blur_layout.addWidget(QLabel("Gölge Bulanıklık:"))
        
        self.rect_shadow_blur_spinbox = QSpinBox()
        self.rect_shadow_blur_spinbox.setRange(0, 20)
        self.rect_shadow_blur_spinbox.setValue(self.current_rect_shadow_blur)
        self.rect_shadow_blur_spinbox.setSuffix(" px")
        self.rect_shadow_blur_spinbox.valueChanged.connect(self.on_rect_shadow_blur_changed)
        rect_blur_layout.addWidget(self.rect_shadow_blur_spinbox)
        rect_blur_layout.addStretch()
        
        rect_layout.addLayout(rect_blur_layout)
        
        # Gölge boyutu
        rect_size_layout = QHBoxLayout()
        rect_size_layout.addWidget(QLabel("Gölge Boyutu:"))
        
        self.rect_shadow_size_spinbox = QSpinBox()
        self.rect_shadow_size_spinbox.setRange(0, 50)
        self.rect_shadow_size_spinbox.setValue(self.current_rect_shadow_size)
        self.rect_shadow_size_spinbox.setSuffix(" px")
        self.rect_shadow_size_spinbox.valueChanged.connect(self.on_rect_shadow_size_changed)
        rect_size_layout.addWidget(self.rect_shadow_size_spinbox)
        rect_size_layout.addStretch()
        
        rect_layout.addLayout(rect_size_layout)
        
        # Gölge şeffaflık
        rect_opacity_layout = QHBoxLayout()
        rect_opacity_layout.addWidget(QLabel("Gölge Şeffaflık:"))
        
        self.rect_shadow_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.rect_shadow_opacity_slider.setRange(0, 100)
        self.rect_shadow_opacity_slider.setValue(int(self.current_rect_shadow_opacity * 100))
        self.rect_shadow_opacity_slider.valueChanged.connect(self.on_rect_shadow_opacity_changed)
        rect_opacity_layout.addWidget(self.rect_shadow_opacity_slider)
        
        self.rect_shadow_opacity_label = QLabel(f"{int(self.current_rect_shadow_opacity * 100)}%")
        self.rect_shadow_opacity_label.setMinimumWidth(35)
        rect_opacity_layout.addWidget(self.rect_shadow_opacity_label)
        
        rect_layout.addLayout(rect_opacity_layout)
        
        # Gölge kalitesi
        rect_quality_layout = QHBoxLayout()
        rect_quality_layout.addWidget(QLabel("Gölge Kalitesi:"))
        
        self.rect_shadow_quality_combo = QComboBox()
        self.rect_shadow_quality_combo.addItems(["low", "medium", "high"])
        self.rect_shadow_quality_combo.setCurrentText(self.current_rect_shadow_quality)
        self.rect_shadow_quality_combo.currentTextChanged.connect(self.on_rect_quality_changed)
        rect_quality_layout.addWidget(self.rect_shadow_quality_combo)
        rect_quality_layout.addStretch()
        
        rect_layout.addLayout(rect_quality_layout)
        
        self.rectangle_group.setLayout(rect_layout)
        layout.addWidget(self.rectangle_group)
        self.rectangle_group.setVisible(False)  # Başlangıçta gizli
        
        # Çember özellikleri grubu (sadece çember için)
        self.circle_group = QGroupBox("Çember Özellikleri")
        circle_layout = QVBoxLayout()
        
        # Gölge etkin/pasif
        self.circle_shadow_checkbox = QCheckBox("Gölge")
        self.circle_shadow_checkbox.setChecked(self.current_circle_shadow_enabled)
        self.circle_shadow_checkbox.toggled.connect(self.on_circle_shadow_enabled_changed)
        circle_layout.addWidget(self.circle_shadow_checkbox)
        
        # Gölge tipi (iç/dış)
        circle_shadow_type_layout = QHBoxLayout()
        circle_shadow_type_layout.addWidget(QLabel("Gölge Tipi:"))
        
        from PyQt6.QtWidgets import QButtonGroup
        self.circle_shadow_type_group = QButtonGroup()
        
        self.circle_outer_shadow_radio = QRadioButton("Dış Gölge")
        self.circle_outer_shadow_radio.setChecked(not self.current_circle_inner_shadow)
        self.circle_shadow_type_group.addButton(self.circle_outer_shadow_radio)
        circle_shadow_type_layout.addWidget(self.circle_outer_shadow_radio)
        
        self.circle_inner_shadow_radio = QRadioButton("İç Gölge")
        self.circle_inner_shadow_radio.setChecked(self.current_circle_inner_shadow)
        self.circle_shadow_type_group.addButton(self.circle_inner_shadow_radio)
        circle_shadow_type_layout.addWidget(self.circle_inner_shadow_radio)
        
        self.circle_shadow_type_group.buttonClicked.connect(self.on_circle_shadow_type_changed)
        circle_layout.addLayout(circle_shadow_type_layout)
        
        # Gölge rengi
        circle_shadow_color_layout = QHBoxLayout()
        circle_shadow_color_layout.addWidget(QLabel("Gölge Rengi:"))
        
        self.circle_shadow_color_button = QPushButton()
        self.circle_shadow_color_button.setFixedSize(40, 25)
        self.circle_shadow_color_button.clicked.connect(self.choose_circle_shadow_color)
        self.update_circle_shadow_color_button()
        circle_shadow_color_layout.addWidget(self.circle_shadow_color_button)
        circle_shadow_color_layout.addStretch()
        
        circle_layout.addLayout(circle_shadow_color_layout)
        
        # Gölge offset
        circle_offset_layout = QHBoxLayout()
        circle_offset_layout.addWidget(QLabel("Gölge Offset:"))
        
        circle_offset_layout.addWidget(QLabel("X:"))
        self.circle_shadow_x_spinbox = QSpinBox()
        self.circle_shadow_x_spinbox.setRange(-20, 20)
        self.circle_shadow_x_spinbox.setValue(self.current_circle_shadow_offset_x)
        self.circle_shadow_x_spinbox.setSuffix(" px")
        self.circle_shadow_x_spinbox.valueChanged.connect(self.on_circle_shadow_offset_changed)
        circle_offset_layout.addWidget(self.circle_shadow_x_spinbox)
        
        circle_offset_layout.addWidget(QLabel("Y:"))
        self.circle_shadow_y_spinbox = QSpinBox()
        self.circle_shadow_y_spinbox.setRange(-20, 20)
        self.circle_shadow_y_spinbox.setValue(self.current_circle_shadow_offset_y)
        self.circle_shadow_y_spinbox.setSuffix(" px")
        self.circle_shadow_y_spinbox.valueChanged.connect(self.on_circle_shadow_offset_changed)
        circle_offset_layout.addWidget(self.circle_shadow_y_spinbox)
        circle_offset_layout.addStretch()
        
        circle_layout.addLayout(circle_offset_layout)
        
        # Gölge bulanıklığı
        circle_blur_layout = QHBoxLayout()
        circle_blur_layout.addWidget(QLabel("Gölge Bulanıklık:"))
        
        self.circle_shadow_blur_spinbox = QSpinBox()
        self.circle_shadow_blur_spinbox.setRange(0, 20)
        self.circle_shadow_blur_spinbox.setValue(self.current_circle_shadow_blur)
        self.circle_shadow_blur_spinbox.setSuffix(" px")
        self.circle_shadow_blur_spinbox.valueChanged.connect(self.on_circle_shadow_blur_changed)
        circle_blur_layout.addWidget(self.circle_shadow_blur_spinbox)
        circle_blur_layout.addStretch()
        
        circle_layout.addLayout(circle_blur_layout)
        
        # Gölge boyutu
        circle_size_layout = QHBoxLayout()
        circle_size_layout.addWidget(QLabel("Gölge Boyutu:"))
        
        self.circle_shadow_size_spinbox = QSpinBox()
        self.circle_shadow_size_spinbox.setRange(0, 50)
        self.circle_shadow_size_spinbox.setValue(self.current_circle_shadow_size)
        self.circle_shadow_size_spinbox.setSuffix(" px")
        self.circle_shadow_size_spinbox.valueChanged.connect(self.on_circle_shadow_size_changed)
        circle_size_layout.addWidget(self.circle_shadow_size_spinbox)
        circle_size_layout.addStretch()
        
        circle_layout.addLayout(circle_size_layout)
        
        # Gölge şeffaflık
        circle_opacity_layout = QHBoxLayout()
        circle_opacity_layout.addWidget(QLabel("Gölge Şeffaflık:"))
        
        self.circle_shadow_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.circle_shadow_opacity_slider.setRange(0, 100)
        self.circle_shadow_opacity_slider.setValue(int(self.current_circle_shadow_opacity * 100))
        self.circle_shadow_opacity_slider.valueChanged.connect(self.on_circle_shadow_opacity_changed)
        circle_opacity_layout.addWidget(self.circle_shadow_opacity_slider)
        
        self.circle_shadow_opacity_label = QLabel(f"{int(self.current_circle_shadow_opacity * 100)}%")
        self.circle_shadow_opacity_label.setMinimumWidth(35)
        circle_opacity_layout.addWidget(self.circle_shadow_opacity_label)
        
        circle_layout.addLayout(circle_opacity_layout)
        
        # Gölge kalitesi
        circle_quality_layout = QHBoxLayout()
        circle_quality_layout.addWidget(QLabel("Gölge Kalitesi:"))
        
        self.circle_shadow_quality_combo = QComboBox()
        self.circle_shadow_quality_combo.addItems(["low", "medium", "high"])
        self.circle_shadow_quality_combo.setCurrentText(self.current_circle_shadow_quality)
        self.circle_shadow_quality_combo.currentTextChanged.connect(self.on_circle_quality_changed)
        circle_quality_layout.addWidget(self.circle_shadow_quality_combo)
        circle_quality_layout.addStretch()
        
        circle_layout.addLayout(circle_quality_layout)
        
        self.circle_group.setLayout(circle_layout)
        layout.addWidget(self.circle_group)
        self.circle_group.setVisible(False)  # Başlangıçta gizli
        
        # Grup işlemleri grubu (çoklu seçim için)
        self.group_operations_group = QGroupBox("Grup İşlemleri")
        group_ops_layout = QVBoxLayout()
        
        group_buttons_layout = QHBoxLayout()
        
        self.group_button = QPushButton("Grupla")
        self.group_button.clicked.connect(self.on_group_shapes)
        group_buttons_layout.addWidget(self.group_button)
        
        self.ungroup_button = QPushButton("Grup Çöz")
        self.ungroup_button.clicked.connect(self.on_ungroup_shapes)
        group_buttons_layout.addWidget(self.ungroup_button)
        
        group_ops_layout.addLayout(group_buttons_layout)
        self.group_operations_group.setLayout(group_ops_layout)
        layout.addWidget(self.group_operations_group)
        
        # Hizalama araçları grubu (çoklu seçim için)
        self.alignment_group = QGroupBox("Hizalama")
        alignment_layout = QVBoxLayout()
        
        # İlk satır - yatay hizalama
        h_align_layout = QHBoxLayout()
        
        self.align_left_btn = QPushButton("◀")
        self.align_left_btn.setToolTip("Sola Hizala")
        self.align_left_btn.setFixedSize(30, 30)
        self.align_left_btn.clicked.connect(self.on_align_left)
        h_align_layout.addWidget(self.align_left_btn)
        
        self.align_center_h_btn = QPushButton("▬")
        self.align_center_h_btn.setToolTip("Yatay Ortala")
        self.align_center_h_btn.setFixedSize(30, 30)
        self.align_center_h_btn.clicked.connect(self.on_align_center_h)
        h_align_layout.addWidget(self.align_center_h_btn)
        
        self.align_right_btn = QPushButton("▶")
        self.align_right_btn.setToolTip("Sağa Hizala")
        self.align_right_btn.setFixedSize(30, 30)
        self.align_right_btn.clicked.connect(self.on_align_right)
        h_align_layout.addWidget(self.align_right_btn)
        
        self.distribute_h_btn = QPushButton("↔")
        self.distribute_h_btn.setToolTip("Yatay Dağıt")
        self.distribute_h_btn.setFixedSize(30, 30)
        self.distribute_h_btn.clicked.connect(self.on_distribute_h)
        h_align_layout.addWidget(self.distribute_h_btn)
        
        alignment_layout.addLayout(h_align_layout)
        
        # İkinci satır - dikey hizalama
        v_align_layout = QHBoxLayout()
        
        self.align_top_btn = QPushButton("▲")
        self.align_top_btn.setToolTip("Yukarı Hizala")
        self.align_top_btn.setFixedSize(30, 30)
        self.align_top_btn.clicked.connect(self.on_align_top)
        v_align_layout.addWidget(self.align_top_btn)
        
        self.align_center_v_btn = QPushButton("▬")
        self.align_center_v_btn.setToolTip("Dikey Ortala")
        self.align_center_v_btn.setFixedSize(30, 30)
        self.align_center_v_btn.clicked.connect(self.on_align_center_v)
        v_align_layout.addWidget(self.align_center_v_btn)
        
        self.align_bottom_btn = QPushButton("▼")
        self.align_bottom_btn.setToolTip("Aşağı Hizala")
        self.align_bottom_btn.setFixedSize(30, 30)
        self.align_bottom_btn.clicked.connect(self.on_align_bottom)
        v_align_layout.addWidget(self.align_bottom_btn)
        
        self.distribute_v_btn = QPushButton("↕")
        self.distribute_v_btn.setToolTip("Dikey Dağıt")
        self.distribute_v_btn.setFixedSize(30, 30)
        self.distribute_v_btn.clicked.connect(self.on_distribute_v)
        v_align_layout.addWidget(self.distribute_v_btn)
        
        alignment_layout.addLayout(v_align_layout)
        self.alignment_group.setLayout(alignment_layout)
        layout.addWidget(self.alignment_group)
        
        # Şekil havuzu grubu (çoklu seçim için)
        self.shape_library_group = QGroupBox("Şekil Havuzu")
        library_layout = QVBoxLayout()
        
        self.add_to_library_button = QPushButton("Şekil Havuzuna Ekle")
        self.add_to_library_button.clicked.connect(self.on_add_to_shape_library)
        library_layout.addWidget(self.add_to_library_button)
        
        self.shape_library_group.setLayout(library_layout)
        layout.addWidget(self.shape_library_group)
        
        # Boşluk ekle
        layout.addStretch()
        
        # Scroll widget'ı ayarla
        scroll_widget.setLayout(layout)
        scroll_area.setWidget(scroll_widget)
        
        # Ana layout'a scroll area'yı ekle
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)
        
        # Başlangıçta UI'ı güncelle
        self.update_ui_values()
        self.update_button_states()
        
    def update_color_button(self):
        """Renk butonunu güncelle"""
        color_str = f"background-color: {self.current_color.name()}; border: 1px solid #000;"
        self.color_button.setStyleSheet(color_str)
        self.color_button.setText("")
        
    def update_fill_color_button(self):
        """Dolgu rengi butonunu güncelle"""
        color_str = f"background-color: {self.current_fill_color.name()}; border: 1px solid #000;"
        self.fill_color_button.setStyleSheet(color_str)
        self.fill_color_button.setText("")
        
    def update_border_color_button(self):
        """Kenarlık rengi butonunu güncelle"""
        color_str = f"background-color: {self.current_border_color.name()}; border: 1px solid #000;"
        self.border_color_button.setStyleSheet(color_str)
        self.border_color_button.setText("")
        
    def update_shadow_color_button(self):
        """Gölge rengi butonunu güncelle"""
        color_str = f"background-color: {self.current_shadow_color.name()}; border: 1px solid #000;"
        self.shadow_color_button.setStyleSheet(color_str)
        self.shadow_color_button.setText("")
        
    def update_rect_shadow_color_button(self):
        """Dikdörtgen gölge rengi butonunu güncelle"""
        color_str = f"background-color: {self.current_rect_shadow_color.name()}; border: 1px solid #000;"
        self.rect_shadow_color_button.setStyleSheet(color_str)
        self.rect_shadow_color_button.setText("")
        
    def update_circle_shadow_color_button(self):
        """Çember gölge rengi butonunu güncelle"""
        color_str = f"background-color: {self.current_circle_shadow_color.name()}; border: 1px solid #000;"
        self.circle_shadow_color_button.setStyleSheet(color_str)
        self.circle_shadow_color_button.setText("")

    def update_stroke_shadow_color_button(self):
        """Çizgi gölge rengi butonunu güncelle"""
        color_str = f"background-color: {self.current_stroke_shadow_color.name()}; border: 1px solid #000;"
        self.stroke_shadow_color_button.setStyleSheet(color_str)
        self.stroke_shadow_color_button.setText("")
        
    def choose_color(self):
        """Çizgi rengi seç"""
        color = QColorDialog.getColor(self.current_color, self, "Çizgi Rengi Seç")
        if color.isValid():
            self.current_color = color
            self.update_color_button()
            # Anlık uygula
            self.apply_color_change()
            
    def choose_fill_color(self):
        """Dolgu rengi seç"""
        color = QColorDialog.getColor(self.current_fill_color, self, "Dolgu Rengi Seç")
        if color.isValid():
            self.current_fill_color = color
            self.update_fill_color_button()
            # Anlık uygula
            self.apply_fill_color_change()
            
    def choose_border_color(self):
        """Kenarlık rengi seç"""
        color = QColorDialog.getColor(self.current_border_color, self, "Kenarlık Rengi Seç")
        if color.isValid():
            self.current_border_color = color
            self.update_border_color_button()
            # Anlık uygula
            self.apply_border_color_change()
            
    def choose_shadow_color(self):
        """Gölge rengi seç"""
        color = QColorDialog.getColor(self.current_shadow_color, self, "Gölge Rengi Seç")
        if color.isValid():
            self.current_shadow_color = color
            self.update_shadow_color_button()
            # Anlık uygula
            self.apply_shadow_color_change()
            
    def choose_rect_shadow_color(self):
        """Dikdörtgen gölge rengi seç"""
        color = QColorDialog.getColor(self.current_rect_shadow_color, self, "Dikdörtgen Gölge Rengi Seç")
        if color.isValid():
            self.current_rect_shadow_color = color
            self.update_rect_shadow_color_button()
            # Anlık uygula
            self.apply_rect_shadow_color_change()
            
    def choose_circle_shadow_color(self):
        """Çember gölge rengi seç"""
        color = QColorDialog.getColor(self.current_circle_shadow_color, self, "Çember Gölge Rengi Seç")
        if color.isValid():
            self.current_circle_shadow_color = color
            self.update_circle_shadow_color_button()
            # Anlık uygula
            self.apply_circle_shadow_color_change()

    def choose_stroke_shadow_color(self):
        """Çizgi gölge rengi seç"""
        color = QColorDialog.getColor(self.current_stroke_shadow_color, self, "Çizgi Gölge Rengi Seç")
        if color.isValid():
            self.current_stroke_shadow_color = color
            self.update_stroke_shadow_color_button()
            self.apply_stroke_shadow_color_change()
            
    def on_width_changed(self, value):
        """Kalınlık değişti"""
        self.current_width = value
        # Anlık uygula
        self.apply_width_change()
        
    def on_style_changed(self, index):
        """Çizgi stili değişti"""
        self.current_line_style = self.style_combo.itemData(index)
        # Anlık uygula
        self.apply_style_change()
        
    def on_fill_enabled_changed(self, enabled):
        """Dolgu etkin/pasif değişti"""
        self.current_fill_enabled = enabled
        self.fill_color_button.setEnabled(enabled)
        self.fill_opacity_slider.setEnabled(enabled)
        self.fill_opacity_label.setEnabled(enabled)
        # Anlık uygula
        self.apply_fill_enabled_change()
        
    def on_fill_opacity_changed(self, value):
        """Dolgu şeffaflığı değişti"""
        self.current_fill_opacity = value / 100.0  # 0-1 aralığına çevir
        self.fill_opacity_label.setText(f"{value}%")
        # Anlık uygula
        self.apply_fill_opacity_change()
        
    def on_image_opacity_changed(self, value):
        """Resim şeffaflığı değişti"""
        self.current_image_opacity = value / 100.0  # 0-1 aralığına çevir
        self.image_opacity_label.setText(f"{value}%")
        # Anlık uygula
        self.apply_image_opacity_change()
        
    def on_border_enabled_changed(self, enabled):
        """Kenarlık etkin/pasif değişti"""
        self.current_border_enabled = enabled
        self.border_color_button.setEnabled(enabled)
        self.border_width_spinbox.setEnabled(enabled)
        self.border_style_combo.setEnabled(enabled)
        # Anlık uygula
        self.apply_border_enabled_change()
        
    def on_border_width_changed(self, value):
        """Kenarlık kalınlığı değişti"""
        self.current_border_width = value
        # Anlık uygula
        self.apply_border_width_change()
        
    def on_border_style_changed(self, index):
        """Kenarlık stili değişti"""
        self.current_border_style = self.border_style_combo.itemData(index)
        # Anlık uygula
        self.apply_border_style_change()
        
    def on_shadow_enabled_changed(self, enabled):
        """Gölge etkin/pasif değişti"""
        self.current_shadow_enabled = enabled
        self.shadow_color_button.setEnabled(enabled)
        self.shadow_x_spinbox.setEnabled(enabled)
        self.shadow_y_spinbox.setEnabled(enabled)
        if hasattr(self, 'shadow_blur_spinbox'):
            self.shadow_blur_spinbox.setEnabled(enabled)
        if hasattr(self, 'shadow_size_spinbox'):
            self.shadow_size_spinbox.setEnabled(enabled)
        if hasattr(self, 'outer_shadow_radio'):
            self.outer_shadow_radio.setEnabled(enabled)
        if hasattr(self, 'inner_shadow_radio'):
            self.inner_shadow_radio.setEnabled(enabled)
        if hasattr(self, 'quality_combo'):
            self.quality_combo.setEnabled(enabled)
        # Anlık uygula
        self.apply_shadow_enabled_change()
        
    def on_shadow_offset_changed(self):
        """Gölge offseti değişti"""
        self.current_shadow_offset_x = self.shadow_x_spinbox.value()
        self.current_shadow_offset_y = self.shadow_y_spinbox.value()
        # Anlık uygula
        self.apply_shadow_offset_change()
        
    def on_shadow_blur_changed(self, value):
        """Gölge bulanıklığı değişti"""
        self.current_shadow_blur = value
        # Anlık uygula
        self.apply_shadow_blur_change()
        
    def on_shadow_size_changed(self, value):
        """Gölge boyutu değişti"""
        self.current_shadow_size = value
        # Anlık uygula
        self.apply_shadow_size_change()
        
    def on_shadow_type_changed(self, button):
        """Gölge tipi değişti (dış/iç)"""
        self.current_inner_shadow = (button == self.inner_shadow_radio)
        # Anlık uygula
        self.apply_inner_shadow_change()
        
    def on_quality_changed(self, index):
        """Gölge kalitesi değişti"""
        self.current_shadow_quality = self.quality_combo.itemData(index)
        # Anlık uygula
        self.apply_quality_change()
        
    def on_filter_type_changed(self, index):
        """Filtre tipi değişti"""
        self.current_filter_type = self.filter_type_combo.itemData(index)
        # Anlık uygula
        self.apply_filter_change()
        
    def on_filter_intensity_changed(self, value):
        """Filtre yoğunluğu değişti"""
        self.current_filter_intensity = value / 100.0
        self.filter_intensity_label.setText(f"{value}%")
        # Anlık uygula
        self.apply_filter_change()
        
    def apply_color_change(self):
        """Renk değişikliğini uygula"""
        if self.selected_strokes:
            self.colorChanged.emit(self.current_color)
    
    def apply_width_change(self):
        """Kalınlık değişikliğini uygula"""
        if self.selected_strokes:
            self.widthChanged.emit(self.current_width)
    
    def apply_style_change(self):
        """Stil değişikliğini uygula"""
        if self.selected_strokes:
            self.lineStyleChanged.emit(self.current_line_style)
    
    def apply_fill_color_change(self):
        """Dolgu rengi değişikliğini uygula"""
        if self.selected_strokes and self.has_fillable_shapes:
            self.fillColorChanged.emit(self.current_fill_color)
    
    def apply_fill_enabled_change(self):
        """Dolgu etkin/pasif değişikliğini uygula"""
        if self.selected_strokes and self.has_fillable_shapes:
            self.fillEnabledChanged.emit(self.current_fill_enabled)
    
    def apply_fill_opacity_change(self):
        """Dolgu şeffaflığı değişikliğini uygula"""
        if self.selected_strokes and self.has_fillable_shapes:
            self.fillOpacityChanged.emit(self.current_fill_opacity)
            
    def apply_image_opacity_change(self):
        """Resim şeffaflığı değişikliğini uygula"""
        if self.selected_strokes and self.has_image_shapes:
            self.imageOpacityChanged.emit(self.current_image_opacity)
            
    def apply_border_enabled_change(self):
        """Kenarlık etkin/pasif değişikliğini uygula"""
        if self.selected_strokes and self.has_image_shapes:
            self.imageBorderEnabledChanged.emit(self.current_border_enabled)
            
    def apply_border_color_change(self):
        """Kenarlık rengi değişikliğini uygula"""
        if self.selected_strokes and self.has_image_shapes:
            self.imageBorderColorChanged.emit(self.current_border_color)
            
    def apply_border_width_change(self):
        """Kenarlık kalınlığı değişikliğini uygula"""
        if self.selected_strokes and self.has_image_shapes:
            self.imageBorderWidthChanged.emit(self.current_border_width)
            
    def apply_border_style_change(self):
        """Kenarlık stili değişikliğini uygula"""
        if self.selected_strokes and self.has_image_shapes:
            self.imageBorderStyleChanged.emit(self.current_border_style)
            
    def apply_shadow_enabled_change(self):
        """Gölge etkin/pasif değişikliğini uygula"""
        if self.selected_strokes and self.has_image_shapes:
            self.imageShadowEnabledChanged.emit(self.current_shadow_enabled)
            
    def apply_shadow_color_change(self):
        """Gölge rengi değişikliğini uygula"""
        if self.selected_strokes and self.has_image_shapes:
            self.imageShadowColorChanged.emit(self.current_shadow_color)
            
    def apply_shadow_offset_change(self):
        """Gölge offseti değişikliğini uygula"""
        if self.selected_strokes and self.has_image_shapes:
            self.imageShadowOffsetChanged.emit(self.current_shadow_offset_x, self.current_shadow_offset_y)
            
    def apply_shadow_blur_change(self):
        """Gölge bulanıklığı değişikliğini uygula"""
        if self.selected_strokes and self.has_image_shapes:
            self.imageShadowBlurChanged.emit(self.current_shadow_blur)
            
    def apply_shadow_size_change(self):
        """Gölge boyutu değişikliğini uygula"""
        if self.selected_strokes and self.has_image_shapes:
            self.imageShadowSizeChanged.emit(self.current_shadow_size)
            
    def apply_inner_shadow_change(self):
        """İç gölge değişikliğini uygula"""
        if self.selected_strokes and self.has_image_shapes:
            self.imageShadowInnerChanged.emit(self.current_inner_shadow)
            
    def apply_quality_change(self):
        """Gölge kalitesi değişikliğini uygula"""
        if self.selected_strokes and self.has_image_shapes:
            self.imageShadowQualityChanged.emit(self.current_shadow_quality)
            
    def apply_filter_change(self):
        """Filtre değişikliğini uygula"""
        if self.selected_strokes and self.has_image_shapes:
            self.imageFilterChanged.emit(self.current_filter_type, self.current_filter_intensity)
    
    def on_transparency_changed(self, value):
        """Ekstra şeffaflık değişti"""
        self.current_transparency = value / 100.0
        self.transparency_label.setText(f"{value}%")
        # Anlık uygula
        self.apply_transparency_change()
        
    def on_blur_changed(self, value):
        """Bulanıklık değişti"""
        self.current_blur_radius = value
        # Anlık uygula
        self.apply_blur_change()
    
    def on_corner_radius_changed(self, value):
        """Kenar yuvarlama değişti"""
        self.current_corner_radius = value
        # Anlık uygula
        self.apply_corner_radius_change()
    
    def on_shadow_opacity_changed(self, value):
        """Gölge şeffaflığı değişti"""
        self.current_shadow_opacity = value / 100.0
        self.shadow_opacity_label.setText(f"{value}%")
        # Anlık uygula
        self.apply_shadow_opacity_change()
        
    def apply_transparency_change(self):
        """Ekstra şeffaflık değişikliğini uygula"""
        if self.selected_strokes and self.has_image_shapes:
            self.imageTransparencyChanged.emit(self.current_transparency)
            
    def apply_blur_change(self):
        """Bulanıklık değişikliğini uygula"""
        if self.selected_strokes and self.has_image_shapes:
            self.imageBlurChanged.emit(self.current_blur_radius)
    
    def apply_corner_radius_change(self):
        """Kenar yuvarlama değişikliğini uygula"""
        if self.selected_strokes and self.has_image_shapes:
            self.imageCornerRadiusChanged.emit(self.current_corner_radius)
    
    def apply_shadow_opacity_change(self):
        """Gölge şeffaflığı değişikliğini uygula"""
        if self.selected_strokes and self.has_image_shapes:
            self.imageShadowOpacityChanged.emit(self.current_shadow_opacity)
    
    # Dikdörtgen özellikleri event handler'ları
    def on_rect_corner_radius_changed(self, value):
        """Dikdörtgen kenar yuvarlama değişti"""
        self.current_rect_corner_radius = value
        # Anlık uygula
        self.apply_rect_corner_radius_change()
    
    def on_rect_shadow_enabled_changed(self, enabled):
        """Dikdörtgen gölge etkin/pasif değişti"""
        self.current_rect_shadow_enabled = enabled
        # Anlık uygula
        self.apply_rect_shadow_enabled_change()
    
    def on_rect_shadow_offset_changed(self):
        """Dikdörtgen gölge offseti değişti"""
        self.current_rect_shadow_offset_x = self.rect_shadow_x_spinbox.value()
        self.current_rect_shadow_offset_y = self.rect_shadow_y_spinbox.value()
        # Anlık uygula
        self.apply_rect_shadow_offset_change()
    
    def on_rect_shadow_blur_changed(self, value):
        """Dikdörtgen gölge bulanıklığı değişti"""
        self.current_rect_shadow_blur = value
        # Anlık uygula
        self.apply_rect_shadow_blur_change()
    
    def on_rect_shadow_size_changed(self, value):
        """Dikdörtgen gölge boyutu değişti"""
        self.current_rect_shadow_size = value
        # Anlık uygula
        self.apply_rect_shadow_size_change()
    
    def on_rect_shadow_opacity_changed(self, value):
        """Dikdörtgen gölge şeffaflığı değişti"""
        self.current_rect_shadow_opacity = value / 100.0
        self.rect_shadow_opacity_label.setText(f"{value}%")
        # Anlık uygula
        self.apply_rect_shadow_opacity_change()
    
    def on_rect_shadow_type_changed(self, button):
        """Dikdörtgen gölge tipi değişti (dış/iç)"""
        self.current_rect_inner_shadow = (button == self.rect_shadow_inner_radio)
        # Anlık uygula
        self.apply_rect_inner_shadow_change()
    
    def on_rect_quality_changed(self, text):
        """Dikdörtgen gölge kalitesi değişti"""
        self.current_rect_shadow_quality = text
        # Anlık uygula
        self.apply_rect_quality_change()
        
    # Çember özellikleri event handler'ları
    def on_circle_shadow_enabled_changed(self, enabled):
        """Çember gölge etkin/pasif değişti"""
        self.current_circle_shadow_enabled = enabled
        self.circle_shadow_color_button.setEnabled(enabled)
        self.circle_shadow_x_spinbox.setEnabled(enabled)
        self.circle_shadow_y_spinbox.setEnabled(enabled)
        self.circle_shadow_blur_spinbox.setEnabled(enabled)
        self.circle_shadow_size_spinbox.setEnabled(enabled)
        self.circle_shadow_opacity_slider.setEnabled(enabled)
        self.circle_outer_shadow_radio.setEnabled(enabled)
        self.circle_inner_shadow_radio.setEnabled(enabled)
        self.circle_shadow_quality_combo.setEnabled(enabled)
        # Anlık uygula
        self.apply_circle_shadow_enabled_change()

    def on_circle_shadow_offset_changed(self):
        """Çember gölge offseti değişti"""
        self.current_circle_shadow_offset_x = self.circle_shadow_x_spinbox.value()
        self.current_circle_shadow_offset_y = self.circle_shadow_y_spinbox.value()
        # Anlık uygula
        self.apply_circle_shadow_offset_change()

    def on_circle_shadow_blur_changed(self, value):
        """Çember gölge bulanıklığı değişti"""
        self.current_circle_shadow_blur = value
        # Anlık uygula
        self.apply_circle_shadow_blur_change()

    def on_circle_shadow_size_changed(self, value):
        """Çember gölge boyutu değişti"""
        self.current_circle_shadow_size = value
        # Anlık uygula
        self.apply_circle_shadow_size_change()

    def on_circle_shadow_opacity_changed(self, value):
        """Çember gölge şeffaflığı değişti"""
        self.current_circle_shadow_opacity = value / 100.0  # 0-1 aralığına çevir
        self.circle_shadow_opacity_label.setText(f"{value}%")
        # Anlık uygula
        self.apply_circle_shadow_opacity_change()

    def on_circle_shadow_type_changed(self, button):
        """Çember gölge tipi değişti"""
        self.current_circle_inner_shadow = self.circle_inner_shadow_radio.isChecked()
        # Anlık uygula
        self.apply_circle_inner_shadow_change()

    def on_circle_quality_changed(self, text):
        """Çember gölge kalitesi değişti"""
        self.current_circle_shadow_quality = text
        # Anlık uygula
        self.apply_circle_quality_change()

    # Çizgi gölge özellikleri event handler'ları
    def on_stroke_shadow_enabled_changed(self, enabled):
        """Çizgi gölge etkin/pasif değişti"""
        self.current_stroke_shadow_enabled = enabled
        self.apply_stroke_shadow_enabled_change()

    def on_stroke_shadow_offset_changed(self):
        """Çizgi gölge offseti değişti"""
        self.current_stroke_shadow_offset_x = self.stroke_shadow_x_spinbox.value()
        self.current_stroke_shadow_offset_y = self.stroke_shadow_y_spinbox.value()
        self.apply_stroke_shadow_offset_change()

    def on_stroke_shadow_blur_changed(self, value):
        """Çizgi gölge bulanıklığı değişti"""
        self.current_stroke_shadow_blur = value
        self.apply_stroke_shadow_blur_change()

    def on_stroke_shadow_size_changed(self, value):
        """Çizgi gölge boyutu değişti"""
        self.current_stroke_shadow_size = value
        self.apply_stroke_shadow_size_change()

    def on_stroke_shadow_type_changed(self, button):
        """Çizgi gölge tipi değişti"""
        self.current_stroke_inner_shadow = (button == self.stroke_shadow_inner_radio)
        self.apply_stroke_shadow_inner_change()

    def on_stroke_shadow_quality_changed(self, index):
        """Çizgi gölge kalitesi değişti"""
        self.current_stroke_shadow_quality = self.stroke_shadow_quality_combo.itemData(index)
        self.apply_stroke_shadow_quality_change()

    def on_stroke_shadow_opacity_changed(self, value):
        """Çizgi gölge şeffaflığı değişti"""
        self.current_stroke_shadow_opacity = value / 100.0
        if hasattr(self, 'stroke_shadow_opacity_label'):
            self.stroke_shadow_opacity_label.setText(f"{value}%")
        self.apply_stroke_shadow_opacity_change()

    def apply_stroke_shadow_enabled_change(self):
        """Çizgi gölge etkin/pasif değişikliğini uygula"""
        if self.selected_strokes and self.has_stroke_shadow_shapes:
            self.strokeShadowEnabledChanged.emit(self.current_stroke_shadow_enabled)

    def apply_stroke_shadow_color_change(self):
        """Çizgi gölge rengi değişikliğini uygula"""
        if self.selected_strokes and self.has_stroke_shadow_shapes:
            self.strokeShadowColorChanged.emit(self.current_stroke_shadow_color)

    def apply_stroke_shadow_offset_change(self):
        """Çizgi gölge offseti değişikliğini uygula"""
        if self.selected_strokes and self.has_stroke_shadow_shapes:
            self.strokeShadowOffsetChanged.emit(self.current_stroke_shadow_offset_x, self.current_stroke_shadow_offset_y)

    def apply_stroke_shadow_blur_change(self):
        """Çizgi gölge bulanıklığı değişikliğini uygula"""
        if self.selected_strokes and self.has_stroke_shadow_shapes:
            self.strokeShadowBlurChanged.emit(self.current_stroke_shadow_blur)

    def apply_stroke_shadow_size_change(self):
        """Çizgi gölge boyutu değişikliğini uygula"""
        if self.selected_strokes and self.has_stroke_shadow_shapes:
            self.strokeShadowSizeChanged.emit(self.current_stroke_shadow_size)

    def apply_stroke_shadow_inner_change(self):
        """Çizgi iç/dış gölge değişikliğini uygula"""
        if self.selected_strokes and self.has_stroke_shadow_shapes:
            self.strokeShadowInnerChanged.emit(self.current_stroke_inner_shadow)

    def apply_stroke_shadow_quality_change(self):
        """Çizgi gölge kalitesi değişikliğini uygula"""
        if self.selected_strokes and self.has_stroke_shadow_shapes:
            self.strokeShadowQualityChanged.emit(self.current_stroke_shadow_quality)

    def apply_stroke_shadow_opacity_change(self):
        """Çizgi gölge şeffaflığı değişikliğini uygula"""
        if self.selected_strokes and self.has_stroke_shadow_shapes:
            self.strokeShadowOpacityChanged.emit(self.current_stroke_shadow_opacity)

    def apply_rect_corner_radius_change(self):
        """Dikdörtgen kenar yuvarlama değişikliğini uygula"""
        if self.selected_strokes and self.has_rectangle_shapes:
            self.rectangleCornerRadiusChanged.emit(self.current_rect_corner_radius)
    
    def apply_rect_shadow_enabled_change(self):
        """Dikdörtgen gölge etkin/pasif değişikliğini uygula"""
        if self.selected_strokes and self.has_rectangle_shapes:
            self.rectangleShadowEnabledChanged.emit(self.current_rect_shadow_enabled)
    
    def apply_rect_shadow_color_change(self):
        """Dikdörtgen gölge rengi değişikliğini uygula"""
        if self.selected_strokes and self.has_rectangle_shapes:
            self.rectangleShadowColorChanged.emit(self.current_rect_shadow_color)
    
    def apply_rect_shadow_offset_change(self):
        """Dikdörtgen gölge offseti değişikliğini uygula"""
        if self.selected_strokes and self.has_rectangle_shapes:
            self.rectangleShadowOffsetChanged.emit(self.current_rect_shadow_offset_x, self.current_rect_shadow_offset_y)
    
    def apply_rect_shadow_blur_change(self):
        """Dikdörtgen gölge bulanıklığı değişikliğini uygula"""
        if self.selected_strokes and self.has_rectangle_shapes:
            self.rectangleShadowBlurChanged.emit(self.current_rect_shadow_blur)
    
    def apply_rect_shadow_size_change(self):
        """Dikdörtgen gölge boyutu değişikliğini uygula"""
        if self.selected_strokes and self.has_rectangle_shapes:
            self.rectangleShadowSizeChanged.emit(self.current_rect_shadow_size)
    
    def apply_rect_shadow_opacity_change(self):
        """Dikdörtgen gölge şeffaflığı değişikliğini uygula"""
        if self.selected_strokes and self.has_rectangle_shapes:
            self.rectangleShadowOpacityChanged.emit(self.current_rect_shadow_opacity)
    
    def apply_rect_inner_shadow_change(self):
        """Dikdörtgen iç gölge değişikliğini uygula"""
        if self.selected_strokes and self.has_rectangle_shapes:
            self.rectangleShadowInnerChanged.emit(self.current_rect_inner_shadow)
    
    def apply_rect_quality_change(self):
        """Dikdörtgen gölge kalitesi değişikliğini uygula"""
        if self.selected_strokes and self.has_rectangle_shapes:
            self.rectangleShadowQualityChanged.emit(self.current_rect_shadow_quality)
            
    def apply_circle_shadow_enabled_change(self):
        """Çember gölge etkin/pasif değişikliğini uygula"""
        if self.selected_strokes and self.has_circle_shapes:
            self.circleShadowEnabledChanged.emit(self.current_circle_shadow_enabled)
        
    def apply_circle_shadow_color_change(self):
        """Çember gölge rengi değişikliğini uygula"""
        if self.selected_strokes and self.has_circle_shapes:
            self.circleShadowColorChanged.emit(self.current_circle_shadow_color)
        
    def apply_circle_shadow_offset_change(self):
        """Çember gölge offseti değişikliğini uygula"""
        if self.selected_strokes and self.has_circle_shapes:
            self.circleShadowOffsetChanged.emit(self.current_circle_shadow_offset_x, self.current_circle_shadow_offset_y)
        
    def apply_circle_shadow_blur_change(self):
        """Çember gölge bulanıklığı değişikliğini uygula"""
        if self.selected_strokes and self.has_circle_shapes:
            self.circleShadowBlurChanged.emit(self.current_circle_shadow_blur)
        
    def apply_circle_shadow_size_change(self):
        """Çember gölge boyutu değişikliğini uygula"""
        if self.selected_strokes and self.has_circle_shapes:
            self.circleShadowSizeChanged.emit(self.current_circle_shadow_size)
        
    def apply_circle_shadow_opacity_change(self):
        """Çember gölge şeffaflığı değişikliğini uygula"""
        if self.selected_strokes and self.has_circle_shapes:
            self.circleShadowOpacityChanged.emit(self.current_circle_shadow_opacity)
        
    def apply_circle_inner_shadow_change(self):
        """Çember iç/dış gölge değişikliğini uygula"""
        if self.selected_strokes and self.has_circle_shapes:
            self.circleShadowInnerChanged.emit(self.current_circle_inner_shadow)
        
    def apply_circle_quality_change(self):
        """Çember gölge kalitesi değişikliğini uygula"""
        if self.selected_strokes and self.has_circle_shapes:
            self.circleShadowQualityChanged.emit(self.current_circle_shadow_quality)
    
    # Grup işlemi event handler'ları
    def on_group_shapes(self):
        """Şekilleri grupla"""
        if len(self.selected_strokes) >= 2:
            self.groupShapes.emit()
    
    def on_ungroup_shapes(self):
        """Grubu çöz"""
        if self.selected_strokes:
            self.ungroupShapes.emit()
    
    # Hizalama event handler'ları
    def on_align_left(self):
        """Sola hizala"""
        if len(self.selected_strokes) >= 2:
            self.alignLeft.emit()
    
    def on_align_right(self):
        """Sağa hizala"""
        if len(self.selected_strokes) >= 2:
            self.alignRight.emit()
    
    def on_align_top(self):
        """Yukarı hizala"""
        if len(self.selected_strokes) >= 2:
            self.alignTop.emit()
    
    def on_align_bottom(self):
        """Aşağı hizala"""
        if len(self.selected_strokes) >= 2:
            self.alignBottom.emit()
    
    def on_align_center_h(self):
        """Yatay ortala"""
        if len(self.selected_strokes) >= 2:
            self.alignCenterH.emit()
    
    def on_align_center_v(self):
        """Dikey ortala"""
        if len(self.selected_strokes) >= 2:
            self.alignCenterV.emit()
    
    def on_distribute_h(self):
        """Yatay dağıt"""
        if len(self.selected_strokes) >= 3:
            self.distributeH.emit()
    
    def on_distribute_v(self):
        """Dikey dağıt"""
        if len(self.selected_strokes) >= 3:
            self.distributeV.emit()
    
    def on_add_to_shape_library(self):
        """Seçili şekilleri şekil havuzuna ekle"""
        if self.selected_strokes:
            self.addToShapeLibrary.emit()

    def apply_changes(self):
        """Tüm değişiklikleri uygula - geriye uyumluluk için"""
        if not self.selected_strokes:
            return
            
        # Sinyalleri gönder
        self.colorChanged.emit(self.current_color)
        self.widthChanged.emit(self.current_width)
        self.lineStyleChanged.emit(self.current_line_style)
        
        if self.has_fillable_shapes:
            self.fillColorChanged.emit(self.current_fill_color)
            self.fillEnabledChanged.emit(self.current_fill_enabled)
            self.fillOpacityChanged.emit(self.current_fill_opacity)
            
    def set_selected_strokes(self, stroke_indices, strokes_data):
        """Seçilen şekilleri ayarla ve özelliklerini yükle"""
        self.selected_strokes = stroke_indices
        self.stroke_data = strokes_data
        
        if not stroke_indices:
            self.set_no_selection()
            return
            
        # Seçilen şekilleri analiz et
        self.analyze_selected_strokes()
        self.update_ui_values()
        self.show_properties()
        
    def analyze_selected_strokes(self):
        """Seçilen stroke'ları analiz et ve ortak özellikleri bul"""
        self.has_fillable_shapes = False
        self.has_bspline_shapes = False
        self.has_image_shapes = False
        self.has_rectangle_shapes = False
        self.has_circle_shapes = False
        self.has_stroke_shadow_shapes = False
        
        if not self.stroke_data or not self.selected_strokes:
            return
            
        for index in self.selected_strokes:
            if index < len(self.stroke_data):
                stroke = self.stroke_data[index]
                
                # Image stroke kontrolü
                if hasattr(stroke, 'stroke_type') and stroke.stroke_type == 'image':
                    self.has_image_shapes = True
                    continue
                    
                # Doldurulabilir şekilleri kontrol et
                if stroke.get('type') in ['rectangle', 'circle'] or stroke.get('tool_type') in ['rectangle', 'circle']:
                    self.has_fillable_shapes = True
                    
                # Dikdörtgen şekillerini kontrol et (gölge/kenar için)
                if stroke.get('type') == 'rectangle' or stroke.get('tool_type') == 'rectangle':
                    self.has_rectangle_shapes = True
                    
                # Çember şekillerini kontrol et (gölge için)
                if stroke.get('type') == 'circle' or stroke.get('tool_type') == 'circle':
                    self.has_circle_shapes = True

                # B-spline şekillerini kontrol et
                if stroke.get('type') == 'bspline' or stroke.get('tool_type') == 'bspline':
                    self.has_bspline_shapes = True

                # Çizgi gölge özellikleri
                if stroke.get('type') in ['line', 'freehand', 'bspline'] or stroke.get('tool_type') in ['line', 'freehand', 'bspline']:
                    self.has_stroke_shadow_shapes = True
        
        # Dolgu özelliklerini göster/gizle
        self.fill_group.setVisible(self.has_fillable_shapes)
        
        # B-spline özelliklerini göster/gizle
        self.bspline_group.setVisible(self.has_bspline_shapes)
        
        # Resim özelliklerini göster/gizle
        self.image_group.setVisible(self.has_image_shapes)
        
        # Dikdörtgen özelliklerini göster/gizle
        self.rectangle_group.setVisible(self.has_rectangle_shapes)

        # Çember özelliklerini göster/gizle
        self.circle_group.setVisible(self.has_circle_shapes)

        # Çizgi gölge özelliklerini göster/gizle
        if hasattr(self, 'stroke_shadow_group'):
            self.stroke_shadow_group.setVisible(self.has_stroke_shadow_shapes)
        
        # Ortak özellikleri analiz et
        if self.selected_strokes:
            self.analyze_common_properties([self.stroke_data[i] for i in self.selected_strokes if i < len(self.stroke_data)])
            
        self.update_ui_values()
        self.update_button_states()
    
    def analyze_common_properties(self, strokes):
        """Çoklu seçimdeki ortak özellikleri analiz et"""
        if not strokes:
            return
            
        # İlk stroke'tan başlangıç değerleri al
        first_stroke = strokes[0]
        
        # Normal stroke'ları ayır (resim stroke'ları hariç)
        normal_strokes = [s for s in strokes if not (hasattr(s, 'stroke_type') and s.stroke_type == 'image')]

        if not normal_strokes:
            return  # Sadece resim stroke'ları varsa normal özellik analizi yapma

        # Varsayılan çizgi gölge değerlerini sıfırla
        self.current_stroke_shadow_enabled = False
        self.current_stroke_shadow_color = QColor(0, 0, 0, 128)
        self.current_stroke_shadow_offset_x = 5
        self.current_stroke_shadow_offset_y = 5
        self.current_stroke_shadow_blur = 10
        self.current_stroke_shadow_size = 0
        self.current_stroke_shadow_opacity = 0.7
        self.current_stroke_inner_shadow = False
        self.current_stroke_shadow_quality = "medium"

        # Renk analizi - ortak renk varsa kullan, yoksa ilk stroke'un rengini kullan
        colors = []
        for stroke in normal_strokes:
            color = stroke.get('color', Qt.GlobalColor.black)
            if isinstance(color, str):
                color = QColor(color)
            elif not isinstance(color, QColor):
                color = QColor(Qt.GlobalColor.black)
            colors.append(color)
        
        # Tüm renkler aynı mı kontrol et
        if all(c.name() == colors[0].name() for c in colors):
            self.current_color = colors[0]
        else:
            # Farklı renkler varsa ilk stroke'un rengini kullan
            self.current_color = colors[0]
        
        # Kalınlık analizi
        widths = []
        for stroke in normal_strokes:
            if stroke['type'] in ['rectangle', 'circle']:
                width = stroke.get('line_width', 2)
            else:
                width = stroke.get('width', 2)
            widths.append(width)
        
        # Tüm kalınlıklar aynı mı kontrol et
        if all(w == widths[0] for w in widths):
            self.current_width = widths[0]
        else:
            # Farklı kalınlıklar varsa ortalama al
            self.current_width = int(sum(widths) / len(widths))
        
        # Çizgi stili analizi
        styles = []
        for stroke in normal_strokes:
            if stroke['type'] in ['rectangle', 'circle']:
                style = stroke.get('line_style', Qt.PenStyle.SolidLine)
            else:
                style = stroke.get('style', Qt.PenStyle.SolidLine)
            if isinstance(style, int):
                style = Qt.PenStyle(style)
            styles.append(style)
        
        # Tüm stiller aynı mı kontrol et
        if all(s == styles[0] for s in styles):
            self.current_line_style = styles[0]
        else:
            # Farklı stiller varsa en yaygın olanı kullan
            style_counts = {}
            for style in styles:
                style_counts[style] = style_counts.get(style, 0) + 1
            self.current_line_style = max(style_counts, key=style_counts.get)

        stroke_shadow_strokes = [s for s in normal_strokes if s.get('type') in ['line', 'freehand', 'bspline'] or s.get('tool_type') in ['line', 'freehand', 'bspline']]
        if stroke_shadow_strokes:
            shadow_states = [s.get('has_shadow', False) for s in stroke_shadow_strokes]
            if all(state == shadow_states[0] for state in shadow_states):
                self.current_stroke_shadow_enabled = shadow_states[0]
            else:
                self.current_stroke_shadow_enabled = any(shadow_states)

            shadow_colors = []
            for s in stroke_shadow_strokes:
                shadow_color = s.get('shadow_color', QColor(0, 0, 0, 128))
                if isinstance(shadow_color, str):
                    shadow_color = QColor(shadow_color)
                elif not isinstance(shadow_color, QColor) and hasattr(shadow_color, 'name'):
                    shadow_color = QColor(shadow_color)
                elif not isinstance(shadow_color, QColor):
                    shadow_color = QColor(Qt.GlobalColor.black)
                shadow_colors.append(shadow_color)
            if shadow_colors:
                if all(c.name() == shadow_colors[0].name() for c in shadow_colors):
                    self.current_stroke_shadow_color = shadow_colors[0]
                else:
                    self.current_stroke_shadow_color = shadow_colors[0]

            x_offsets = [s.get('shadow_offset_x', 5) for s in stroke_shadow_strokes]
            y_offsets = [s.get('shadow_offset_y', 5) for s in stroke_shadow_strokes]
            if x_offsets:
                if all(x == x_offsets[0] for x in x_offsets):
                    self.current_stroke_shadow_offset_x = x_offsets[0]
                else:
                    self.current_stroke_shadow_offset_x = int(sum(x_offsets) / len(x_offsets))
            if y_offsets:
                if all(y == y_offsets[0] for y in y_offsets):
                    self.current_stroke_shadow_offset_y = y_offsets[0]
                else:
                    self.current_stroke_shadow_offset_y = int(sum(y_offsets) / len(y_offsets))

            blur_values = [s.get('shadow_blur', 10) for s in stroke_shadow_strokes]
            if blur_values:
                if all(b == blur_values[0] for b in blur_values):
                    self.current_stroke_shadow_blur = blur_values[0]
                else:
                    self.current_stroke_shadow_blur = int(sum(blur_values) / len(blur_values))

            size_values = [s.get('shadow_size', 0) for s in stroke_shadow_strokes]
            if size_values:
                if all(sz == size_values[0] for sz in size_values):
                    self.current_stroke_shadow_size = size_values[0]
                else:
                    self.current_stroke_shadow_size = int(sum(size_values) / len(size_values))

            opacity_values = [s.get('shadow_opacity', 0.7) for s in stroke_shadow_strokes]
            if opacity_values:
                if all(abs(op - opacity_values[0]) < 1e-3 for op in opacity_values):
                    self.current_stroke_shadow_opacity = opacity_values[0]
                else:
                    self.current_stroke_shadow_opacity = sum(opacity_values) / len(opacity_values)

            inner_values = [s.get('inner_shadow', False) for s in stroke_shadow_strokes]
            if inner_values:
                if all(val == inner_values[0] for val in inner_values):
                    self.current_stroke_inner_shadow = inner_values[0]
                else:
                    self.current_stroke_inner_shadow = False

            quality_values = [s.get('shadow_quality', 'medium') for s in stroke_shadow_strokes]
            if quality_values:
                if all(q == quality_values[0] for q in quality_values):
                    self.current_stroke_shadow_quality = quality_values[0]
                else:
                    self.current_stroke_shadow_quality = 'medium'

        # Dolgu özellikleri analizi (sadece fillable shapes varsa)
        if self.has_fillable_shapes:
            fillable_strokes = [s for s in normal_strokes if s['type'] in ['rectangle', 'circle']]
            
            if fillable_strokes:
                # Dolgu durumu analizi
                fill_states = [s.get('fill', False) for s in fillable_strokes]
                if all(f == fill_states[0] for f in fill_states):
                    self.current_fill_enabled = fill_states[0]
                else:
                    # Farklı dolgu durumları varsa çoğunluğu al
                    self.current_fill_enabled = sum(fill_states) > len(fill_states) / 2
                
                # Dolgu rengi analizi
                fill_colors = []
                for stroke in fillable_strokes:
                    fill_color = stroke.get('fill_color', Qt.GlobalColor.white)
                    if isinstance(fill_color, QColor):
                        fill_colors.append(fill_color)
                    elif fill_color is not None:
                        fill_colors.append(QColor(fill_color))
                    else:
                        fill_colors.append(QColor(Qt.GlobalColor.white))
                
                if fill_colors:
                    if all(c.name() == fill_colors[0].name() for c in fill_colors):
                        self.current_fill_color = fill_colors[0]
                    else:
                        # Farklı dolgu renkleri varsa ilk stroke'un rengini kullan
                        self.current_fill_color = fill_colors[0]
                
                # Dolgu şeffaflığı analizi
                opacities = [s.get('fill_opacity', 1.0) for s in fillable_strokes]
                if all(abs(o - opacities[0]) < 0.01 for o in opacities):
                    self.current_fill_opacity = opacities[0]
                else:
                    # Farklı şeffaflıklar varsa ortalama al
                    self.current_fill_opacity = sum(opacities) / len(opacities)
                    
        # Resim özellikleri analizi (sadece image shapes varsa)
        if self.has_image_shapes:
            image_strokes = [s for s in strokes if hasattr(s, 'stroke_type') and s.stroke_type == 'image']
            
            if image_strokes:
                # Resim şeffaflığı analizi
                image_opacities = [s.opacity for s in image_strokes]
                if all(abs(o - image_opacities[0]) < 0.01 for o in image_opacities):
                    self.current_image_opacity = image_opacities[0]
                else:
                    # Farklı şeffaflıklar varsa ortalama al
                    self.current_image_opacity = sum(image_opacities) / len(image_opacities)
                
                # Kenarlık durumu analizi
                border_states = [s.has_border for s in image_strokes]
                if all(b == border_states[0] for b in border_states):
                    self.current_border_enabled = border_states[0]
                else:
                    # Farklı kenarlık durumları varsa çoğunluğu al
                    self.current_border_enabled = sum(border_states) > len(border_states) / 2
                
                # Kenarlık rengi analizi
                border_colors = [s.border_color for s in image_strokes]
                if all(c.name() == border_colors[0].name() for c in border_colors):
                    self.current_border_color = border_colors[0]
                else:
                    # Farklı kenarlık renkleri varsa ilk stroke'un rengini kullan
                    self.current_border_color = border_colors[0]
                
                # Kenarlık kalınlığı analizi
                border_widths = [s.border_width for s in image_strokes]
                if all(w == border_widths[0] for w in border_widths):
                    self.current_border_width = border_widths[0]
                else:
                    # Farklı kalınlıklar varsa ortalama al
                    self.current_border_width = int(sum(border_widths) / len(border_widths))
                
                # Kenarlık stili analizi
                border_styles = [s.border_style for s in image_strokes]
                if all(s == border_styles[0] for s in border_styles):
                    self.current_border_style = border_styles[0]
                else:
                    # Farklı stiller varsa en yaygın olanı kullan
                    style_counts = {}
                    for style in border_styles:
                        style_counts[style] = style_counts.get(style, 0) + 1
                    self.current_border_style = max(style_counts, key=style_counts.get)
                
                # Gölge durumu analizi
                shadow_states = [s.has_shadow for s in image_strokes]
                if all(sh == shadow_states[0] for sh in shadow_states):
                    self.current_shadow_enabled = shadow_states[0]
                else:
                    # Farklı gölge durumları varsa çoğunluğu al
                    self.current_shadow_enabled = sum(shadow_states) > len(shadow_states) / 2
                
                # Gölge rengi analizi
                shadow_colors = [s.shadow_color for s in image_strokes]
                if all(c.name() == shadow_colors[0].name() for c in shadow_colors):
                    self.current_shadow_color = shadow_colors[0]
                else:
                    # Farklı gölge renkleri varsa ilk stroke'un rengini kullan
                    self.current_shadow_color = shadow_colors[0]
                
                # Gölge offseti analizi
                shadow_x_offsets = [s.shadow_offset_x for s in image_strokes]
                shadow_y_offsets = [s.shadow_offset_y for s in image_strokes]
                
                if all(x == shadow_x_offsets[0] for x in shadow_x_offsets):
                    self.current_shadow_offset_x = shadow_x_offsets[0]
                else:
                    self.current_shadow_offset_x = int(sum(shadow_x_offsets) / len(shadow_x_offsets))
                    
                if all(y == shadow_y_offsets[0] for y in shadow_y_offsets):
                    self.current_shadow_offset_y = shadow_y_offsets[0]
                else:
                    self.current_shadow_offset_y = int(sum(shadow_y_offsets) / len(shadow_y_offsets))
                
                # Gölge bulanıklığı analizi
                shadow_blurs = [s.shadow_blur for s in image_strokes]
                if all(b == shadow_blurs[0] for b in shadow_blurs):
                    self.current_shadow_blur = shadow_blurs[0]
                else:
                    self.current_shadow_blur = int(sum(shadow_blurs) / len(shadow_blurs))
                
                # Gölge boyutu analizi
                shadow_sizes = [getattr(s, 'shadow_size', 0) for s in image_strokes]
                if all(s == shadow_sizes[0] for s in shadow_sizes):
                    self.current_shadow_size = shadow_sizes[0]
                else:
                    self.current_shadow_size = int(sum(shadow_sizes) / len(shadow_sizes))
                
                # İç gölge analizi
                inner_shadows = [getattr(s, 'inner_shadow', False) for s in image_strokes]
                if all(i == inner_shadows[0] for i in inner_shadows):
                    self.current_inner_shadow = inner_shadows[0]
                else:
                    self.current_inner_shadow = False  # Karışık durumda false
                
                # Gölge kalitesi analizi
                qualities = [getattr(s, 'shadow_quality', 'medium') for s in image_strokes]
                if all(q == qualities[0] for q in qualities):
                    self.current_shadow_quality = qualities[0]
                else:
                    self.current_shadow_quality = 'medium'  # Karışık durumda medium
                
                # Filtre analizi
                filter_types = [s.filter_type for s in image_strokes]
                if all(f == filter_types[0] for f in filter_types):
                    self.current_filter_type = filter_types[0]
                else:
                    # Farklı filtre tipleri varsa "none" kullan
                    self.current_filter_type = "none"
                
                filter_intensities = [s.filter_intensity for s in image_strokes]
                if all(abs(i - filter_intensities[0]) < 0.01 for i in filter_intensities):
                    self.current_filter_intensity = filter_intensities[0]
                else:
                    self.current_filter_intensity = sum(filter_intensities) / len(filter_intensities)
                
                # Şeffaflık analizi (transparency)
                transparencies = [getattr(s, 'transparency', 1.0) for s in image_strokes]
                if all(abs(t - transparencies[0]) < 0.01 for t in transparencies):
                    self.current_transparency = transparencies[0]
                else:
                    self.current_transparency = sum(transparencies) / len(transparencies)
                
                # Bulanıklık analizi (blur_radius)
                blur_radii = [getattr(s, 'blur_radius', 0) for s in image_strokes]
                if all(b == blur_radii[0] for b in blur_radii):
                    self.current_blur_radius = blur_radii[0]
                else:
                    self.current_blur_radius = int(sum(blur_radii) / len(blur_radii))
                    
    def update_ui_values(self):
        """UI değerlerini güncelle - sinyalleri geçici olarak kes"""
        # Sinyalleri geçici olarak kes
        self.width_spinbox.blockSignals(True)
        self.style_combo.blockSignals(True)
        self.fill_checkbox.blockSignals(True)
        self.fill_opacity_slider.blockSignals(True)
        
        # Resim sinyallerini de kes
        if hasattr(self, 'image_opacity_slider'):
            self.image_opacity_slider.blockSignals(True)
        if hasattr(self, 'border_checkbox'):
            self.border_checkbox.blockSignals(True)
        if hasattr(self, 'border_width_spinbox'):
            self.border_width_spinbox.blockSignals(True)
        if hasattr(self, 'border_style_combo'):
            self.border_style_combo.blockSignals(True)
        if hasattr(self, 'shadow_checkbox'):
            self.shadow_checkbox.blockSignals(True)
        if hasattr(self, 'shadow_x_spinbox'):
            self.shadow_x_spinbox.blockSignals(True)
        if hasattr(self, 'shadow_y_spinbox'):
            self.shadow_y_spinbox.blockSignals(True)
        if hasattr(self, 'shadow_size_spinbox'):
            self.shadow_size_spinbox.blockSignals(True)
        if hasattr(self, 'shadow_type_group'):
            self.shadow_type_group.blockSignals(True)
        if hasattr(self, 'quality_combo'):
            self.quality_combo.blockSignals(True)
        if hasattr(self, 'transparency_slider'):
            self.transparency_slider.blockSignals(True)
        if hasattr(self, 'blur_spinbox'):
            self.blur_spinbox.blockSignals(True)
        if hasattr(self, 'stroke_shadow_checkbox'):
            self.stroke_shadow_checkbox.blockSignals(True)
        if hasattr(self, 'stroke_shadow_type_group'):
            self.stroke_shadow_type_group.blockSignals(True)
        if hasattr(self, 'stroke_shadow_x_spinbox'):
            self.stroke_shadow_x_spinbox.blockSignals(True)
        if hasattr(self, 'stroke_shadow_y_spinbox'):
            self.stroke_shadow_y_spinbox.blockSignals(True)
        if hasattr(self, 'stroke_shadow_blur_spinbox'):
            self.stroke_shadow_blur_spinbox.blockSignals(True)
        if hasattr(self, 'stroke_shadow_size_spinbox'):
            self.stroke_shadow_size_spinbox.blockSignals(True)
        if hasattr(self, 'stroke_shadow_quality_combo'):
            self.stroke_shadow_quality_combo.blockSignals(True)
        if hasattr(self, 'stroke_shadow_opacity_slider'):
            self.stroke_shadow_opacity_slider.blockSignals(True)
        
        try:
            # Renk butonlarını güncelle
            self.update_color_button()
            self.update_fill_color_button()
            if hasattr(self, 'border_color_button'):
                self.update_border_color_button()
            if hasattr(self, 'shadow_color_button'):
                self.update_shadow_color_button()
            if hasattr(self, 'stroke_shadow_color_button'):
                self.update_stroke_shadow_color_button()
            
            # Kalınlık
            self.width_spinbox.setValue(self.current_width)
            
            # Çizgi stili
            for i in range(self.style_combo.count()):
                if self.style_combo.itemData(i) == self.current_line_style:
                    self.style_combo.setCurrentIndex(i)
                    break
                    
            # Dolgu
            self.fill_checkbox.setChecked(self.current_fill_enabled)
            self.fill_color_button.setEnabled(self.current_fill_enabled)
            
            # Dolgu şeffaflığı
            self.fill_opacity_slider.setValue(int(self.current_fill_opacity * 100))
            self.fill_opacity_label.setText(f"{int(self.current_fill_opacity * 100)}%")
            self.fill_opacity_slider.setEnabled(self.current_fill_enabled)
            self.fill_opacity_label.setEnabled(self.current_fill_enabled)
            
            # Resim özellikleri
            if hasattr(self, 'image_opacity_slider'):
                self.image_opacity_slider.setValue(int(self.current_image_opacity * 100))
                self.image_opacity_label.setText(f"{int(self.current_image_opacity * 100)}%")
            
            if hasattr(self, 'border_checkbox'):
                self.border_checkbox.setChecked(self.current_border_enabled)
                self.border_color_button.setEnabled(self.current_border_enabled)
                self.border_width_spinbox.setEnabled(self.current_border_enabled)
                self.border_style_combo.setEnabled(self.current_border_enabled)
                
            if hasattr(self, 'border_width_spinbox'):
                self.border_width_spinbox.setValue(self.current_border_width)
                
            if hasattr(self, 'border_style_combo'):
                for i in range(self.border_style_combo.count()):
                    if self.border_style_combo.itemData(i) == self.current_border_style:
                        self.border_style_combo.setCurrentIndex(i)
                        break
            
            if hasattr(self, 'shadow_checkbox'):
                self.shadow_checkbox.setChecked(self.current_shadow_enabled)
                self.shadow_color_button.setEnabled(self.current_shadow_enabled)
                self.shadow_x_spinbox.setEnabled(self.current_shadow_enabled)
                self.shadow_y_spinbox.setEnabled(self.current_shadow_enabled)
                if hasattr(self, 'shadow_blur_spinbox'):
                    self.shadow_blur_spinbox.setEnabled(self.current_shadow_enabled)
                if hasattr(self, 'shadow_size_spinbox'):
                    self.shadow_size_spinbox.setEnabled(self.current_shadow_enabled)
                if hasattr(self, 'outer_shadow_radio'):
                    self.outer_shadow_radio.setEnabled(self.current_shadow_enabled)
                if hasattr(self, 'inner_shadow_radio'):
                    self.inner_shadow_radio.setEnabled(self.current_shadow_enabled)
                if hasattr(self, 'quality_combo'):
                    self.quality_combo.setEnabled(self.current_shadow_enabled)
                
            if hasattr(self, 'shadow_x_spinbox'):
                self.shadow_x_spinbox.setValue(self.current_shadow_offset_x)
                
            if hasattr(self, 'shadow_y_spinbox'):
                self.shadow_y_spinbox.setValue(self.current_shadow_offset_y)
                
            if hasattr(self, 'shadow_size_spinbox'):
                self.shadow_size_spinbox.setValue(self.current_shadow_size)
                
            if hasattr(self, 'outer_shadow_radio'):
                self.outer_shadow_radio.setChecked(not self.current_inner_shadow)
            if hasattr(self, 'inner_shadow_radio'):
                self.inner_shadow_radio.setChecked(self.current_inner_shadow)
                
            if hasattr(self, 'quality_combo'):
                for i in range(self.quality_combo.count()):
                    if self.quality_combo.itemData(i) == self.current_shadow_quality:
                        self.quality_combo.setCurrentIndex(i)
                        break

            if hasattr(self, 'stroke_shadow_checkbox'):
                self.stroke_shadow_checkbox.setChecked(self.current_stroke_shadow_enabled)
                self.stroke_shadow_color_button.setEnabled(self.current_stroke_shadow_enabled)
                self.stroke_shadow_x_spinbox.setEnabled(self.current_stroke_shadow_enabled)
                self.stroke_shadow_y_spinbox.setEnabled(self.current_stroke_shadow_enabled)
                self.stroke_shadow_blur_spinbox.setEnabled(self.current_stroke_shadow_enabled)
                self.stroke_shadow_size_spinbox.setEnabled(self.current_stroke_shadow_enabled)
                self.stroke_shadow_outer_radio.setEnabled(self.current_stroke_shadow_enabled)
                self.stroke_shadow_inner_radio.setEnabled(self.current_stroke_shadow_enabled)
                self.stroke_shadow_quality_combo.setEnabled(self.current_stroke_shadow_enabled)
                self.stroke_shadow_opacity_slider.setEnabled(self.current_stroke_shadow_enabled)
                self.stroke_shadow_opacity_label.setEnabled(self.current_stroke_shadow_enabled)

            if hasattr(self, 'stroke_shadow_x_spinbox'):
                self.stroke_shadow_x_spinbox.setValue(self.current_stroke_shadow_offset_x)
            if hasattr(self, 'stroke_shadow_y_spinbox'):
                self.stroke_shadow_y_spinbox.setValue(self.current_stroke_shadow_offset_y)
            if hasattr(self, 'stroke_shadow_blur_spinbox'):
                self.stroke_shadow_blur_spinbox.setValue(self.current_stroke_shadow_blur)
            if hasattr(self, 'stroke_shadow_size_spinbox'):
                self.stroke_shadow_size_spinbox.setValue(self.current_stroke_shadow_size)
            if hasattr(self, 'stroke_shadow_outer_radio'):
                self.stroke_shadow_outer_radio.setChecked(not self.current_stroke_inner_shadow)
            if hasattr(self, 'stroke_shadow_inner_radio'):
                self.stroke_shadow_inner_radio.setChecked(self.current_stroke_inner_shadow)
            if hasattr(self, 'stroke_shadow_quality_combo'):
                for i in range(self.stroke_shadow_quality_combo.count()):
                    if self.stroke_shadow_quality_combo.itemData(i) == self.current_stroke_shadow_quality:
                        self.stroke_shadow_quality_combo.setCurrentIndex(i)
                        break
            if hasattr(self, 'stroke_shadow_opacity_slider'):
                self.stroke_shadow_opacity_slider.setValue(int(self.current_stroke_shadow_opacity * 100))
                self.stroke_shadow_opacity_label.setText(f"{int(self.current_stroke_shadow_opacity * 100)}%")
                
            # Yeni kontroller - Şeffaflık ve Blur
            if hasattr(self, 'transparency_slider'):
                self.transparency_slider.setValue(int(self.current_transparency * 100))
                self.transparency_label.setText(f"{int(self.current_transparency * 100)}%")
                
            if hasattr(self, 'blur_spinbox'):
                self.blur_spinbox.setValue(self.current_blur_radius)
                
            if hasattr(self, 'corner_radius_spinbox'):
                self.corner_radius_spinbox.setValue(self.current_corner_radius)
                
            if hasattr(self, 'shadow_opacity_slider'):
                self.shadow_opacity_slider.setValue(int(self.current_shadow_opacity * 100))
                self.shadow_opacity_label.setText(f"{int(self.current_shadow_opacity * 100)}%")
                
        finally:
            # Sinyalleri tekrar aktif et
            self.width_spinbox.blockSignals(False)
            self.style_combo.blockSignals(False)
            self.fill_checkbox.blockSignals(False)
            self.fill_opacity_slider.blockSignals(False)
            
            # Resim sinyallerini de aktif et
            if hasattr(self, 'image_opacity_slider'):
                self.image_opacity_slider.blockSignals(False)
            if hasattr(self, 'border_checkbox'):
                self.border_checkbox.blockSignals(False)
            if hasattr(self, 'border_width_spinbox'):
                self.border_width_spinbox.blockSignals(False)
            if hasattr(self, 'border_style_combo'):
                self.border_style_combo.blockSignals(False)
            if hasattr(self, 'shadow_checkbox'):
                self.shadow_checkbox.blockSignals(False)
            if hasattr(self, 'shadow_x_spinbox'):
                self.shadow_x_spinbox.blockSignals(False)
            if hasattr(self, 'shadow_y_spinbox'):
                self.shadow_y_spinbox.blockSignals(False)
            if hasattr(self, 'shadow_size_spinbox'):
                self.shadow_size_spinbox.blockSignals(False)
            if hasattr(self, 'shadow_type_group'):
                self.shadow_type_group.blockSignals(False)
            if hasattr(self, 'quality_combo'):
                self.quality_combo.blockSignals(False)
            if hasattr(self, 'transparency_slider'):
                self.transparency_slider.blockSignals(False)
            if hasattr(self, 'blur_spinbox'):
                self.blur_spinbox.blockSignals(False)
            if hasattr(self, 'stroke_shadow_checkbox'):
                self.stroke_shadow_checkbox.blockSignals(False)
            if hasattr(self, 'stroke_shadow_type_group'):
                self.stroke_shadow_type_group.blockSignals(False)
            if hasattr(self, 'stroke_shadow_x_spinbox'):
                self.stroke_shadow_x_spinbox.blockSignals(False)
            if hasattr(self, 'stroke_shadow_y_spinbox'):
                self.stroke_shadow_y_spinbox.blockSignals(False)
            if hasattr(self, 'stroke_shadow_blur_spinbox'):
                self.stroke_shadow_blur_spinbox.blockSignals(False)
            if hasattr(self, 'stroke_shadow_size_spinbox'):
                self.stroke_shadow_size_spinbox.blockSignals(False)
            if hasattr(self, 'stroke_shadow_quality_combo'):
                self.stroke_shadow_quality_combo.blockSignals(False)
            if hasattr(self, 'stroke_shadow_opacity_slider'):
                self.stroke_shadow_opacity_slider.blockSignals(False)
            if hasattr(self, 'corner_radius_spinbox'):
                self.corner_radius_spinbox.blockSignals(False)
            if hasattr(self, 'shadow_opacity_slider'):
                self.shadow_opacity_slider.blockSignals(False)
        
    def show_properties(self):
        """Özellikleri göster"""
        self.setVisible(True)
        
        # Dolgu grubunu sadece gerektiğinde göster
        self.fill_group.setVisible(self.has_fillable_shapes)
        
        # Resim grubunu sadece gerektiğinde göster
        self.image_group.setVisible(self.has_image_shapes)
        
        # Grup işlemleri - çoklu seçim için
        multiple_selection = len(self.selected_strokes) > 1
        self.group_operations_group.setVisible(multiple_selection)
        
        # Hizalama araçları - çoklu seçim için
        self.alignment_group.setVisible(multiple_selection)
        
        # Şekil havuzu - herhangi bir seçim varsa
        any_selection = len(self.selected_strokes) > 0
        self.shape_library_group.setVisible(any_selection)
        
        # Buton durumlarını güncelle
        if multiple_selection:
            self.update_button_states()
    
    def update_button_states(self):
        """Buton durumlarını güncelle"""
        stroke_count = len(self.selected_strokes)
        
        # Grup durumunu kontrol et
        is_grouped = self.check_if_selection_is_grouped()
        
        # Grup işlemleri
        # Grupla butonu: 2+ seçili ve henüz gruplu değilse
        self.group_button.setEnabled(stroke_count >= 2 and not is_grouped)
        # Grup çöz butonu: en az 1 seçili ve gruplu ise
        self.ungroup_button.setEnabled(stroke_count >= 1 and is_grouped)
        
        # Hizalama (2+ nesne gerekli)
        align_enabled = stroke_count >= 2
        self.align_left_btn.setEnabled(align_enabled)
        self.align_right_btn.setEnabled(align_enabled)
        self.align_top_btn.setEnabled(align_enabled)
        self.align_bottom_btn.setEnabled(align_enabled)
        self.align_center_h_btn.setEnabled(align_enabled)
        self.align_center_v_btn.setEnabled(align_enabled)
        
        # Dağıtma (3+ nesne gerekli)
        distribute_enabled = stroke_count >= 3
        self.distribute_h_btn.setEnabled(distribute_enabled)
        self.distribute_v_btn.setEnabled(distribute_enabled)
    
    def check_if_selection_is_grouped(self):
        """Seçili stroke'ların hepsi aynı gruba ait mi kontrol et"""
        if len(self.selected_strokes) < 2:
            return False
            
        # İlk stroke'un grup ID'sini al
        if not self.selected_strokes or self.selected_strokes[0] >= len(self.stroke_data):
            return False
            
        first_stroke = self.stroke_data[self.selected_strokes[0]]
        first_group_id = self.get_stroke_group_id(first_stroke)
        
        if not first_group_id:
            return False
            
        # Diğer stroke'ların aynı grup ID'sine sahip olup olmadığını kontrol et
        for stroke_index in self.selected_strokes[1:]:
            if stroke_index >= len(self.stroke_data):
                continue
            stroke = self.stroke_data[stroke_index]
            group_id = self.get_stroke_group_id(stroke)
            if group_id != first_group_id:
                return False
                
        return True
    
    def get_stroke_group_id(self, stroke):
        """Stroke'un grup ID'sini al"""
        if hasattr(stroke, 'group_id'):
            return getattr(stroke, 'group_id', None)
        elif isinstance(stroke, dict):
            return stroke.get('group_id', None)
        return None
        
    def set_no_selection(self):
        """Hiçbir şey seçili değil"""
        self.selected_strokes = []
        self.stroke_data = []
        self.has_fillable_shapes = False
        self.has_bspline_shapes = False
        self.has_image_shapes = False
        self.has_rectangle_shapes = False
        self.has_circle_shapes = False
        self.has_stroke_shadow_shapes = False
        self.setVisible(False)

    def on_toggle_control_points(self):
        """Kontrol noktalarını göster/gizle"""
        self.toggleControlPoints.emit()
        
    def update_control_points_button(self, show_points):
        """Kontrol noktaları butonunu güncelle"""
        if show_points:
            self.toggle_control_points_button.setText("Noktaları Gizle")
        else:
            self.toggle_control_points_button.setText("Noktaları Göster")
        
 