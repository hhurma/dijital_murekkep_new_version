from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QPainter, QPen, QBrush
from PyQt6.QtCore import Qt
from stroke_handler import StrokeHandler
from grid_snap_utils import GridSnapUtils
import numpy as np
import math

class ScaleTool:
    def __init__(self):
        self.is_scaling = False
        self.scale_center = None
        self.initial_distance = 0
        self.scale_factor = 1.0
        self.scale_handles = []      # Boyutlandırma tutamakları
        self.active_handle = None    # Aktif tutamak
        self.handle_types = []       # Tutamak tipleri (corner, edge)
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
        
        # Padding ekle
        padding = 15
        return QRectF(min_x - padding, min_y - padding, 
                     max_x - min_x + 2*padding, max_y - min_y + 2*padding)
        
    def create_scale_handles(self, strokes, selected_strokes):
        """Boyutlandırma tutamakları oluştur"""
        self.scale_handles = []
        self.handle_types = []
        
        bounding_rect = self.get_selection_bounding_rect(strokes, selected_strokes)
        if not bounding_rect:
            return
            
        handle_size = 8
        
        # 4 köşe tutamağı (proportional scaling)
        corners = [
            ("top-left", bounding_rect.topLeft()),
            ("top-right", bounding_rect.topRight()),
            ("bottom-right", bounding_rect.bottomRight()),
            ("bottom-left", bounding_rect.bottomLeft())
        ]
        
        for handle_type, pos in corners:
            handle_rect = QRectF(pos.x() - handle_size/2, 
                               pos.y() - handle_size/2,
                               handle_size, handle_size)
            self.scale_handles.append(handle_rect)
            self.handle_types.append(handle_type)
            
        # 4 kenar ortası tutamağı (non-proportional scaling)
        edges = [
            ("top", QPointF(bounding_rect.center().x(), bounding_rect.top())),
            ("right", QPointF(bounding_rect.right(), bounding_rect.center().y())),
            ("bottom", QPointF(bounding_rect.center().x(), bounding_rect.bottom())),
            ("left", QPointF(bounding_rect.left(), bounding_rect.center().y()))
        ]
        
        for handle_type, pos in edges:
            handle_rect = QRectF(pos.x() - handle_size/2, 
                               pos.y() - handle_size/2,
                               handle_size, handle_size)
            self.scale_handles.append(handle_rect)
            self.handle_types.append(handle_type)
    
    def get_handle_at_point(self, pos):
        """Belirtilen noktadaki tutamağı bul"""
        for i, handle in enumerate(self.scale_handles):
            if handle.contains(pos):
                return i
        return None
        
    def start_scale(self, pos, strokes, selected_strokes):
        """Boyutlandırma işlemini başlat"""
        if not selected_strokes:
            return False
            
        # Boyutlandırma tutamaklarını oluştur
        self.create_scale_handles(strokes, selected_strokes)
        
        # Tutamağa tıklandı mı kontrol et
        self.active_handle = self.get_handle_at_point(pos)
        if self.active_handle is None:
            return False
            
        self.scale_center = self.get_selection_center(strokes, selected_strokes)
        if not self.scale_center:
            return False
            
        self.is_scaling = True
        
        # Başlangıç mesafesini hesapla (sadece köşe tutamakları için)
        handle_type = self.handle_types[self.active_handle]
        if handle_type in ["top-left", "top-right", "bottom-left", "bottom-right"]:
            delta = pos - self.scale_center
            self.initial_distance = math.sqrt(delta.x()**2 + delta.y()**2)
            if self.initial_distance == 0:
                self.initial_distance = 1  # Sıfıra bölme hatası önlemi
        else:
            # Kenar tutamakları için scale değerlerini başlat
            self.last_scale_x = 1.0
            self.last_scale_y = 1.0
            
        self.scale_factor = 1.0
        
        return True
        
    def update_scale(self, pos, strokes, selected_strokes):
        """Seçilen stroke'ları boyutlandır"""
        if not self.is_scaling or not selected_strokes or not self.scale_center:
            return False
            
        if self.active_handle is None:
            return False
            
        # Grid snap uygula - daha hassas snap kullan
        snapped_pos = pos
        if (self.background_settings and 
            self.background_settings.get('snap_to_grid', False)):
            snapped_pos = GridSnapUtils.snap_point_to_grid_precise(pos, self.background_settings)
            
        # Tutamak tipine göre boyutlandırma yöntemini belirle
        handle_type = self.handle_types[self.active_handle]
        
        if handle_type in ["top-left", "top-right", "bottom-left", "bottom-right"]:
            # Köşe tutamakları - proportional scaling
            delta = snapped_pos - self.scale_center
            current_distance = math.sqrt(delta.x()**2 + delta.y()**2)
            
            if current_distance == 0 or self.initial_distance == 0:
                return False
                
            new_scale_factor = current_distance / self.initial_distance
            scale_change = new_scale_factor / self.scale_factor
            
            # Grid snap aktifse minimum scale değişimini kontrol et
            if (self.background_settings and 
                self.background_settings.get('snap_to_grid', False)):
                grid_size = self.background_settings.get('grid_size', 20)
                # Scale değişimi çok küçükse atla
                if abs(scale_change - 1.0) < 0.05:
                    return False
            
            # Minimum ve maksimum scale sınırları
            scale_change = max(0.1, min(5.0, scale_change))
            
            # Tüm seçili stroke'ları boyutlandır
            for selected_stroke in selected_strokes:
                if selected_stroke < len(strokes):
                    stroke_data = strokes[selected_stroke]
                    # Hassas grid snap ile scale uygula
                    self.scale_stroke_precise(stroke_data, scale_change)
                
            self.scale_factor = new_scale_factor
            
        else:
            # Kenar tutamakları - tek yönlü scaling
            # Bounding rect'i al
            bounding_rect = self.get_selection_bounding_rect(strokes, selected_strokes)
            if not bounding_rect:
                return False
                
            # Grid snap için pozisyonu ayarla
            effective_pos = snapped_pos
            
            # Orijinal kontrol noktalarına göre yeni scale hesapla
            scale_change_x = 1.0
            scale_change_y = 1.0
            
            if handle_type == "left":
                # Sol kenara göre genişlik değişimi
                new_width = bounding_rect.right() - effective_pos.x()
                old_width = bounding_rect.width()
                if old_width > 0:
                    scale_change_x = new_width / old_width
                    scale_change_x = max(0.1, min(5.0, scale_change_x))
                    
            elif handle_type == "right":
                # Sağ kenara göre genişlik değişimi
                new_width = effective_pos.x() - bounding_rect.left()
                old_width = bounding_rect.width()
                if old_width > 0:
                    scale_change_x = new_width / old_width
                    scale_change_x = max(0.1, min(5.0, scale_change_x))
                    
            elif handle_type == "top":
                # Üst kenara göre yükseklik değişimi
                new_height = bounding_rect.bottom() - effective_pos.y()
                old_height = bounding_rect.height()
                if old_height > 0:
                    scale_change_y = new_height / old_height
                    scale_change_y = max(0.1, min(5.0, scale_change_y))
                    
            elif handle_type == "bottom":
                # Alt kenara göre yükseklik değişimi
                new_height = effective_pos.y() - bounding_rect.top()
                old_height = bounding_rect.height()
                if old_height > 0:
                    scale_change_y = new_height / old_height
                    scale_change_y = max(0.1, min(5.0, scale_change_y))
            
            # Grid snap aktifse minimum scale değişimini kontrol et
            if (self.background_settings and 
                self.background_settings.get('snap_to_grid', False)):
                # Scale değişimi çok küçükse atla
                if (abs(scale_change_x - 1.0) < 0.05 and abs(scale_change_y - 1.0) < 0.05):
                    return False
            
            # Tüm seçili stroke'ları tek seferde scale uygula
            for selected_stroke in selected_strokes:
                if selected_stroke < len(strokes):
                    stroke_data = strokes[selected_stroke]
                    
                    # Önceki scale'i tersine çevir
                    if hasattr(self, 'last_scale_x') and hasattr(self, 'last_scale_y'):
                        StrokeHandler.scale_stroke(stroke_data, self.scale_center.x(), self.scale_center.y(), 
                                                 1.0/self.last_scale_x, 1.0/self.last_scale_y)
                    
                    # Yeni scale uygula
                    StrokeHandler.scale_stroke(stroke_data, self.scale_center.x(), self.scale_center.y(), 
                                             scale_change_x, scale_change_y)
                
            # Sonraki iterasyon için scale değerlerini sakla
            self.last_scale_x = scale_change_x
            self.last_scale_y = scale_change_y
        
        return True
        
    def finish_scale(self):
        """Boyutlandırma işlemini tamamla"""
        self.is_scaling = False
        self.scale_center = None
        self.initial_distance = 0
        self.scale_factor = 1.0
        self.active_handle = None
        self.scale_handles = []
        self.handle_types = []
        # Tek yönlü scaling için kullanılan değişkenleri temizle
        if hasattr(self, 'initial_pos'):
            delattr(self, 'initial_pos')
        if hasattr(self, 'last_scale_x'):
            delattr(self, 'last_scale_x')
        if hasattr(self, 'last_scale_y'):
            delattr(self, 'last_scale_y')
        
    def get_scale_factor(self, pos):
        """Şu anki scale faktörünü döndür"""
        if not self.scale_center or self.initial_distance == 0:
            return 1.0
            
        delta = pos - self.scale_center
        current_distance = math.sqrt(delta.x()**2 + delta.y()**2)
        
        if current_distance == 0:
            return 1.0
            
        return current_distance / self.initial_distance
        
    def draw_scale_handles(self, painter, strokes, selected_strokes):
        """Boyutlandırma tutamaklarını çiz"""
        if not selected_strokes:
            return
            
        # Tutamakları güncelle
        self.create_scale_handles(strokes, selected_strokes)
        
        painter.save()
        
        # Tutamakları çiz
        for i, handle in enumerate(self.scale_handles):
            handle_type = self.handle_types[i]
            
            if i == self.active_handle:
                # Aktif tutamak farklı renkte
                painter.setBrush(QBrush(Qt.GlobalColor.yellow))
                painter.setPen(QPen(Qt.GlobalColor.red, 2))
            elif handle_type in ["top-left", "top-right", "bottom-left", "bottom-right"]:
                # Köşe tutamakları - kare şekil
                painter.setBrush(QBrush(Qt.GlobalColor.white))
                painter.setPen(QPen(Qt.GlobalColor.blue, 2))
            else:
                # Kenar tutamakları - dikdörtgen şekil
                painter.setBrush(QBrush(Qt.GlobalColor.lightGray))
                painter.setPen(QPen(Qt.GlobalColor.darkBlue, 2))
                
            if handle_type in ["top-left", "top-right", "bottom-left", "bottom-right"]:
                # Köşe tutamakları kare olarak çiz
                painter.drawRect(handle)
            else:
                # Kenar tutamakları daire olarak çiz
                painter.drawEllipse(handle)
            
        # Boyutlandırma merkezi
        if self.scale_center and self.is_scaling:
            painter.setBrush(QBrush(Qt.GlobalColor.red))
            painter.setPen(QPen(Qt.GlobalColor.red, 2))
            center_size = 4
            painter.drawEllipse(QRectF(self.scale_center.x() - center_size/2,
                                     self.scale_center.y() - center_size/2,
                                     center_size, center_size))
            
        # Bounding rectangle çiz
        bounding_rect = self.get_selection_bounding_rect(strokes, selected_strokes)
        if bounding_rect:
            painter.setPen(QPen(Qt.GlobalColor.gray, 1, Qt.PenStyle.DashLine))
            painter.setBrush(QBrush())  # Şeffaf fill
            painter.drawRect(bounding_rect)
                
        painter.restore()
        
    def set_current_mouse_pos(self, pos):
        """Mevcut mouse pozisyonunu kaydet (görsel feedback için)"""
        self._current_mouse_pos = pos
        
    def set_background_settings(self, settings):
        """Arka plan ayarlarını güncelle (grid snap için)"""
        self.background_settings = settings 

    def mouseMoveEvent(self, event):
        """Mouse hareket ettirildiğinde"""
        if self.is_scaling and self.selected_strokes and self.scale_center:
            current_pos = event.position()
            
            # Grid snap aktifse pozisyonu snap'le
            if self.background_settings and self.background_settings.get('snap_to_grid', False):
                current_pos = GridSnapUtils.snap_point_to_grid_precise(current_pos, self.background_settings)
            
            # Ölçek faktörünü hesapla
            initial_distance = self.calculate_distance(self.start_pos, self.scale_center)
            current_distance = self.calculate_distance(current_pos, self.scale_center)
            
            if initial_distance > 0:
                scale_factor = current_distance / initial_distance
                
                # Minimum ölçek değişimi kontrolü - grid snap aktifse daha hassas
                min_scale_change = 0.02 if self.background_settings and self.background_settings.get('snap_to_grid', False) else 0.05
                if abs(scale_factor - 1.0) < min_scale_change:
                    return
                
                # Grid snap aktifse ölçek faktörünü grid'e uygun hale getir
                if self.background_settings and self.background_settings.get('snap_to_grid', False):
                    grid_size = self.background_settings.get('grid_size', 20)
                    # Ölçek faktörünü 0.1 katlarına yuvarlama
                    scale_factor = round(scale_factor * 10) / 10
                    if scale_factor <= 0.1:
                        scale_factor = 0.1
                
                # Seçili stroke'ları ölçeklendir
                for stroke in self.selected_strokes:
                    original_data = self.original_stroke_data[id(stroke)]
                    self.scale_stroke(stroke, original_data, scale_factor)
                
                self.drawing_widget.update()

    def scale_stroke_precise(self, stroke_data, scale_factor):
        """Stroke'u hassas grid snap ile boyutlandır"""
        if not hasattr(self, 'original_stroke_data') or id(stroke_data) not in self.original_stroke_data:
            # İlk kez scale ediliyorsa orijinal veriyi sakla
            if not hasattr(self, 'original_stroke_data'):
                self.original_stroke_data = {}
            self.original_stroke_data[id(stroke_data)] = stroke_data.copy()
        
        original_data = self.original_stroke_data[id(stroke_data)]
        self.scale_stroke(stroke_data, original_data, scale_factor)
    
    def scale_stroke(self, stroke, original_data, scale_factor):
        """Stroke'u belirtilen faktörle ölçeklendir"""
        stroke_type = stroke.get('type', '')
        
        if stroke_type == 'freehand':
            if 'points' in original_data:
                stroke['points'] = []
                for point in original_data['points']:
                    if isinstance(point, dict):
                        # Dict formatında - serbest çizimler için her noktayı snap'leme
                        original_point = QPointF(point['x'], point['y'])
                        scaled_point = self.scale_point(original_point, self.scale_center, scale_factor)
                        stroke['points'].append({'x': scaled_point.x(), 'y': scaled_point.y()})
                    else:
                        # QPointF formatında - serbest çizimler için her noktayı snap'leme
                        from stroke_handler import ensure_qpointf
                        original_point = ensure_qpointf(point)
                        scaled_point = self.scale_point(original_point, self.scale_center, scale_factor)
                        stroke['points'].append(scaled_point)
        
        elif stroke_type == 'bspline':
            if 'control_points' in original_data:
                stroke['control_points'] = []
                for cp in original_data['control_points']:
                    original_point = QPointF(cp[0], cp[1])
                    scaled_point = self.scale_point(original_point, self.scale_center, scale_factor)
                    
                    # Grid snap aktifse control point'i snap'le
                    if self.background_settings and self.background_settings.get('snap_to_grid', False):
                        scaled_point = GridSnapUtils.snap_point_to_grid_precise(scaled_point, self.background_settings)
                    
                    stroke['control_points'].append([scaled_point.x(), scaled_point.y()])
        
        elif stroke_type == 'line':
            if 'start_point' in original_data:
                original_start = QPointF(original_data['start_point'][0], original_data['start_point'][1])
                scaled_start = self.scale_point(original_start, self.scale_center, scale_factor)
                
                # Grid snap aktifse endpoint'i snap'le
                if self.background_settings and self.background_settings.get('snap_to_grid', False):
                    scaled_start = GridSnapUtils.snap_point_to_grid_precise(scaled_start, self.background_settings)
                
                stroke['start_point'] = (scaled_start.x(), scaled_start.y())
            
            if 'end_point' in original_data:
                original_end = QPointF(original_data['end_point'][0], original_data['end_point'][1])
                scaled_end = self.scale_point(original_end, self.scale_center, scale_factor)
                
                # Grid snap aktifse endpoint'i snap'le
                if self.background_settings and self.background_settings.get('snap_to_grid', False):
                    scaled_end = GridSnapUtils.snap_point_to_grid_precise(scaled_end, self.background_settings)
                
                stroke['end_point'] = (scaled_end.x(), scaled_end.y())
        
        elif stroke_type == 'rectangle':
            if 'corners' in original_data:
                stroke['corners'] = []
                for corner in original_data['corners']:
                    original_corner = QPointF(corner[0], corner[1])
                    scaled_corner = self.scale_point(original_corner, self.scale_center, scale_factor)
                    
                    # Grid snap aktifse corner'ı snap'le
                    if self.background_settings and self.background_settings.get('snap_to_grid', False):
                        scaled_corner = GridSnapUtils.snap_point_to_grid_precise(scaled_corner, self.background_settings)
                    
                    stroke['corners'].append((scaled_corner.x(), scaled_corner.y()))
            elif 'top_left' in original_data and 'bottom_right' in original_data:
                # Eski format desteği
                original_tl = QPointF(original_data['top_left'][0], original_data['top_left'][1])
                original_br = QPointF(original_data['bottom_right'][0], original_data['bottom_right'][1])
                
                scaled_tl = self.scale_point(original_tl, self.scale_center, scale_factor)
                scaled_br = self.scale_point(original_br, self.scale_center, scale_factor)
                
                # Grid snap aktifse corner'ları snap'le
                if self.background_settings and self.background_settings.get('snap_to_grid', False):
                    scaled_tl = GridSnapUtils.snap_point_to_grid_precise(scaled_tl, self.background_settings)
                    scaled_br = GridSnapUtils.snap_point_to_grid_precise(scaled_br, self.background_settings)
                
                stroke['top_left'] = (scaled_tl.x(), scaled_tl.y())
                stroke['bottom_right'] = (scaled_br.x(), scaled_br.y())
        
        elif stroke_type == 'circle':
            if 'center' in original_data:
                original_center = QPointF(original_data['center'][0], original_data['center'][1])
                scaled_center = self.scale_point(original_center, self.scale_center, scale_factor)
                
                # Grid snap aktifse center'ı snap'le
                if self.background_settings and self.background_settings.get('snap_to_grid', False):
                    scaled_center = GridSnapUtils.snap_point_to_grid_precise(scaled_center, self.background_settings)
                
                stroke['center'] = (scaled_center.x(), scaled_center.y())
            
            if 'radius' in original_data:
                scaled_radius = original_data['radius'] * scale_factor
                
                # Grid snap aktifse radius'u da grid'e uygun hale getir
                if self.background_settings and self.background_settings.get('snap_to_grid', False):
                    grid_size = self.background_settings.get('grid_size', 20)
                    scaled_radius = round(scaled_radius / grid_size) * grid_size
                    if scaled_radius == 0:
                        scaled_radius = grid_size
                
                stroke['radius'] = scaled_radius 