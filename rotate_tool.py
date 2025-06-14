from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QPainter, QPen, QBrush
from PyQt6.QtCore import Qt
from stroke_handler import StrokeHandler
from grid_snap_utils import GridSnapUtils
import numpy as np
import math

class RotateTool:
    def __init__(self):
        self.is_rotating = False
        self.rotation_center = None
        self.last_angle = 0
        self.start_angle = 0
        self.rotation_handles = []  # Döndürme tutamakları
        self.active_handle = None   # Aktif tutamak
        self.background_settings = None  # Grid snap için
        
    def get_selection_center(self, strokes, selected_strokes):
        """Seçilen stroke'ların merkezini hesapla"""
        if not selected_strokes:
            return None
            
        all_points = []
        for stroke_index in selected_strokes:
            if stroke_index < len(strokes):
                stroke_data = strokes[stroke_index]
                points = StrokeHandler.get_stroke_points(stroke_data)
                all_points.extend(points)
                
        if not all_points:
            return None
            
        # Tüm kontrol noktalarının merkezi
        center_x = sum(cp[0] for cp in all_points) / len(all_points)
        center_y = sum(cp[1] for cp in all_points) / len(all_points)
        
        return QPointF(center_x, center_y)
        
    def get_selection_bounding_rect(self, strokes, selected_strokes):
        """Seçilen stroke'ların bounding rectangle'ını hesapla"""
        if not selected_strokes:
            return None
            
        all_points = []
        for stroke_index in selected_strokes:
            if stroke_index < len(strokes):
                stroke_data = strokes[stroke_index]
                points = StrokeHandler.get_stroke_points(stroke_data)
                all_points.extend(points)
                
        if not all_points:
            return None
            
        min_x = min(cp[0] for cp in all_points)
        max_x = max(cp[0] for cp in all_points)
        min_y = min(cp[1] for cp in all_points)
        max_y = max(cp[1] for cp in all_points)
        
        # Biraz padding ekle
        padding = 20
        return QRectF(min_x - padding, min_y - padding, 
                     max_x - min_x + 2*padding, max_y - min_y + 2*padding)
        
    def create_rotation_handles(self, strokes, selected_strokes):
        """Döndürme tutamakları oluştur"""
        self.rotation_handles = []
        
        bounding_rect = self.get_selection_bounding_rect(strokes, selected_strokes)
        if not bounding_rect:
            return
            
        center = bounding_rect.center()
        
        # 4 köşe tutamağı
        corners = [
            bounding_rect.topLeft(),
            bounding_rect.topRight(), 
            bounding_rect.bottomRight(),
            bounding_rect.bottomLeft()
        ]
        
        # Her köşe için döndürme tutamağı oluştur
        handle_size = 8
        for corner in corners:
            # Köşeden merkeze doğru biraz içeri al
            direction = center - corner
            direction_normalized = direction / math.sqrt(direction.x()**2 + direction.y()**2)
            handle_pos = corner + direction_normalized * 15
            
            handle_rect = QRectF(handle_pos.x() - handle_size/2, 
                               handle_pos.y() - handle_size/2,
                               handle_size, handle_size)
            self.rotation_handles.append(handle_rect)
    
    def get_handle_at_point(self, pos):
        """Belirtilen noktadaki tutamağı bul"""
        for i, handle in enumerate(self.rotation_handles):
            if handle.contains(pos):
                return i
        return None
        
    def start_rotate(self, pos, strokes, selected_strokes):
        """Döndürme işlemini başlat"""
        if not selected_strokes:
            return False
            
        # Döndürme tutamaklarını oluştur
        self.create_rotation_handles(strokes, selected_strokes)
        
        # Tutamağa tıklandı mı kontrol et
        self.active_handle = self.get_handle_at_point(pos)
        if self.active_handle is None:
            return False
            
        self.rotation_center = self.get_selection_center(strokes, selected_strokes)
        if not self.rotation_center:
            return False
            
        self.is_rotating = True
        
        # Başlangıç açısını hesapla
        delta = pos - self.rotation_center
        self.start_angle = math.atan2(delta.y(), delta.x())
        self.last_angle = self.start_angle
        
        return True
        
    def update_rotate(self, pos, strokes, selected_strokes):
        """Seçilen stroke'ları döndür"""
        if not self.is_rotating or not selected_strokes or not self.rotation_center:
            return False
            
        # Grid snap uygula - pozisyon bazında, daha hassas snap kullan
        snapped_pos = pos
        if (self.background_settings and 
            self.background_settings.get('snap_to_grid', False)):
            snapped_pos = GridSnapUtils.snap_point_to_grid_precise(pos, self.background_settings)
            
        # Şu anki açıyı hesapla
        delta = snapped_pos - self.rotation_center
        current_angle = math.atan2(delta.y(), delta.x())
        
        # Grid snap aktifse açıyı da snap'le (15 derece aralıklarla)
        if (self.background_settings and 
            self.background_settings.get('snap_to_grid', False)):
            # Açıyı 15 derece aralıklarla snap'le
            angle_degrees = math.degrees(current_angle)
            snap_angle_degrees = round(angle_degrees / 15) * 15
            current_angle = math.radians(snap_angle_degrees)
        
        # Açı farkı
        angle_diff = current_angle - self.last_angle
        
        # Çok küçük açı değişimlerini atla
        if abs(angle_diff) < 0.01:  # ~0.6 derece
            return False
        
        # Tüm seçili stroke'ların kontrol noktalarını döndür
        cos_angle = math.cos(angle_diff)
        sin_angle = math.sin(angle_diff)
        
        for selected_stroke in selected_strokes:
            if selected_stroke < len(strokes):
                stroke_data = strokes[selected_stroke]
                # Hassas grid snap ile rotate uygula
                self.rotate_stroke_precise(stroke_data, math.degrees(angle_diff))
            
        self.last_angle = current_angle
        return True
        
    def finish_rotate(self):
        """Döndürme işlemini tamamla"""
        self.is_rotating = False
        self.rotation_center = None
        self.last_angle = 0
        self.start_angle = 0
        self.active_handle = None
        self.rotation_handles = []
        
    def get_rotation_angle(self, pos):
        """Şu anki döndürme açısını derece cinsinden döndür"""
        if not self.rotation_center:
            return 0
            
        delta = pos - self.rotation_center
        current_angle = math.atan2(delta.y(), delta.x())
        total_rotation = current_angle - self.start_angle
        
        return math.degrees(total_rotation)
        
    def draw_rotation_handles(self, painter, strokes, selected_strokes):
        """Döndürme tutamaklarını çiz"""
        if not selected_strokes:
            return
            
        # Tutamakları güncelle
        self.create_rotation_handles(strokes, selected_strokes)
        
        painter.save()
        
        # Tutamakları çiz
        for i, handle in enumerate(self.rotation_handles):
            if i == self.active_handle:
                # Aktif tutamak farklı renkte
                painter.setBrush(QBrush(Qt.GlobalColor.yellow))
                painter.setPen(QPen(Qt.GlobalColor.red, 2))
            else:
                painter.setBrush(QBrush(Qt.GlobalColor.white))
                painter.setPen(QPen(Qt.GlobalColor.blue, 2))
                
            painter.drawEllipse(handle)
            
        # Döndürme merkezi
        if self.rotation_center and self.is_rotating:
            painter.setBrush(QBrush(Qt.GlobalColor.red))
            painter.setPen(QPen(Qt.GlobalColor.red, 2))
            center_size = 6
            painter.drawEllipse(QRectF(self.rotation_center.x() - center_size/2,
                                     self.rotation_center.y() - center_size/2,
                                     center_size, center_size))
            
            # Döndürme çizgisi (merkezden mouse'a)
            if hasattr(self, '_current_mouse_pos'):
                painter.setPen(QPen(Qt.GlobalColor.red, 1, Qt.PenStyle.DashLine))
                painter.drawLine(self.rotation_center, self._current_mouse_pos)
                
        painter.restore()
        
    def set_current_mouse_pos(self, pos):
        """Mevcut mouse pozisyonunu kaydet (çizim için)"""
        self._current_mouse_pos = pos
        
    def set_background_settings(self, settings):
        """Arka plan ayarlarını güncelle (grid snap için)"""
        self.background_settings = settings
    
    def rotate_stroke_precise(self, stroke_data, angle_degrees):
        """Stroke'u hassas grid snap ile döndür"""
        if not hasattr(self, 'original_stroke_data') or id(stroke_data) not in self.original_stroke_data:
            # İlk kez rotate ediliyorsa orijinal veriyi sakla
            if not hasattr(self, 'original_stroke_data'):
                self.original_stroke_data = {}
            self.original_stroke_data[id(stroke_data)] = stroke_data.copy()
        
        original_data = self.original_stroke_data[id(stroke_data)]
        self.rotate_stroke(stroke_data, original_data, angle_degrees) 

    def mouseMoveEvent(self, event):
        """Mouse hareket ettirildiğinde"""
        if self.is_rotating and self.selected_strokes and self.rotation_center:
            current_pos = event.position()
            
            # Grid snap aktifse pozisyonu snap'le
            if self.background_settings and self.background_settings.get('snap_to_grid', False):
                current_pos = GridSnapUtils.snap_point_to_grid_precise(current_pos, self.background_settings)
            
            # Döndürme açısını hesapla
            angle = self.calculate_angle(self.start_pos, current_pos, self.rotation_center)
            
            # Minimum açı değişimi kontrolü - grid snap aktifse daha hassas
            min_angle_change = 2.0 if self.background_settings and self.background_settings.get('snap_to_grid', False) else 5.0
            if abs(angle) < min_angle_change:
                return
            
            # Grid snap aktifse açıyı 15 derece katlarına yuvarlama
            if self.background_settings and self.background_settings.get('snap_to_grid', False):
                angle = round(angle / 15.0) * 15.0
                if angle == 0:
                    return
            
            # Seçili stroke'ları döndür
            for stroke in self.selected_strokes:
                original_data = self.original_stroke_data[id(stroke)]
                self.rotate_stroke(stroke, original_data, angle)
            
            self.drawing_widget.update()

    def rotate_stroke(self, stroke, original_data, angle):
        """Stroke'u belirtilen açıyla döndür"""
        stroke_type = stroke.get('type', '')
        
        if stroke_type == 'freehand':
            if 'points' in original_data:
                stroke['points'] = []
                for point in original_data['points']:
                    if isinstance(point, dict):
                        # Dict formatında - serbest çizimler için her noktayı snap'leme
                        original_point = QPointF(point['x'], point['y'])
                        rotated_point = self.rotate_point(original_point, self.rotation_center, angle)
                        stroke['points'].append({'x': rotated_point.x(), 'y': rotated_point.y()})
                    else:
                        # QPointF formatında - serbest çizimler için her noktayı snap'leme
                        from stroke_handler import ensure_qpointf
                        original_point = ensure_qpointf(point)
                        rotated_point = self.rotate_point(original_point, self.rotation_center, angle)
                        stroke['points'].append(rotated_point)
        
        elif stroke_type == 'bspline':
            if 'control_points' in original_data:
                stroke['control_points'] = []
                for cp in original_data['control_points']:
                    original_point = QPointF(cp[0], cp[1])
                    rotated_point = self.rotate_point(original_point, self.rotation_center, angle)
                    
                    # Grid snap aktifse control point'i snap'le
                    if self.background_settings and self.background_settings.get('snap_to_grid', False):
                        rotated_point = GridSnapUtils.snap_point_to_grid_precise(rotated_point, self.background_settings)
                    
                    stroke['control_points'].append([rotated_point.x(), rotated_point.y()])
        
        elif stroke_type == 'line':
            if 'start_point' in original_data:
                original_start = QPointF(original_data['start_point'][0], original_data['start_point'][1])
                rotated_start = self.rotate_point(original_start, self.rotation_center, angle)
                
                # Grid snap aktifse endpoint'i snap'le
                if self.background_settings and self.background_settings.get('snap_to_grid', False):
                    rotated_start = GridSnapUtils.snap_point_to_grid_precise(rotated_start, self.background_settings)
                
                stroke['start_point'] = (rotated_start.x(), rotated_start.y())
            
            if 'end_point' in original_data:
                original_end = QPointF(original_data['end_point'][0], original_data['end_point'][1])
                rotated_end = self.rotate_point(original_end, self.rotation_center, angle)
                
                # Grid snap aktifse endpoint'i snap'le
                if self.background_settings and self.background_settings.get('snap_to_grid', False):
                    rotated_end = GridSnapUtils.snap_point_to_grid_precise(rotated_end, self.background_settings)
                
                stroke['end_point'] = (rotated_end.x(), rotated_end.y())
        
        elif stroke_type == 'rectangle':
            if 'corners' in original_data:
                stroke['corners'] = []
                for corner in original_data['corners']:
                    original_corner = QPointF(corner[0], corner[1])
                    rotated_corner = self.rotate_point(original_corner, self.rotation_center, angle)
                    
                    # Grid snap aktifse corner'ı snap'le
                    if self.background_settings and self.background_settings.get('snap_to_grid', False):
                        rotated_corner = GridSnapUtils.snap_point_to_grid_precise(rotated_corner, self.background_settings)
                    
                    stroke['corners'].append((rotated_corner.x(), rotated_corner.y()))
            elif 'top_left' in original_data and 'bottom_right' in original_data:
                # Eski format desteği
                original_tl = QPointF(original_data['top_left'][0], original_data['top_left'][1])
                original_br = QPointF(original_data['bottom_right'][0], original_data['bottom_right'][1])
                
                rotated_tl = self.rotate_point(original_tl, self.rotation_center, angle)
                rotated_br = self.rotate_point(original_br, self.rotation_center, angle)
                
                # Grid snap aktifse corner'ları snap'le
                if self.background_settings and self.background_settings.get('snap_to_grid', False):
                    rotated_tl = GridSnapUtils.snap_point_to_grid_precise(rotated_tl, self.background_settings)
                    rotated_br = GridSnapUtils.snap_point_to_grid_precise(rotated_br, self.background_settings)
                
                stroke['top_left'] = (rotated_tl.x(), rotated_tl.y())
                stroke['bottom_right'] = (rotated_br.x(), rotated_br.y())
        
        elif stroke_type == 'circle':
            if 'center' in original_data:
                original_center = QPointF(original_data['center'][0], original_data['center'][1])
                rotated_center = self.rotate_point(original_center, self.rotation_center, angle)
                
                # Grid snap aktifse center'ı snap'le
                if self.background_settings and self.background_settings.get('snap_to_grid', False):
                    rotated_center = GridSnapUtils.snap_point_to_grid_precise(rotated_center, self.background_settings)
                
                stroke['center'] = (rotated_center.x(), rotated_center.y())
            
            # Çember için radius değişmez, sadece merkez döner
            if 'radius' in original_data:
                stroke['radius'] = original_data['radius'] 