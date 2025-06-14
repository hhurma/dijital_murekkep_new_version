import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QToolBar, QPushButton, 
                            QButtonGroup, QVBoxLayout, QWidget, QTabWidget, QHBoxLayout,
                            QMenuBar, QDockWidget)
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QAction, QIcon
import qtawesome as qta
from splash_screen import show_splash_screen
from DrawingWidget import DrawingWidget
from pdf_exporter import PDFExporter
from tab_manager import TabManager
from zoom_manager import ZoomWidget
from color_palette import ColorPalette
from line_width_widget import LineWidthWidget
from fill_widget import FillWidget
from fill_color_widget import FillColorWidget
from line_style_widget import LineStyleWidget
from background_widget import BackgroundWidget
from opacity_widget import OpacityWidget
from undo_redo_manager import UndoRedoManager
from settings_manager import SettingsManager
from session_manager import SessionManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Settings manager'ı başlat
        self.settings = SettingsManager()
        
        # Session manager'ı başlat
        self.session_manager = SessionManager()
        self.current_session_file = None  # Açık olan dosya yolu
        
        # PDF exporter'ı başlat
        self.pdf_exporter = PDFExporter(self)
        
        # Tab manager'ı başlat
        self.tab_manager = TabManager(self)
        
        self.setWindowTitle("Dijital Mürekkep - Çizim Uygulaması")
        
        # Uygulama ikonunu ayarla
        self.set_application_icon()
        
        # Ayarlardan pencere boyutunu yükle
        width, height = self.settings.get_window_size()
        self.setGeometry(100, 100, width, height)
        
        # Uygulama tam ekran açılsın
        self.showMaximized()

        # Ana widget ve layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Menü oluştur
        self.create_menu()
        
        # Toolbar oluştur
        self.create_toolbar()
        
        # Status bar oluştur
        self.create_status_bar()
        
        # Background dock widget oluştur
        self.create_background_dock()
        
        # Tab widget'ını layout'a ekle
        self.tab_widget = self.tab_manager.get_tab_widget()
        layout.addWidget(self.tab_widget)
        
        # İlk tab'ı oluştur
        self.tab_manager.create_new_tab()
        
        # Toolbar ile aktif tab arasında bağlantı kur
        self.connect_toolbar_to_active_tab()

    def create_toolbar(self):
        """Araç çubuğunu oluştur"""
        toolbar = QToolBar("Ana Araçlar")
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        toolbar.setIconSize(toolbar.iconSize() * 0.9)  # İkonları biraz küçült
        self.addToolBar(toolbar)
        
        # Dosya işlemleri
        new_tab_action = QAction(qta.icon('fa5s.plus', color='#4CAF50'), "Yeni Tab", self)
        new_tab_action.setToolTip("Yeni çizim tab'ı oluştur")
        new_tab_action.triggered.connect(lambda: self.tab_manager.create_new_tab())
        toolbar.addAction(new_tab_action)
        
        toolbar.addSeparator()
        
        # Çizim araçları
        self.bspline_action = QAction(qta.icon('fa5s.bezier-curve', color='#2196F3'), "B-Spline", self)
        self.bspline_action.setCheckable(True)
        self.bspline_action.setChecked(True)
        self.bspline_action.setToolTip("B-Spline eğri çizimi")
        self.bspline_action.triggered.connect(lambda: self.set_tool("bspline"))
        toolbar.addAction(self.bspline_action)
        
        self.freehand_action = QAction(qta.icon('fa5s.pencil-alt', color='#FF9800'), "Serbest Çizim", self)
        self.freehand_action.setCheckable(True)
        self.freehand_action.setToolTip("Serbest el çizimi")
        self.freehand_action.triggered.connect(lambda: self.set_tool("freehand"))
        toolbar.addAction(self.freehand_action)
        
        self.line_action = QAction(qta.icon('fa5s.minus', color='#607D8B'), "Düz Çizgi", self)
        self.line_action.setCheckable(True)
        self.line_action.setToolTip("Düz çizgi çizimi")
        self.line_action.triggered.connect(lambda: self.set_tool("line"))
        toolbar.addAction(self.line_action)
        
        self.rectangle_action = QAction(qta.icon('fa5s.square', color='#9C27B0'), "Dikdörtgen", self)
        self.rectangle_action.setCheckable(True)
        self.rectangle_action.setToolTip("Dikdörtgen çizimi")
        self.rectangle_action.triggered.connect(lambda: self.set_tool("rectangle"))
        toolbar.addAction(self.rectangle_action)
        
        self.circle_action = QAction(qta.icon('fa5s.circle', color='#E91E63'), "Çember", self)
        self.circle_action.setCheckable(True)
        self.circle_action.setToolTip("Çember çizimi")
        self.circle_action.triggered.connect(lambda: self.set_tool("circle"))
        toolbar.addAction(self.circle_action)
        
        toolbar.addSeparator()
        
        # Düzenleme araçları
        self.select_action = QAction(qta.icon('fa5s.mouse-pointer', color='#795548'), "Seçim", self)
        self.select_action.setCheckable(True)
        self.select_action.setToolTip("Nesne seçimi")
        self.select_action.triggered.connect(lambda: self.set_tool("select"))
        toolbar.addAction(self.select_action)
        
        self.move_action = QAction(qta.icon('fa5s.arrows-alt', color='#3F51B5'), "Taşıma", self)
        self.move_action.setCheckable(True)
        self.move_action.setToolTip("Nesne taşıma")
        self.move_action.triggered.connect(lambda: self.set_tool("move"))
        toolbar.addAction(self.move_action)
        
        self.rotate_action = QAction(qta.icon('fa5s.undo', color='#00BCD4'), "Döndürme", self)
        self.rotate_action.setCheckable(True)
        self.rotate_action.setToolTip("Nesne döndürme")
        self.rotate_action.triggered.connect(lambda: self.set_tool("rotate"))
        toolbar.addAction(self.rotate_action)
        
        self.scale_action = QAction(qta.icon('fa5s.expand-arrows-alt', color='#8BC34A'), "Boyutlandırma", self)
        self.scale_action.setCheckable(True)
        self.scale_action.setToolTip("Nesne boyutlandırma")
        self.scale_action.triggered.connect(lambda: self.set_tool("scale"))
        toolbar.addAction(self.scale_action)
        
        toolbar.addSeparator()
        
        # Zoom araçları
        self.zoom_in_action = QAction(qta.icon('fa5s.search-plus', color='#4CAF50'), "Yakınlaştır", self)
        self.zoom_in_action.setShortcut("Ctrl++")
        self.zoom_in_action.setToolTip("Yakınlaştır (Ctrl++)")
        self.zoom_in_action.triggered.connect(self.zoom_in)
        toolbar.addAction(self.zoom_in_action)
        
        self.zoom_out_action = QAction(qta.icon('fa5s.search-minus', color='#FF5722'), "Uzaklaştır", self)
        self.zoom_out_action.setShortcut("Ctrl+-")
        self.zoom_out_action.setToolTip("Uzaklaştır (Ctrl+-)")
        self.zoom_out_action.triggered.connect(self.zoom_out)
        toolbar.addAction(self.zoom_out_action)
        
        self.zoom_reset_action = QAction(qta.icon('fa5s.expand', color='#2196F3'), "Zoom Sıfırla", self)
        self.zoom_reset_action.setShortcut("Ctrl+0")
        self.zoom_reset_action.setToolTip("Zoom sıfırla (Ctrl+0)")
        self.zoom_reset_action.triggered.connect(self.zoom_reset)
        toolbar.addAction(self.zoom_reset_action)
        
        # Zoom widget
        self.zoom_widget = ZoomWidget()
        self.zoom_widget.zoomChanged.connect(self.on_zoom_changed)
        self.zoom_widget.panChanged.connect(self.on_pan_changed)
        toolbar.addWidget(self.zoom_widget)
        
        toolbar.addSeparator()
        
        # Undo/Redo
        self.undo_action = QAction(qta.icon('fa5s.undo', color='#FF9800'), "Geri Al", self)
        self.undo_action.setShortcut("Ctrl+Z")
        self.undo_action.setToolTip("Geri al (Ctrl+Z)")
        self.undo_action.triggered.connect(self.undo)
        self.undo_action.setEnabled(False)
        toolbar.addAction(self.undo_action)
        
        self.redo_action = QAction(qta.icon('fa5s.redo', color='#4CAF50'), "İleri Al", self)
        self.redo_action.setShortcut("Ctrl+Y")
        self.redo_action.setToolTip("İleri al (Ctrl+Y)")
        self.redo_action.triggered.connect(self.redo)
        self.redo_action.setEnabled(False)
        toolbar.addAction(self.redo_action)
        
        toolbar.addSeparator()
        
        # Color palette
        self.color_palette = ColorPalette()
        self.color_palette.set_settings_manager(self.settings)
        self.color_palette.colorSelected.connect(self.on_color_selected)
        self.color_palette.paletteChanged.connect(self.on_palette_changed)
        toolbar.addWidget(self.color_palette)
        
        toolbar.addSeparator()
        
        # Çizgi kalınlığı
        self.line_width_widget = LineWidthWidget()
        self.line_width_widget.widthChanged.connect(self.on_width_changed)
        toolbar.addWidget(self.line_width_widget)
        
        toolbar.addSeparator()
        
        # Fill/Dolgu
        self.fill_widget = FillWidget()
        self.fill_widget.fillChanged.connect(self.on_fill_changed)
        toolbar.addWidget(self.fill_widget)
        
        # Fill Color/Dolgu Rengi
        self.fill_color_widget = FillColorWidget()
        self.fill_color_widget.fillColorChanged.connect(self.on_fill_color_changed)
        toolbar.addWidget(self.fill_color_widget)
        
        # Line Style/Çizgi Stili
        self.line_style_widget = LineStyleWidget()
        self.line_style_widget.styleChanged.connect(self.on_line_style_changed)
        toolbar.addWidget(self.line_style_widget)
        
        # Opacity/Şeffaflık
        self.opacity_widget = OpacityWidget()
        self.opacity_widget.opacityChanged.connect(self.on_opacity_changed)
        toolbar.addWidget(self.opacity_widget)
        
        toolbar.addSeparator()
        
        # Diğer işlemler
        self.clear_action = QAction(qta.icon('fa5s.trash', color='#F44336'), "Temizle", self)
        self.clear_action.setToolTip("Aktif tab'ı temizle")
        self.clear_action.triggered.connect(self.clear_all)
        toolbar.addAction(self.clear_action)
        
    def create_menu(self):
        """Menü çubuğunu oluştur"""
        menubar = self.menuBar()
        
        # Dosya menüsü
        file_menu = menubar.addMenu("Dosya")
        
        # Oturum kaydetme
        save_session_action = QAction(qta.icon('fa5s.save', color='#4CAF50'), "Kaydet", self)
        save_session_action.setShortcut("Ctrl+S")
        save_session_action.setToolTip("Oturumu kaydet")
        save_session_action.triggered.connect(self.save_session)
        file_menu.addAction(save_session_action)
        
        # Farklı kaydet
        save_as_action = QAction(qta.icon('fa5s.save', color='#FF9800'), "Farklı Kaydet", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.setToolTip("Oturumu farklı dosya adıyla kaydet")
        save_as_action.triggered.connect(self.save_session_as)
        file_menu.addAction(save_as_action)
        
        # Oturum açma
        load_session_action = QAction(qta.icon('fa5s.folder-open', color='#2196F3'), "Oturum Aç", self)
        load_session_action.setShortcut("Ctrl+O")
        load_session_action.setToolTip("Kaydedilmiş oturumu aç")
        load_session_action.triggered.connect(self.load_session)
        file_menu.addAction(load_session_action)
        
        file_menu.addSeparator()
        
        # PDF dışa aktarma
        export_pdf_action = QAction(qta.icon('fa5s.file-pdf', color='#DC143C'), "PDF Olarak Dışa Aktar", self)
        export_pdf_action.setShortcut("Ctrl+E")
        export_pdf_action.setToolTip("Tüm sekmeleri PDF olarak dışa aktar")
        export_pdf_action.triggered.connect(self.export_to_pdf)
        file_menu.addAction(export_pdf_action)
        
        file_menu.addSeparator()
        
        # Son oturumlar
        recent_menu = file_menu.addMenu(qta.icon('fa5s.history', color='#FF9800'), "Son Oturumlar")
        self.update_recent_sessions_menu(recent_menu)
        
        # Görünüm menüsü
        view_menu = menubar.addMenu("Görünüm")
        
        # Arka plan ayarları
        background_action = QAction("Arka Plan Ayarları", self)
        background_action.triggered.connect(self.toggle_background_dock)
        view_menu.addAction(background_action)
        
        # Şekil havuzu
        shape_library_action = QAction("Şekil Havuzu", self)
        shape_library_action.triggered.connect(self.toggle_shape_library_dock)
        view_menu.addAction(shape_library_action)
        
    def create_status_bar(self):
        """Status bar oluştur"""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Hazır - Çizime başlayabilirsiniz", 3000)
        
        # Zoom bilgisi için permanent widget
        self.zoom_status_label = QPushButton("100%")
        self.zoom_status_label.setFlat(True)
        self.zoom_status_label.setMaximumWidth(60)
        self.zoom_status_label.clicked.connect(self.zoom_reset)
        self.status_bar.addPermanentWidget(self.zoom_status_label)
        
        # Aktif araç bilgisi
        self.tool_status_label = QPushButton("B-Spline")
        self.tool_status_label.setFlat(True)
        self.tool_status_label.setMaximumWidth(100)
        self.status_bar.addPermanentWidget(self.tool_status_label)
        
    def show_status_message(self, message, timeout=3000):
        """Status bar'da mesaj göster"""
        self.status_bar.showMessage(message, timeout)
        
    def update_zoom_status(self, zoom_level):
        """Zoom durumunu status bar'da güncelle"""
        self.zoom_status_label.setText(f"{int(zoom_level)}%")
        
    def update_tool_status(self, tool_name):
        """Aktif araç durumunu status bar'da güncelle"""
        tool_names = {
            "bspline": "B-Spline",
            "freehand": "Serbest",
            "line": "Düz Çizgi",
            "rectangle": "Dikdörtgen",
            "circle": "Çember",
            "select": "Seçim",
            "move": "Taşıma", 
            "rotate": "Döndürme",
            "scale": "Boyutlandırma"
        }
        display_name = tool_names.get(tool_name, tool_name)
        self.tool_status_label.setText(display_name)
        
    def create_background_dock(self):
        """Arka plan ayarları dock widget'ı oluştur"""
        self.background_dock = QDockWidget("Arka Plan Ayarları", self)
        self.background_widget = BackgroundWidget()
        self.background_widget.backgroundChanged.connect(self.on_background_changed)
        
        self.background_dock.setWidget(self.background_widget)
        self.background_dock.setFloating(False)
        self.background_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | 
                                        QDockWidget.DockWidgetFeature.DockWidgetClosable)
        
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.background_dock)
        
        # Dock görünürlüğünü ayarlardan yükle
        if self.settings.get_background_dock_visible():
            self.background_dock.show()
        else:
            self.background_dock.hide()
            
        # Şekil havuzu dock widget'ı oluştur
        self.create_shape_library_dock()
        
    def toggle_background_dock(self):
        """Arka plan dock widget'ını aç/kapat"""
        if self.background_dock.isVisible():
            self.background_dock.hide()
            self.settings.set_background_dock_visible(False)
        else:
            self.background_dock.show()
            self.settings.set_background_dock_visible(True)
        self.settings.save_settings()
        
    def create_shape_library_dock(self):
        """Şekil havuzu dock widget'ı oluştur"""
        from shape_library import ShapeLibraryWidget
        
        self.shape_library_dock = QDockWidget("Şekil Havuzu", self)
        self.shape_library_widget = ShapeLibraryWidget()
        
        # Şekil seçildiğinde canvas'a ekle
        self.shape_library_widget.shapeSelected.connect(self.add_shape_to_canvas)
        
        self.shape_library_dock.setWidget(self.shape_library_widget)
        self.shape_library_dock.setFloating(False)
        self.shape_library_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | 
                                           QDockWidget.DockWidgetFeature.DockWidgetClosable)
        
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.shape_library_dock)
        
        # Varsayılan olarak gizli
        self.shape_library_dock.hide()
        
    def toggle_shape_library_dock(self):
        """Şekil havuzu dock widget'ını aç/kapat"""
        if self.shape_library_dock.isVisible():
            self.shape_library_dock.hide()
        else:
            self.shape_library_dock.show()
            
    def add_shape_to_canvas(self, strokes):
        """Şekil havuzundan seçilen şekli canvas'a ekle"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and strokes:
            # Canvas merkezini world koordinatlarında hesapla
            canvas_center_x, canvas_center_y = self.transform_canvas_to_world(
                current_widget.width() // 2, 
                current_widget.height() // 2, 
                current_widget
            )
            
            # Şeklin merkez noktasını hesapla (zaten world koordinatlarında)
            if strokes:
                min_x = min_y = float('inf')
                max_x = max_y = float('-inf')
                
                for stroke in strokes:
                    # Stroke tipine göre point'leri al
                    points = self.get_stroke_points_for_bounds(stroke)
                    for x, y in points:
                        min_x = min(min_x, x)
                        max_x = max(max_x, x)
                        min_y = min(min_y, y)
                        max_y = max(max_y, y)
                
                # Şeklin merkezi
                shape_center_x = (min_x + max_x) / 2
                shape_center_y = (min_y + max_y) / 2
                
                # Offset hesapla
                offset_x = canvas_center_x - shape_center_x
                offset_y = canvas_center_y - shape_center_y
                
                # Undo için state kaydet
                current_widget.save_current_state("Add shape from library")
                
                # Stroke'ları offset ile ekle ve seçili yap
                added_stroke_indices = []
                for stroke in strokes:
                    new_stroke = self.apply_offset_to_stroke(stroke, offset_x, offset_y)
                    current_widget.strokes.append(new_stroke)
                    added_stroke_indices.append(len(current_widget.strokes) - 1)
                
                # Eklenen şekilleri seç
                current_widget.selection_tool.selected_strokes = added_stroke_indices
                
                # Seçim aracına geç
                current_widget.set_active_tool("select")
                self.set_tool("select")
                
                current_widget.update()

    def transform_canvas_to_world(self, canvas_x, canvas_y, drawing_widget):
        """Canvas koordinatlarını world koordinatlarına dönüştür"""
        if not hasattr(drawing_widget, 'zoom_level') or not hasattr(drawing_widget, 'zoom_offset'):
            return canvas_x, canvas_y
            
        zoom_level = getattr(drawing_widget, 'zoom_level', 1.0)
        zoom_offset = getattr(drawing_widget, 'zoom_offset', QPointF(0, 0))
        
        # Canvas koordinatlarını world koordinatlarına dönüştür
        world_x = (canvas_x - zoom_offset.x()) / zoom_level
        world_y = (canvas_y - zoom_offset.y()) / zoom_level
        
        return world_x, world_y
        
    def get_stroke_points_for_bounds(self, stroke):
        """Stroke'tan bounding hesaplama için point'leri al"""
        points = []
        
        if stroke['type'] == 'freehand':
            for point in stroke.get('points', []):
                if isinstance(point, dict):
                    points.append((point['x'], point['y']))
                    
        elif stroke['type'] == 'bspline':
            for cp in stroke.get('control_points', []):
                points.append((cp[0], cp[1]))
                
        elif stroke['type'] == 'line':
            if 'start_point' in stroke:
                points.append(stroke['start_point'])
            if 'end_point' in stroke:
                points.append(stroke['end_point'])
                
        elif stroke['type'] == 'rectangle':
            if 'corners' in stroke:
                points.extend(stroke['corners'])
            elif 'top_left' in stroke and 'bottom_right' in stroke:
                points.extend([stroke['top_left'], stroke['bottom_right']])
                
        elif stroke['type'] == 'circle':
            if 'center' in stroke:
                center = stroke['center']
                radius = stroke.get('radius', 0)
                # Çemberin bounding box'ını hesapla
                points.extend([
                    (center[0] - radius, center[1] - radius),
                    (center[0] + radius, center[1] + radius)
                ])
        
        return points
        
    def apply_offset_to_stroke(self, stroke, offset_x, offset_y):
        """Stroke'a offset uygula"""
        new_stroke = stroke.copy()
        
        if new_stroke['type'] == 'freehand':
            if 'points' in new_stroke:
                new_points = []
                for point in new_stroke['points']:
                    if isinstance(point, dict):
                        new_points.append({
                            'x': point['x'] + offset_x,
                            'y': point['y'] + offset_y
                        })
                    else:
                        new_points.append(point)  # Değiştirilmemiş bırak
                new_stroke['points'] = new_points
                
        elif new_stroke['type'] == 'bspline':
            if 'control_points' in new_stroke:
                new_control_points = []
                for cp in new_stroke['control_points']:
                    new_control_points.append([cp[0] + offset_x, cp[1] + offset_y])
                new_stroke['control_points'] = new_control_points
                
        elif new_stroke['type'] == 'line':
            if 'start_point' in new_stroke:
                start = new_stroke['start_point']
                new_stroke['start_point'] = (start[0] + offset_x, start[1] + offset_y)
            if 'end_point' in new_stroke:
                end = new_stroke['end_point']
                new_stroke['end_point'] = (end[0] + offset_x, end[1] + offset_y)
                
        elif new_stroke['type'] == 'rectangle':
            if 'corners' in new_stroke:
                new_corners = []
                for corner in new_stroke['corners']:
                    new_corners.append((corner[0] + offset_x, corner[1] + offset_y))
                new_stroke['corners'] = new_corners
            elif 'top_left' in new_stroke and 'bottom_right' in new_stroke:
                tl = new_stroke['top_left']
                br = new_stroke['bottom_right']
                new_stroke['top_left'] = (tl[0] + offset_x, tl[1] + offset_y)
                new_stroke['bottom_right'] = (br[0] + offset_x, br[1] + offset_y)
                
        elif new_stroke['type'] == 'circle':
            if 'center' in new_stroke:
                center = new_stroke['center']
                new_stroke['center'] = (center[0] + offset_x, center[1] + offset_y)
        
        return new_stroke

    def get_current_drawing_widget(self):
        """Aktif tab'daki drawing widget'ı al"""
        return self.tab_manager.get_current_drawing_widget()
        
    def connect_toolbar_to_active_tab(self):
        """Toolbar'ı aktif tab ile bağla"""
        current_widget = self.get_current_drawing_widget()
        if current_widget:
            current_widget.set_main_window(self)
        
    def set_tool(self, tool_name):
        """Aktif aracı değiştir"""
        # Diğer butonları deselect yap
        self.bspline_action.setChecked(tool_name == "bspline")
        self.freehand_action.setChecked(tool_name == "freehand")
        self.line_action.setChecked(tool_name == "line")
        self.rectangle_action.setChecked(tool_name == "rectangle")
        self.circle_action.setChecked(tool_name == "circle")
        self.select_action.setChecked(tool_name == "select")
        self.move_action.setChecked(tool_name == "move")
        self.rotate_action.setChecked(tool_name == "rotate")
        self.scale_action.setChecked(tool_name == "scale")
        
        # Aktif tab'daki drawing widget'a aktif aracı bildir
        current_widget = self.get_current_drawing_widget()
        if current_widget:
            current_widget.set_active_tool(tool_name)
            
        # Aktif aracı ayarlara kaydet
        self.settings.set_active_tool(tool_name)
        self.settings.save_settings()
        
        # Status bar'ı güncelle
        self.update_tool_status(tool_name)
        
    def on_color_selected(self, color):
        """Renk seçildiğinde aktif tab'a bildir"""
        current_widget = self.get_current_drawing_widget()
        if current_widget:
            current_widget.set_current_color(color)
            
        # Rengi ayarlara kaydet
        self.settings.set_drawing_color(color)
        self.settings.save_settings()
        
    def on_palette_changed(self):
        """Color palette değiştiğinde"""
        self.show_status_message("Renk paleti kaydedildi")
            
    def on_width_changed(self, width):
        """Çizgi kalınlığı değiştiğinde aktif tab'a bildir"""
        current_widget = self.get_current_drawing_widget()
        if current_widget:
            current_widget.set_current_width(width)
        
        # Kalınlığı ayarlara kaydet
        self.settings.set_line_width(width)
        self.settings.save_settings()
            
    def on_fill_changed(self, filled):
        """Fill durumu değiştiğinde aktif tab'a bildir"""
        current_widget = self.get_current_drawing_widget()
        if current_widget:
            current_widget.set_current_fill(filled)
        
        # Fill durumunu ayarlara kaydet
        self.settings.set_fill_enabled(filled)
        self.settings.save_settings()
            
    def on_opacity_changed(self, opacity):
        """Opacity değiştiğinde aktif tab'a bildir"""
        current_widget = self.get_current_drawing_widget()
        if current_widget:
            current_widget.set_current_opacity(opacity)
        
        # Opacity'yi ayarlara kaydet
        self.settings.set_opacity(opacity)
        self.settings.save_settings()
            
    def on_fill_color_changed(self, color):
        """Dolgu rengi değiştiğinde aktif tab'a bildir"""
        current_widget = self.get_current_drawing_widget()
        if current_widget:
            current_widget.set_fill_color(color)
        
        # Dolgu rengini ayarlara kaydet
        self.settings.set_fill_color(color)
        self.settings.save_settings()
            
    def on_line_style_changed(self, style):
        """Çizgi stili değiştiğinde aktif tab'a bildir"""
        current_widget = self.get_current_drawing_widget()
        if current_widget:
            current_widget.set_line_style(style)
        
        # Çizgi stilini ayarlara kaydet
        self.settings.set_line_style(style)
        self.settings.save_settings()
            
    def on_background_changed(self, settings):
        """Arka plan ayarları değiştiğinde aktif tab'a bildir"""
        current_widget = self.get_current_drawing_widget()
        if current_widget:
            current_widget.set_background_settings(settings)
        
        # Arka plan ayarlarını kaydet
        self.settings.set_background_settings(settings)
        self.settings.save_settings()
    
    def zoom_in(self):
        """Yakınlaştır"""
        self.zoom_widget.zoom_in()
    
    def zoom_out(self):
        """Uzaklaştır"""
        self.zoom_widget.zoom_out()
    
    def zoom_reset(self):
        """Zoom'u sıfırla"""
        self.zoom_widget.reset_zoom()
    
    def on_zoom_changed(self, zoom_level):
        """Zoom değiştiğinde aktif tab'a bildir"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and hasattr(current_widget, 'set_zoom_level'):
            current_widget.set_zoom_level(zoom_level)
        # Status bar zoom bilgisini güncelle
        self.update_zoom_status(zoom_level)
    
    def on_pan_changed(self, pan_offset):
        """Pan değiştiğinde aktif tab'a bildir"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and hasattr(current_widget, 'set_pan_offset'):
            current_widget.set_pan_offset(pan_offset)
            
    def undo(self):
        """Geri al"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and hasattr(current_widget, 'undo_manager'):
            current_widget.undo()
            
    def redo(self):
        """İleri al"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and hasattr(current_widget, 'undo_manager'):
            current_widget.redo()
            
    def clear_all(self):
        """Aktif tab'ı temizle"""
        current_widget = self.get_current_drawing_widget()
        if current_widget:
            current_widget.clear_all_strokes()
            self.show_status_message("Çizim alanı temizlendi")
            
    def load_settings_to_tab(self, drawing_widget):
        """Ayarları tab'a yükle"""
        # Çizim ayarları
        drawing_widget.set_current_color(self.settings.get_drawing_color())
        drawing_widget.set_current_width(self.settings.get_line_width())
        drawing_widget.set_current_fill(self.settings.get_fill_enabled())
        drawing_widget.set_fill_color(self.settings.get_fill_color())
        drawing_widget.set_current_opacity(self.settings.get_opacity())
        drawing_widget.set_line_style(self.settings.get_line_style())
        
        # Arka plan ayarları
        bg_settings = self.settings.get_background_settings()
        drawing_widget.set_background_settings(bg_settings)
        
        # UI widget'larını güncelle
        self.color_palette.load_from_settings()
        self.line_width_widget.set_width(self.settings.get_line_width())
        self.fill_widget.set_filled(self.settings.get_fill_enabled())
        self.fill_color_widget.set_fill_color(self.settings.get_fill_color())
        self.opacity_widget.set_opacity(self.settings.get_opacity())
        self.line_style_widget.set_style(self.settings.get_line_style())
        self.background_widget.set_background_settings(bg_settings)
        
    def save_session(self):
        """Oturumu kaydet (mevcut dosya varsa üzerine yaz)"""
        if self.current_session_file:
            # Mevcut dosya üzerine kaydet
            if self.session_manager.save_session(self, self.current_session_file):
                self.update_window_title()
        else:
            # İlk kez kaydetme - dosya adı sor
            self.save_session_as()
            
    def save_session_as(self):
        """Oturumu farklı kaydet"""
        filename = self.session_manager.save_session(self)
        if filename:
            self.current_session_file = filename
            self.update_window_title()
        
    def load_session(self):
        """Oturum aç"""
        filename = self.session_manager.load_session(self)
        if filename:
            self.current_session_file = filename
            self.update_window_title()
        
    def load_recent_session(self, filepath):
        """Son oturumlardan birini aç"""
        if self.session_manager.load_session(self, filepath):
            self.current_session_file = filepath
            self.update_window_title()
            
    def update_window_title(self):
        """Pencere başlığını güncelle"""
        base_title = "Dijital Mürekkep - Çizim Uygulaması"
        if self.current_session_file:
            import os
            filename = os.path.basename(self.current_session_file)
            self.setWindowTitle(f"{base_title} - {filename}")
        else:
            self.setWindowTitle(base_title)
        
    def update_recent_sessions_menu(self, menu):
        """Son oturumlar menüsünü güncelle"""
        menu.clear()
        recent_sessions = self.session_manager.get_recent_sessions()
        
        if not recent_sessions:
            no_sessions_action = QAction("Henüz oturum yok", self)
            no_sessions_action.setEnabled(False)
            menu.addAction(no_sessions_action)
            return
            
        for filepath, filename in recent_sessions:
            action = QAction(filename, self)
            action.setToolTip(filepath)
            action.triggered.connect(lambda checked, path=filepath: self.load_recent_session(path))
            menu.addAction(action)
    
    def set_application_icon(self):
        """Uygulama ikonunu ayarla"""
        icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            # Eğer icon.ico yoksa qtawesome'dan ikon kullan
            self.setWindowIcon(qta.icon('fa5s.paint-brush', color='#2196F3'))
    
    def export_to_pdf(self):
        """Tüm sekmeleri PDF olarak dışa aktar"""
        self.show_status_message("PDF dışa aktarılıyor...")
        success = self.pdf_exporter.export_to_pdf()
        if success:
            self.show_status_message("PDF başarıyla dışa aktarıldı")
        else:
            self.show_status_message("PDF dışa aktarma başarısız")
        
    def closeEvent(self, event):
        """Uygulama kapanırken ayarları kaydet"""
        # Otomatik oturum kaydetme
        self.session_manager.auto_save_session(self)
        
        # Pencere boyutunu kaydet
        self.settings.set_window_size(self.width(), self.height())
        
        # Background dock görünürlüğünü kaydet
        self.settings.set_background_dock_visible(self.background_dock.isVisible())
        
        # Ayarları kaydet
        self.settings.save_settings()
        
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Uygulama ikonunu ayarla
    icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Splash screen göster
    splash = show_splash_screen()
    
    # Ana pencereyi oluştur
    window = MainWindow()
    
    # Splash screen'i kapat ve ana pencereyi göster
    splash.finish_splash(window)
    window.show()
    
    sys.exit(app.exec())
