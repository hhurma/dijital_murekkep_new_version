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
        self.background_settings = None  # (Eski) arka plan ayarları
        self.grid_settings = None  # Tek kaynak snap ayarları
        self.shift_pressed = False   # Shift tuşu durumu
        
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
        
        # Seçilen şekillerin tümü düz çizgi mi kontrol et
        all_lines = True
        single_line = None
        
        for selected_stroke in selected_strokes:
            if selected_stroke < len(strokes):
                stroke_data = strokes[selected_stroke]
                if not hasattr(stroke_data, 'get') or stroke_data.get('type') != 'line':
                    all_lines = False
                    break
                if single_line is None:
                    single_line = stroke_data
                    
        # Tek bir düz çizgi seçiliyse, özel tutamaçlar oluştur
        if all_lines and len(selected_strokes) == 1 and single_line is not None:
            self.create_line_handles(single_line)
            return
            
        # Diğer şekiller için standart tutamaçlar
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
            
    def create_line_handles(self, line_stroke):
        """Düz çizgi için özel tutamaçlar oluştur"""
        if not line_stroke or 'start_point' not in line_stroke or 'end_point' not in line_stroke:
            return
            
        handle_size = 8
        
        # Başlangıç ve bitiş noktaları
        start_point = QPointF(line_stroke['start_point'][0], line_stroke['start_point'][1])
        end_point = QPointF(line_stroke['end_point'][0], line_stroke['end_point'][1])
        
        # Başlangıç ve bitiş noktalarında tutamaçlar
        start_handle = QRectF(start_point.x() - handle_size/2, 
                            start_point.y() - handle_size/2,
                            handle_size, handle_size)
        end_handle = QRectF(end_point.x() - handle_size/2, 
                          end_point.y() - handle_size/2,
                          handle_size, handle_size)
        
        # Tutamaçları ekle
        self.scale_handles.append(start_handle)
        self.handle_types.append("start")
        
        self.scale_handles.append(end_handle)
        self.handle_types.append("end")
        
        # Orta nokta (çizgiyi taşımak için)
        mid_point = QPointF((start_point.x() + end_point.x()) / 2, 
                          (start_point.y() + end_point.y()) / 2)
        mid_handle = QRectF(mid_point.x() - handle_size/2, 
                          mid_point.y() - handle_size/2,
                          handle_size, handle_size)
        self.scale_handles.append(mid_handle)
        self.handle_types.append("middle")
    
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
        
        # Orijinal stroke verilerini kaydet
        if not hasattr(self, 'original_stroke_data'):
            self.original_stroke_data = {}
        for stroke_index in selected_strokes:
            if stroke_index < len(strokes):
                stroke_data = strokes[stroke_index]
                # Image stroke kontrolü
                if not hasattr(stroke_data, 'stroke_type'):
                    self.original_stroke_data[id(stroke_data)] = stroke_data.copy()
        
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
            
        # Grid snap uygula - tek kaynak grid_settings
        snapped_pos = pos
        if hasattr(self, 'grid_settings') and self.grid_settings and self.grid_settings.get('snap_to_grid', False):
            snapped_pos = GridSnapUtils.snap_point_to_grid_precise(pos, self.grid_settings)
            
        # Tutamak tipine göre boyutlandırma yöntemini belirle
        handle_type = self.handle_types[self.active_handle]
        
        # Seçilen şekillerin tümü düz çizgi mi kontrol et
        all_lines = True
        for selected_stroke in selected_strokes:
            if selected_stroke < len(strokes):
                stroke_data = strokes[selected_stroke]
                if not hasattr(stroke_data, 'get') or stroke_data.get('type') != 'line':
                    all_lines = False
                    break
        
        # Eğer tüm seçilen şekiller düz çizgi ise, özel ölçeklendirme uygula
        if all_lines and len(selected_strokes) == 1:
            # Tek bir düz çizgi seçiliyse, doğrudan scale_stroke metodunu kullan
            selected_stroke = selected_strokes[0]
            stroke_data = strokes[selected_stroke]
            
            # Orijinal stroke verilerini sakla
            if not hasattr(self, 'original_stroke_data'):
                self.original_stroke_data = {}
            if id(stroke_data) not in self.original_stroke_data:
                self.original_stroke_data[id(stroke_data)] = stroke_data.copy()
            
            original_data = self.original_stroke_data[id(stroke_data)]
            original_start = QPointF(original_data['start_point'][0], original_data['start_point'][1])
            original_end = QPointF(original_data['end_point'][0], original_data['end_point'][1])
            
            # Düz çizgi için özel tutamaçlar
            if handle_type == "start":
                # Başlangıç noktasını doğrudan güncelle
                stroke_data['start_point'] = (snapped_pos.x(), snapped_pos.y())
                return True
            elif handle_type == "end":
                # Bitiş noktasını doğrudan güncelle
                stroke_data['end_point'] = (snapped_pos.x(), snapped_pos.y())
                return True
            elif handle_type == "middle":
                # Orta noktadan taşıma - çizginin tamamını taşı
                mid_x = (original_start.x() + original_end.x()) / 2
                mid_y = (original_start.y() + original_end.y()) / 2
                
                # Taşıma miktarını hesapla
                delta_x = snapped_pos.x() - mid_x
                delta_y = snapped_pos.y() - mid_y
                
                # Yeni başlangıç ve bitiş noktaları
                new_start_x = original_start.x() + delta_x
                new_start_y = original_start.y() + delta_y
                new_end_x = original_end.x() + delta_x
                new_end_y = original_end.y() + delta_y
                
                # Çizgiyi güncelle
                stroke_data['start_point'] = (new_start_x, new_start_y)
                stroke_data['end_point'] = (new_end_x, new_end_y)
                return True
            
            # Ölçek faktörünü hesapla
            scale_factor = 1.5  # Varsayılan değer
            
            # Tutamak tipine göre ölçeklendirme faktörünü hesapla
            # Çizgi uzunluğunu hesapla
            original_length = math.sqrt((original_end.x() - original_start.x())**2 + (original_end.y() - original_start.y())**2)
            
            # Tutamak tipine göre yeni uzunluğu hesapla
            if handle_type == "right":
                # Sağ tutamak - sağ ucu hareket ettir
                # Mouse pozisyonu ile sabit uç arasındaki mesafeyi hesapla
                new_length = math.sqrt((snapped_pos.x() - original_start.x())**2 + (snapped_pos.y() - original_start.y())**2)
                if original_length > 0:
                    scale_factor = new_length / original_length
            elif handle_type == "left":
                # Sol tutamak - sol ucu hareket ettir
                # Mouse pozisyonu ile sabit uç arasındaki mesafeyi hesapla
                new_length = math.sqrt((snapped_pos.x() - original_end.x())**2 + (snapped_pos.y() - original_end.y())**2)
                if original_length > 0:
                    scale_factor = new_length / original_length
            elif handle_type == "top" or handle_type == "bottom":
                # Üst/alt tutamak - dikey uzunluğa göre ölçeklendir
                # Çizginin yatay/dikey durumuna göre ölçeklendirme yap
                dx = original_end.x() - original_start.x()
                dy = original_end.y() - original_start.y()
                
                if abs(dx) > abs(dy):  # Yatay çizgi
                    if handle_type == "top":
                        fixed_point = original_start if original_start.y() >= original_end.y() else original_end
                    else:
                        fixed_point = original_start if original_start.y() <= original_end.y() else original_end
                else:  # Dikey çizgi
                    if handle_type == "top":
                        fixed_point = original_start if original_start.y() <= original_end.y() else original_end
                    else:
                        fixed_point = original_start if original_start.y() >= original_end.y() else original_end
                
                new_length = math.sqrt((snapped_pos.x() - fixed_point.x())**2 + (snapped_pos.y() - fixed_point.y())**2)
                if original_length > 0:
                    scale_factor = new_length / original_length
            
            # Ölçek sınırlarını kontrol et
            scale_factor = max(0.1, min(5.0, scale_factor))
            
            # Çizgiyi ölçeklendir
            self.scale_stroke(stroke_data, original_data, scale_factor)
            
            return True
            
        # Diğer şekiller için standart ölçeklendirme
        if handle_type in ["top-left", "top-right", "bottom-left", "bottom-right"]:
            # Köşe tutamakları - proportional scaling
            delta = snapped_pos - self.scale_center
            current_distance = math.sqrt(delta.x()**2 + delta.y()**2)
            
            if current_distance == 0 or self.initial_distance == 0:
                return False
                
            # Orijinal boyuttan direkt scale faktörü hesapla
            new_scale_factor = current_distance / self.initial_distance
            
            # Minimum scale değişimini kontrol et
            if abs(new_scale_factor - self.scale_factor) < 0.001:  # Çok küçük değişim varsa atla
                return False
            
            # Minimum ve maksimum scale sınırları
            new_scale_factor = max(0.1, min(5.0, new_scale_factor))
            
            # Tüm seçili stroke'ları boyutlandır
            for selected_stroke in selected_strokes:
                if selected_stroke < len(strokes):
                    stroke_data = strokes[selected_stroke]
                    
                    # Image stroke kontrolü
                    if hasattr(stroke_data, 'stroke_type') and stroke_data.stroke_type == 'image':
                        # İlk kez scale ediliyorsa orijinal boyutu sakla
                        if not hasattr(self, 'original_image_sizes'):
                            self.original_image_sizes = {}
                        if id(stroke_data) not in self.original_image_sizes:
                            self.original_image_sizes[id(stroke_data)] = QPointF(stroke_data.size)
                        
                        # Orijinal boyuttan yeni boyutu hesapla
                        original_size = self.original_image_sizes[id(stroke_data)]
                        new_size = QPointF(original_size.x() * new_scale_factor, original_size.y() * new_scale_factor)
                        stroke_data.set_size(new_size)
                        continue
                    
                    # Orijinal boyuttan direkt scale uygula (daha stabil)
                    self.scale_stroke_precise(stroke_data, new_scale_factor)
                
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
            
            # Minimum scale değişimini kontrol et
            if (abs(scale_change_x - 1.0) < 0.001 and abs(scale_change_y - 1.0) < 0.001):  # %0.1'den az değişim varsa atla
                return False
            
            # Tüm seçili stroke'ları tek seferde scale uygula
            for selected_stroke in selected_strokes:
                if selected_stroke < len(strokes):
                    stroke_data = strokes[selected_stroke]
                    
                    # Image stroke kontrolü
                    if hasattr(stroke_data, 'stroke_type') and stroke_data.stroke_type == 'image':
                        # İlk kez scale ediliyorsa orijinal boyutu sakla
                        if not hasattr(self, 'original_image_sizes'):
                            self.original_image_sizes = {}
                        if id(stroke_data) not in self.original_image_sizes:
                            self.original_image_sizes[id(stroke_data)] = QPointF(stroke_data.size)
                        
                        # Orijinal boyuttan yeni boyutu hesapla
                        original_size = self.original_image_sizes[id(stroke_data)]
                        new_size = QPointF(original_size.x() * scale_change_x, original_size.y() * scale_change_y)
                        stroke_data.set_size(new_size)
                        continue
                    
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
        # Resim boyutları cache'ini temizle
        if hasattr(self, 'original_image_sizes'):
            delattr(self, 'original_image_sizes')
        if hasattr(self, 'total_scale_factors'):
            delattr(self, 'total_scale_factors')
        # Orijinal stroke verilerini temizle
        if hasattr(self, 'original_stroke_data'):
            delattr(self, 'original_stroke_data')
        
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
        
        # Seçilen şekillerin tümü düz çizgi mi kontrol et
        is_single_line = False
        if len(selected_strokes) == 1:
            selected_stroke = selected_strokes[0]
            if selected_stroke < len(strokes):
                stroke_data = strokes[selected_stroke]
                if hasattr(stroke_data, 'get') and stroke_data.get('type') == 'line':
                    is_single_line = True
        
        # Tutamakları çiz
        for i, handle in enumerate(self.scale_handles):
            handle_type = self.handle_types[i]
            
            if i == self.active_handle:
                # Aktif tutamak farklı renkte
                painter.setBrush(QBrush(Qt.GlobalColor.yellow))
                painter.setPen(QPen(Qt.GlobalColor.red, 2))
            elif handle_type in ["start", "end"]:
                # Düz çizgi uç noktaları - kare şekil
                painter.setBrush(QBrush(Qt.GlobalColor.green))
                painter.setPen(QPen(Qt.GlobalColor.darkGreen, 2))
            elif handle_type == "middle":
                # Düz çizgi orta noktası - daire şekil
                painter.setBrush(QBrush(Qt.GlobalColor.blue))
                painter.setPen(QPen(Qt.GlobalColor.darkBlue, 2))
            elif handle_type in ["top-left", "top-right", "bottom-left", "bottom-right"]:
                # Köşe tutamakları - kare şekil
                painter.setBrush(QBrush(Qt.GlobalColor.white))
                painter.setPen(QPen(Qt.GlobalColor.blue, 2))
            else:
                # Kenar tutamakları - daire şekil
                painter.setBrush(QBrush(Qt.GlobalColor.lightGray))
                painter.setPen(QPen(Qt.GlobalColor.darkBlue, 2))
                
            if handle_type in ["top-left", "top-right", "bottom-left", "bottom-right", "start", "end"]:
                # Köşe tutamakları ve çizgi uç noktaları kare olarak çiz
                painter.drawRect(handle)
            else:
                # Kenar tutamakları ve çizgi orta noktası daire olarak çiz
                painter.drawEllipse(handle)
            
        # Boyutlandırma merkezi
        if self.scale_center and self.is_scaling:
            painter.setBrush(QBrush(Qt.GlobalColor.red))
            painter.setPen(QPen(Qt.GlobalColor.red, 2))
            center_size = 4
            painter.drawEllipse(QRectF(self.scale_center.x() - center_size/2,
                                     self.scale_center.y() - center_size/2,
                                     center_size, center_size))
            
        # Bounding rectangle çiz (düz çizgi için çizme)
        if not is_single_line:
            bounding_rect = self.get_selection_bounding_rect(strokes, selected_strokes)
            if bounding_rect:
                painter.setPen(QPen(Qt.GlobalColor.gray, 1, Qt.PenStyle.DashLine))
                painter.setBrush(QBrush())  # Şeffaf fill
                painter.drawRect(bounding_rect)
        else:
            # Düz çizgi için çizgiyi vurgula
            selected_stroke = selected_strokes[0]
            if selected_stroke < len(strokes):
                stroke_data = strokes[selected_stroke]
                if 'start_point' in stroke_data and 'end_point' in stroke_data:
                    start_point = QPointF(stroke_data['start_point'][0], stroke_data['start_point'][1])
                    end_point = QPointF(stroke_data['end_point'][0], stroke_data['end_point'][1])
                    
                    # Çizgiyi vurgula
                    painter.setPen(QPen(Qt.GlobalColor.gray, 1, Qt.PenStyle.DashLine))
                    painter.drawLine(start_point, end_point)
                
        painter.restore()
        
    def set_current_mouse_pos(self, pos):
        """Mevcut mouse pozisyonunu kaydet (görsel feedback için)"""
        self._current_mouse_pos = pos
        
    def set_background_settings(self, settings):
        """Arka plan ayarlarını güncelle (grid snap için)"""
        self.background_settings = settings
    
    def scale_point(self, point, center, scale_factor):
        """Bir noktayı merkez etrafında ölçeklendir"""
        # Merkeze göre relatif pozisyon
        relative_x = point.x() - center.x()
        relative_y = point.y() - center.y()
        
        # Ölçeklendir
        scaled_x = relative_x * scale_factor
        scaled_y = relative_y * scale_factor
        
        # Merkezi geri ekle
        return QPointF(center.x() + scaled_x, center.y() + scaled_y) 

    def mouseMoveEvent(self, event):
        """Mouse hareket ettirildiğinde"""
        if self.is_scaling and self.selected_strokes and self.scale_center:
            current_pos = event.position()
            
            # Grid snap aktifse pozisyonu snap'le (tek kaynak grid_settings)
            if hasattr(self, 'grid_settings') and self.grid_settings and self.grid_settings.get('snap_to_grid', False):
                current_pos = GridSnapUtils.snap_point_to_grid_precise(current_pos, self.grid_settings)
            
            # Ölçek faktörünü hesapla
            initial_distance = self.calculate_distance(self.start_pos, self.scale_center)
            current_distance = self.calculate_distance(current_pos, self.scale_center)
            
            if initial_distance > 0:
                scale_factor = current_distance / initial_distance
                
                # Minimum ölçek değişimi kontrolü - çok hassas yapıldı
                min_scale_change = 0.001  # %0.1 değişim bile algılansın
                if abs(scale_factor - 1.0) < min_scale_change:
                    return
                
                # Grid snap aktifse ölçek faktörünü daha hassas hale getir (tek kaynak grid_settings)
                if hasattr(self, 'grid_settings') and self.grid_settings and self.grid_settings.get('snap_to_grid', False):
                    # Ölçek faktörünü 0.01 katlarına yuvarlama (daha hassas)
                    scale_factor = round(scale_factor * 100) / 100
                    if scale_factor <= 0.01:
                        scale_factor = 0.01
                
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
                    if hasattr(self, 'grid_settings') and self.grid_settings and self.grid_settings.get('snap_to_grid', False):
                        scaled_point = GridSnapUtils.snap_point_to_grid_precise(scaled_point, self.background_settings)
                    
                    stroke['control_points'].append([scaled_point.x(), scaled_point.y()])
        
        elif stroke_type == 'line':
            # Düz çizgi için özel ölçeklendirme
            if 'start_point' in original_data and 'end_point' in original_data:
                original_start = QPointF(original_data['start_point'][0], original_data['start_point'][1])
                original_end = QPointF(original_data['end_point'][0], original_data['end_point'][1])
                
                # Aktif tutamak tipini kontrol et
                handle_type = self.handle_types[self.active_handle] if self.active_handle is not None else None
                
                # Shift tuşu basılıysa her iki ucu da ölçeklendir
                if self.shift_pressed:
                    # Her iki ucu da merkeze göre ölçeklendir
                    scaled_start = self.scale_point(original_start, self.scale_center, scale_factor)
                    scaled_end = self.scale_point(original_end, self.scale_center, scale_factor)
                else:
                    # update_scale metodunda tutamak tipine göre ölçeklendirme yapıldı
                    # Burada sadece scale_point_from_fixed kullanarak ölçeklendirme yapıyoruz
                    if handle_type == "right":
                        scaled_start = original_start
                        scaled_end = self.scale_point_from_fixed(original_end, original_start, scale_factor)
                    elif handle_type == "left":
                        scaled_start = self.scale_point_from_fixed(original_start, original_end, scale_factor)
                        scaled_end = original_end
                    elif handle_type == "top":
                        if original_start.y() <= original_end.y():
                            scaled_start = self.scale_point_from_fixed(original_start, original_end, scale_factor)
                            scaled_end = original_end
                        else:
                            scaled_start = original_start
                            scaled_end = self.scale_point_from_fixed(original_end, original_start, scale_factor)
                    elif handle_type == "bottom":
                        if original_start.y() >= original_end.y():
                            scaled_start = self.scale_point_from_fixed(original_start, original_end, scale_factor)
                            scaled_end = original_end
                        else:
                            scaled_start = original_start
                            scaled_end = self.scale_point_from_fixed(original_end, original_start, scale_factor)
                    else:
                        # Köşe tutamakları - her iki ucu da merkeze göre ölçeklendir
                        scaled_start = self.scale_point(original_start, self.scale_center, scale_factor)
                        scaled_end = self.scale_point(original_end, self.scale_center, scale_factor)
                
                # Grid snap aktifse endpoint'leri snap'le
                if hasattr(self, 'grid_settings') and self.grid_settings and self.grid_settings.get('snap_to_grid', False):
                    scaled_start = GridSnapUtils.snap_point_to_grid_precise(scaled_start, self.background_settings)
                    scaled_end = GridSnapUtils.snap_point_to_grid_precise(scaled_end, self.background_settings)
                
                stroke['start_point'] = (scaled_start.x(), scaled_start.y())
                stroke['end_point'] = (scaled_end.x(), scaled_end.y())
        
        elif stroke_type == 'rectangle':
            if 'corners' in original_data:
                stroke['corners'] = []
                for corner in original_data['corners']:
                    original_corner = QPointF(corner[0], corner[1])
                    scaled_corner = self.scale_point(original_corner, self.scale_center, scale_factor)
                    
                    # Grid snap aktifse corner'ı snap'le
                    if hasattr(self, 'grid_settings') and self.grid_settings and self.grid_settings.get('snap_to_grid', False):
                        scaled_corner = GridSnapUtils.snap_point_to_grid_precise(scaled_corner, self.background_settings)
                    
                    stroke['corners'].append((scaled_corner.x(), scaled_corner.y()))
            elif 'top_left' in original_data and 'bottom_right' in original_data:
                # Eski format desteği
                original_tl = QPointF(original_data['top_left'][0], original_data['top_left'][1])
                original_br = QPointF(original_data['bottom_right'][0], original_data['bottom_right'][1])
                
                scaled_tl = self.scale_point(original_tl, self.scale_center, scale_factor)
                scaled_br = self.scale_point(original_br, self.scale_center, scale_factor)
                
                # Grid snap aktifse corner'ları snap'le
                if hasattr(self, 'grid_settings') and self.grid_settings and self.grid_settings.get('snap_to_grid', False):
                    scaled_tl = GridSnapUtils.snap_point_to_grid_precise(scaled_tl, self.background_settings)
                    scaled_br = GridSnapUtils.snap_point_to_grid_precise(scaled_br, self.background_settings)
                
                stroke['top_left'] = (scaled_tl.x(), scaled_tl.y())
                stroke['bottom_right'] = (scaled_br.x(), scaled_br.y())
        
        elif stroke_type == 'circle':
            if 'center' in original_data:
                original_center = QPointF(original_data['center'][0], original_data['center'][1])
                scaled_center = self.scale_point(original_center, self.scale_center, scale_factor)
                
                # Grid snap aktifse center'ı snap'le
                if hasattr(self, 'grid_settings') and self.grid_settings and self.grid_settings.get('snap_to_grid', False):
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
                
    def distance_to_handle(self, point, handle_type):
        """Bir noktanın belirli bir tutamaca olan uzaklığını hesapla"""
        if not self.scale_handles or handle_type is None:
            return float('inf')
            
        # Tutamak indeksini bul
        handle_index = -1
        for i, h_type in enumerate(self.handle_types):
            if h_type == handle_type:
                handle_index = i
                break
                
        if handle_index == -1:
            return float('inf')
            
        # Tutamak merkezi
        handle = self.scale_handles[handle_index]
        handle_center = QPointF(handle.center())
        
        # Düz çizgiler için özel kontroller
        # Kenar tutamakları için özel kontrol
        if handle_type == "left" or handle_type == "right":
            # X koordinatına göre uzaklık (yatay tutamaçlar için)
            return abs(point.x() - handle_center.x())
        elif handle_type == "top" or handle_type == "bottom":
            # Y koordinatına göre uzaklık (dikey tutamaçlar için)
            return abs(point.y() - handle_center.y())
        else:
            # Köşe tutamakları için normal uzaklık hesapla
            dx = point.x() - handle_center.x()
            dy = point.y() - handle_center.y()
            return math.sqrt(dx*dx + dy*dy)
        
    def set_shift_pressed(self, pressed):
        """Shift tuşu durumunu ayarla"""
        self.shift_pressed = pressed 

    def scale_point_from_fixed(self, point_to_scale, fixed_point, scale_factor):
        """Bir noktayı sabit bir noktaya göre ölçeklendir"""
        # Sabit noktaya göre relatif pozisyon
        relative_x = point_to_scale.x() - fixed_point.x()
        relative_y = point_to_scale.y() - fixed_point.y()
        
        # Orijinal mesafe ve açıyı hesapla
        original_distance = math.sqrt(relative_x**2 + relative_y**2)
        if original_distance == 0:
            return QPointF(point_to_scale)  # Sıfır uzunluk, değişiklik yok
            
        # Açıyı hesapla
        angle = math.atan2(relative_y, relative_x)
        
        # Yeni mesafeyi hesapla
        new_distance = original_distance * scale_factor
        
        # Yeni koordinatları hesapla (açıyı koruyarak)
        new_x = fixed_point.x() + new_distance * math.cos(angle)
        new_y = fixed_point.y() + new_distance * math.sin(angle)
        
        return QPointF(new_x, new_y) 