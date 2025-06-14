from PyQt6.QtCore import QObject, pyqtSignal, Qt, QPointF
from PyQt6.QtWidgets import QWidget, QSlider, QLabel, QHBoxLayout

class ZoomManager(QObject):
    """Zoom işlemlerini yöneten sınıf"""
    
    zoomChanged = pyqtSignal(float)  # Zoom değeri değiştiğinde sinyal
    panChanged = pyqtSignal(object)  # Pan offset değiştiğinde sinyal (QPointF)
    
    def __init__(self):
        super().__init__()
        self.zoom_level = 1.0  # %100 zoom
        self.min_zoom = 0.1    # %10 minimum
        self.max_zoom = 5.0    # %500 maksimum
        self.zoom_step = 0.1   # Zoom adımı
        self.wheel_zoom_step = 0.05  # Mouse wheel zoom adımı
        
        # Pan ayarları
        self.pan_offset = QPointF(0, 0)
        self.is_panning = False
        self.last_pan_point = QPointF(0, 0)
    
    def zoom_in(self):
        """Yakınlaştır"""
        new_zoom = min(self.zoom_level + self.zoom_step, self.max_zoom)
        self.set_zoom_level(new_zoom)
    
    def zoom_out(self):
        """Uzaklaştır"""
        new_zoom = max(self.zoom_level - self.zoom_step, self.min_zoom)
        self.set_zoom_level(new_zoom)
    
    def wheel_zoom_in(self, center_point=None):
        """Mouse wheel ile yakınlaştır"""
        old_zoom = self.zoom_level
        new_zoom = min(self.zoom_level + self.wheel_zoom_step, self.max_zoom)
        
        if center_point and abs(new_zoom - old_zoom) > 0.001:
            # Zoom merkezi etrafında yakınlaştır
            self.zoom_at_point(new_zoom, center_point)
        else:
            self.set_zoom_level(new_zoom)
    
    def wheel_zoom_out(self, center_point=None):
        """Mouse wheel ile uzaklaştır"""
        old_zoom = self.zoom_level
        new_zoom = max(self.zoom_level - self.wheel_zoom_step, self.min_zoom)
        
        if center_point and abs(new_zoom - old_zoom) > 0.001:
            # Zoom merkezi etrafında uzaklaştır
            self.zoom_at_point(new_zoom, center_point)
        else:
            self.set_zoom_level(new_zoom)
    
    def zoom_at_point(self, new_zoom, center_point):
        """Belirtilen nokta etrafında zoom yap"""
        if abs(self.zoom_level - new_zoom) < 0.001:
            return
            
        # Zoom merkezi hesapla
        zoom_factor = new_zoom / self.zoom_level
        
        # Pan offset'i ayarla (zoom merkezi sabit kalsın)
        self.pan_offset = QPointF(
            center_point.x() - (center_point.x() - self.pan_offset.x()) * zoom_factor,
            center_point.y() - (center_point.y() - self.pan_offset.y()) * zoom_factor
        )
        
        self.zoom_level = new_zoom
        self.zoomChanged.emit(self.zoom_level)
        self.panChanged.emit(self.pan_offset)
    
    def reset_zoom(self):
        """Zoom'u sıfırla (%100)"""
        self.set_zoom_level(1.0)
        self.reset_pan()
    
    def start_pan(self, start_point):
        """Pan işlemini başlat"""
        self.is_panning = True
        self.last_pan_point = QPointF(start_point)
    
    def update_pan(self, current_point):
        """Pan işlemini güncelle"""
        if not self.is_panning:
            return False
            
        # Pan delta hesapla
        delta = QPointF(current_point) - self.last_pan_point
        
        # Pan offset'i güncelle
        self.pan_offset += delta
        self.last_pan_point = QPointF(current_point)
        
        self.panChanged.emit(self.pan_offset)
        return True
    
    def finish_pan(self):
        """Pan işlemini bitir"""
        self.is_panning = False
    
    def reset_pan(self):
        """Pan'i sıfırla"""
        self.pan_offset = QPointF(0, 0)
        self.panChanged.emit(self.pan_offset)
    
    def get_pan_offset(self):
        """Pan offset'ini döndür"""
        return self.pan_offset
    
    def set_pan_offset(self, offset):
        """Pan offset'ini ayarla"""
        self.pan_offset = QPointF(offset)
        self.panChanged.emit(self.pan_offset)
    
    def fit_to_window(self, widget_size, content_size):
        """İçeriği pencereye sığdır"""
        if content_size.width() == 0 or content_size.height() == 0:
            return
            
        scale_x = widget_size.width() / content_size.width()
        scale_y = widget_size.height() / content_size.height()
        scale = min(scale_x, scale_y) * 0.9  # %90 sığdır (margin için)
        
        self.set_zoom_level(max(self.min_zoom, min(scale, self.max_zoom)))
    
    def set_zoom_level(self, zoom_level):
        """Zoom seviyesini ayarla"""
        zoom_level = max(self.min_zoom, min(zoom_level, self.max_zoom))
        if abs(self.zoom_level - zoom_level) > 0.001:  # Küçük değişiklikleri göz ardı et
            self.zoom_level = zoom_level
            self.zoomChanged.emit(self.zoom_level)
    
    def get_zoom_level(self):
        """Mevcut zoom seviyesini döndür"""
        return self.zoom_level
    
    def get_zoom_percentage(self):
        """Zoom seviyesini yüzde olarak döndür"""
        return int(self.zoom_level * 100)

class ZoomWidget(QWidget):
    """Zoom kontrolü için widget"""
    
    zoomChanged = pyqtSignal(float)
    panChanged = pyqtSignal(object)  # QPointF
    
    def __init__(self):
        super().__init__()
        self.zoom_manager = ZoomManager()
        self.setup_ui()
        
        # Zoom manager sinyallerini bağla
        self.zoom_manager.zoomChanged.connect(self.on_zoom_changed)
        self.zoom_manager.zoomChanged.connect(self.zoomChanged.emit)
        self.zoom_manager.panChanged.connect(self.panChanged.emit)
    
    def setup_ui(self):
        """UI'yi oluştur"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)
        
        # Zoom etiketi
        self.zoom_label = QLabel("100%")
        self.zoom_label.setMinimumWidth(40)
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.zoom_label)
        
        # Zoom slider
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setMinimum(int(self.zoom_manager.min_zoom * 100))  # %10
        self.zoom_slider.setMaximum(int(self.zoom_manager.max_zoom * 100))  # %500
        self.zoom_slider.setValue(100)  # %100
        self.zoom_slider.setFixedWidth(100)
        self.zoom_slider.valueChanged.connect(self.on_slider_changed)
        layout.addWidget(self.zoom_slider)
    
    def on_slider_changed(self, value):
        """Slider değiştiğinde"""
        zoom_level = value / 100.0
        self.zoom_manager.set_zoom_level(zoom_level)
    
    def on_zoom_changed(self, zoom_level):
        """Zoom değiştiğinde UI'yi güncelle"""
        percentage = int(zoom_level * 100)
        self.zoom_label.setText(f"{percentage}%")
        
        # Slider'ı güncelle (sinyal döngüsünü önlemek için)
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(percentage)
        self.zoom_slider.blockSignals(False)
    
    def zoom_in(self):
        """Yakınlaştır"""
        self.zoom_manager.zoom_in()
    
    def zoom_out(self):
        """Uzaklaştır"""
        self.zoom_manager.zoom_out()
    
    def reset_zoom(self):
        """Zoom'u sıfırla"""
        self.zoom_manager.reset_zoom()
    
    def fit_to_window(self, widget_size, content_size):
        """İçeriği pencereye sığdır"""
        self.zoom_manager.fit_to_window(widget_size, content_size)
    
    def get_zoom_level(self):
        """Mevcut zoom seviyesini döndür"""
        return self.zoom_manager.get_zoom_level()
    
    def wheel_zoom_in(self, center_point=None):
        """Mouse wheel ile yakınlaştır"""
        self.zoom_manager.wheel_zoom_in(center_point)
    
    def wheel_zoom_out(self, center_point=None):
        """Mouse wheel ile uzaklaştır"""
        self.zoom_manager.wheel_zoom_out(center_point)
    
    def start_pan(self, start_point):
        """Pan işlemini başlat"""
        self.zoom_manager.start_pan(start_point)
    
    def update_pan(self, current_point):
        """Pan işlemini güncelle"""
        return self.zoom_manager.update_pan(current_point)
    
    def finish_pan(self):
        """Pan işlemini bitir"""
        self.zoom_manager.finish_pan()
    
    def reset_pan(self):
        """Pan'i sıfırla"""
        self.zoom_manager.reset_pan()
    
    def get_pan_offset(self):
        """Pan offset'ini döndür"""
        return self.zoom_manager.get_pan_offset()
    
    def set_pan_offset(self, offset):
        """Pan offset'ini ayarla"""
        self.zoom_manager.set_pan_offset(offset) 