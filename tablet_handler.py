from PyQt6.QtCore import QObject, QPointF
from PyQt6.QtGui import QTabletEvent
import time

class TabletHandler(QObject):
    """Tablet kalemi için optimize edilmiş event handler"""
    
    def __init__(self):
        super().__init__()
        self.is_tablet_active = False
        self.last_pressure = 1.0
        self.pressure_threshold = 0.01  # Çok hassas pressure değişimi
        self.last_tablet_time = 0
        self.tablet_throttle_interval = 1.0 / 500.0  # 500 FPS max tablet (real-time yazım)
        
        # Tablet pressure smoothing
        self.pressure_buffer = []
        self.pressure_buffer_size = 3
        
        # Performance flags
        self.high_frequency_mode = False  # Tablet yüksek frekansta event gönderiyorsa
        
    def handle_tablet_event(self, event: QTabletEvent):
        """Tablet event'lerini işle - throttling YOK"""
        self.is_tablet_active = True
        
        # Position al
        pos = QPointF(event.position())
        
        # Raw pressure - smoothing yok
        raw_pressure = event.pressure()
        self.last_pressure = raw_pressure
        
        return pos, raw_pressure, True
        
    def _smooth_pressure(self, pressure):
        """Pressure değerini smooth et"""
        # Buffer'a ekle
        self.pressure_buffer.append(pressure)
        if len(self.pressure_buffer) > self.pressure_buffer_size:
            self.pressure_buffer.pop(0)
            
        # Ortalama al (basit smoothing)
        if len(self.pressure_buffer) == 1:
            return pressure
        else:
            return sum(self.pressure_buffer) / len(self.pressure_buffer)
    
    def get_optimized_pressure(self, event):
        """Event'ten optimize edilmiş pressure al"""
        if hasattr(event, 'pressure'):
            pressure = event.pressure()
            
            # Tablet aktifse smooth pressure kullan
            if self.is_tablet_active:
                return self._smooth_pressure(pressure)
            else:
                return pressure
        else:
            return 1.0
            
    def is_tablet_in_use(self):
        """Tablet kullanımda mı?"""
        return self.is_tablet_active
        
    def reset_tablet_state(self):
        """Tablet state'ini sıfırla"""
        self.is_tablet_active = False
        self.pressure_buffer = []
        
    def set_high_frequency_mode(self, enabled):
        """Yüksek frekanslı tablet için mod ayarla"""
        self.high_frequency_mode = enabled
        if enabled:
            self.tablet_throttle_interval = 1.0 / 200.0  # Yüksek frekans için orta throttling
            self.pressure_buffer_size = 2  # Daha küçük buffer
        else:
            self.tablet_throttle_interval = 1.0 / 500.0  # Normal tablet için çok yüksek FPS
            self.pressure_buffer_size = 2  # Yazım için küçük buffer 