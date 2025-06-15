from PyQt6.QtWidgets import QTabWidget, QWidget, QVBoxLayout, QScrollArea
from PyQt6.QtCore import Qt, pyqtSignal
from DrawingWidget import DrawingWidget
from undo_redo_manager import UndoRedoManager

class TabManager:
    """Tab yönetimi işlemlerini yöneten sınıf"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.tab_widget = None
        self.setup_tab_widget()
    
    def setup_tab_widget(self):
        """Tab widget'ını oluştur ve ayarla"""
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.setDocumentMode(True)  # Daha modern görünüm
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        
        # Tab styling
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #c0c0c0;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #f0f0f0;
                border: 1px solid #c0c0c0;
                padding: 8px 16px;
                margin-right: 2px;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 1px solid white;
            }
            QTabBar::tab:hover {
                background-color: #e8e8e8;
            }
        """)
        
        # Tab değişikliklerini takip et
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
    
    def get_tab_widget(self):
        """Tab widget'ını döndür"""
        return self.tab_widget
    
    def create_new_tab(self, tab_name=None):
        """Yeni tab oluştur"""
        # Yeni DrawingWidget oluştur
        drawing_widget = DrawingWidget()
        drawing_widget.set_main_window(self.main_window)
        
        # DrawingWidget'ı QScrollArea ile sar
        scroll_area = QScrollArea()
        scroll_area.setWidget(drawing_widget)
        scroll_area.setWidgetResizable(False)  # Widget'ın kendi boyutunu korusun
        scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Merkezde konumlandır
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Scroll area stil ayarları
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f0f0f0;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 14px;
                border-radius: 7px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                border-radius: 7px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
            QScrollBar:horizontal {
                border: none;
                background: #f0f0f0;
                height: 14px;
                border-radius: 7px;
            }
            QScrollBar::handle:horizontal {
                background: #c0c0c0;
                border-radius: 7px;
                min-width: 30px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #a0a0a0;
            }
        """)
        
        # Undo/Redo manager ekle
        undo_manager = UndoRedoManager()
        drawing_widget.set_undo_manager(undo_manager)
        
        # Undo/Redo sinyallerini bağla
        undo_manager.canUndoChanged.connect(self.main_window.undo_action.setEnabled)
        undo_manager.canRedoChanged.connect(self.main_window.redo_action.setEnabled)
        
        # Tab adını belirle
        if tab_name is None:
            tab_count = self.tab_widget.count() + 1
            tab_name = f"Çizim {tab_count}"
        
        # Tab'ı ekle (scroll_area'yı tab olarak ekle)
        index = self.tab_widget.addTab(scroll_area, tab_name)
        self.tab_widget.setCurrentIndex(index)
        
        # Yeni tab için ayarları yükle
        self.main_window.load_settings_to_tab(drawing_widget)
        
        # Aktif aracı ayarlardan yükle
        active_tool = self.main_window.settings.get_active_tool()
        drawing_widget.set_active_tool(active_tool)
        
        # Toolbar'da aktif aracı seç
        self.main_window.set_tool(active_tool)
        
        # Zoom level'ı %100 olarak ayarla
        drawing_widget.set_zoom_level(1.0)  # %100 zoom
        if hasattr(self.main_window, 'zoom_widget'):
            self.main_window.zoom_widget.zoom_manager.set_zoom_level(1.0)  # %100 olarak göster
        
        return drawing_widget
    
    def close_tab(self, index):
        """Tab'ı kapat"""
        if self.tab_widget.count() > 1:  # En az bir tab kalsın
            self.tab_widget.removeTab(index)
        else:
            # Son tab ise sadece temizle
            widget = self.tab_widget.widget(index)
            if widget and hasattr(widget, 'widget'):
                # Eğer QScrollArea ise, içindeki drawing widget'ı al
                drawing_widget = widget.widget()
            else:
                drawing_widget = widget
                
            if drawing_widget:
                drawing_widget.clear_all_strokes()
    
    def get_current_drawing_widget(self):
        """Aktif çizim widget'ını döndür"""
        current_widget = self.tab_widget.currentWidget()
        if current_widget and hasattr(current_widget, 'widget'):
            # Eğer QScrollArea ise, içindeki widget'ı döndür
            return current_widget.widget()
        return current_widget
    
    def on_tab_changed(self, index):
        """Tab değiştiğinde çağrılır"""
        self.main_window.connect_toolbar_to_active_tab()
        
        # Aktif tab'ın undo/redo durumunu güncelle
        current_widget = self.get_current_drawing_widget()
        if current_widget and hasattr(current_widget, 'undo_manager'):
            self.main_window.undo_action.setEnabled(current_widget.undo_manager.can_undo())
            self.main_window.redo_action.setEnabled(current_widget.undo_manager.can_redo())
    
    def get_tab_count(self):
        """Tab sayısını döndür"""
        return self.tab_widget.count()
    
    def get_tab_widget_at_index(self, index):
        """Belirtilen indeksteki widget'ı döndür"""
        widget = self.tab_widget.widget(index)
        if widget and hasattr(widget, 'widget'):
            # Eğer QScrollArea ise, içindeki widget'ı döndür
            return widget.widget()
        return widget
    
    def get_tab_text(self, index):
        """Belirtilen indeksteki tab adını döndür"""
        return self.tab_widget.tabText(index)
    
    def set_tab_text(self, index, text):
        """Belirtilen indeksteki tab adını değiştir"""
        self.tab_widget.setTabText(index, text)
    
    def get_current_index(self):
        """Aktif tab indeksini döndür"""
        return self.tab_widget.currentIndex()
    
    def set_current_index(self, index):
        """Belirtilen indeksteki tab'ı aktif yap"""
        self.tab_widget.setCurrentIndex(index)
    
    def clear_all_tabs(self):
        """Tüm tab'ları temizle"""
        while self.tab_widget.count() > 0:
            self.tab_widget.removeTab(0) 