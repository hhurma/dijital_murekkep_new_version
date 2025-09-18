import time
from enum import Enum

class ThrottleType(Enum):
    """Throttle türleri"""
    GENERAL = "general"
    FREEHAND = "freehand"
    TABLET = "tablet"

class ThrottleManager:
    """DrawingWidget için throttling işlemlerini yöneten sınıf"""
    
    def __init__(self, drawing_widget):
        self.drawing_widget = drawing_widget
        
        # Throttle türleri için ayrı time tracking
        self._last_update_times = {
            ThrottleType.GENERAL: 0,
            ThrottleType.FREEHAND: 0,
            ThrottleType.TABLET: 0
        }
        
        # Throttle ayarları
        self.throttle_settings = {
            ThrottleType.GENERAL: {
                'stroke_threshold': 100,  # 100'den fazla stroke varsa throttling
                'fps_limit': 30,          # 30 FPS limit
                'enabled': True
            },
            ThrottleType.FREEHAND: {
                'stroke_threshold': 50,   # 50'den fazla stroke varsa hafif throttling
                'fps_limit': 60,          # 60 FPS limit
                'enabled': True
            },
            ThrottleType.TABLET: {
                'stroke_threshold': 80,   # 80'den fazla stroke varsa hafif throttling
                'fps_limit': 90,          # 90 FPS - tablet için yüksek
                'enabled': True
            }
        }
    
    def should_throttle(self, throttle_type: ThrottleType) -> bool:
        """Throttling gerekip gerekmediğini kontrol et"""
        settings = self.throttle_settings[throttle_type]
        
        if not settings['enabled']:
            return False
            
        # Stroke sayısı threshold'u geçmişse throttling aktif
        stroke_count = 0
        if hasattr(self.drawing_widget, 'layer_manager'):
            stroke_count = self.drawing_widget.layer_manager.count_visible_strokes()
        elif hasattr(self.drawing_widget, 'strokes'):
            stroke_count = len(self.drawing_widget.strokes)
        return stroke_count > settings['stroke_threshold']
    
    def can_update(self, throttle_type: ThrottleType) -> bool:
        """Update yapılıp yapılamayacağını kontrol et"""
        if not self.should_throttle(throttle_type):
            return True  # Throttling gerekmiyor, direkt update
            
        settings = self.throttle_settings[throttle_type]
        current_time = time.time()
        last_time = self._last_update_times[throttle_type]
        min_interval = 1.0 / settings['fps_limit']
        
        return current_time - last_time > min_interval
    
    def update_with_throttle(self, throttle_type: ThrottleType) -> bool:
        """Throttling kontrolü yaparak update işlemi"""
        if self.can_update(throttle_type):
            self.drawing_widget.update()
            self._last_update_times[throttle_type] = time.time()
            return True
        return False
    
    def throttled_update(self) -> bool:
        """Genel akıllı throttling"""
        return self.update_with_throttle(ThrottleType.GENERAL)
            
    def throttled_freehand_update(self) -> bool:
        """Freehand için minimal throttling"""
        return self.update_with_throttle(ThrottleType.FREEHAND)
    
    def throttled_tablet_update(self) -> bool:
        """Tablet için akıllı throttling - yazım kalitesini korur"""
        return self.update_with_throttle(ThrottleType.TABLET)
    
    def force_update(self):
        """Throttling'i bypass ederek direkt update"""
        self.drawing_widget.update()
        # Tüm throttle timer'larını güncelle
        current_time = time.time()
        for throttle_type in ThrottleType:
            self._last_update_times[throttle_type] = current_time
    
    def configure_throttle(self, throttle_type: ThrottleType, **kwargs):
        """Throttle ayarlarını güncelle"""
        settings = self.throttle_settings[throttle_type]
        
        if 'stroke_threshold' in kwargs:
            settings['stroke_threshold'] = kwargs['stroke_threshold']
        if 'fps_limit' in kwargs:
            settings['fps_limit'] = kwargs['fps_limit']
        if 'enabled' in kwargs:
            settings['enabled'] = kwargs['enabled']
    
    def disable_throttle(self, throttle_type: ThrottleType = None):
        """Throttling'i devre dışı bırak"""
        if throttle_type is None:
            # Tüm throttling'i devre dışı bırak
            for t_type in ThrottleType:
                self.throttle_settings[t_type]['enabled'] = False
        else:
            self.throttle_settings[throttle_type]['enabled'] = False
    
    def enable_throttle(self, throttle_type: ThrottleType = None):
        """Throttling'i etkinleştir"""
        if throttle_type is None:
            # Tüm throttling'i etkinleştir
            for t_type in ThrottleType:
                self.throttle_settings[t_type]['enabled'] = True
        else:
            self.throttle_settings[throttle_type]['enabled'] = True
    
    def get_throttle_stats(self) -> dict:
        """Throttle istatistiklerini döndür"""
        if hasattr(self.drawing_widget, 'layer_manager'):
            stroke_count = self.drawing_widget.layer_manager.count_visible_strokes()
        else:
            stroke_count = len(self.drawing_widget.strokes) if hasattr(self.drawing_widget, 'strokes') else 0
        current_time = time.time()
        
        stats = {
            'stroke_count': stroke_count,
            'throttle_states': {}
        }
        
        for throttle_type in ThrottleType:
            settings = self.throttle_settings[throttle_type]
            last_time = self._last_update_times[throttle_type]
            
            stats['throttle_states'][throttle_type.value] = {
                'enabled': settings['enabled'],
                'should_throttle': self.should_throttle(throttle_type),
                'can_update': self.can_update(throttle_type),
                'fps_limit': settings['fps_limit'],
                'stroke_threshold': settings['stroke_threshold'],
                'time_since_last_update': current_time - last_time if last_time > 0 else 0
            }
        
        return stats
    
    def reset_timers(self):
        """Tüm throttle timer'larını sıfırla"""
        for throttle_type in ThrottleType:
            self._last_update_times[throttle_type] = 0
    
    def set_performance_mode(self, mode: str):
        """Performans modunu ayarla"""
        if mode == "high_performance":
            # Yüksek performans - daha az throttling
            self.configure_throttle(ThrottleType.GENERAL, stroke_threshold=200, fps_limit=60)
            self.configure_throttle(ThrottleType.FREEHAND, stroke_threshold=100, fps_limit=120)
            self.configure_throttle(ThrottleType.TABLET, stroke_threshold=150, fps_limit=144)
            
        elif mode == "balanced":
            # Dengeli mod - varsayılan ayarlar
            self.configure_throttle(ThrottleType.GENERAL, stroke_threshold=100, fps_limit=30)
            self.configure_throttle(ThrottleType.FREEHAND, stroke_threshold=50, fps_limit=60)
            self.configure_throttle(ThrottleType.TABLET, stroke_threshold=80, fps_limit=90)
            
        elif mode == "battery_saver":
            # Pil tasarrufu - daha fazla throttling
            self.configure_throttle(ThrottleType.GENERAL, stroke_threshold=50, fps_limit=20)
            self.configure_throttle(ThrottleType.FREEHAND, stroke_threshold=25, fps_limit=30)
            self.configure_throttle(ThrottleType.TABLET, stroke_threshold=40, fps_limit=45)
            
        elif mode == "no_throttling":
            # Throttling yok - maksimum kalite
            self.disable_throttle()
    
    def auto_adjust_settings(self):
        """Sistem performansına göre otomatik ayarlama"""
        import psutil
        
        try:
            # CPU kullanımı kontrol et
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_percent = psutil.virtual_memory().percent
            
            if cpu_percent > 80 or memory_percent > 85:
                # Yüksek sistem yükü - daha agresif throttling
                self.set_performance_mode("battery_saver")
            elif cpu_percent > 60 or memory_percent > 70:
                # Orta sistem yükü - dengeli mod
                self.set_performance_mode("balanced")
            else:
                # Düşük sistem yükü - yüksek performans
                self.set_performance_mode("high_performance")
                
        except ImportError:
            # psutil yoksa varsayılan dengeli moda geç
            self.set_performance_mode("balanced") 