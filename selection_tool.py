from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QPainter, QPen, QBrush
from PyQt6.QtCore import Qt
from stroke_handler import StrokeHandler
import numpy as np

class SelectionTool:
    def __init__(self):
        self.selected_strokes = []   # Seçilen stroke'ların index'leri (çoklu seçim)
        self.selection_rect = None   # Seçim dikdörtgeni
        self.is_selecting = False    # Seçim yapılıyor mu
        self.ctrl_pressed = False    # Ctrl tuşu basılı mı
        self.preview_strokes = []    # Preview (geçici) seçili stroke'lar
        
    def start_selection(self, pos):
        """Seçim işlemini başlat"""
        self.is_selecting = True
        # Minimum 1x1 boyutunda başlat
        self.selection_rect = QRectF(pos.x(), pos.y(), 1, 1)
        
    def update_selection(self, pos):
        """Seçim dikdörtgenini güncelle"""
        # is_selecting kontrolü yeterli, selection_rect zaten var
        if self.is_selecting:
            # Başlangıç noktasını al
            start_x = self.selection_rect.x()
            start_y = self.selection_rect.y()
            
            # Yeni dikdörtgen oluştur
            width = pos.x() - start_x
            height = pos.y() - start_y
            self.selection_rect = QRectF(start_x, start_y, width, height).normalized()
        
    def set_preview_strokes(self, stroke_list):
        """Preview stroke listesini ayarla"""
        self.preview_strokes = stroke_list
            
    def finish_selection(self, strokes):
        """Seçim işlemini tamamla ve seçilen stroke'ları bul"""
        if not self.is_selecting or not self.selection_rect:
            return []
            
        self.is_selecting = False
        self.preview_strokes = []  # Preview listesini temizle
        
        # Eğer seçim dikdörtgeni çok küçükse, nokta seçimi yap
        if (self.selection_rect.width() < 5 and self.selection_rect.height() < 5):
            center = self.selection_rect.center()
            return self.select_stroke_at_point(center, strokes)
        
        # Ctrl tuşu basılı değilse, mevcut seçimi temizle
        if not self.ctrl_pressed:
            self.selected_strokes = []
        
        # Stroke'ların seçim dikdörtgenine çakışıp çakışmadığını kontrol et
        newly_selected = []
        for stroke_index, stroke_data in enumerate(strokes):
            # Image stroke kontrolü
            if hasattr(stroke_data, 'stroke_type') and stroke_data.stroke_type == 'image':
                # Resmin bounding rect'i seçim alanıyla kesişiyor mu?
                image_bounds = stroke_data.get_bounds()
                if self.selection_rect.intersects(image_bounds):
                    if stroke_index not in self.selected_strokes:
                        self.selected_strokes.append(stroke_index)
                        newly_selected.append(stroke_index)
                continue
                
            # Güvenlik kontrolü - eski stroke'lar için
            if 'type' not in stroke_data:
                continue
                
            stroke_selected = False
            
            # Stroke dikdörtgen seçim alanında mı kontrol et
            stroke_selected = StrokeHandler.is_stroke_in_rect(stroke_data, self.selection_rect)
            
            # B-spline için eğri kesişimi de kontrol et
            if not stroke_selected and stroke_data['type'] == 'bspline':
                stroke_selected = self.check_curve_intersection(stroke_data, self.selection_rect)
            
            # Stroke seçildiyse listeye ekle
            if stroke_selected:
                if stroke_index not in self.selected_strokes:
                    self.selected_strokes.append(stroke_index)
                    newly_selected.append(stroke_index)
                    
        return newly_selected if newly_selected else self.selected_strokes
        
    def select_stroke_at_point(self, pos, strokes, tolerance=15):
        """Belirli bir noktadaki stroke'u seç"""
        from scipy.interpolate import splev
        import numpy as np
        
        for stroke_index, stroke_data in enumerate(strokes):
            # Image stroke kontrolü
            if hasattr(stroke_data, 'stroke_type') and stroke_data.stroke_type == 'image':
                if stroke_data.contains_point(pos):
                    return self.toggle_stroke_selection(stroke_index)
                continue
                
            # Güvenlik kontrolü - eski stroke'lar için
            if 'type' not in stroke_data:
                continue
                
            # Modüler yakınlık kontrolü
            if StrokeHandler.is_point_near_stroke(stroke_data, pos, tolerance):
                return self.toggle_stroke_selection(stroke_index)
            
            # B-spline için ek eğri kontrolü
            if stroke_data['type'] == 'bspline':
                try:
                    from scipy.interpolate import splev
                    control_points = stroke_data['control_points']
                    knots = stroke_data['knots']
                    degree = stroke_data['degree']
                    u = stroke_data['u']
                    
                    # B-spline eğrisini değerlendir
                    tck = (knots, control_points.T, degree)
                    u_values = np.linspace(0, u[-1], 100)  # Eğri üzerinde 100 nokta
                    x_curve, y_curve = splev(u_values, tck)
                    
                    # Eğri üzerindeki her noktaya mesafe kontrolü
                    for i in range(len(x_curve)):
                        curve_point = QPointF(x_curve[i], y_curve[i])
                        if (pos - curve_point).manhattanLength() < tolerance:
                            return self.toggle_stroke_selection(stroke_index)
                except:
                    pass
                    
        # Hiçbir şey seçilmediyse ve Ctrl basılı değilse, seçimi temizle
        if not self.ctrl_pressed:
            self.selected_strokes = []
            
        return self.selected_strokes
        
    def check_curve_intersection(self, stroke_data, selection_rect):
        """B-spline eğrisinin seçim dikdörtgeniyle kesişip kesişmediğini kontrol et"""
        try:
            from scipy.interpolate import splev
            import numpy as np
            
            control_points = stroke_data['control_points']
            knots = stroke_data['knots']
            degree = stroke_data['degree']
            u = stroke_data['u']
            
            # B-spline eğrisini değerlendir
            tck = (knots, control_points.T, degree)
            u_values = np.linspace(0, u[-1], 50)  # Daha az nokta ile hızlı kontrol
            x_curve, y_curve = splev(u_values, tck)
            
            # Eğri üzerindeki noktalara seçim dikdörtgeni içinde mi kontrol et
            for i in range(len(x_curve)):
                curve_point = QPointF(x_curve[i], y_curve[i])
                if selection_rect.contains(curve_point):
                    return True
                    
            return False
        except:
            return False
        
    def toggle_stroke_selection(self, stroke_index):
        """Stroke seçimini toggle et (ekle/kaldır)"""
        if self.ctrl_pressed:
            # Ctrl basılıysa toggle yap
            if stroke_index in self.selected_strokes:
                self.selected_strokes.remove(stroke_index)
            else:
                self.selected_strokes.append(stroke_index)
        else:
            # Ctrl basılı değilse, sadece bu stroke'u seç
            self.selected_strokes = [stroke_index]
            
        return self.selected_strokes
        
    def clear_selection(self):
        """Seçimi temizle"""
        self.selected_strokes = []
        self.selection_rect = None
        self.is_selecting = False
        self.preview_strokes = []
        
    def set_ctrl_pressed(self, pressed):
        """Ctrl tuşu durumunu ayarla"""
        self.ctrl_pressed = pressed
        
    def get_selected_count(self):
        """Seçilen stroke sayısını döndür"""
        return len(self.selected_strokes)
        
    def is_stroke_selected(self, stroke_index):
        """Belirtilen stroke seçili mi kontrol et"""
        return stroke_index in self.selected_strokes
        
    def get_selection_center(self, strokes):
        """Seçilen tüm stroke'ların merkezini hesapla"""
        if not self.selected_strokes:
            return None
            
        all_points = []
        for stroke_index in self.selected_strokes:
            if stroke_index < len(strokes):
                stroke_data = strokes[stroke_index]
                
                # Image stroke kontrolü
                if hasattr(stroke_data, 'stroke_type') and stroke_data.stroke_type == 'image':
                    bounds = stroke_data.get_bounds()
                    # Köşe noktalarını ekle
                    all_points.extend([
                        (bounds.left(), bounds.top()),
                        (bounds.right(), bounds.top()),
                        (bounds.left(), bounds.bottom()),
                        (bounds.right(), bounds.bottom())
                    ])
                    continue
                
                # Güvenlik kontrolü - eski stroke'lar için
                if 'type' not in stroke_data:
                    continue
                points = StrokeHandler.get_stroke_points(stroke_data)
                all_points.extend(points)
                
        if not all_points:
            return None
            
        center_x = sum(cp[0] for cp in all_points) / len(all_points)
        center_y = sum(cp[1] for cp in all_points) / len(all_points)
        
        return QPointF(center_x, center_y)
        
    def get_selection_bounding_rect(self, strokes):
        """Seçilen tüm stroke'ların bounding rectangle'ını hesapla"""
        if not self.selected_strokes:
            return None
            
        all_points = []
        for stroke_index in self.selected_strokes:
            if stroke_index < len(strokes):
                stroke_data = strokes[stroke_index]
                
                # Image stroke kontrolü
                if hasattr(stroke_data, 'stroke_type') and stroke_data.stroke_type == 'image':
                    bounds = stroke_data.get_bounds()
                    # Köşe noktalarını ekle
                    all_points.extend([
                        (bounds.left(), bounds.top()),
                        (bounds.right(), bounds.top()),
                        (bounds.left(), bounds.bottom()),
                        (bounds.right(), bounds.bottom())
                    ])
                    continue
                
                # Güvenlik kontrolü - eski stroke'lar için
                if 'type' not in stroke_data:
                    continue
                points = StrokeHandler.get_stroke_points(stroke_data)
                all_points.extend(points)
                
        if not all_points:
            return None
            
        min_x = min(cp[0] for cp in all_points)
        max_x = max(cp[0] for cp in all_points)
        min_y = min(cp[1] for cp in all_points)
        max_y = max(cp[1] for cp in all_points)
        
        padding = 15
        return QRectF(min_x - padding, min_y - padding, 
                     max_x - min_x + 2*padding, max_y - min_y + 2*padding)
        
    def draw_selection(self, painter):
        """Seçim göstergelerini çiz"""
        # Seçim dikdörtgenini çiz
        if self.is_selecting and self.selection_rect:
            painter.save()
            
            # Şeffaf mavi dolgu
            blue_color = Qt.GlobalColor.blue
            fill_brush = QBrush(blue_color)
            fill_brush.setStyle(Qt.BrushStyle.SolidPattern)
            painter.setBrush(fill_brush)
            painter.setOpacity(0.2)  # %20 şeffaflık
            
            # Mavi kenarlık
            pen = QPen(Qt.GlobalColor.blue, 2, Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            
            # Dikdörtgeni çiz
            painter.drawRect(self.selection_rect)
            
            painter.restore()
            
    def draw_selected_stroke_highlight(self, painter, strokes):
        """Seçilen stroke'ları vurgula"""
        if not self.selected_strokes and not self.preview_strokes:
            return
            
        painter.save()
        
        # Kesin seçili stroke'ları vurgula
        for stroke_index in self.selected_strokes:
            if stroke_index < len(strokes):
                stroke_data = strokes[stroke_index]
                
                # Image stroke kontrolü
                if hasattr(stroke_data, 'stroke_type') and stroke_data.stroke_type == 'image':
                    # Resim için özel vurgulama
                    bounds = stroke_data.get_bounds()
                    pen = QPen(Qt.GlobalColor.green, 3, Qt.PenStyle.SolidLine)
                    painter.setPen(pen)
                    painter.drawRect(bounds)
                    continue
                
                # Güvenlik kontrolü - eski stroke'lar için
                if hasattr(stroke_data, 'get') and 'type' not in stroke_data:
                    continue
                elif hasattr(stroke_data, 'get'):
                    StrokeHandler.draw_stroke_highlight(painter, stroke_data, Qt.GlobalColor.green, 8)
                    
        # Preview (geçici) seçili stroke'ları açık yeşil ile vurgula
        for stroke_index in self.preview_strokes:
            if stroke_index < len(strokes) and stroke_index not in self.selected_strokes:
                stroke_data = strokes[stroke_index]
                
                # Image stroke kontrolü
                if hasattr(stroke_data, 'stroke_type') and stroke_data.stroke_type == 'image':
                    # Resim için özel preview vurgulama
                    bounds = stroke_data.get_bounds()
                    pen = QPen(Qt.GlobalColor.cyan, 2, Qt.PenStyle.DashLine)
                    painter.setPen(pen)
                    painter.drawRect(bounds)
                    continue
                
                # Güvenlik kontrolü - eski stroke'lar için
                if hasattr(stroke_data, 'get') and 'type' not in stroke_data:
                    continue
                elif hasattr(stroke_data, 'get'):
                    StrokeHandler.draw_stroke_highlight(painter, stroke_data, Qt.GlobalColor.cyan, 6)
                
        # Tüm seçimin bounding box'ını çiz
        all_selected = list(set(self.selected_strokes + self.preview_strokes))
        if all_selected:
            # Geçici bounding rect hesapla
            all_points = []
            for stroke_index in all_selected:
                if stroke_index < len(strokes):
                    stroke_data = strokes[stroke_index]
                    
                    # Image stroke kontrolü
                    if hasattr(stroke_data, 'stroke_type') and stroke_data.stroke_type == 'image':
                        bounds = stroke_data.get_bounds()
                        all_points.extend([
                            (bounds.left(), bounds.top()),
                            (bounds.right(), bounds.top()),
                            (bounds.left(), bounds.bottom()),
                            (bounds.right(), bounds.bottom())
                        ])
                        continue
                    
                    # Güvenlik kontrolü - eski stroke'lar için
                    if hasattr(stroke_data, 'get') and 'type' not in stroke_data:
                        continue
                    elif hasattr(stroke_data, 'get'):
                        points = StrokeHandler.get_stroke_points(stroke_data)
                        all_points.extend(points)
                    
            if all_points:
                min_x = min(cp[0] for cp in all_points)
                max_x = max(cp[0] for cp in all_points)
                min_y = min(cp[1] for cp in all_points)
                max_y = max(cp[1] for cp in all_points)
                
                padding = 15
                bounding_rect = QRectF(min_x - padding, min_y - padding, 
                                     max_x - min_x + 2*padding, max_y - min_y + 2*padding)
                
                pen = QPen(Qt.GlobalColor.green, 2, Qt.PenStyle.DashLine)
                painter.setPen(pen)
                painter.drawRect(bounding_rect)
                
                # Seçim sayısını göster
                total_count = len(self.selected_strokes)
                preview_count = len([s for s in self.preview_strokes if s not in self.selected_strokes])
                
                if total_count > 1 or preview_count > 0:
                    if preview_count > 0:
                        text = f"{total_count} seçili + {preview_count} önizleme"
                    else:
                        text = f"{total_count} öğe seçili"
                        
                    text_rect = painter.fontMetrics().boundingRect(text)
                    text_pos = QPointF(bounding_rect.right() - text_rect.width() - 5, 
                                     bounding_rect.top() - 5)
                    
                    # Arka plan
                    painter.setBrush(QBrush(Qt.GlobalColor.white))
                    painter.drawRect(QRectF(text_pos.x() - 2, text_pos.y() - text_rect.height() - 2,
                                           text_rect.width() + 4, text_rect.height() + 4))
                    
                    # Metin
                    painter.setPen(QPen(Qt.GlobalColor.black, 1))
                    painter.drawText(text_pos, text)
                
        painter.restore() 