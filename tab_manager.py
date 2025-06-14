from PyQt6.QtWidgets import QTabWidget, QWidget, QVBoxLayout
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
        
        # Tab'ı ekle
        index = self.tab_widget.addTab(drawing_widget, tab_name)
        self.tab_widget.setCurrentIndex(index)
        
        # Yeni tab için ayarları yükle
        self.main_window.load_settings_to_tab(drawing_widget)
        
        # Aktif aracı ayarlardan yükle
        active_tool = self.main_window.settings.get_active_tool()
        drawing_widget.set_active_tool(active_tool)
        
        # Toolbar'da aktif aracı seç
        self.main_window.set_tool(active_tool)
        
        return drawing_widget
    
    def close_tab(self, index):
        """Tab'ı kapat"""
        if self.tab_widget.count() > 1:  # En az bir tab kalsın
            self.tab_widget.removeTab(index)
        else:
            # Son tab ise sadece temizle
            drawing_widget = self.tab_widget.widget(index)
            if drawing_widget:
                drawing_widget.clear_all_strokes()
    
    def get_current_drawing_widget(self):
        """Aktif çizim widget'ını döndür"""
        return self.tab_widget.currentWidget()
    
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
        return self.tab_widget.widget(index)
    
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