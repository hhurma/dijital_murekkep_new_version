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
            
        # Şu anki açıyı hesapla - grid snap kullanmadan
        delta = pos - self.rotation_center
        current_angle = math.atan2(delta.y(), delta.x())
        
        # Opsiyonel: Shift tuşu basılıysa 15 derece aralıklarla snap'le
        # (Grid snap yerine manuel snap)
        # if shift_pressed:  # Bu özellik ileride eklenebilir
        #     angle_degrees = math.degrees(current_angle)
        #     snap_angle_degrees = round(angle_degrees / 15) * 15
        #     current_angle = math.radians(snap_angle_degrees)
        
        # Açı farkı
        angle_diff = current_angle - self.last_angle
        
        # Çok küçük açı değişimlerini atla
        if abs(angle_diff) < 0.02:  # ~1 derece - daha hassas
            return False
        
        # Tüm seçili stroke'ların kontrol noktalarını döndür
        cos_angle = math.cos(angle_diff)
        sin_angle = math.sin(angle_diff)
        
        for selected_stroke in selected_strokes:
            if selected_stroke < len(strokes):
                stroke_data = strokes[selected_stroke]
                
                # Image stroke kontrolü
                if hasattr(stroke_data, 'stroke_type') and stroke_data.stroke_type == 'image':
                    # İlk kez rotate ediliyorsa orijinal değerleri sakla
                    if not hasattr(self, 'original_image_data'):
                        self.original_image_data = {}
                    if not hasattr(self, 'total_rotation_angles'):
                        self.total_rotation_angles = {}
                    if id(stroke_data) not in self.original_image_data:
                        self.original_image_data[id(stroke_data)] = {
                            'position': QPointF(stroke_data.position),
                            'rotation': stroke_data.rotation
                        }
                        self.total_rotation_angles[id(stroke_data)] = 0.0
                    
                    # Toplam açı değişimini güncelle
                    total_angle = self.last_angle - self.start_angle
                    self.total_rotation_angles[id(stroke_data)] = total_angle
                    
                    # Orijinal değerlerden yeni pozisyonu hesapla
                    original_data = self.original_image_data[id(stroke_data)]
                    original_pos = original_data['position']
                    original_bounds = QRectF(original_pos.x(), original_pos.y(), 
                                           stroke_data.size.x(), stroke_data.size.y())
                    original_center = original_bounds.center()
                    
                    # Orijinal merkezi döndürme merkezi etrafında döndür
                    rel_x = original_center.x() - self.rotation_center.x()
                    rel_y = original_center.y() - self.rotation_center.y()
                    
                    cos_a = math.cos(total_angle)
                    sin_a = math.sin(total_angle)
                    
                    new_center_x = rel_x * cos_a - rel_y * sin_a + self.rotation_center.x()
                    new_center_y = rel_x * sin_a + rel_y * cos_a + self.rotation_center.y()
                    
                    # Yeni pozisyonu ayarla (merkez pozisyonundan sol üst köşeye çevir)
                    offset_x = new_center_x - stroke_data.size.x() / 2
                    offset_y = new_center_y - stroke_data.size.y() / 2
                    stroke_data.set_position(QPointF(offset_x, offset_y))
                    
                    # Resmin kendi rotasyonunu da güncelle
                    original_rotation = original_data['rotation']
                    stroke_data.rotation = original_rotation + math.degrees(total_angle)
                    continue
                
                # Hassas grid snap ile rotate uygula
                self.rotate_stroke_precise(stroke_data)
            
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
        
        # Orijinal stroke data'yı güncelle (temizleme yerine)
        if hasattr(self, 'original_stroke_data'):
            # Döndürülmüş data'yı yeni orijinal olarak kaydet
            for stroke_id in self.original_stroke_data.keys():
                # Bu strokes listesinde karşılık gelen stroke'u bul ve güncelle
                # Not: Bu manuel yaklaşım yerine stroke referanslarını korumak daha iyi olacak
                pass
            # Bu sefer temizleme, bir sonraki rotate için hazır olsun
            delattr(self, 'original_stroke_data')
        
        # Resim cache'ini temizle
        if hasattr(self, 'original_image_data'):
            delattr(self, 'original_image_data')
        if hasattr(self, 'total_rotation_angles'):
            delattr(self, 'total_rotation_angles')
        
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
    
    def rotate_stroke_precise(self, stroke_data):
        """Stroke'u hassas döndürme ile döndür - orijinal data'dan hesapla"""
        if not hasattr(self, 'original_stroke_data') or id(stroke_data) not in self.original_stroke_data:
            # İlk kez rotate ediliyorsa format conversion ile birlikte orijinal veriyi sakla
            if not hasattr(self, 'original_stroke_data'):
                self.original_stroke_data = {}
                
            # Eski rectangle formatını yeni formata çevir (orijinal data için)
            original_copy = stroke_data.copy()
            if (original_copy.get('type') == 'rectangle' and 
                'corners' not in original_copy and 
                'top_left' in original_copy and 'bottom_right' in original_copy):
                tl = original_copy['top_left']
                br = original_copy['bottom_right']
                # 4 köşeyi oluştur
                original_copy['corners'] = [
                    tl,  # Sol üst
                    (br[0], tl[1]),  # Sağ üst  
                    br,  # Sağ alt
                    (tl[0], br[1])   # Sol alt
                ]
                # Eski formatı kaldır
                del original_copy['top_left']
                del original_copy['bottom_right']
            
            self.original_stroke_data[id(stroke_data)] = original_copy
        
        # Mevcut gölge verilerini koru
        current_shadow_data = {}
        shadow_keys = ['has_shadow', 'shadow_color', 'shadow_blur', 'shadow_size', 
                      'shadow_opacity', 'shadow_offset_x', 'shadow_offset_y', 
                      'inner_shadow', 'shadow_quality']
        for key in shadow_keys:
            if key in stroke_data:
                current_shadow_data[key] = stroke_data[key]
        
        # Önce orijinal data'yı geri yükle
        original_data = self.original_stroke_data[id(stroke_data)]
        stroke_data.clear()
        stroke_data.update(original_data.copy())
        
        # Mevcut gölge verilerini geri yükle
        for key, value in current_shadow_data.items():
            stroke_data[key] = value
        
        # Sonra total angle ile döndür
        total_angle = self.last_angle - self.start_angle
        angle_rad = total_angle
        
        # Tüm şekiller için StrokeHandler kullan
        StrokeHandler.rotate_stroke(stroke_data, self.rotation_center.x(), self.rotation_center.y(), angle_rad)
