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
        
        # Seçilen şekil bilgileri
        self.selected_strokes = []
        self.stroke_data = []
        self.has_fillable_shapes = False  # Dikdörtgen/daire var mı
        self.has_bspline_shapes = False   # B-spline şekilleri var mı
        
        self.setup_ui()
        
    def setup_ui(self):
        """UI bileşenlerini oluştur"""
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
        self.toggle_control_points_button = QPushButton("Noktaları Düzenle")
        self.toggle_control_points_button.clicked.connect(self.on_toggle_control_points)
        bspline_layout.addWidget(self.toggle_control_points_button)
        
        self.bspline_group.setLayout(bspline_layout)
        layout.addWidget(self.bspline_group)
        self.bspline_group.setVisible(False)  # Başlangıçta gizli
        
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
        
        self.setLayout(layout)
        
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
        
        if not self.stroke_data or not self.selected_strokes:
            return
            
        for index in self.selected_strokes:
            if index < len(self.stroke_data):
                stroke = self.stroke_data[index]
                
                # Image stroke kontrolü
                if hasattr(stroke, 'stroke_type'):
                    continue
                    
                # Doldurulabilir şekilleri kontrol et
                if stroke.get('type') in ['rectangle', 'circle'] or stroke.get('tool_type') in ['rectangle', 'circle']:
                    self.has_fillable_shapes = True
                    
                # B-spline şekillerini kontrol et
                if stroke.get('type') == 'bspline' or stroke.get('tool_type') == 'bspline':
                    self.has_bspline_shapes = True
        
        # Dolgu özelliklerini göster/gizle
        self.fill_group.setVisible(self.has_fillable_shapes)
        
        # B-spline özelliklerini göster/gizle
        self.bspline_group.setVisible(self.has_bspline_shapes)
        
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
        
        # Renk analizi - ortak renk varsa kullan, yoksa ilk stroke'un rengini kullan
        colors = []
        for stroke in strokes:
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
        for stroke in strokes:
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
        for stroke in strokes:
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
        
        # Dolgu özellikleri analizi (sadece fillable shapes varsa)
        if self.has_fillable_shapes:
            fillable_strokes = [s for s in strokes if s['type'] in ['rectangle', 'circle']]
            
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
                    
    def update_ui_values(self):
        """UI değerlerini güncelle - sinyalleri geçici olarak kes"""
        # Sinyalleri geçici olarak kes
        self.width_spinbox.blockSignals(True)
        self.style_combo.blockSignals(True)
        self.fill_checkbox.blockSignals(True)
        self.fill_opacity_slider.blockSignals(True)
        
        try:
            # Renk butonlarını güncelle
            self.update_color_button()
            self.update_fill_color_button()
            
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
        finally:
            # Sinyalleri tekrar aktif et
            self.width_spinbox.blockSignals(False)
            self.style_combo.blockSignals(False)
            self.fill_checkbox.blockSignals(False)
            self.fill_opacity_slider.blockSignals(False)
        
    def show_properties(self):
        """Özellikleri göster"""
        self.setVisible(True)
        
        # Dolgu grubunu sadece gerektiğinde göster
        self.fill_group.setVisible(self.has_fillable_shapes)
        
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
        self.setVisible(False)

    def on_toggle_control_points(self):
        """Kontrol noktalarını göster/gizle"""
        self.toggleControlPoints.emit()
        
    def analyze_selected_strokes(self):
        """Seçilen stroke'ları analiz et ve UI'ı güncelle"""
        self.has_fillable_shapes = False
        self.has_bspline_shapes = False
        
        if not self.stroke_data or not self.selected_strokes:
            return
            
        for index in self.selected_strokes:
            if index < len(self.stroke_data):
                stroke = self.stroke_data[index]
                
                # Image stroke kontrolü
                if hasattr(stroke, 'stroke_type'):
                    continue
                    
                # Doldurulabilir şekilleri kontrol et
                if stroke.get('type') in ['rectangle', 'circle'] or stroke.get('tool_type') in ['rectangle', 'circle']:
                    self.has_fillable_shapes = True
                    
                # B-spline şekillerini kontrol et
                if stroke.get('type') == 'bspline' or stroke.get('tool_type') == 'bspline':
                    self.has_bspline_shapes = True
                    
        # Dolgu özelliklerini göster/gizle
        self.fill_group.setVisible(self.has_fillable_shapes)
        
        # B-spline özelliklerini göster/gizle
        self.bspline_group.setVisible(self.has_bspline_shapes)
        
        # Ortak özellikleri analiz et
        if self.selected_strokes:
            self.analyze_common_properties([self.stroke_data[i] for i in self.selected_strokes if i < len(self.stroke_data)])
            
        self.update_ui_values()
        self.update_button_states() 