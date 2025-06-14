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
            
        # Grid snap uygula
        if (self.background_settings and 
            self.background_settings.get('snap_to_grid', False)):
            pos = GridSnapUtils.snap_point_to_grid(pos, self.background_settings)
            
        # Tutamak tipine göre boyutlandırma yöntemini belirle
        handle_type = self.handle_types[self.active_handle]
        
        if handle_type in ["top-left", "top-right", "bottom-left", "bottom-right"]:
            # Köşe tutamakları - proportional scaling
            delta = pos - self.scale_center
            current_distance = math.sqrt(delta.x()**2 + delta.y()**2)
            
            if current_distance == 0 or self.initial_distance == 0:
                return False
                
            new_scale_factor = current_distance / self.initial_distance
            scale_change = new_scale_factor / self.scale_factor
            
            # Minimum ve maksimum scale sınırları
            scale_change = max(0.1, min(5.0, scale_change))
            
            # Tüm seçili stroke'ları boyutlandır
            for selected_stroke in selected_strokes:
                if selected_stroke < len(strokes):
                    stroke_data = strokes[selected_stroke]
                    StrokeHandler.scale_stroke(stroke_data, self.scale_center.x(), self.scale_center.y(), scale_change, scale_change)
                
            self.scale_factor = new_scale_factor
            
        else:
            # Kenar tutamakları - tek yönlü scaling
            # Bounding rect'i al
            bounding_rect = self.get_selection_bounding_rect(strokes, selected_strokes)
            if not bounding_rect:
                return False
                
            # Orijinal kontrol noktalarına göre yeni scale hesapla
            scale_change_x = 1.0
            scale_change_y = 1.0
            
            if handle_type == "left":
                # Sol kenara göre genişlik değişimi
                new_width = bounding_rect.right() - pos.x()
                old_width = bounding_rect.width()
                if old_width > 0:
                    scale_change_x = new_width / old_width
                    scale_change_x = max(0.1, min(5.0, scale_change_x))
                    
            elif handle_type == "right":
                # Sağ kenara göre genişlik değişimi
                new_width = pos.x() - bounding_rect.left()
                old_width = bounding_rect.width()
                if old_width > 0:
                    scale_change_x = new_width / old_width
                    scale_change_x = max(0.1, min(5.0, scale_change_x))
                    
            elif handle_type == "top":
                # Üst kenara göre yükseklik değişimi
                new_height = bounding_rect.bottom() - pos.y()
                old_height = bounding_rect.height()
                if old_height > 0:
                    scale_change_y = new_height / old_height
                    scale_change_y = max(0.1, min(5.0, scale_change_y))
                    
            elif handle_type == "bottom":
                # Alt kenara göre yükseklik değişimi
                new_height = pos.y() - bounding_rect.top()
                old_height = bounding_rect.height()
                if old_height > 0:
                    scale_change_y = new_height / old_height
                    scale_change_y = max(0.1, min(5.0, scale_change_y))
            
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