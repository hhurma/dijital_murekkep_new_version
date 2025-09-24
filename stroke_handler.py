from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QPen, QBrush
from PyQt6.QtCore import Qt
import numpy as np

def ensure_qpointf(point):
    """Point'i QPointF'e dönüştür (dict'ten veya zaten QPointF'ten)"""
    if isinstance(point, dict):
        return QPointF(point['x'], point['y'])
    elif isinstance(point, QPointF):
        return point
    else:
        # Başka bir format, deneme
        return QPointF(point.x(), point.y())

class StrokeHandler:
    """Tüm stroke tiplerini modüler şekilde işleyen base sınıf"""
    
    @staticmethod
    def get_stroke_points(stroke_data):
        """Stroke tipine göre noktaları döndür"""
        # Image stroke kontrolü
        if hasattr(stroke_data, 'stroke_type') and stroke_data.stroke_type == 'image':
            bounds = stroke_data.get_bounds()
            return [
                (bounds.left(), bounds.top()),
                (bounds.right(), bounds.top()),
                (bounds.left(), bounds.bottom()),
                (bounds.right(), bounds.bottom())
            ]
        
        # Dict kontrolü
        if not hasattr(stroke_data, 'get'):
            return []
            
        if stroke_data['type'] == 'bspline':
            return stroke_data['control_points']
        elif stroke_data['type'] == 'freehand':
            # Point'leri (x, y) tuple'larına çevir
            points = []
            for p in stroke_data['points']:
                point_qf = ensure_qpointf(p)
                points.append((point_qf.x(), point_qf.y()))
            return points
        elif stroke_data['type'] == 'line':
            return [stroke_data['start_point'], stroke_data['end_point']]
        elif stroke_data['type'] == 'rectangle':
            if 'corners' in stroke_data:
                return stroke_data['corners']
            else:
                # Eski format - top_left ve bottom_right
                return [stroke_data['top_left'], stroke_data['bottom_right']]
        elif stroke_data['type'] == 'circle':
            # Çember için merkez ve çevre noktaları
            center = stroke_data['center']
            radius = stroke_data['radius']
            return [center, (center[0] + radius, center[1]), (center[0], center[1] + radius), 
                   (center[0] - radius, center[1]), (center[0], center[1] - radius)]
        return []
    
    @staticmethod
    def set_stroke_points(stroke_data, points):
        """Stroke tipine göre noktaları ayarla"""
        if stroke_data['type'] == 'bspline':
            stroke_data['control_points'] = points
        elif stroke_data['type'] == 'freehand':
            # (x, y) tuple'larını QPointF'lere çevir
            stroke_data['points'] = [QPointF(p[0], p[1]) for p in points]
        elif stroke_data['type'] == 'line':
            if len(points) >= 2:
                stroke_data['start_point'] = points[0]
                stroke_data['end_point'] = points[1]
        elif stroke_data['type'] == 'rectangle':
            if 'corners' in stroke_data:
                # Yeni format - 4 köşe noktası
                if len(points) >= 4:
                    stroke_data['corners'] = points[:4]
            else:
                # Eski format - top_left ve bottom_right
                if len(points) >= 2:
                    stroke_data['top_left'] = points[0]
                    stroke_data['bottom_right'] = points[1]
        elif stroke_data['type'] == 'circle':
            if len(points) >= 2:
                import math
                stroke_data['center'] = points[0]
                # Yeni yarıçapı hesapla (merkez ve başka bir nokta arası mesafe)
                center = points[0]
                edge_point = points[1]
                stroke_data['radius'] = math.sqrt((edge_point[0] - center[0])**2 + 
                                                (edge_point[1] - center[1])**2)
    
    @staticmethod
    def move_stroke(stroke_data, delta_x, delta_y):
        """Stroke'u belirtilen miktarda taşı"""
        if stroke_data['type'] == 'bspline':
            # B-spline için hem edit_points hem control_points taşınmalı
            if 'edit_points' in stroke_data:
                edit_points = stroke_data['edit_points']
                for i in range(len(edit_points)):
                    edit_points[i][0] += delta_x
                    edit_points[i][1] += delta_y
            if 'control_points' in stroke_data:
                control_points = stroke_data['control_points']
                for i in range(len(control_points)):
                    control_points[i][0] += delta_x
                    control_points[i][1] += delta_y
                
        elif stroke_data['type'] == 'freehand':
            points = stroke_data['points']
            for i in range(len(points)):
                point_qf = ensure_qpointf(points[i])
                points[i] = QPointF(point_qf.x() + delta_x, point_qf.y() + delta_y)
                
        elif stroke_data['type'] == 'line':
            start = stroke_data['start_point']
            end = stroke_data['end_point']
            stroke_data['start_point'] = (start[0] + delta_x, start[1] + delta_y)
            stroke_data['end_point'] = (end[0] + delta_x, end[1] + delta_y)
            
        elif stroke_data['type'] == 'rectangle':
            if 'corners' in stroke_data:
                # Yeni format - 4 köşe noktası
                corners = stroke_data['corners']
                for i in range(len(corners)):
                    corners[i] = (corners[i][0] + delta_x, corners[i][1] + delta_y)
            else:
                # Eski format
                tl = stroke_data['top_left']
                br = stroke_data['bottom_right']
                stroke_data['top_left'] = (tl[0] + delta_x, tl[1] + delta_y)
                stroke_data['bottom_right'] = (br[0] + delta_x, br[1] + delta_y)
            
        elif stroke_data['type'] == 'circle':
            center = stroke_data['center']
            stroke_data['center'] = (center[0] + delta_x, center[1] + delta_y)
    
    @staticmethod
    def rotate_stroke(stroke_data, center_x, center_y, angle_rad):
        """Stroke'u belirtilen merkez etrafında döndür"""
        cos_a = np.cos(angle_rad)
        sin_a = np.sin(angle_rad)
        
        # Gölge verilerini koru
        shadow_backup = {}
        shadow_keys = ['has_shadow', 'shadow_color', 'shadow_blur', 'shadow_size', 
                      'shadow_opacity', 'shadow_offset_x', 'shadow_offset_y', 
                      'inner_shadow', 'shadow_quality']
        for key in shadow_keys:
            if key in stroke_data:
                shadow_backup[key] = stroke_data[key]
        
        if stroke_data['type'] == 'bspline':
            control_points = stroke_data['control_points']
            for i in range(len(control_points)):
                # Merkeze göre relatif pozisyon
                rel_x = control_points[i][0] - center_x
                rel_y = control_points[i][1] - center_y
                
                # Döndürme matrisi uygula
                new_x = rel_x * cos_a - rel_y * sin_a
                new_y = rel_x * sin_a + rel_y * cos_a
                
                # Merkezi geri ekle
                control_points[i][0] = new_x + center_x
                control_points[i][1] = new_y + center_y
                
        elif stroke_data['type'] == 'freehand':
            points = stroke_data['points']
            for i in range(len(points)):
                # Merkeze göre relatif pozisyon
                point_qf = ensure_qpointf(points[i])
                rel_x = point_qf.x() - center_x
                rel_y = point_qf.y() - center_y
                
                # Döndürme matrisi uygula
                new_x = rel_x * cos_a - rel_y * sin_a
                new_y = rel_x * sin_a + rel_y * cos_a
                
                # Merkezi geri ekle ve kaydet
                points[i] = QPointF(new_x + center_x, new_y + center_y)
                
        elif stroke_data['type'] == 'line':
            # Başlangıç noktası
            rel_x = stroke_data['start_point'][0] - center_x
            rel_y = stroke_data['start_point'][1] - center_y
            new_x = rel_x * cos_a - rel_y * sin_a + center_x
            new_y = rel_x * sin_a + rel_y * cos_a + center_y
            stroke_data['start_point'] = (new_x, new_y)
            
            # Bitiş noktası
            rel_x = stroke_data['end_point'][0] - center_x
            rel_y = stroke_data['end_point'][1] - center_y
            new_x = rel_x * cos_a - rel_y * sin_a + center_x
            new_y = rel_x * sin_a + rel_y * cos_a + center_y
            stroke_data['end_point'] = (new_x, new_y)
            
        elif stroke_data['type'] == 'rectangle':
            if 'corners' in stroke_data:
                # Yeni format - 4 köşe noktasını döndür
                corners = stroke_data['corners']
                for i in range(len(corners)):
                    rel_x = corners[i][0] - center_x
                    rel_y = corners[i][1] - center_y
                    new_x = rel_x * cos_a - rel_y * sin_a + center_x
                    new_y = rel_x * sin_a + rel_y * cos_a + center_y
                    corners[i] = (new_x, new_y)
            else:
                # Eski format
                # Sol üst köşe
                rel_x = stroke_data['top_left'][0] - center_x
                rel_y = stroke_data['top_left'][1] - center_y
                new_x = rel_x * cos_a - rel_y * sin_a + center_x
                new_y = rel_x * sin_a + rel_y * cos_a + center_y
                stroke_data['top_left'] = (new_x, new_y)
                
                # Sağ alt köşe
                rel_x = stroke_data['bottom_right'][0] - center_x
                rel_y = stroke_data['bottom_right'][1] - center_y
                new_x = rel_x * cos_a - rel_y * sin_a + center_x
                new_y = rel_x * sin_a + rel_y * cos_a + center_y
                stroke_data['bottom_right'] = (new_x, new_y)
            
        elif stroke_data['type'] == 'circle':
            # Çember için sadece merkezi döndür, yarıçap değişmez
            rel_x = stroke_data['center'][0] - center_x
            rel_y = stroke_data['center'][1] - center_y
            new_x = rel_x * cos_a - rel_y * sin_a + center_x
            new_y = rel_x * sin_a + rel_y * cos_a + center_y
            stroke_data['center'] = (new_x, new_y)
        
        # Gölge verilerini geri yükle
        for key, value in shadow_backup.items():
            stroke_data[key] = value
    
    @staticmethod
    def scale_stroke(stroke_data, center_x, center_y, scale_x, scale_y):
        """Stroke'u belirtilen merkez etrafında boyutlandır"""
        if stroke_data['type'] == 'bspline':
            control_points = stroke_data['control_points']
            for i in range(len(control_points)):
                # Merkeze göre relatif pozisyon
                rel_x = control_points[i][0] - center_x
                rel_y = control_points[i][1] - center_y
                
                # Ölçekleme uygula
                new_x = rel_x * scale_x
                new_y = rel_y * scale_y
                
                # Merkezi geri ekle
                control_points[i][0] = new_x + center_x
                control_points[i][1] = new_y + center_y
                
        elif stroke_data['type'] == 'freehand':
            points = stroke_data['points']
            for i in range(len(points)):
                # Merkeze göre relatif pozisyon
                point_qf = ensure_qpointf(points[i])
                rel_x = point_qf.x() - center_x
                rel_y = point_qf.y() - center_y
                
                # Ölçekleme uygula
                new_x = rel_x * scale_x
                new_y = rel_y * scale_y
                
                # Merkezi geri ekle ve kaydet
                points[i] = QPointF(new_x + center_x, new_y + center_y)
                
        elif stroke_data['type'] == 'line':
            # Başlangıç noktası
            rel_x = stroke_data['start_point'][0] - center_x
            rel_y = stroke_data['start_point'][1] - center_y
            new_x = rel_x * scale_x + center_x
            new_y = rel_y * scale_y + center_y
            stroke_data['start_point'] = (new_x, new_y)
            
            # Bitiş noktası
            rel_x = stroke_data['end_point'][0] - center_x
            rel_y = stroke_data['end_point'][1] - center_y
            new_x = rel_x * scale_x + center_x
            new_y = rel_y * scale_y + center_y
            stroke_data['end_point'] = (new_x, new_y)
            
        elif stroke_data['type'] == 'rectangle':
            if 'corners' in stroke_data:
                # Yeni format - 4 köşe noktasını ölçekle
                corners = stroke_data['corners']
                for i in range(len(corners)):
                    rel_x = corners[i][0] - center_x
                    rel_y = corners[i][1] - center_y
                    new_x = rel_x * scale_x + center_x
                    new_y = rel_y * scale_y + center_y
                    corners[i] = (new_x, new_y)
            else:
                # Eski format
                # Sol üst köşe
                rel_x = stroke_data['top_left'][0] - center_x
                rel_y = stroke_data['top_left'][1] - center_y
                new_x = rel_x * scale_x + center_x
                new_y = rel_y * scale_y + center_y
                stroke_data['top_left'] = (new_x, new_y)
                
                # Sağ alt köşe
                rel_x = stroke_data['bottom_right'][0] - center_x
                rel_y = stroke_data['bottom_right'][1] - center_y
                new_x = rel_x * scale_x + center_x
                new_y = rel_y * scale_y + center_y
                stroke_data['bottom_right'] = (new_x, new_y)
            
        elif stroke_data['type'] == 'circle':
            # Merkezi ölçekle
            rel_x = stroke_data['center'][0] - center_x
            rel_y = stroke_data['center'][1] - center_y
            new_x = rel_x * scale_x + center_x
            new_y = rel_y * scale_y + center_y
            stroke_data['center'] = (new_x, new_y)
            
            # Yarıçapı da ölçekle (ortalama ölçek kullan)
            avg_scale = (scale_x + scale_y) / 2
            stroke_data['radius'] *= avg_scale
    
    @staticmethod
    def get_stroke_bounds(stroke_data):
        """Stroke'un bounding box'ını hesapla"""
        points = StrokeHandler.get_stroke_points(stroke_data)
        if not points:
            return None
            
        min_x = min(p[0] for p in points)
        max_x = max(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_y = max(p[1] for p in points)
        
        return QRectF(min_x, min_y, max_x - min_x, max_y - min_y)
    
    @staticmethod
    def get_stroke_center(stroke_data):
        """Stroke'un merkezini hesapla"""
        points = StrokeHandler.get_stroke_points(stroke_data)
        if not points:
            return None
            
        center_x = sum(p[0] for p in points) / len(points)
        center_y = sum(p[1] for p in points) / len(points)
        
        return QPointF(center_x, center_y)
    
    @staticmethod
    def is_point_near_stroke(stroke_data, pos, tolerance=15):
        """Nokta stroke'a yakın mı kontrol et"""
        if stroke_data['type'] == 'bspline':
            # B-spline için kontrol noktalarına yakınlık
            control_points = stroke_data['control_points']
            for cp in control_points:
                cp_point = QPointF(cp[0], cp[1])
                if (pos - cp_point).manhattanLength() < tolerance:
                    return True
            
            # Eğriye yakınlık: knots/u/degree varsa yaklaşık örnekleme ile kontrol et
            try:
                from scipy.interpolate import splev
                knots = stroke_data.get('knots')
                u = stroke_data.get('u')
                degree = stroke_data.get('degree', 3)
                cps = stroke_data.get('control_points', [])
                if isinstance(cps, list):
                    cps = np.array(cps, dtype=float)
                if isinstance(knots, list):
                    knots = np.array(knots, dtype=float)
                if isinstance(u, list):
                    u = np.array(u, dtype=float)
                if cps is not None and knots is not None and u is not None and len(cps) >= 4:
                    tck = (knots, cps.T, int(degree))
                    x_fine, y_fine = splev(np.linspace(0, u[-1], 100), tck)
                    pos_vec = np.array([pos.x(), pos.y()], dtype=float)
                    curve = np.stack([x_fine, y_fine], axis=1)
                    # Noktaya en yakın segmentin mesafesi
                    diffs = curve - pos_vec
                    dists = np.linalg.norm(diffs, axis=1)
                    if np.min(dists) <= tolerance:
                        return True
            except Exception:
                pass
            return False
            
        elif stroke_data['type'] == 'freehand':
            # Serbest çizim için noktalara yakınlık
            points = stroke_data['points']
            for point in points:
                point_qf = ensure_qpointf(point)
                if (pos - point_qf).manhattanLength() < tolerance:
                    return True
                    
        elif stroke_data['type'] == 'line':
            # Çizgiye yakınlık kontrolü
            start = QPointF(stroke_data['start_point'][0], stroke_data['start_point'][1])
            end = QPointF(stroke_data['end_point'][0], stroke_data['end_point'][1])

            # Çizgi segmentine dik uzaklığı kontrol et
            start_vec = np.array([start.x(), start.y()], dtype=float)
            end_vec = np.array([end.x(), end.y()], dtype=float)
            pos_vec = np.array([pos.x(), pos.y()], dtype=float)

            segment_vec = end_vec - start_vec
            segment_len_sq = np.dot(segment_vec, segment_vec)

            if segment_len_sq == 0:
                # Degenerate case: çizgi noktaya dönüşmüş
                return (pos - start).manhattanLength() <= tolerance

            # Hit test noktasını çizgi segmentine projekte et
            t = np.dot(pos_vec - start_vec, segment_vec) / segment_len_sq
            t = max(0.0, min(1.0, t))
            projection = start_vec + t * segment_vec

            distance = np.linalg.norm(pos_vec - projection)
            if distance <= tolerance:
                return True

        elif stroke_data['type'] == 'rectangle':
            if 'corners' in stroke_data:
                # Yeni format - köşe noktalarına yakınlık
                corners = stroke_data['corners']
                for corner in corners:
                    corner_point = QPointF(corner[0], corner[1])
                    if (pos - corner_point).manhattanLength() < tolerance:
                        return True
            else:
                # Eski format - dikdörtgen çerçevesine yakınlık
                tl = QPointF(stroke_data['top_left'][0], stroke_data['top_left'][1])
                br = QPointF(stroke_data['bottom_right'][0], stroke_data['bottom_right'][1])
                rect = QRectF(tl, br).normalized()
                
                # Çerçeve yakınlığı kontrolü (basit)
                expanded_rect = rect.adjusted(-tolerance, -tolerance, tolerance, tolerance)
                if expanded_rect.contains(pos) and not rect.adjusted(tolerance, tolerance, -tolerance, -tolerance).contains(pos):
                    return True
                
        elif stroke_data['type'] == 'circle':
            # Çember çevresine yakınlık
            center = QPointF(stroke_data['center'][0], stroke_data['center'][1])
            radius = stroke_data['radius']
            
            distance_to_center = ((pos.x() - center.x())**2 + (pos.y() - center.y())**2)**0.5
            # Çember çevresine yakınlık kontrolü
            if abs(distance_to_center - radius) < tolerance:
                return True
                    
        return False
    
    @staticmethod
    def is_stroke_in_rect(stroke_data, rect):
        """Stroke'un herhangi bir noktası dikdörtgen içinde mi"""
        if stroke_data['type'] == 'bspline':
            control_points = stroke_data['control_points']
            for cp in control_points:
                if rect.contains(QPointF(cp[0], cp[1])):
                    return True
                    
        elif stroke_data['type'] == 'freehand':
            points = stroke_data['points']
            for point in points:
                point_qf = ensure_qpointf(point)
                if rect.contains(point_qf):
                    return True
                    
        elif stroke_data['type'] == 'line':
            start = QPointF(stroke_data['start_point'][0], stroke_data['start_point'][1])
            end = QPointF(stroke_data['end_point'][0], stroke_data['end_point'][1])
            if rect.contains(start) or rect.contains(end):
                return True
                
        elif stroke_data['type'] == 'rectangle':
            if 'corners' in stroke_data:
                # Yeni format - köşe noktalarının herhangi biri seçim içinde mi
                corners = stroke_data['corners']
                for corner in corners:
                    if rect.contains(QPointF(corner[0], corner[1])):
                        return True
            else:
                # Eski format
                tl = QPointF(stroke_data['top_left'][0], stroke_data['top_left'][1])
                br = QPointF(stroke_data['bottom_right'][0], stroke_data['bottom_right'][1])
                shape_rect = QRectF(tl, br).normalized()
                if rect.intersects(shape_rect):
                    return True
                
        elif stroke_data['type'] == 'circle':
            center = QPointF(stroke_data['center'][0], stroke_data['center'][1])
            if rect.contains(center):
                return True
                    
        return False
    
    @staticmethod
    def draw_stroke_highlight(painter, stroke_data, color=Qt.GlobalColor.green, size=8):
        """Stroke'u vurgulayarak çiz"""
        pen = QPen(color, size, Qt.PenStyle.SolidLine)
        painter.setPen(pen)
        
        if stroke_data['type'] == 'bspline':
            control_points = stroke_data['control_points']
            for cp in control_points:
                painter.drawPoint(QPointF(cp[0], cp[1]))
                
        elif stroke_data['type'] == 'freehand':
            points = stroke_data['points']
            pen.setWidth(max(2, size // 2))
            painter.setPen(pen)
            for i, point in enumerate(points):
                if i % 5 == 0:  # Performans için her 5. noktayı çiz
                    painter.drawPoint(ensure_qpointf(point))
                    
        elif stroke_data['type'] == 'line':
            # Çizginin uç noktalarını vurgula
            start = QPointF(stroke_data['start_point'][0], stroke_data['start_point'][1])
            end = QPointF(stroke_data['end_point'][0], stroke_data['end_point'][1])
            painter.drawPoint(start)
            painter.drawPoint(end)
            
        elif stroke_data['type'] == 'rectangle':
            if 'corners' in stroke_data:
                # Yeni format - köşe noktalarını vurgula
                corners = stroke_data['corners']
                for corner in corners:
                    painter.drawPoint(QPointF(corner[0], corner[1]))
            else:
                # Eski format - dikdörtgenin köşelerini vurgula
                tl = QPointF(stroke_data['top_left'][0], stroke_data['top_left'][1])
                br = QPointF(stroke_data['bottom_right'][0], stroke_data['bottom_right'][1])
                tr = QPointF(br.x(), tl.y())
                bl = QPointF(tl.x(), br.y())
                painter.drawPoint(tl)
                painter.drawPoint(tr)
                painter.drawPoint(bl)
                painter.drawPoint(br)
            
        elif stroke_data['type'] == 'circle':
            # Çemberin merkez ve çevre noktalarını vurgula
            center = QPointF(stroke_data['center'][0], stroke_data['center'][1])
            radius = stroke_data['radius']
            painter.drawPoint(center)
            # 4 ana yön
            painter.drawPoint(QPointF(center.x() + radius, center.y()))
            painter.drawPoint(QPointF(center.x() - radius, center.y()))
            painter.drawPoint(QPointF(center.x(), center.y() + radius))
            painter.drawPoint(QPointF(center.x(), center.y() - radius)) 