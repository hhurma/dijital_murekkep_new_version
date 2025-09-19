import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QPushButton,
    QButtonGroup, QVBoxLayout, QWidget, QTabWidget, QHBoxLayout,
    QMenuBar, QDockWidget, QMessageBox, QFileDialog, QInputDialog, QSpinBox
)
from PyQt6.QtCore import Qt, QPointF, QTimer
from PyQt6.QtGui import QAction, QIcon, QActionGroup, QKeySequence, QImage, QPainter
import qtawesome as qta
from splash_screen import show_splash_screen
from DrawingWidget import DrawingWidget
from pdf_exporter import PDFExporter
from tab_manager import TabManager
from color_palette import ColorPalette
from line_width_widget import LineWidthWidget
from settings_manager import SettingsManager
from session_manager import SessionManager
from shape_properties_widget import ShapePropertiesWidget
from layer_manager_widget import LayerManagerWidget
from pdf_importer import PDFImporter

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Settings manager'ı başlat
        self.settings = SettingsManager()

        # PDF importer'ı başlat
        self.pdf_importer = PDFImporter()
        self.default_pdf_dpi = 150
        self.last_opened_pdf_dir = os.path.expanduser("~")

        # Session manager'ı başlat
        self.session_manager = SessionManager()
        self.session_manager.set_pdf_importer(self.pdf_importer)
        self.current_session_file = None  # Açık olan dosya yolu
        self._setup_autosave_timer()
        
        # PDF exporter'ı başlat
        self.pdf_exporter = PDFExporter(self)
        
        # Tab manager'ı başlat
        self.tab_manager = TabManager(self)
        
        # Resim cache klasörü
        self.image_cache_dir = os.path.join(os.path.dirname(__file__), "image_cache")
        self.cached_images = {}  # Hash -> cache path mapping
        
        # Threaded image cache manager
        from image_cache_manager import ImageCacheManager
        self.image_cache_manager = ImageCacheManager(self.image_cache_dir, max_workers=2)
        self.image_cache_manager.imageLoaded.connect(self.on_image_loaded)
        
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
        
        # Shape properties dock widget oluştur
        self.create_shape_properties_dock()

        # Layer manager dock widget oluştur
        self.create_layer_dock()

        # Tab widget'ını layout'a ekle
        self.tab_widget = self.tab_manager.get_tab_widget()
        layout.addWidget(self.tab_widget)
        
        # İlk tab'ı oluştur
        self.tab_manager.create_new_tab()
        
        # Toolbar ile aktif tab arasında bağlantı kur
        self.connect_toolbar_to_active_tab()

        # Clipboard için
        self.clipboard_strokes = []  # Kopyalanan/kesilen stroke'lar
        self.clipboard_offset = QPointF(20, 20)  # Yapıştırma offseti
        
        # Actions'ları ayarla
        self.setup_actions()
        
        # Menü çubuğunu oluştur
        self.setup_menubar()

        # Otomatik kayıt varsa kullanıcıya sor
        QTimer.singleShot(0, self._prompt_auto_save_restore)
        
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

        # PDF navigasyon kontrolleri
        self.pdf_prev_action = QAction(qta.icon('fa5s.arrow-left', color='#607D8B'), "Önceki PDF Sayfası", self)
        self.pdf_prev_action.setToolTip("PDF arka planında önceki sayfa")
        self.pdf_prev_action.triggered.connect(self.go_to_previous_pdf_page)
        self.pdf_prev_action.setEnabled(False)
        toolbar.addAction(self.pdf_prev_action)

        self.pdf_next_action = QAction(qta.icon('fa5s.arrow-right', color='#607D8B'), "Sonraki PDF Sayfası", self)
        self.pdf_next_action.setToolTip("PDF arka planında sonraki sayfa")
        self.pdf_next_action.triggered.connect(self.go_to_next_pdf_page)
        self.pdf_next_action.setEnabled(False)
        toolbar.addAction(self.pdf_next_action)

        self.pdf_dpi_action = QAction(qta.icon('fa5s.cog', color='#9C27B0'), "PDF Çözünürlüğü", self)
        self.pdf_dpi_action.setToolTip("PDF sayfalarının çözünürlüğünü (DPI) ayarla")
        self.pdf_dpi_action.triggered.connect(self.prompt_pdf_resolution_change)
        self.pdf_dpi_action.setEnabled(False)
        toolbar.addAction(self.pdf_dpi_action)

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
        

        
        toolbar.addSeparator()
        
        # Kes/Kopyala/Yapıştır/Sil butonları
        copy_action_toolbar = QAction(qta.icon('fa5s.copy', color='#2196F3'), "Kopyala", self)
        copy_action_toolbar.setShortcut("Ctrl+C")
        copy_action_toolbar.setToolTip("Seçili öğeleri kopyala (Ctrl+C)")
        copy_action_toolbar.triggered.connect(self.copy_selected_strokes)
        toolbar.addAction(copy_action_toolbar)
        
        cut_action_toolbar = QAction(qta.icon('fa5s.cut', color='#FF9800'), "Kes", self)
        cut_action_toolbar.setShortcut("Ctrl+X")
        cut_action_toolbar.setToolTip("Seçili öğeleri kes (Ctrl+X)")
        cut_action_toolbar.triggered.connect(self.cut_selected_strokes)
        toolbar.addAction(cut_action_toolbar)
        
        paste_action_toolbar = QAction(qta.icon('fa5s.paste', color='#4CAF50'), "Yapıştır", self)
        paste_action_toolbar.setShortcut("Ctrl+V")
        paste_action_toolbar.setToolTip("Clipboard'dan yapıştır (Ctrl+V)")
        paste_action_toolbar.triggered.connect(self.paste_strokes)
        toolbar.addAction(paste_action_toolbar)
        
        delete_action_toolbar = QAction(qta.icon('fa5s.times', color='#F44336'), "Sil", self)
        delete_action_toolbar.setShortcut("Del")
        delete_action_toolbar.setToolTip("Seçili öğeleri sil (Del)")
        delete_action_toolbar.triggered.connect(self.delete_selected_strokes)
        toolbar.addAction(delete_action_toolbar)
        
        toolbar.addSeparator()
        
        # Diğer işlemler
        self.clear_action = QAction(qta.icon('fa5s.trash-alt', color='#F44336'), "Temizle", self)
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

        # PDF açma
        open_pdf_action = QAction(qta.icon('fa5s.file-pdf', color='#9C27B0'), "PDF Aç", self)
        open_pdf_action.setShortcut("Ctrl+Alt+O")
        open_pdf_action.setToolTip("PDF dosyasını arka plan olarak yükle")
        open_pdf_action.triggered.connect(self.open_pdf)
        file_menu.addAction(open_pdf_action)

        self.save_pdf_action = QAction(qta.icon('fa5s.save', color='#C62828'), "PDF'yi Kaydet", self)
        self.save_pdf_action.setToolTip("PDF arka planını kaynağına kaydet")
        self.save_pdf_action.setEnabled(False)
        self.save_pdf_action.triggered.connect(self.save_pdf_to_source)
        file_menu.addAction(self.save_pdf_action)

        file_menu.addSeparator()

        # Resim import
        import_image_action = QAction(qta.icon('fa5s.image', color='#4CAF50'), "Resim Ekle", self)
        import_image_action.setShortcut("Ctrl+I")
        import_image_action.setToolTip("Canvas'a resim ekle")
        import_image_action.triggered.connect(self.import_image)
        file_menu.addAction(import_image_action)
        
        file_menu.addSeparator()

        # Resim dışa aktarma
        export_image_action = QAction(
            qta.icon('fa5s.file-image', color='#009688'),
            "Resim Olarak Dışa Aktar",
            self
        )
        export_image_action.setShortcut("Ctrl+Shift+E")
        export_image_action.setToolTip("Aktif sekmeyi resim olarak dışa aktar")
        export_image_action.triggered.connect(self.export_current_tab_as_image)
        file_menu.addAction(export_image_action)

        # PDF dışa aktarma
        export_pdf_action = QAction(qta.icon('fa5s.file-pdf', color='#DC143C'), "PDF Olarak Dışa Aktar", self)
        export_pdf_action.setShortcut("Ctrl+E")
        export_pdf_action.setToolTip("Tüm sekmeleri PDF olarak dışa aktar")
        export_pdf_action.triggered.connect(self.export_to_pdf)
        file_menu.addAction(export_pdf_action)
        
        # Geçerli sekmeyi PDF'ye kaydet (PDF arka planının TÜM sayfaları)
        export_pdf_pages_action = QAction(qta.icon('fa5s.file-pdf', color='#F44336'), "PDF'ye Kaydet (Bu Sekme)", self)
        export_pdf_pages_action.setShortcut("Ctrl+Alt+E")
        export_pdf_pages_action.setToolTip("Geçerli sekmenin PDF arka planındaki tüm sayfaları tek PDF'e kaydet")
        export_pdf_pages_action.triggered.connect(self.export_current_tab_with_pdf_pages)
        file_menu.addAction(export_pdf_pages_action)
        
        file_menu.addSeparator()
        
        # Son oturumlar
        recent_menu = file_menu.addMenu(qta.icon('fa5s.history', color='#FF9800'), "Son Oturumlar")
        self.update_recent_sessions_menu(recent_menu)
        
        # Görünüm menüsü
        view_menu = menubar.addMenu("Görünüm")
        
        # Ayarlar
        settings_action = QAction("Ayarlar", self)
        settings_action.triggered.connect(self.toggle_background_dock)
        view_menu.addAction(settings_action)
        
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

        self.pdf_page_selector = QSpinBox()
        self.pdf_page_selector.setEnabled(False)
        self.pdf_page_selector.setRange(0, 0)
        self.pdf_page_selector.setSpecialValueText("PDF: Yok")
        self.pdf_page_selector.setMaximumWidth(180)
        self.pdf_page_selector.valueChanged.connect(self.on_pdf_page_selector_changed)
        self.status_bar.addPermanentWidget(self.pdf_page_selector)
        
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

    def update_pdf_controls_state(self):
        """PDF navigasyon ve durum kontrollerini güncelle"""
        if not hasattr(self, 'pdf_prev_action'):
            return

        current_widget = self.get_current_drawing_widget()
        has_pdf = bool(current_widget and hasattr(current_widget, 'has_pdf_background') and current_widget.has_pdf_background())
        can_prev = False
        can_next = False
        status_text = "PDF: Yok"
        layer = None

        if has_pdf:
            layer = current_widget.get_pdf_background_layer()
            if layer:
                can_prev = layer.current_page > 0
                can_next = layer.current_page < (layer.page_count - 1)
                status_text = f"PDF: {layer.current_page + 1}/{layer.page_count} ({layer.dpi} DPI)"
                self.default_pdf_dpi = layer.dpi

        self.pdf_prev_action.setEnabled(can_prev)
        self.pdf_next_action.setEnabled(can_next)
        self.pdf_dpi_action.setEnabled(has_pdf)
        if hasattr(self, 'save_pdf_action'):
            has_target = bool(has_pdf and layer and getattr(layer, 'source_path', None))
            self.save_pdf_action.setEnabled(has_target)
            if has_target:
                base_name = os.path.basename(layer.source_path)
                self.save_pdf_action.setToolTip(f"PDF arka planını kaynağına kaydet ({base_name})")
            else:
                self.save_pdf_action.setToolTip("PDF arka planını kaynağına kaydet")

        page_selector = getattr(self, 'pdf_page_selector', None)
        if not page_selector:
            return

        if has_pdf and layer:
            page_selector.blockSignals(True)
            page_selector.setEnabled(True)
            page_selector.setPrefix("PDF ")
            page_selector.setSpecialValueText("")
            page_selector.setRange(1, layer.page_count)
            page_selector.setSuffix(f"/{layer.page_count} ({layer.dpi} DPI)")
            page_selector.setValue(layer.current_page + 1)
            page_selector.blockSignals(False)
            page_selector.setToolTip(status_text)
        else:
            page_selector.blockSignals(True)
            page_selector.setEnabled(False)
            page_selector.setPrefix("")
            page_selector.setSuffix("")
            page_selector.setRange(0, 0)
            page_selector.setSpecialValueText(status_text)
            page_selector.setValue(0)
            page_selector.blockSignals(False)
            page_selector.setToolTip(status_text)

    def on_pdf_page_selector_changed(self, page_number):
        """PDF sayfa seçicisi değiştiğinde ilgili PDF sayfasına geç"""
        current_widget = self.get_current_drawing_widget()
        if not current_widget or not current_widget.has_pdf_background():
            return

        layer = current_widget.get_pdf_background_layer()
        if not layer:
            return

        target_index = page_number - 1
        if target_index == layer.current_page:
            return

        if current_widget.go_to_pdf_page(target_index):
            self.show_status_message(
                f"PDF sayfası: {layer.current_page + 1}/{layer.page_count}"
            )

        self.update_pdf_controls_state()
        
    def create_background_dock(self):
        """Ayarlar dock widget'ı oluştur"""
        from settings_widget import SettingsWidget
        
        self.settings_dock = QDockWidget("Ayarlar", self)
        self.settings_widget = SettingsWidget()
        
        # Sinyalleri bağla
        self.settings_widget.backgroundChanged.connect(self.on_background_changed)
        self.settings_widget.pdfOrientationChanged.connect(self.on_pdf_orientation_changed)
        self.settings_widget.canvasOrientationChanged.connect(self.on_canvas_orientation_changed)
        self.settings_widget.canvasSizeChanged.connect(self.on_canvas_size_changed)
        
        self.settings_dock.setWidget(self.settings_widget)
        self.settings_dock.setFloating(False)
        self.settings_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | 
                                      QDockWidget.DockWidgetFeature.DockWidgetClosable)
        
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.settings_dock)
        
        # Dock görünürlüğünü ayarlardan yükle
        if self.settings.get_background_dock_visible():
            self.settings_dock.show()
        else:
            self.settings_dock.hide()
            
        # Şekil havuzu dock widget'ı oluştur
        self.create_shape_library_dock()
        
    def toggle_background_dock(self):
        """Ayarlar dock widget'ını aç/kapat"""
        if self.settings_dock.isVisible():
            self.settings_dock.hide()
            self.settings.set_background_dock_visible(False)
        else:
            self.settings_dock.show()
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
        
    def create_shape_properties_dock(self):
        """Şekil özellikleri dock widget'ı oluştur"""
        self.shape_properties_dock = QDockWidget("Şekil Özellikleri", self)
        self.shape_properties_widget = ShapePropertiesWidget()

        dock_width = self.shape_properties_widget.PANEL_WIDTH
        self.shape_properties_dock.setMinimumWidth(dock_width)
        self.shape_properties_dock.setMaximumWidth(dock_width)

        # Sinyalleri bağla
        self.shape_properties_widget.colorChanged.connect(self.on_shape_color_changed)
        self.shape_properties_widget.widthChanged.connect(self.on_shape_width_changed)
        self.shape_properties_widget.lineStyleChanged.connect(self.on_shape_line_style_changed)
        self.shape_properties_widget.fillColorChanged.connect(self.on_shape_fill_color_changed)
        self.shape_properties_widget.fillEnabledChanged.connect(self.on_shape_fill_enabled_changed)
        self.shape_properties_widget.fillOpacityChanged.connect(self.on_shape_fill_opacity_changed)
        
        # Resim özellikleri sinyalleri
        self.shape_properties_widget.imageOpacityChanged.connect(self.on_image_opacity_changed)
        self.shape_properties_widget.imageBorderEnabledChanged.connect(self.on_image_border_enabled_changed)
        self.shape_properties_widget.imageBorderColorChanged.connect(self.on_image_border_color_changed)
        self.shape_properties_widget.imageBorderWidthChanged.connect(self.on_image_border_width_changed)
        self.shape_properties_widget.imageBorderStyleChanged.connect(self.on_image_border_style_changed)
        self.shape_properties_widget.imageShadowEnabledChanged.connect(self.on_image_shadow_enabled_changed)
        self.shape_properties_widget.imageShadowColorChanged.connect(self.on_image_shadow_color_changed)
        self.shape_properties_widget.imageShadowOffsetChanged.connect(self.on_image_shadow_offset_changed)
        self.shape_properties_widget.imageShadowBlurChanged.connect(self.on_image_shadow_blur_changed)
        self.shape_properties_widget.imageShadowSizeChanged.connect(self.on_image_shadow_size_changed)
        self.shape_properties_widget.imageShadowInnerChanged.connect(self.on_image_shadow_inner_changed)
        self.shape_properties_widget.imageShadowQualityChanged.connect(self.on_image_shadow_quality_changed)
        self.shape_properties_widget.imageFilterChanged.connect(self.on_image_filter_changed)
        self.shape_properties_widget.imageTransparencyChanged.connect(self.on_image_transparency_changed)
        self.shape_properties_widget.imageBlurChanged.connect(self.on_image_blur_changed)
        self.shape_properties_widget.imageCornerRadiusChanged.connect(self.on_image_corner_radius_changed)
        self.shape_properties_widget.imageShadowOpacityChanged.connect(self.on_image_shadow_opacity_changed)
        
        # Dikdörtgen özellikleri sinyalleri
        self.shape_properties_widget.rectangleCornerRadiusChanged.connect(self.on_rectangle_corner_radius_changed)
        self.shape_properties_widget.rectangleShadowEnabledChanged.connect(self.on_rectangle_shadow_enabled_changed)
        self.shape_properties_widget.rectangleShadowColorChanged.connect(self.on_rectangle_shadow_color_changed)
        self.shape_properties_widget.rectangleShadowOffsetChanged.connect(self.on_rectangle_shadow_offset_changed)
        self.shape_properties_widget.rectangleShadowBlurChanged.connect(self.on_rectangle_shadow_blur_changed)
        self.shape_properties_widget.rectangleShadowSizeChanged.connect(self.on_rectangle_shadow_size_changed)
        self.shape_properties_widget.rectangleShadowOpacityChanged.connect(self.on_rectangle_shadow_opacity_changed)
        self.shape_properties_widget.rectangleShadowInnerChanged.connect(self.on_rectangle_shadow_inner_changed)
        self.shape_properties_widget.rectangleShadowQualityChanged.connect(self.on_rectangle_shadow_quality_changed)
        
        # Çember özellikleri sinyalleri
        self.shape_properties_widget.circleShadowEnabledChanged.connect(self.on_circle_shadow_enabled_changed)
        self.shape_properties_widget.circleShadowColorChanged.connect(self.on_circle_shadow_color_changed)
        self.shape_properties_widget.circleShadowOffsetChanged.connect(self.on_circle_shadow_offset_changed)
        self.shape_properties_widget.circleShadowBlurChanged.connect(self.on_circle_shadow_blur_changed)
        self.shape_properties_widget.circleShadowSizeChanged.connect(self.on_circle_shadow_size_changed)
        self.shape_properties_widget.circleShadowOpacityChanged.connect(self.on_circle_shadow_opacity_changed)
        self.shape_properties_widget.circleShadowInnerChanged.connect(self.on_circle_shadow_inner_changed)
        self.shape_properties_widget.circleShadowQualityChanged.connect(self.on_circle_shadow_quality_changed)

        # Çizgi gölge özellikleri sinyalleri
        self.shape_properties_widget.strokeShadowEnabledChanged.connect(self.on_stroke_shadow_enabled_changed)
        self.shape_properties_widget.strokeShadowColorChanged.connect(self.on_stroke_shadow_color_changed)
        self.shape_properties_widget.strokeShadowOffsetChanged.connect(self.on_stroke_shadow_offset_changed)
        self.shape_properties_widget.strokeShadowBlurChanged.connect(self.on_stroke_shadow_blur_changed)
        self.shape_properties_widget.strokeShadowSizeChanged.connect(self.on_stroke_shadow_size_changed)
        self.shape_properties_widget.strokeShadowOpacityChanged.connect(self.on_stroke_shadow_opacity_changed)
        self.shape_properties_widget.strokeShadowInnerChanged.connect(self.on_stroke_shadow_inner_changed)
        self.shape_properties_widget.strokeShadowQualityChanged.connect(self.on_stroke_shadow_quality_changed)
        
        # Grup işlemi sinyalleri
        self.shape_properties_widget.groupShapes.connect(self.on_group_shapes)
        self.shape_properties_widget.ungroupShapes.connect(self.on_ungroup_shapes)
        
        # Hizalama sinyalleri
        self.shape_properties_widget.alignLeft.connect(self.on_align_left)
        self.shape_properties_widget.alignRight.connect(self.on_align_right)
        self.shape_properties_widget.alignTop.connect(self.on_align_top)
        self.shape_properties_widget.alignBottom.connect(self.on_align_bottom)
        self.shape_properties_widget.alignCenterH.connect(self.on_align_center_h)
        self.shape_properties_widget.alignCenterV.connect(self.on_align_center_v)
        self.shape_properties_widget.distributeH.connect(self.on_distribute_h)
        self.shape_properties_widget.distributeV.connect(self.on_distribute_v)
        
        # Şekil havuzu sinyali
        self.shape_properties_widget.addToShapeLibrary.connect(self.on_add_selected_to_shape_library)
        
        # B-spline kontrol noktaları sinyali
        self.shape_properties_widget.toggleControlPoints.connect(self.on_toggle_control_points)
        
        self.shape_properties_dock.setWidget(self.shape_properties_widget)
        self.shape_properties_dock.setFloating(False)
        self.shape_properties_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | 
                                              QDockWidget.DockWidgetFeature.DockWidgetClosable)
        
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.shape_properties_dock)

        # Başlangıçta gizli, resim seçildiğinde görünür olacak
        self.shape_properties_dock.setVisible(False)

    def create_layer_dock(self):
        """Katman yöneticisi dock widget'ını oluştur"""
        self.layer_dock = QDockWidget("Katmanlar", self)
        self.layer_manager_widget = LayerManagerWidget()
        self.layer_dock.setWidget(self.layer_manager_widget)
        self.layer_dock.setFloating(False)
        self.layer_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable |
                                     QDockWidget.DockWidgetFeature.DockWidgetClosable)

        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.layer_dock)
        
    def toggle_shape_properties_dock(self):
        """Şekil özellikleri dock widget'ını aç/kapat"""
        if self.shape_properties_dock.isVisible():
            self.shape_properties_dock.hide()
        else:
            self.shape_properties_dock.show()
        
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
        if hasattr(self, 'layer_manager_widget'):
            self.layer_manager_widget.set_drawing_widget(current_widget)
        self.update_pdf_controls_state()

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
    
    def on_shape_color_changed(self, color):
        """Seçilen şekillerin rengini değiştir"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and current_widget.selection_tool.selected_strokes:
            # Undo için state kaydet
            current_widget.save_current_state("Change shape color")
            
            # Seçilen şekillerin rengini değiştir
            for stroke_index in current_widget.selection_tool.selected_strokes:
                if stroke_index < len(current_widget.strokes):
                    stroke = current_widget.strokes[stroke_index]
                    # Image stroke'ları atla
                    if hasattr(stroke, 'stroke_type') and stroke.stroke_type == 'image':
                        continue
                    # Eski stroke formatı kontrolü
                    if 'type' not in stroke:
                        continue
                    stroke['color'] = color
            
            current_widget.update()
            self.show_status_message("Şekil rengi değiştirildi")
    
    def on_shape_width_changed(self, width):
        """Seçilen şekillerin kalınlığını değiştir"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and current_widget.selection_tool.selected_strokes:
            # Undo için state kaydet
            current_widget.save_current_state("Change shape width")
            
            # Seçilen şekillerin kalınlığını değiştir
            for stroke_index in current_widget.selection_tool.selected_strokes:
                if stroke_index < len(current_widget.strokes):
                    stroke = current_widget.strokes[stroke_index]
                    # Image stroke'ları atla
                    if hasattr(stroke, 'stroke_type') and stroke.stroke_type == 'image':
                        continue
                    # Eski stroke formatı kontrolü
                    if 'type' not in stroke:
                        continue
                    
                    # Stroke tipine göre doğru field'ı kullan
                    if stroke['type'] in ['rectangle', 'circle']:
                        stroke['line_width'] = width
                    else:
                        # Line, bspline, freehand için 'width' kullan
                        stroke['width'] = width
            
            current_widget.update()
            self.show_status_message("Şekil kalınlığı değiştirildi")
    
    def on_shape_line_style_changed(self, line_style):
        """Seçilen şekillerin çizgi stilini değiştir"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and current_widget.selection_tool.selected_strokes:
            # Undo için state kaydet
            current_widget.save_current_state("Change shape line style")
            
            # Seçilen şekillerin çizgi stilini değiştir
            for stroke_index in current_widget.selection_tool.selected_strokes:
                if stroke_index < len(current_widget.strokes):
                    stroke = current_widget.strokes[stroke_index]
                    # Image stroke'ları atla
                    if hasattr(stroke, 'stroke_type') and stroke.stroke_type == 'image':
                        continue
                    # Eski stroke formatı kontrolü
                    if 'type' not in stroke:
                        continue
                    
                    # Stroke tipine göre doğru field'ı kullan
                    if stroke['type'] in ['rectangle', 'circle']:
                        stroke['line_style'] = line_style
                    else:
                        # Line, bspline, freehand için 'style' kullan
                        stroke['style'] = line_style
            
            current_widget.update()
            self.show_status_message("Şekil çizgi stili değiştirildi")
    
    def on_shape_fill_color_changed(self, color):
        """Seçilen şekillerin dolgu rengini değiştir"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and current_widget.selection_tool.selected_strokes:
            # Undo için state kaydet
            current_widget.save_current_state("Change shape fill color")
            
            # Sadece dikdörtgen ve daire şekillerini değiştir
            for stroke_index in current_widget.selection_tool.selected_strokes:
                if stroke_index < len(current_widget.strokes):
                    stroke = current_widget.strokes[stroke_index]
                    # Image stroke'ları atla
                    if hasattr(stroke, 'stroke_type') and stroke.stroke_type == 'image':
                        continue
                    # Eski stroke formatı kontrolü
                    if 'type' not in stroke:
                        continue
                    # Sadece dikdörtgen ve daire için
                    if stroke['type'] in ['rectangle', 'circle']:
                        stroke['fill_color'] = color
            
            current_widget.update()
            self.show_status_message("Şekil dolgu rengi değiştirildi")
    
    def on_shape_fill_enabled_changed(self, enabled):
        """Seçilen şekillerin dolgu durumunu değiştir"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and current_widget.selection_tool.selected_strokes:
            # Undo için state kaydet
            current_widget.save_current_state("Change shape fill enabled")
            
            # Sadece dikdörtgen ve daire şekillerini değiştir
            for stroke_index in current_widget.selection_tool.selected_strokes:
                if stroke_index < len(current_widget.strokes):
                    stroke = current_widget.strokes[stroke_index]
                    # Image stroke'ları atla
                    if hasattr(stroke, 'stroke_type') and stroke.stroke_type == 'image':
                        continue
                    # Eski stroke formatı kontrolü
                    if 'type' not in stroke:
                        continue
                    # Sadece dikdörtgen ve daire için
                    if stroke['type'] in ['rectangle', 'circle']:
                        stroke['fill'] = enabled
            
            current_widget.update()
            self.show_status_message("Şekil dolgu durumu değiştirildi")
    
    def on_shape_fill_opacity_changed(self, opacity):
        """Seçilen şekillerin dolgu şeffaflığını değiştir"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and current_widget.selection_tool.selected_strokes:
            # Undo için state kaydet
            current_widget.save_current_state("Change shape fill opacity")
            
            # Sadece rectangle ve circle'ların dolgu şeffaflığını değiştir
            for stroke_index in current_widget.selection_tool.selected_strokes:
                if stroke_index < len(current_widget.strokes):
                    stroke = current_widget.strokes[stroke_index]
                    # Image stroke'ları atla
                    if hasattr(stroke, 'stroke_type') and stroke.stroke_type == 'image':
                        continue
                    # Eski stroke formatı kontrolü
                    if 'type' not in stroke:
                        continue
                    # Sadece rectangle ve circle
                    if stroke['type'] in ['rectangle', 'circle']:
                        stroke['fill_opacity'] = opacity
            
            current_widget.update()
            self.show_status_message("Şekil dolgu şeffaflığı değiştirildi")
            
    def on_background_changed(self, settings):
        """Arka plan ayarları değiştiğinde aktif tab'a bildir"""
        current_widget = self.get_current_drawing_widget()
        if current_widget:
            current_widget.set_background_settings(settings)
        
        # Arka plan ayarlarını kaydet
        self.settings.set_background_settings(settings)
        self.settings.save_settings()
    
    def on_pdf_orientation_changed(self, orientation):
        """PDF yönü değiştiğinde"""
        self.settings.set_pdf_orientation(orientation)
        self.settings.save_settings()
        self.show_status_message(f"PDF yönü: {'Yatay' if orientation == 'landscape' else 'Dikey'}")
        
    def on_canvas_orientation_changed(self, orientation):
        """Canvas yönü değiştiğinde"""
        self.settings.set_canvas_orientation(orientation)
        # Tüm açık tab'lara uygula
        for i in range(self.tab_widget.count()):
            drawing_widget = self.tab_manager.get_tab_widget_at_index(i)
            if drawing_widget:
                drawing_widget.set_canvas_orientation(orientation)
        self.settings.save_settings()
        self.show_status_message(f"Canvas yönü: {'Yatay' if orientation == 'landscape' else 'Dikey'}")
        
    def on_canvas_size_changed(self, size):
        """Canvas boyutu değiştiğinde"""
        # Canvas boyutlarını güncelle
        self.update_canvas_sizes(size)
        self.settings.save_settings()
        size_names = {'small': 'Küçük', 'medium': 'Orta', 'large': 'Büyük'}
        self.show_status_message(f"Canvas boyutu: {size_names.get(size, size)}")
        
    def on_image_loaded(self, image_hash, pixmap):
        """Resim async yüklendiğinde canvas'ı güncelle"""
        current_widget = self.get_current_drawing_widget()
        if current_widget:
            current_widget.update()  # Canvas'ı yeniden çiz
        
    def update_canvas_sizes(self, size):
        """Canvas boyutlarını güncelle"""
        # Tüm açık tab'lara yeni boyutları uygula
        for i in range(self.tab_widget.count()):
            drawing_widget = self.tab_manager.get_tab_widget_at_index(i)
            if drawing_widget:
                if size == 'medium':
                    drawing_widget.a4_width_portrait = 1240
                    drawing_widget.a4_height_portrait = 1754
                    drawing_widget.a4_width_landscape = 1754
                    drawing_widget.a4_height_landscape = 1240
                elif size == 'large':
                    drawing_widget.a4_width_portrait = 2480
                    drawing_widget.a4_height_portrait = 3508
                    drawing_widget.a4_width_landscape = 3508
                    drawing_widget.a4_height_landscape = 2480
                else:  # small
                    drawing_widget.a4_width_portrait = 827
                    drawing_widget.a4_height_portrait = 1169
                    drawing_widget.a4_width_landscape = 1169
                    drawing_widget.a4_height_landscape = 827
                
                drawing_widget.update_canvas_size()
    
    def zoom_in(self):
        """Yakınlaştır"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and hasattr(current_widget, 'zoom_manager'):
            current_widget.zoom_manager.zoom_in()
        
    def zoom_out(self):
        """Uzaklaştır"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and hasattr(current_widget, 'zoom_manager'):
            current_widget.zoom_manager.zoom_out()
        
    def zoom_reset(self):
        """Zoom'u sıfırla"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and hasattr(current_widget, 'zoom_manager'):
            current_widget.zoom_manager.reset_zoom()
    
    def on_zoom_changed(self, zoom_level):
        """Zoom değiştiğinde aktif tab'a bildir"""
        current_widget = self.get_current_drawing_widget()
        if current_widget:
            current_widget.update()  # Sadece yeniden çiz
        # Status bar zoom bilgisini güncelle
        self.update_zoom_status(zoom_level)
    
    def on_pan_changed(self, pan_offset):
        """Pan değiştiğinde aktif tab'a bildir"""
        current_widget = self.get_current_drawing_widget()
        if current_widget:
            current_widget.update()  # Sadece yeniden çiz
            
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
        
        # Canvas yönü
        canvas_orientation = self.settings.get_canvas_orientation()
        drawing_widget.set_canvas_orientation(canvas_orientation)
        
        # Arka plan ayarları
        bg_settings = self.settings.get_background_settings()
        drawing_widget.set_background_settings(bg_settings)
        
        # UI widget'larını güncelle
        self.color_palette.load_from_settings()
        self.line_width_widget.set_width(self.settings.get_line_width())
        self.settings_widget.set_background_settings(bg_settings)
        
    def save_session(self):
        """Oturumu kaydet (mevcut dosya varsa üzerine yaz)"""
        if self.current_session_file:
            # Mevcut dosya üzerine kaydet
            if self.session_manager.save_session(self, self.current_session_file):
                self.update_window_title()
                self.session_manager.clear_auto_save()
        else:
            # İlk kez kaydetme - dosya adı sor
            self.save_session_as()

    def save_session_as(self):
        """Oturumu farklı kaydet"""
        filename = self.session_manager.save_session(self)
        if filename:
            self.current_session_file = filename
            self.update_window_title()
            self.session_manager.clear_auto_save()

    def load_session(self):
        """Oturum aç"""
        filename = self.session_manager.load_session(self)
        if filename:
            self.current_session_file = filename
            self.update_window_title()
            self.session_manager.clear_auto_save()
            self.update_pdf_controls_state()

    def load_recent_session(self, filepath):
        """Son oturumlardan birini aç"""
        if self.session_manager.load_session(self, filepath):
            self.current_session_file = filepath
            self.update_window_title()
            self.session_manager.clear_auto_save()
            self.update_pdf_controls_state()
            
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
    
    def set_pdf_orientation(self, orientation):
        """PDF sayfa yönünü ayarla"""
        self.settings.set_pdf_orientation(orientation)
        self.settings.save_settings()
        self.show_status_message(f"PDF sayfa yönü: {'Yatay' if orientation == 'landscape' else 'Dikey'}")
    
    def set_canvas_orientation(self, orientation):
        """Canvas yönünü ayarla"""
        self.settings.set_canvas_orientation(orientation)
        self.settings.save_settings()
        
        # Tüm tab'lardaki canvas'ları güncelle
        for i in range(self.tab_widget.count()):
            drawing_widget = self.tab_manager.get_tab_widget_at_index(i)
            if drawing_widget:
                drawing_widget.set_canvas_orientation(orientation)
        
        self.show_status_message(f"Canvas yönü: {'Yatay' if orientation == 'landscape' else 'Dikey'}")
    
    def export_current_tab_as_image(self):
        """Aktif sekmeyi resim olarak dışa aktar"""
        current_widget = self.get_current_drawing_widget()
        if not current_widget:
            QMessageBox.warning(self, "Uyarı", "Dışa aktarılacak çizim bulunamadı.")
            return

        default_name = "cizim"
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            tab_title = self.tab_widget.tabText(current_index).strip()
            if tab_title:
                default_name = tab_title.replace(" ", "_").lower()
        default_path = f"{default_name}.png"

        filename, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Resim Olarak Dışa Aktar",
            default_path,
            "PNG Dosyaları (*.png);;JPEG Dosyaları (*.jpg *.jpeg)"
        )

        if not filename:
            return

        filter_text = (selected_filter or "").lower()
        lower_filename = filename.lower()
        if 'jpeg' in filter_text or 'jpg' in filter_text or lower_filename.endswith(('.jpg', '.jpeg')):
            image_format = 'JPEG'
            if not lower_filename.endswith(('.jpg', '.jpeg')):
                filename += '.jpg'
        else:
            image_format = 'PNG'
            if not lower_filename.endswith('.png'):
                filename += '.png'

        scale_factor, ok = QInputDialog.getDouble(
            self,
            "Ölçek Faktörü",
            "Çıkış ölçek faktörü (1.0 = orijinal boyut):",
            1.0,
            0.1,
            10.0,
            1
        )
        if not ok:
            return

        if scale_factor <= 0:
            QMessageBox.warning(self, "Uyarı", "Ölçek faktörü 0'dan büyük olmalıdır.")
            return

        image_width = max(1, int(round(current_widget.width() * scale_factor)))
        image_height = max(1, int(round(current_widget.height() * scale_factor)))

        image = QImage(image_width, image_height, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.white)

        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        try:
            if scale_factor != 1.0:
                painter.scale(scale_factor, scale_factor)
            current_widget.render(painter)
        finally:
            painter.end()

        if not image.save(filename, image_format):
            QMessageBox.critical(self, "Hata", "Resim kaydedilemedi.")
            self.show_status_message("Resim dışa aktarılamadı")
            return

        QMessageBox.information(self, "Başarılı", f"Resim başarıyla kaydedildi:\n{filename}")
        self.show_status_message("Resim başarıyla dışa aktarıldı")

    def open_pdf(self):
        """Seçilen PDF dosyasını arka plan olarak yükle"""
        current_widget = self.get_current_drawing_widget()
        if not current_widget:
            QMessageBox.warning(self, "Uyarı", "PDF yüklemek için açık bir çizim sekmesi bulunmuyor.")
            return

        start_dir = self.last_opened_pdf_dir if os.path.isdir(self.last_opened_pdf_dir) else ""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "PDF Aç",
            start_dir,
            "PDF Dosyaları (*.pdf);;Tüm Dosyalar (*)"
        )

        if not filename:
            return

        self.last_opened_pdf_dir = os.path.dirname(filename) or self.last_opened_pdf_dir

        try:
            pdf_layer = self.pdf_importer.load_pdf(filename, dpi=self.default_pdf_dpi)
        except Exception as exc:
            QMessageBox.critical(self, "PDF Yükleme Hatası", str(exc))
            return

        current_widget.set_pdf_background_layer(pdf_layer)
        base_name = os.path.basename(filename)
        self.show_status_message(
            f"PDF yüklendi: {base_name} ({pdf_layer.current_page + 1}/{pdf_layer.page_count})"
        )
        self.update_pdf_controls_state()

    def go_to_previous_pdf_page(self):
        """PDF arka planında bir önceki sayfaya geç"""
        current_widget = self.get_current_drawing_widget()
        if not current_widget or not current_widget.has_pdf_background():
            return

        if current_widget.previous_pdf_page():
            layer = current_widget.get_pdf_background_layer()
            if layer:
                self.show_status_message(
                    f"PDF sayfası: {layer.current_page + 1}/{layer.page_count}"
                )
        self.update_pdf_controls_state()

    def go_to_next_pdf_page(self):
        """PDF arka planında bir sonraki sayfaya geç"""
        current_widget = self.get_current_drawing_widget()
        if not current_widget or not current_widget.has_pdf_background():
            return

        if current_widget.next_pdf_page():
            layer = current_widget.get_pdf_background_layer()
            if layer:
                self.show_status_message(
                    f"PDF sayfası: {layer.current_page + 1}/{layer.page_count}"
                )
        self.update_pdf_controls_state()

    def prompt_pdf_resolution_change(self):
        """PDF rasterizasyon çözünürlüğünü ayarla"""
        current_widget = self.get_current_drawing_widget()
        if not current_widget or not current_widget.has_pdf_background():
            return

        layer = current_widget.get_pdf_background_layer()
        if not layer:
            return

        dpi, ok = QInputDialog.getInt(
            self,
            "PDF Çözünürlüğü",
            "DPI değeri (72-600):",
            layer.dpi,
            72,
            600,
            10
        )
        if not ok:
            return

        if current_widget.set_pdf_dpi(dpi):
            self.default_pdf_dpi = dpi
            self.show_status_message(f"PDF çözünürlüğü {dpi} DPI olarak ayarlandı")
        else:
            self.show_status_message("PDF çözünürlüğü değiştirilmedi")

        self.update_pdf_controls_state()

    def import_image(self):
        """Canvas'a resim ekle"""
        from image_stroke import ImageStroke
        
        # Resim dosyası seç
        filename, _ = QFileDialog.getOpenFileName(
            self, "Resim Seç",
            "",
            "Resim Dosyaları (*.png *.jpg *.jpeg *.bmp *.gif *.tiff);;Tüm Dosyalar (*)"
        )
        
        if not filename:
            return
        
        try:
            current_widget = self.get_current_drawing_widget()
            if not current_widget:
                return
            
            # Resim stroke'u oluştur - sol üst köşeye yerleştir (cache manager olmadan)
            image_stroke = ImageStroke(filename, QPointF(50, 50), cache_manager=None)
            
            # Undo için state kaydet
            current_widget.save_current_state("Add image")
            
            # Stroke'u ekle
            current_widget.strokes.append(image_stroke)
            
            # Resimi seç
            stroke_index = len(current_widget.strokes) - 1
            current_widget.selection_tool.selected_strokes = [stroke_index]
            
            # Seçim aracına geç
            current_widget.set_active_tool("select")
            self.set_tool("select")
            
            current_widget.update()
            
            self.show_status_message(f"Resim eklendi: {os.path.basename(filename)}")
            
        except Exception as e:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Hata", f"Resim eklenemedi:\n{str(e)}")
    
    def export_to_pdf(self):
        """Tüm sekmeleri PDF olarak dışa aktar"""
        self.show_status_message("PDF dışa aktarılıyor...")
        success = self.pdf_exporter.export_to_pdf()
        if success:
            self.show_status_message("PDF başarıyla dışa aktarıldı")
        else:
            self.show_status_message("PDF dışa aktarma başarısız")
    
    def export_current_tab_with_pdf_pages(self):
        """Geçerli sekmenin PDF arka planındaki tüm sayfaları tek PDF'e kaydet"""
        self.show_status_message("PDF'ye kaydediliyor...")
        self.pdf_exporter.export_current_tab_with_pdf_pages()

    def save_pdf_to_source(self):
        """Aktif sekmedeki PDF'yi orijinal kaynağına kaydet."""
        current_widget = self.get_current_drawing_widget()
        if not current_widget or not hasattr(current_widget, 'has_pdf_background') or not current_widget.has_pdf_background():
            QMessageBox.warning(self, "Uyarı", "Bu sekmede PDF arka planı bulunmuyor.")
            self.show_status_message("Kaydedilecek PDF bulunamadı")
            self.update_pdf_controls_state()
            return

        self.show_status_message("PDF kaydediliyor...")
        saved = self.pdf_exporter.save_current_pdf_to_source()
        if saved:
            self.show_status_message("PDF kaynağına kaydedildi")
        else:
            self.show_status_message("PDF kaydedilmedi")
        self.update_pdf_controls_state()

    def closeEvent(self, event):
        """Uygulama kapanırken ayarları kaydet"""
        # Otomatik oturum kaydetme
        self.session_manager.auto_save_session(self)
        
        # Eğer kullanıcı manuel olarak kaydetmediyse image cache'i temizle
        if not self.current_session_file:
            self.clear_image_cache()
        
        # Threaded cache manager'ı kapat
        self.image_cache_manager.shutdown()
        
        # Pencere boyutunu kaydet
        self.settings.set_window_size(self.width(), self.height())
        
        # Settings dock görünürlüğünü kaydet
        self.settings.set_background_dock_visible(self.settings_dock.isVisible())
        
        # Ayarları kaydet
        self.settings.save_settings()
        
        super().closeEvent(event)

    def _setup_autosave_timer(self):
        """Belirli aralıklarla otomatik kayıt yapacak zamanlayıcıyı ayarla"""
        self._auto_save_interval_minutes = 5
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.setInterval(self._auto_save_interval_minutes * 60 * 1000)
        self.auto_save_timer.timeout.connect(lambda: self.session_manager.auto_save_session(self))
        self.auto_save_timer.start()

    def _prompt_auto_save_restore(self):
        """Mevcut otomatik kaydı yüklemek için kullanıcıdan onay iste"""
        if not self.session_manager.has_auto_save():
            return

        reply = QMessageBox.question(
            self,
            "Otomatik Kayıt Bulundu",
            "Son otomatik kaydı açmak ister misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.session_manager.load_auto_save(self):
                # Otomatik kayıttan sonra aktif dosya kullanıcı tarafından belirlenmeli
                self.current_session_file = None
                self.update_window_title()
                self.session_manager.clear_auto_save()
    
    # Grup işlemi handler'ları
    def on_group_shapes(self):
        """Seçili şekilleri grupla"""
        current_widget = self.get_current_drawing_widget()
        if not current_widget or len(current_widget.selection_tool.selected_strokes) < 2:
            return
            
        selected_indices = current_widget.selection_tool.selected_strokes[:]
        
        # Undo için state kaydet
        current_widget.save_current_state("Group shapes")
        
        # Grup ID oluştur
        import time
        group_id = f"group_{int(time.time() * 1000)}"
        
        # Seçili stroke'ları grupla
        for index in selected_indices:
            if index < len(current_widget.strokes):
                stroke = current_widget.strokes[index]
                if hasattr(stroke, 'group_id'):
                    stroke.group_id = group_id
                elif isinstance(stroke, dict):
                    stroke['group_id'] = group_id
        
        current_widget.update()
        
        # Shape properties widget'ını güncelle (buton durumları için)
        current_widget.update_shape_properties()
        
        self.show_status_message(f"{len(selected_indices)} şekil gruplandı")
    
    # Resim özellikleri handler'ları
    def on_image_opacity_changed(self, opacity):
        """Resim şeffaflığı değişti"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and current_widget.selection_tool.selected_strokes:
            # Undo için state kaydet
            current_widget.save_current_state("Change image opacity")
            
            # Seçili resim stroke'larını güncelle
            for stroke_index in current_widget.selection_tool.selected_strokes:
                if stroke_index < len(current_widget.strokes):
                    stroke = current_widget.strokes[stroke_index]
                    if hasattr(stroke, 'stroke_type') and stroke.stroke_type == 'image':
                        stroke.set_opacity(opacity)
            
            current_widget.update()
    
    def on_image_border_enabled_changed(self, enabled):
        """Resim kenarlığı etkin/pasif değişti"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and current_widget.selection_tool.selected_strokes:
            # Undo için state kaydet
            current_widget.save_current_state("Toggle image border")
            
            # Seçili resim stroke'larını güncelle
            for stroke_index in current_widget.selection_tool.selected_strokes:
                if stroke_index < len(current_widget.strokes):
                    stroke = current_widget.strokes[stroke_index]
                    if hasattr(stroke, 'stroke_type') and stroke.stroke_type == 'image':
                        stroke.has_border = enabled
            
            current_widget.update()
    
    def on_image_border_color_changed(self, color):
        """Resim kenarlık rengi değişti"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and current_widget.selection_tool.selected_strokes:
            # Undo için state kaydet
            current_widget.save_current_state("Change image border color")
            
            # Seçili resim stroke'larını güncelle
            for stroke_index in current_widget.selection_tool.selected_strokes:
                if stroke_index < len(current_widget.strokes):
                    stroke = current_widget.strokes[stroke_index]
                    if hasattr(stroke, 'stroke_type') and stroke.stroke_type == 'image':
                        from PyQt6.QtGui import QColor
                        stroke.border_color = QColor(color)
            
            current_widget.update()
    
    def on_image_border_width_changed(self, width):
        """Resim kenarlık kalınlığı değişti"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and current_widget.selection_tool.selected_strokes:
            # Undo için state kaydet
            current_widget.save_current_state("Change image border width")
            
            # Seçili resim stroke'larını güncelle
            for stroke_index in current_widget.selection_tool.selected_strokes:
                if stroke_index < len(current_widget.strokes):
                    stroke = current_widget.strokes[stroke_index]
                    if hasattr(stroke, 'stroke_type') and stroke.stroke_type == 'image':
                        stroke.border_width = width
            
            current_widget.update()
    
    def on_image_border_style_changed(self, style):
        """Resim kenarlık stili değişti"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and current_widget.selection_tool.selected_strokes:
            # Undo için state kaydet
            current_widget.save_current_state("Change image border style")
            
            # Seçili resim stroke'larını güncelle
            for stroke_index in current_widget.selection_tool.selected_strokes:
                if stroke_index < len(current_widget.strokes):
                    stroke = current_widget.strokes[stroke_index]
                    if hasattr(stroke, 'stroke_type') and stroke.stroke_type == 'image':
                        stroke.border_style = style
            
            current_widget.update()
    
    def on_image_shadow_enabled_changed(self, enabled):
        """Resim gölgesi etkin/pasif değişti"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and current_widget.selection_tool.selected_strokes:
            # Undo için state kaydet
            current_widget.save_current_state("Toggle image shadow")
            
            # Seçili resim stroke'larını güncelle
            for stroke_index in current_widget.selection_tool.selected_strokes:
                if stroke_index < len(current_widget.strokes):
                    stroke = current_widget.strokes[stroke_index]
                    if hasattr(stroke, 'stroke_type') and stroke.stroke_type == 'image':
                        stroke.has_shadow = enabled
            
            current_widget.update()
    
    def on_image_shadow_color_changed(self, color):
        """Resim gölge rengi değişti"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and current_widget.selection_tool.selected_strokes:
            # Undo için state kaydet
            current_widget.save_current_state("Change image shadow color")
            
            # Seçili resim stroke'larını güncelle
            for stroke_index in current_widget.selection_tool.selected_strokes:
                if stroke_index < len(current_widget.strokes):
                    stroke = current_widget.strokes[stroke_index]
                    if hasattr(stroke, 'stroke_type') and stroke.stroke_type == 'image':
                        from PyQt6.QtGui import QColor
                        stroke.shadow_color = QColor(color)
            
            current_widget.update()
    
    def on_image_shadow_offset_changed(self, offset_x, offset_y):
        """Resim gölge offseti değişti"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and current_widget.selection_tool.selected_strokes:
            # Undo için state kaydet
            current_widget.save_current_state("Change image shadow offset")
            
            # Seçili resim stroke'larını güncelle
            for stroke_index in current_widget.selection_tool.selected_strokes:
                if stroke_index < len(current_widget.strokes):
                    stroke = current_widget.strokes[stroke_index]
                    if hasattr(stroke, 'stroke_type') and stroke.stroke_type == 'image':
                        stroke.shadow_offset_x = offset_x
                        stroke.shadow_offset_y = offset_y
            
                        current_widget.update()

    def on_image_shadow_blur_changed(self, blur):
        """Resim gölge bulanıklığı değişti"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and current_widget.selection_tool.selected_strokes:
            # Undo için state kaydet
            current_widget.save_current_state("Change image shadow blur")
            
            # Seçili resim stroke'larını güncelle
            for stroke_index in current_widget.selection_tool.selected_strokes:
                if stroke_index < len(current_widget.strokes):
                    stroke = current_widget.strokes[stroke_index]
                    if hasattr(stroke, 'stroke_type') and stroke.stroke_type == 'image':
                        stroke.shadow_blur = blur
            
            current_widget.update()

    def on_image_shadow_size_changed(self, size):
        """Resim gölge boyutu değişti"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and current_widget.selection_tool.selected_strokes:
            # Undo için state kaydet
            current_widget.save_current_state("Change image shadow size")
            
            # Seçili resim stroke'larını güncelle
            for stroke_index in current_widget.selection_tool.selected_strokes:
                if stroke_index < len(current_widget.strokes):
                    stroke = current_widget.strokes[stroke_index]
                    if hasattr(stroke, 'stroke_type') and stroke.stroke_type == 'image':
                        stroke.shadow_size = size
            
            current_widget.update()

    def on_image_shadow_inner_changed(self, inner):
        """Resim iç gölge değişti"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and current_widget.selection_tool.selected_strokes:
            # Undo için state kaydet
            current_widget.save_current_state("Change image inner shadow")
            
            # Seçili resim stroke'larını güncelle
            for stroke_index in current_widget.selection_tool.selected_strokes:
                if stroke_index < len(current_widget.strokes):
                    stroke = current_widget.strokes[stroke_index]
                    if hasattr(stroke, 'stroke_type') and stroke.stroke_type == 'image':
                        stroke.inner_shadow = inner
            
            current_widget.update()

    def on_image_shadow_quality_changed(self, quality):
        """Resim gölge kalitesi değişti"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and current_widget.selection_tool.selected_strokes:
            # Undo için state kaydet
            current_widget.save_current_state("Change image shadow quality")
            
            # Seçili resim stroke'larını güncelle
            for stroke_index in current_widget.selection_tool.selected_strokes:
                if stroke_index < len(current_widget.strokes):
                    stroke = current_widget.strokes[stroke_index]
                    if hasattr(stroke, 'stroke_type') and stroke.stroke_type == 'image':
                        stroke.shadow_quality = quality
            
            current_widget.update()

    def on_image_filter_changed(self, filter_type, intensity):
        """Resim filtresi değişti"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and current_widget.selection_tool.selected_strokes:
            # Undo için state kaydet
            current_widget.save_current_state("Change image filter")
            
            # Seçili resim stroke'larını güncelle
            for stroke_index in current_widget.selection_tool.selected_strokes:
                if stroke_index < len(current_widget.strokes):
                    stroke = current_widget.strokes[stroke_index]
                    if hasattr(stroke, 'stroke_type') and stroke.stroke_type == 'image':
                        stroke.filter_type = filter_type
                        stroke.filter_intensity = intensity
            
            current_widget.update()

    def on_image_transparency_changed(self, transparency):
        """Resim ekstra şeffaflığı değişti"""
        drawing_widget = self.get_current_drawing_widget()
        if not drawing_widget:
            return
            
        # Undo için state kaydet
        drawing_widget.save_current_state("Image Transparency Change")
            
        # Seçili resim strokes'larını güncelle
        for index in drawing_widget.selection_tool.selected_strokes:
            if index < len(drawing_widget.strokes):
                stroke = drawing_widget.strokes[index]
                if hasattr(stroke, 'stroke_type') and stroke.stroke_type == 'image':
                    stroke.transparency = transparency
                    
        drawing_widget.update()
        
    def on_image_blur_changed(self, blur_radius):
        """Resim bulanıklığı değişti"""
        drawing_widget = self.get_current_drawing_widget()
        if not drawing_widget:
            return
            
        # Undo için state kaydet
        drawing_widget.save_current_state("Image Blur Change")
            
        # Seçili resim strokes'larını güncelle
        for index in drawing_widget.selection_tool.selected_strokes:
            if index < len(drawing_widget.strokes):
                stroke = drawing_widget.strokes[index]
                if hasattr(stroke, 'stroke_type') and stroke.stroke_type == 'image':
                    stroke.blur_radius = blur_radius
                    
        drawing_widget.update()

    def on_image_corner_radius_changed(self, corner_radius):
        """Resim kenar yuvarlama değişti"""
        drawing_widget = self.get_current_drawing_widget()
        if not drawing_widget:
            return
            
        # Undo için state kaydet
        drawing_widget.save_current_state("Image Corner Radius Change")
            
        # Seçili resim strokes'larını güncelle
        for index in drawing_widget.selection_tool.selected_strokes:
            if index < len(drawing_widget.strokes):
                stroke = drawing_widget.strokes[index]
                if hasattr(stroke, 'stroke_type') and stroke.stroke_type == 'image':
                    stroke.corner_radius = corner_radius
                    
        drawing_widget.update()

    def on_image_shadow_opacity_changed(self, shadow_opacity):
        """Resim gölge şeffaflığı değişti"""
        drawing_widget = self.get_current_drawing_widget()
        if not drawing_widget:
            return
            
        # Undo için state kaydet
        drawing_widget.save_current_state("Image Shadow Opacity Change")
            
        # Seçili resim strokes'larını güncelle
        for index in drawing_widget.selection_tool.selected_strokes:
            if index < len(drawing_widget.strokes):
                stroke = drawing_widget.strokes[index]
                if hasattr(stroke, 'stroke_type') and stroke.stroke_type == 'image':
                    stroke.shadow_opacity = shadow_opacity
                    
        drawing_widget.update()

    def on_ungroup_shapes(self):
        """Seçili şekillerin grubunu çöz"""
        current_widget = self.get_current_drawing_widget()
        if not current_widget or not current_widget.selection_tool.selected_strokes:
            return
            
        selected_indices = current_widget.selection_tool.selected_strokes[:]
        ungrouped_count = 0
        
        # Undo için state kaydet
        current_widget.save_current_state("Ungroup shapes")
        
        # Seçili stroke'ların gruplarını çöz
        for index in selected_indices:
            if index < len(current_widget.strokes):
                stroke = current_widget.strokes[index]
                if hasattr(stroke, 'group_id'):
                    if hasattr(stroke, 'group_id') and stroke.group_id:
                        stroke.group_id = None
                        ungrouped_count += 1
                elif isinstance(stroke, dict) and 'group_id' in stroke:
                    if stroke['group_id']:
                        stroke['group_id'] = None
                        ungrouped_count += 1
        
        current_widget.update()
        
        # Shape properties widget'ını güncelle (buton durumları için)
        current_widget.update_shape_properties()
        
        if ungrouped_count > 0:
            self.show_status_message(f"{ungrouped_count} şekil gruptan çıkarıldı")
    
    # Hizalama handler'ları
    def on_align_left(self):
        """Seçili şekilleri sola hizala"""
        self.align_shapes('left')
    
    def on_align_right(self):
        """Seçili şekilleri sağa hizala"""
        self.align_shapes('right')
    
    def on_align_top(self):
        """Seçili şekilleri yukarı hizala"""
        self.align_shapes('top')
    
    def on_align_bottom(self):
        """Seçili şekilleri aşağı hizala"""
        self.align_shapes('bottom')
    
    def on_align_center_h(self):
        """Seçili şekilleri yatay ortala"""
        self.align_shapes('center_h')
    
    def on_align_center_v(self):
        """Seçili şekilleri dikey ortala"""
        self.align_shapes('center_v')
    
    def on_distribute_h(self):
        """Seçili şekilleri yatay dağıt"""
        self.distribute_shapes('horizontal')
    
    def on_distribute_v(self):
        """Seçili şekilleri dikey dağıt"""
        self.distribute_shapes('vertical')
    
    def on_add_selected_to_shape_library(self):
        """Seçilen şekilleri şekil havuzuna ekler"""
        if hasattr(self, 'shape_library_widget'):
            self.shape_library_widget.add_selected_shapes()
        else:
            self.show_status_message("Şekil havuzu açık değil.")
            
    def on_toggle_control_points(self):
        """B-spline kontrol noktalarını göster/gizle"""
        drawing_widget = self.get_current_drawing_widget()
        if not drawing_widget or not drawing_widget.selection_tool.selected_strokes:
            return
            
        # Undo için state kaydet
        drawing_widget.save_current_state("Toggle control points")
        
        # Seçili stroke'ların kontrol noktalarını aç/kapat
        changed = False
        show_points = False  # Noktaların gösterilip gösterilmeyeceğini takip et
        
        for index in drawing_widget.selection_tool.selected_strokes:
            if index < len(drawing_widget.strokes):
                stroke = drawing_widget.strokes[index]
                
                # B-spline kontrolü
                if stroke.get('type') == 'bspline' or stroke.get('tool_type') == 'bspline':
                    # Kontrol noktalarının görünürlüğünü değiştir
                    current = stroke.get('show_control_points', False)
                    stroke['show_control_points'] = not current
                    show_points = not current  # Yeni durumu kaydet
                    changed = True
                    
        if changed:
            # Buton metnini güncelle
            if hasattr(self, 'shape_properties_widget'):
                self.shape_properties_widget.update_control_points_button(show_points)
                
            if show_points:
                # Noktalar gösterildiğinde B-spline aracını aktif et
                self.set_tool("bspline")
                drawing_widget.set_active_tool("bspline")
                
                # Seçim dörtgenini kaldır (seçimi temizle)
                drawing_widget.selection_tool.clear_selection()
            else:
                # Noktalar gizlendiğinde seçim aracını aktif et
                self.set_tool("select")
                drawing_widget.set_active_tool("select")
                
            drawing_widget.update()
            self.show_status_message("Kontrol noktaları görünürlüğü değiştirildi")
    
    def align_shapes(self, alignment_type):
        """Seçili şekilleri hizalar"""
        drawing_widget = self.get_current_drawing_widget()
        if not drawing_widget or len(drawing_widget.selection_tool.selected_strokes) < 2:
            return
            
        selected_indices = drawing_widget.selection_tool.selected_strokes[:]
        
        # Undo için state kaydet
        drawing_widget.save_current_state(f"Align {alignment_type}")
        
        # Seçili şekillerin sınırlarını hesapla
        bounds = []
        for index in selected_indices:
            if index < len(drawing_widget.strokes):
                stroke = drawing_widget.strokes[index]
                bound = self.get_stroke_bounds(stroke)
                if bound:
                    bounds.append((index, bound))
        
        if len(bounds) < 2:
            return
        
        # Hizalama referansını belirle (ilk şeklin sınırları)
        ref_bound = bounds[0][1]
        
        # Hizalama tipine göre referans değeri
        if alignment_type == 'left':
            ref_value = ref_bound[0]  # min_x
        elif alignment_type == 'right':
            ref_value = ref_bound[2]  # max_x
        elif alignment_type == 'top':
            ref_value = ref_bound[1]  # min_y
        elif alignment_type == 'bottom':
            ref_value = ref_bound[3]  # max_y
        elif alignment_type == 'center_h':
            ref_value = (ref_bound[0] + ref_bound[2]) / 2  # center_x
        elif alignment_type == 'center_v':
            ref_value = (ref_bound[1] + ref_bound[3]) / 2  # center_y
        
        # Diğer şekilleri hizala
        for index, bound in bounds[1:]:
            stroke = drawing_widget.strokes[index]
            
            if alignment_type == 'left':
                offset_x = ref_value - bound[0]
                offset_y = 0
            elif alignment_type == 'right':
                offset_x = ref_value - bound[2]
                offset_y = 0
            elif alignment_type == 'top':
                offset_x = 0
                offset_y = ref_value - bound[1]
            elif alignment_type == 'bottom':
                offset_x = 0
                offset_y = ref_value - bound[3]
            elif alignment_type == 'center_h':
                current_center_x = (bound[0] + bound[2]) / 2
                offset_x = ref_value - current_center_x
                offset_y = 0
            elif alignment_type == 'center_v':
                current_center_y = (bound[1] + bound[3]) / 2
                offset_x = 0
                offset_y = ref_value - current_center_y
            
            # Offset uygula
            self.apply_offset_to_stroke_inplace(stroke, offset_x, offset_y)
        
        drawing_widget.update()
        self.show_status_message(f"Şekiller {alignment_type} hizalandı")
    
    def distribute_shapes(self, direction):
        """Şekilleri dağıt"""
        drawing_widget = self.get_current_drawing_widget()
        if not drawing_widget or len(drawing_widget.selection_tool.selected_strokes) < 3:
            return
            
        selected_indices = drawing_widget.selection_tool.selected_strokes[:]
        
        # Undo için state kaydet
        drawing_widget.save_current_state(f"Distribute {direction}")
        
        # Seçili şekillerin sınırlarını hesapla
        shapes_with_bounds = []
        for index in selected_indices:
            if index < len(drawing_widget.strokes):
                stroke = drawing_widget.strokes[index]
                bound = self.get_stroke_bounds(stroke)
                if bound:
                    if direction == 'horizontal':
                        center = (bound[0] + bound[2]) / 2  # center_x
                    else:  # vertical
                        center = (bound[1] + bound[3]) / 2  # center_y
                    shapes_with_bounds.append((index, stroke, center))
        
        if len(shapes_with_bounds) < 3:
            return
        
        # Merkez konumlarına göre sırala
        shapes_with_bounds.sort(key=lambda x: x[2])
        
        # İlk ve son şekil arasındaki mesafeyi eşit böl
        first_center = shapes_with_bounds[0][2]
        last_center = shapes_with_bounds[-1][2]
        total_distance = last_center - first_center
        step = total_distance / (len(shapes_with_bounds) - 1)
        
        # Orta şekilleri yeniden konumlandır
        for i in range(1, len(shapes_with_bounds) - 1):
            index, stroke, current_center = shapes_with_bounds[i]
            target_center = first_center + (i * step)
            
            if direction == 'horizontal':
                offset_x = target_center - current_center
                offset_y = 0
            else:  # vertical
                offset_x = 0
                offset_y = target_center - current_center
            
            self.apply_offset_to_stroke_inplace(stroke, offset_x, offset_y)
        
        drawing_widget.update()
        self.show_status_message(f"Şekiller {direction} dağıtıldı")
    
    def get_stroke_bounds(self, stroke):
        """Stroke'un sınırlarını hesapla (min_x, min_y, max_x, max_y)"""
        if hasattr(stroke, 'stroke_type') and stroke.stroke_type == 'image':
            bounds = stroke.get_bounds()
            return (bounds.left(), bounds.top(), bounds.right(), bounds.bottom())
        
        if 'type' not in stroke:
            return None
            
        points = self.get_stroke_points_for_bounds(stroke)
        if not points:
            return None
            
        min_x = min(p[0] for p in points)
        max_x = max(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_y = max(p[1] for p in points)
        
        return (min_x, min_y, max_x, max_y)
    
    def apply_offset_to_stroke_inplace(self, stroke, offset_x, offset_y):
        """Stroke'a offset uygula (in-place)"""
        if hasattr(stroke, 'stroke_type') and stroke.stroke_type == 'image':
            stroke.position += QPointF(offset_x, offset_y)
            return
            
        if 'type' not in stroke:
            return
            
        if stroke['type'] == 'freehand':
            if 'points' in stroke:
                for point in stroke['points']:
                    if isinstance(point, dict):
                        point['x'] += offset_x
                        point['y'] += offset_y
                        
        elif stroke['type'] == 'bspline':
            if 'control_points' in stroke:
                for cp in stroke['control_points']:
                    cp[0] += offset_x
                    cp[1] += offset_y
                    
        elif stroke['type'] == 'line':
            if 'start_point' in stroke:
                start = stroke['start_point']
                stroke['start_point'] = (start[0] + offset_x, start[1] + offset_y)
            if 'end_point' in stroke:
                end = stroke['end_point']
                stroke['end_point'] = (end[0] + offset_x, end[1] + offset_y)
                
        elif stroke['type'] == 'rectangle':
            if 'corners' in stroke:
                for i, corner in enumerate(stroke['corners']):
                    stroke['corners'][i] = (corner[0] + offset_x, corner[1] + offset_y)
            elif 'top_left' in stroke and 'bottom_right' in stroke:
                tl = stroke['top_left']
                br = stroke['bottom_right']
                stroke['top_left'] = (tl[0] + offset_x, tl[1] + offset_y)
                stroke['bottom_right'] = (br[0] + offset_x, br[1] + offset_y)
                
        elif stroke['type'] == 'circle':
            if 'center' in stroke:
                center = stroke['center']
                stroke['center'] = (center[0] + offset_x, center[1] + offset_y)

    # Dikdörtgen özellikleri event handler'ları
    def on_rectangle_corner_radius_changed(self, corner_radius):
        """Dikdörtgen kenar yuvarlama değişti"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and hasattr(current_widget, 'selection_tool'):
            selected = current_widget.selection_tool.selected_strokes
            if selected:
                # Undo için state kaydet
                current_widget.save_current_state("Change rectangle corner radius")
                
                # Sadece dikdörtgen stroke'larını güncelle
                for index in selected:
                    if index < len(current_widget.strokes):
                        stroke = current_widget.strokes[index]
                        if stroke.get('type') == 'rectangle':
                            stroke['corner_radius'] = corner_radius
                
                current_widget.update()
    
    def on_rectangle_shadow_enabled_changed(self, enabled):
        """Dikdörtgen gölge etkin/pasif değişti"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and hasattr(current_widget, 'selection_tool'):
            selected = current_widget.selection_tool.selected_strokes
            if selected:
                # Undo için state kaydet
                current_widget.save_current_state("Change rectangle shadow enabled")
                
                # Sadece dikdörtgen stroke'larını güncelle
                for index in selected:
                    if index < len(current_widget.strokes):
                        stroke = current_widget.strokes[index]
                        if stroke.get('type') == 'rectangle':
                            stroke['has_shadow'] = enabled
                
                current_widget.update()
    
    def on_rectangle_shadow_color_changed(self, color):
        """Dikdörtgen gölge rengi değişti"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and hasattr(current_widget, 'selection_tool'):
            selected = current_widget.selection_tool.selected_strokes
            if selected:
                # Undo için state kaydet
                current_widget.save_current_state("Change rectangle shadow color")
                
                # Sadece dikdörtgen stroke'larını güncelle
                for index in selected:
                    if index < len(current_widget.strokes):
                        stroke = current_widget.strokes[index]
                        if stroke.get('type') == 'rectangle':
                            stroke['shadow_color'] = color
                
                current_widget.update()
    
    def on_rectangle_shadow_offset_changed(self, offset_x, offset_y):
        """Dikdörtgen gölge offseti değişti"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and hasattr(current_widget, 'selection_tool'):
            selected = current_widget.selection_tool.selected_strokes
            if selected:
                # Undo için state kaydet
                current_widget.save_current_state("Change rectangle shadow offset")
                
                # Sadece dikdörtgen stroke'larını güncelle
                for index in selected:
                    if index < len(current_widget.strokes):
                        stroke = current_widget.strokes[index]
                        if stroke.get('type') == 'rectangle':
                            stroke['shadow_offset_x'] = offset_x
                            stroke['shadow_offset_y'] = offset_y
                
                current_widget.update()
    
    def on_rectangle_shadow_blur_changed(self, blur):
        """Dikdörtgen gölge bulanıklığı değişti"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and hasattr(current_widget, 'selection_tool'):
            selected = current_widget.selection_tool.selected_strokes
            if selected:
                # Undo için state kaydet
                current_widget.save_current_state("Change rectangle shadow blur")
                
                # Sadece dikdörtgen stroke'larını güncelle
                for index in selected:
                    if index < len(current_widget.strokes):
                        stroke = current_widget.strokes[index]
                        if stroke.get('type') == 'rectangle':
                            stroke['shadow_blur'] = blur
                
                current_widget.update()
    
    def on_rectangle_shadow_size_changed(self, size):
        """Dikdörtgen gölge boyutu değişti"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and hasattr(current_widget, 'selection_tool'):
            selected = current_widget.selection_tool.selected_strokes
            if selected:
                # Undo için state kaydet
                current_widget.save_current_state("Change rectangle shadow size")
                
                # Sadece dikdörtgen stroke'larını güncelle
                for index in selected:
                    if index < len(current_widget.strokes):
                        stroke = current_widget.strokes[index]
                        if stroke.get('type') == 'rectangle':
                            stroke['shadow_size'] = size
                
                current_widget.update()
    
    def on_rectangle_shadow_opacity_changed(self, opacity):
        """Dikdörtgen gölge şeffaflığı değişti"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and hasattr(current_widget, 'selection_tool'):
            selected = current_widget.selection_tool.selected_strokes
            if selected:
                # Undo için state kaydet
                current_widget.save_current_state("Change rectangle shadow opacity")
                
                # Sadece dikdörtgen stroke'larını güncelle
                for index in selected:
                    if index < len(current_widget.strokes):
                        stroke = current_widget.strokes[index]
                        if stroke.get('type') == 'rectangle':
                            stroke['shadow_opacity'] = opacity
                
                current_widget.update()
    
    def on_rectangle_shadow_inner_changed(self, inner):
        """Dikdörtgen iç/dış gölge değişti"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and hasattr(current_widget, 'selection_tool'):
            selected = current_widget.selection_tool.selected_strokes
            if selected:
                # Undo için state kaydet
                current_widget.save_current_state("Change rectangle shadow type")
                
                # Sadece dikdörtgen stroke'larını güncelle
                for index in selected:
                    if index < len(current_widget.strokes):
                        stroke = current_widget.strokes[index]
                        if stroke.get('type') == 'rectangle':
                            stroke['inner_shadow'] = inner
                
                current_widget.update()
    
    def on_rectangle_shadow_quality_changed(self, quality):
        """Dikdörtgen gölge kalitesi değişti"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and hasattr(current_widget, 'selection_tool'):
            selected = current_widget.selection_tool.selected_strokes
            if selected:
                # Undo için state kaydet
                current_widget.save_current_state("Change rectangle shadow quality")
                
                # Sadece dikdörtgen stroke'larını güncelle
                for index in selected:
                    if index < len(current_widget.strokes):
                        stroke = current_widget.strokes[index]
                        if stroke.get('type') == 'rectangle':
                            stroke['shadow_quality'] = quality
                
                current_widget.update()
                
    # Çember özellikleri event handler'ları
    def on_circle_shadow_enabled_changed(self, enabled):
        """Çember gölge etkin/pasif değişti"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and hasattr(current_widget, 'selection_tool'):
            selected = current_widget.selection_tool.selected_strokes
            if selected:
                # Undo için state kaydet
                current_widget.save_current_state("Change circle shadow enabled")
                
                # Sadece çember stroke'larını güncelle
                for index in selected:
                    if index < len(current_widget.strokes):
                        stroke = current_widget.strokes[index]
                        if stroke.get('type') == 'circle':
                            stroke['has_shadow'] = enabled
                
                current_widget.update()
    
    def on_circle_shadow_color_changed(self, color):
        """Çember gölge rengi değişti"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and hasattr(current_widget, 'selection_tool'):
            selected = current_widget.selection_tool.selected_strokes
            if selected:
                # Undo için state kaydet
                current_widget.save_current_state("Change circle shadow color")
                
                # Sadece çember stroke'larını güncelle
                for index in selected:
                    if index < len(current_widget.strokes):
                        stroke = current_widget.strokes[index]
                        if stroke.get('type') == 'circle':
                            stroke['shadow_color'] = color
                
                current_widget.update()
    
    def on_circle_shadow_offset_changed(self, offset_x, offset_y):
        """Çember gölge offseti değişti"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and hasattr(current_widget, 'selection_tool'):
            selected = current_widget.selection_tool.selected_strokes
            if selected:
                # Undo için state kaydet
                current_widget.save_current_state("Change circle shadow offset")
                
                # Sadece çember stroke'larını güncelle
                for index in selected:
                    if index < len(current_widget.strokes):
                        stroke = current_widget.strokes[index]
                        if stroke.get('type') == 'circle':
                            stroke['shadow_offset_x'] = offset_x
                            stroke['shadow_offset_y'] = offset_y
                
                current_widget.update()
    
    def on_circle_shadow_blur_changed(self, blur):
        """Çember gölge bulanıklığı değişti"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and hasattr(current_widget, 'selection_tool'):
            selected = current_widget.selection_tool.selected_strokes
            if selected:
                # Undo için state kaydet
                current_widget.save_current_state("Change circle shadow blur")
                
                # Sadece çember stroke'larını güncelle
                for index in selected:
                    if index < len(current_widget.strokes):
                        stroke = current_widget.strokes[index]
                        if stroke.get('type') == 'circle':
                            stroke['shadow_blur'] = blur
                
                current_widget.update()
    
    def on_circle_shadow_size_changed(self, size):
        """Çember gölge boyutu değişti"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and hasattr(current_widget, 'selection_tool'):
            selected = current_widget.selection_tool.selected_strokes
            if selected:
                # Undo için state kaydet
                current_widget.save_current_state("Change circle shadow size")
                
                # Sadece çember stroke'larını güncelle
                for index in selected:
                    if index < len(current_widget.strokes):
                        stroke = current_widget.strokes[index]
                        if stroke.get('type') == 'circle':
                            stroke['shadow_size'] = size
                
                current_widget.update()
    
    def on_circle_shadow_opacity_changed(self, opacity):
        """Çember gölge şeffaflığı değişti"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and hasattr(current_widget, 'selection_tool'):
            selected = current_widget.selection_tool.selected_strokes
            if selected:
                # Undo için state kaydet
                current_widget.save_current_state("Change circle shadow opacity")
                
                # Sadece çember stroke'larını güncelle
                for index in selected:
                    if index < len(current_widget.strokes):
                        stroke = current_widget.strokes[index]
                        if stroke.get('type') == 'circle':
                            stroke['shadow_opacity'] = opacity
                
                current_widget.update()
    
    def on_circle_shadow_inner_changed(self, inner):
        """Çember iç/dış gölge değişti"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and hasattr(current_widget, 'selection_tool'):
            selected = current_widget.selection_tool.selected_strokes
            if selected:
                # Undo için state kaydet
                current_widget.save_current_state("Change circle shadow type")
                
                # Sadece çember stroke'larını güncelle
                for index in selected:
                    if index < len(current_widget.strokes):
                        stroke = current_widget.strokes[index]
                        if stroke.get('type') == 'circle':
                            stroke['inner_shadow'] = inner
                
                current_widget.update()
    
    def on_circle_shadow_quality_changed(self, quality):
        """Çember gölge kalitesi değişti"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and hasattr(current_widget, 'selection_tool'):
            selected = current_widget.selection_tool.selected_strokes
            if selected:
                # Undo için state kaydet
                current_widget.save_current_state("Change circle shadow quality")

                # Sadece çember stroke'larını güncelle
                for index in selected:
                    if index < len(current_widget.strokes):
                        stroke = current_widget.strokes[index]
                        if stroke.get('type') == 'circle':
                            stroke['shadow_quality'] = quality

                current_widget.update()

    def on_stroke_shadow_enabled_changed(self, enabled):
        """Çizgi gölge etkin/pasif değişti"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and hasattr(current_widget, 'selection_tool'):
            selected = current_widget.selection_tool.selected_strokes
            if selected:
                current_widget.save_current_state("Change stroke shadow enabled")
                for index in selected:
                    if index < len(current_widget.strokes):
                        stroke = current_widget.strokes[index]
                        if hasattr(stroke, 'stroke_type') and stroke.stroke_type == 'image':
                            continue
                        if not isinstance(stroke, dict) or 'type' not in stroke:
                            continue
                        if stroke['type'] in ['line', 'freehand', 'bspline']:
                            stroke['has_shadow'] = enabled
                current_widget.update()
        if current_widget:
            if hasattr(current_widget.line_tool, 'set_shadow_enabled'):
                current_widget.line_tool.set_shadow_enabled(enabled)
            if hasattr(current_widget.freehand_tool, 'set_shadow_enabled'):
                current_widget.freehand_tool.set_shadow_enabled(enabled)
            if hasattr(current_widget.bspline_tool, 'set_shadow_enabled'):
                current_widget.bspline_tool.set_shadow_enabled(enabled)

    def on_stroke_shadow_color_changed(self, color):
        """Çizgi gölge rengi değişti"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and hasattr(current_widget, 'selection_tool'):
            selected = current_widget.selection_tool.selected_strokes
            if selected:
                current_widget.save_current_state("Change stroke shadow color")
                for index in selected:
                    if index < len(current_widget.strokes):
                        stroke = current_widget.strokes[index]
                        if hasattr(stroke, 'stroke_type') and stroke.stroke_type == 'image':
                            continue
                        if not isinstance(stroke, dict) or 'type' not in stroke:
                            continue
                        if stroke['type'] in ['line', 'freehand', 'bspline']:
                            stroke['shadow_color'] = color
                current_widget.update()
        if current_widget:
            if hasattr(current_widget.line_tool, 'set_shadow_color'):
                current_widget.line_tool.set_shadow_color(color)
            if hasattr(current_widget.freehand_tool, 'set_shadow_color'):
                current_widget.freehand_tool.set_shadow_color(color)
            if hasattr(current_widget.bspline_tool, 'set_shadow_color'):
                current_widget.bspline_tool.set_shadow_color(color)

    def on_stroke_shadow_offset_changed(self, offset_x, offset_y):
        """Çizgi gölge offseti değişti"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and hasattr(current_widget, 'selection_tool'):
            selected = current_widget.selection_tool.selected_strokes
            if selected:
                current_widget.save_current_state("Change stroke shadow offset")
                for index in selected:
                    if index < len(current_widget.strokes):
                        stroke = current_widget.strokes[index]
                        if hasattr(stroke, 'stroke_type') and stroke.stroke_type == 'image':
                            continue
                        if not isinstance(stroke, dict) or 'type' not in stroke:
                            continue
                        if stroke['type'] in ['line', 'freehand', 'bspline']:
                            stroke['shadow_offset_x'] = offset_x
                            stroke['shadow_offset_y'] = offset_y
                current_widget.update()
        if current_widget:
            if hasattr(current_widget.line_tool, 'set_shadow_offset'):
                current_widget.line_tool.set_shadow_offset(offset_x, offset_y)
            if hasattr(current_widget.freehand_tool, 'set_shadow_offset'):
                current_widget.freehand_tool.set_shadow_offset(offset_x, offset_y)
            if hasattr(current_widget.bspline_tool, 'set_shadow_offset'):
                current_widget.bspline_tool.set_shadow_offset(offset_x, offset_y)

    def on_stroke_shadow_blur_changed(self, blur):
        """Çizgi gölge bulanıklığı değişti"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and hasattr(current_widget, 'selection_tool'):
            selected = current_widget.selection_tool.selected_strokes
            if selected:
                current_widget.save_current_state("Change stroke shadow blur")
                for index in selected:
                    if index < len(current_widget.strokes):
                        stroke = current_widget.strokes[index]
                        if hasattr(stroke, 'stroke_type') and stroke.stroke_type == 'image':
                            continue
                        if not isinstance(stroke, dict) or 'type' not in stroke:
                            continue
                        if stroke['type'] in ['line', 'freehand', 'bspline']:
                            stroke['shadow_blur'] = blur
                current_widget.update()
        if current_widget:
            if hasattr(current_widget.line_tool, 'set_shadow_blur'):
                current_widget.line_tool.set_shadow_blur(blur)
            if hasattr(current_widget.freehand_tool, 'set_shadow_blur'):
                current_widget.freehand_tool.set_shadow_blur(blur)
            if hasattr(current_widget.bspline_tool, 'set_shadow_blur'):
                current_widget.bspline_tool.set_shadow_blur(blur)

    def on_stroke_shadow_size_changed(self, size):
        """Çizgi gölge boyutu değişti"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and hasattr(current_widget, 'selection_tool'):
            selected = current_widget.selection_tool.selected_strokes
            if selected:
                current_widget.save_current_state("Change stroke shadow size")
                for index in selected:
                    if index < len(current_widget.strokes):
                        stroke = current_widget.strokes[index]
                        if hasattr(stroke, 'stroke_type') and stroke.stroke_type == 'image':
                            continue
                        if not isinstance(stroke, dict) or 'type' not in stroke:
                            continue
                        if stroke['type'] in ['line', 'freehand', 'bspline']:
                            stroke['shadow_size'] = size
                current_widget.update()
        if current_widget:
            if hasattr(current_widget.line_tool, 'set_shadow_size'):
                current_widget.line_tool.set_shadow_size(size)
            if hasattr(current_widget.freehand_tool, 'set_shadow_size'):
                current_widget.freehand_tool.set_shadow_size(size)
            if hasattr(current_widget.bspline_tool, 'set_shadow_size'):
                current_widget.bspline_tool.set_shadow_size(size)

    def on_stroke_shadow_opacity_changed(self, opacity):
        """Çizgi gölge şeffaflığı değişti"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and hasattr(current_widget, 'selection_tool'):
            selected = current_widget.selection_tool.selected_strokes
            if selected:
                current_widget.save_current_state("Change stroke shadow opacity")
                for index in selected:
                    if index < len(current_widget.strokes):
                        stroke = current_widget.strokes[index]
                        if hasattr(stroke, 'stroke_type') and stroke.stroke_type == 'image':
                            continue
                        if not isinstance(stroke, dict) or 'type' not in stroke:
                            continue
                        if stroke['type'] in ['line', 'freehand', 'bspline']:
                            stroke['shadow_opacity'] = opacity
                current_widget.update()
        if current_widget:
            if hasattr(current_widget.line_tool, 'set_shadow_opacity'):
                current_widget.line_tool.set_shadow_opacity(opacity)
            if hasattr(current_widget.freehand_tool, 'set_shadow_opacity'):
                current_widget.freehand_tool.set_shadow_opacity(opacity)
            if hasattr(current_widget.bspline_tool, 'set_shadow_opacity'):
                current_widget.bspline_tool.set_shadow_opacity(opacity)

    def on_stroke_shadow_inner_changed(self, inner):
        """Çizgi iç/dış gölge değişti"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and hasattr(current_widget, 'selection_tool'):
            selected = current_widget.selection_tool.selected_strokes
            if selected:
                current_widget.save_current_state("Change stroke inner shadow")
                for index in selected:
                    if index < len(current_widget.strokes):
                        stroke = current_widget.strokes[index]
                        if hasattr(stroke, 'stroke_type') and stroke.stroke_type == 'image':
                            continue
                        if not isinstance(stroke, dict) or 'type' not in stroke:
                            continue
                        if stroke['type'] in ['line', 'freehand', 'bspline']:
                            stroke['inner_shadow'] = inner
                current_widget.update()
        if current_widget:
            if hasattr(current_widget.line_tool, 'set_inner_shadow'):
                current_widget.line_tool.set_inner_shadow(inner)
            if hasattr(current_widget.freehand_tool, 'set_inner_shadow'):
                current_widget.freehand_tool.set_inner_shadow(inner)
            if hasattr(current_widget.bspline_tool, 'set_inner_shadow'):
                current_widget.bspline_tool.set_inner_shadow(inner)

    def on_stroke_shadow_quality_changed(self, quality):
        """Çizgi gölge kalitesi değişti"""
        current_widget = self.get_current_drawing_widget()
        if current_widget and hasattr(current_widget, 'selection_tool'):
            selected = current_widget.selection_tool.selected_strokes
            if selected:
                current_widget.save_current_state("Change stroke shadow quality")
                for index in selected:
                    if index < len(current_widget.strokes):
                        stroke = current_widget.strokes[index]
                        if hasattr(stroke, 'stroke_type') and stroke.stroke_type == 'image':
                            continue
                        if not isinstance(stroke, dict) or 'type' not in stroke:
                            continue
                        if stroke['type'] in ['line', 'freehand', 'bspline']:
                            stroke['shadow_quality'] = quality
                current_widget.update()
        if current_widget:
            if hasattr(current_widget.line_tool, 'set_shadow_quality'):
                current_widget.line_tool.set_shadow_quality(quality)
            if hasattr(current_widget.freehand_tool, 'set_shadow_quality'):
                current_widget.freehand_tool.set_shadow_quality(quality)
            if hasattr(current_widget.bspline_tool, 'set_shadow_quality'):
                current_widget.bspline_tool.set_shadow_quality(quality)

    def clear_image_cache(self):
        """Image cache klasörünü temizle"""
        try:
            import shutil
            if os.path.exists(self.image_cache_dir):
                shutil.rmtree(self.image_cache_dir)
                os.makedirs(self.image_cache_dir, exist_ok=True)
            self.cached_images.clear()
        except Exception as e:
            print(f"Image cache temizlenirken hata: {e}")

    def setup_actions(self):
        """Menü ve toolbar aksiyonlarını ayarla"""
        # Edit menüsü için kes/kopyala/yapıştır aksiyonları
        self.copy_action = QAction("Kopyala", self)
        self.copy_action.setShortcut(QKeySequence.StandardKey.Copy)
        self.copy_action.triggered.connect(self.copy_selected_strokes)
        
        self.cut_action = QAction("Kes", self)
        self.cut_action.setShortcut(QKeySequence.StandardKey.Cut)
        self.cut_action.triggered.connect(self.cut_selected_strokes)
        
        self.paste_action = QAction("Yapıştır", self)
        self.paste_action.setShortcut(QKeySequence.StandardKey.Paste)
        self.paste_action.triggered.connect(self.paste_strokes)
        
        # Silme aksiyonu
        self.delete_action = QAction("Sil", self)
        self.delete_action.setShortcut(QKeySequence.StandardKey.Delete)
        self.delete_action.triggered.connect(self.delete_selected_strokes)
        
    def setup_menubar(self):
        """Menü çubuğunu oluştur"""
        menubar = self.menuBar()
        
        # Edit menüsü
        edit_menu = menubar.addMenu("Düzenle")
        edit_menu.addAction(self.copy_action)
        edit_menu.addAction(self.cut_action)
        edit_menu.addAction(self.paste_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self.delete_action)
        
    def copy_selected_strokes(self):
        """Seçili stroke'ları kopyala"""
        current_widget = self.get_current_drawing_widget()
        if not current_widget or not current_widget.selection_tool.selected_strokes:
            self.show_status_message("Kopyalanacak öğe seçilmedi")
            return
        
        self.clipboard_strokes = []
        
        # Seçili stroke'ları clipboard'a kopyala
        for index in current_widget.selection_tool.selected_strokes:
            if index < len(current_widget.strokes):
                stroke = current_widget.strokes[index]
                # Deep copy yap
                import copy
                copied_stroke = copy.deepcopy(stroke)
                self.clipboard_strokes.append(copied_stroke)
        
        self.show_status_message(f"{len(self.clipboard_strokes)} öğe kopyalandı")
        
    def cut_selected_strokes(self):
        """Seçili stroke'ları kes"""
        current_widget = self.get_current_drawing_widget()
        if not current_widget or not current_widget.selection_tool.selected_strokes:
            self.show_status_message("Kesilecek öğe seçilmedi")
            return

        if hasattr(current_widget, 'ensure_layer_editable') and not current_widget.ensure_layer_editable():
            return

        # Önce kopyala
        self.copy_selected_strokes()
        
        # Undo için state kaydet
        current_widget.save_current_state("Cut strokes")
        
        # Seçili stroke'ları sil (geriye doğru sıralayarak index problemi olmasın)
        sorted_indices = sorted(current_widget.selection_tool.selected_strokes, reverse=True)
        for index in sorted_indices:
            if index < len(current_widget.strokes):
                current_widget.strokes.pop(index)
        
        # Seçimi temizle
        current_widget.selection_tool.clear_selection()
        current_widget.update_shape_properties()
        current_widget.update()
        
        self.show_status_message(f"{len(self.clipboard_strokes)} öğe kesildi")
        
    def paste_strokes(self):
        """Clipboard'daki stroke'ları yapıştır"""
        current_widget = self.get_current_drawing_widget()
        if not current_widget:
            return

        if not self.clipboard_strokes:
            self.show_status_message("Yapıştırılacak öğe yok")
            return

        if hasattr(current_widget, 'ensure_layer_editable') and not current_widget.ensure_layer_editable():
            return

        # Undo için state kaydet
        current_widget.save_current_state("Paste strokes")
        
        import copy
        pasted_indices = []
        
        # Clipboard'daki her stroke'u yapıştır
        for clipboard_stroke in self.clipboard_strokes:
            # Deep copy yap
            new_stroke = copy.deepcopy(clipboard_stroke)
            
            # Offset uygula (üst üste yapıştırılmasın)
            self.apply_offset_to_stroke_inplace(new_stroke, self.clipboard_offset.x(), self.clipboard_offset.y())
            
            # Stroke'u ekle
            current_widget.strokes.append(new_stroke)
            pasted_indices.append(len(current_widget.strokes) - 1)
        
        # Yapıştırılan stroke'ları seç
        current_widget.selection_tool.selected_strokes = pasted_indices
        current_widget.update_shape_properties()
        current_widget.update()
        
        # Offset'i artır (bir sonraki yapıştırma için)
        self.clipboard_offset += QPointF(20, 20)
        if self.clipboard_offset.x() > 100:  # Reset after 5 pastes
            self.clipboard_offset = QPointF(20, 20)
        
        self.show_status_message(f"{len(self.clipboard_strokes)} öğe yapıştırıldı")
        
    def delete_selected_strokes(self):
        """Seçili stroke'ları sil"""
        current_widget = self.get_current_drawing_widget()
        if not current_widget or not current_widget.selection_tool.selected_strokes:
            self.show_status_message("Silinecek öğe seçilmedi")
            return

        if hasattr(current_widget, 'ensure_layer_editable') and not current_widget.ensure_layer_editable():
            return

        # Undo için state kaydet
        current_widget.save_current_state("Delete strokes")
        
        # Seçili stroke'ları sil (geriye doğru sıralayarak index problemi olmasın)
        sorted_indices = sorted(current_widget.selection_tool.selected_strokes, reverse=True)
        deleted_count = len(sorted_indices)
        
        for index in sorted_indices:
            if index < len(current_widget.strokes):
                current_widget.strokes.pop(index)
        
        # Seçimi temizle
        current_widget.selection_tool.clear_selection()
        current_widget.update_shape_properties()
        current_widget.update()
        
        self.show_status_message(f"{deleted_count} öğe silindi")

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
