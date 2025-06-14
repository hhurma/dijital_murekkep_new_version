from PyQt6.QtCore import QPointF
import math

class GridSnapUtils:
    """Grid'e yapıştırma yardımcı fonksiyonları"""
    
    @staticmethod
    def snap_point_to_grid(point, background_settings):
        """Bir noktayı grid'e yapıştır"""
        if not background_settings or not background_settings.get('snap_to_grid', False):
            return point
            
        grid_size = background_settings.get('grid_size', 20)
        if grid_size <= 0:
            return point
            
        # En yakın grid noktasına yuvarlama
        x = round(point.x() / grid_size) * grid_size
        y = round(point.y() / grid_size) * grid_size
        
        return QPointF(x, y)
    
    @staticmethod
    def snap_rect_to_grid(rect, background_settings):
        """Bir dikdörtgeni grid'e yapıştır"""
        if not background_settings or not background_settings.get('snap_to_grid', False):
            return rect
            
        # Köşeleri grid'e yapıştır
        top_left = GridSnapUtils.snap_point_to_grid(rect.topLeft(), background_settings)
        bottom_right = GridSnapUtils.snap_point_to_grid(rect.bottomRight(), background_settings)
        
        from PyQt6.QtCore import QRectF
        return QRectF(top_left, bottom_right)
    
    @staticmethod
    def snap_line_to_grid(start_point, end_point, background_settings):
        """Bir çizgiyi grid'e yapıştır"""
        if not background_settings or not background_settings.get('snap_to_grid', False):
            return start_point, end_point
            
        snapped_start = GridSnapUtils.snap_point_to_grid(start_point, background_settings)
        snapped_end = GridSnapUtils.snap_point_to_grid(end_point, background_settings)
        
        return snapped_start, snapped_end
    
    @staticmethod
    def snap_circle_to_grid(center, radius, background_settings):
        """Bir çemberi grid'e yapıştır"""
        if not background_settings or not background_settings.get('snap_to_grid', False):
            return center, radius
            
        grid_size = background_settings.get('grid_size', 20)
        if grid_size <= 0:
            return center, radius
            
        # Merkezi grid'e yapıştır
        snapped_center = GridSnapUtils.snap_point_to_grid(center, background_settings)
        
        # Yarıçapı grid'in katına yuvarlama (isteğe bağlı)
        snapped_radius = round(radius / grid_size) * grid_size
        if snapped_radius == 0:
            snapped_radius = grid_size
            
        return snapped_center, snapped_radius
    
    @staticmethod
    def get_snap_indicator_points(point, background_settings):
        """Snap noktası için görsel gösterge noktaları al"""
        if not background_settings or not background_settings.get('snap_to_grid', False):
            return []
            
        snap_point = GridSnapUtils.snap_point_to_grid(point, background_settings)
        
        # Çapraz gösterge için noktalar
        indicator_size = 5
        points = [
            QPointF(snap_point.x() - indicator_size, snap_point.y()),
            QPointF(snap_point.x() + indicator_size, snap_point.y()),
            QPointF(snap_point.x(), snap_point.y() - indicator_size),
            QPointF(snap_point.x(), snap_point.y() + indicator_size)
        ]
        
        return points
    
    @staticmethod
    def is_near_grid_point(point, background_settings, tolerance=10):
        """Nokta grid çizgisine yakın mı kontrol et"""
        if not background_settings or not background_settings.get('snap_to_grid', False):
            return False
            
        grid_size = background_settings.get('grid_size', 20)
        if grid_size <= 0:
            return False
            
        # En yakın grid noktası
        snap_point = GridSnapUtils.snap_point_to_grid(point, background_settings)
        
        # Mesafe kontrolü
        distance = math.sqrt((point.x() - snap_point.x())**2 + (point.y() - snap_point.y())**2)
        
        return distance <= tolerance 