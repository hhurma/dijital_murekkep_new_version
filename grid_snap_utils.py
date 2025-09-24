from PyQt6.QtCore import QPointF
import math

class GridSnapUtils:
    """Grid'e yapıştırma yardımcı fonksiyonları (tek kaynak: grid_settings)."""
    
    @staticmethod
    def _get_snap_step(grid_settings):
        """Snap grid aralığını döndür"""
        if not grid_settings:
            return 20.0
        return float(grid_settings.get('snap_grid_size', 20))
    
    @staticmethod
    def _get_minor_step(grid_settings):
        """İnce adım: snap grid aralığına eşit kabul edilir (tek kaynak)."""
        if not grid_settings:
            return 20.0
        step = float(grid_settings.get('snap_grid_size', 20))
        return max(1.0, step)

    @staticmethod
    def snap_point_to_grid(point, grid_settings):
        """Bir noktayı snap grid'e yapıştır"""
        if not grid_settings or not grid_settings.get('snap_to_grid', False):
            return point
            
        step = GridSnapUtils._get_snap_step(grid_settings)
        if step <= 0:
            return point
            
        # En yakın grid noktasına yuvarlama - daha hassas
        x = round(point.x() / step) * step
        y = round(point.y() / step) * step
        
        return QPointF(float(x), float(y))
    
    @staticmethod
    def snap_point_to_grid_precise(point, grid_settings, force_snap=True):
        """Bir noktayı snap grid'e kesin olarak yapıştır"""
        if not grid_settings or (not grid_settings.get('snap_to_grid', False) and not force_snap):
            return point
            
        step = GridSnapUtils._get_snap_step(grid_settings)
        if step <= 0:
            return point
            
        # Tam grid koordinatlarına yuvarlama
        x = round(point.x() / step) * step
        y = round(point.y() / step) * step
        
        # Float precision sorunlarını önle
        x = round(x, 2)
        y = round(y, 2)
        
        return QPointF(x, y)
    
    @staticmethod
    def snap_rect_to_grid(rect, grid_settings):
        """Bir dikdörtgeni grid'e yapıştır"""
        if not grid_settings or not grid_settings.get('snap_to_grid', False):
            return rect
            
        # Köşeleri grid'e yapıştır
        top_left = GridSnapUtils.snap_point_to_grid_precise(rect.topLeft(), grid_settings)
        bottom_right = GridSnapUtils.snap_point_to_grid_precise(rect.bottomRight(), grid_settings)
        
        from PyQt6.QtCore import QRectF
        return QRectF(top_left, bottom_right)
    
    @staticmethod
    def snap_line_to_grid(start_point, end_point, grid_settings):
        """Bir çizgiyi grid'e yapıştır"""
        if not grid_settings or not grid_settings.get('snap_to_grid', False):
            return start_point, end_point
            
        snapped_start = GridSnapUtils.snap_point_to_grid_precise(start_point, grid_settings)
        snapped_end = GridSnapUtils.snap_point_to_grid_precise(end_point, grid_settings)
        
        return snapped_start, snapped_end
    
    @staticmethod
    def snap_circle_to_grid(center, radius, grid_settings):
        """Bir çemberi grid'e yapıştır"""
        if not grid_settings or not grid_settings.get('snap_to_grid', False):
            return center, radius
            
        step = GridSnapUtils._get_minor_step(grid_settings)
        if step <= 0:
            return center, radius
            
        # Merkezi grid'e yapıştır
        snapped_center = GridSnapUtils.snap_point_to_grid_precise(center, grid_settings)
        
        # Yarıçapı grid'in katına yuvarlama (isteğe bağlı)
        snapped_radius = round(radius / step) * step
        if snapped_radius == 0:
            snapped_radius = step
            
        return snapped_center, snapped_radius
    
    @staticmethod
    def snap_stroke_to_grid(stroke_data, grid_settings):
        """Bir stroke'u tamamen grid'e yapıştır"""
        if not grid_settings or not grid_settings.get('snap_to_grid', False):
            return stroke_data
            
        stroke_copy = stroke_data.copy()
        stroke_type = stroke_copy.get('type', '')
        
        if stroke_type == 'freehand':
            # Freehand points'leri snap'le
            if 'points' in stroke_copy:
                snapped_points = []
                for point in stroke_copy['points']:
                    if isinstance(point, dict):
                        original_point = QPointF(point['x'], point['y'])
                        snapped_point = GridSnapUtils.snap_point_to_grid_precise(original_point, grid_settings)
                        snapped_points.append({'x': snapped_point.x(), 'y': snapped_point.y()})
                    else:
                        snapped_points.append(point)
                stroke_copy['points'] = snapped_points
                
        elif stroke_type == 'bspline':
            # B-spline control points'leri snap'le
            if 'control_points' in stroke_copy:
                snapped_points = []
                for cp in stroke_copy['control_points']:
                    original_point = QPointF(cp[0], cp[1])
                    snapped_point = GridSnapUtils.snap_point_to_grid_precise(original_point, grid_settings)
                    snapped_points.append([snapped_point.x(), snapped_point.y()])
                stroke_copy['control_points'] = snapped_points
                
        elif stroke_type == 'line':
            # Line endpoints'leri snap'le
            if 'start_point' in stroke_copy:
                start = QPointF(stroke_copy['start_point'][0], stroke_copy['start_point'][1])
                snapped_start = GridSnapUtils.snap_point_to_grid_precise(start, grid_settings)
                stroke_copy['start_point'] = (snapped_start.x(), snapped_start.y())
                
            if 'end_point' in stroke_copy:
                end = QPointF(stroke_copy['end_point'][0], stroke_copy['end_point'][1])
                snapped_end = GridSnapUtils.snap_point_to_grid_precise(end, grid_settings)
                stroke_copy['end_point'] = (snapped_end.x(), snapped_end.y())
                
        elif stroke_type == 'rectangle':
            # Rectangle corner'larını snap'le
            if 'corners' in stroke_copy:
                snapped_corners = []
                for corner in stroke_copy['corners']:
                    original_point = QPointF(corner[0], corner[1])
                    snapped_point = GridSnapUtils.snap_point_to_grid_precise(original_point, grid_settings)
                    snapped_corners.append((snapped_point.x(), snapped_point.y()))
                stroke_copy['corners'] = snapped_corners
            elif 'top_left' in stroke_copy and 'bottom_right' in stroke_copy:
                # Eski format
                tl = QPointF(stroke_copy['top_left'][0], stroke_copy['top_left'][1])
                br = QPointF(stroke_copy['bottom_right'][0], stroke_copy['bottom_right'][1])
                snapped_tl = GridSnapUtils.snap_point_to_grid_precise(tl, grid_settings)
                snapped_br = GridSnapUtils.snap_point_to_grid_precise(br, grid_settings)
                stroke_copy['top_left'] = (snapped_tl.x(), snapped_tl.y())
                stroke_copy['bottom_right'] = (snapped_br.x(), snapped_br.y())
                
        elif stroke_type == 'circle':
            # Circle center'ını snap'le
            if 'center' in stroke_copy:
                center = QPointF(stroke_copy['center'][0], stroke_copy['center'][1])
                snapped_center = GridSnapUtils.snap_point_to_grid_precise(center, grid_settings)
                stroke_copy['center'] = (snapped_center.x(), snapped_center.y())
                
            # Radius'u da grid'e uygun hale getir
            if 'radius' in stroke_copy:
                grid_size = float(grid_settings.get('snap_grid_size', 20))
                snapped_radius = round(float(stroke_copy['radius']) / grid_size) * grid_size
                if snapped_radius == 0:
                    snapped_radius = grid_size
                stroke_copy['radius'] = snapped_radius
        
        return stroke_copy
    
    @staticmethod
    def get_snap_indicator_points(point, grid_settings):
        """Snap noktası için görsel gösterge noktaları al"""
        if not grid_settings or not grid_settings.get('snap_to_grid', False):
            return []
            
        snap_point = GridSnapUtils.snap_point_to_grid_precise(point, grid_settings)
        
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
    def is_near_grid_point(point, grid_settings, tolerance=10):
        """Nokta grid çizgisine yakın mı kontrol et"""
        if not grid_settings or not grid_settings.get('snap_to_grid', False):
            return False
            
        step = GridSnapUtils._get_minor_step(grid_settings)
        if step <= 0:
            return False
            
        # En yakın grid noktası
        snap_point = GridSnapUtils.snap_point_to_grid_precise(point, grid_settings)
        
        # Mesafe kontrolü
        distance = math.sqrt((point.x() - snap_point.x())**2 + (point.y() - snap_point.y())**2)
        
        return distance <= tolerance 