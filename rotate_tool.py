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
            
        # Grid snap uygula
        if (self.background_settings and 
            self.background_settings.get('snap_to_grid', False)):
            pos = GridSnapUtils.snap_point_to_grid(pos, self.background_settings)
            
        # Şu anki açıyı hesapla
        delta = pos - self.rotation_center
        current_angle = math.atan2(delta.y(), delta.x())
        
        # Açı farkı
        angle_diff = current_angle - self.last_angle
        
        # Tüm seçili stroke'ların kontrol noktalarını döndür
        cos_angle = math.cos(angle_diff)
        sin_angle = math.sin(angle_diff)
        
        for selected_stroke in selected_strokes:
            if selected_stroke < len(strokes):
                stroke_data = strokes[selected_stroke]
                StrokeHandler.rotate_stroke(stroke_data, self.rotation_center.x(), self.rotation_center.y(), angle_diff)
            
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