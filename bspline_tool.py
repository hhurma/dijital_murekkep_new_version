from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QPen, QPainter, QPainterPath
from PyQt6.QtCore import Qt, QPointF
from scipy.interpolate import splprep, splev
import numpy as np

class BSplineTool:
    def __init__(self):
        self.current_stroke = []  # Aktif çizim [(QPoint, pressure)]
        self.selected_control_point = None  # (stroke_index, cp_index)
        self.is_drawing = False
        self.current_color = Qt.GlobalColor.black
        self.current_width = 2
        self.line_style = Qt.PenStyle.SolidLine
        
    def start_stroke(self, pos, pressure=1.0):
        """Yeni bir çizim başlat"""
        self.current_stroke = [(pos, pressure)]
        self.is_drawing = True
        self.selected_control_point = None
        
    def add_point(self, pos, pressure=1.0):
        """Aktif çizime nokta ekle"""
        if self.is_drawing:
            self.current_stroke.append((pos, pressure))
            
    def finish_stroke(self):
        """Çizimi tamamla ve B-spline oluştur"""
        if not self.is_drawing or len(self.current_stroke) <= 1:
            self.current_stroke = []
            self.is_drawing = False
            return None
            
        # Benzersiz noktaları filtrele
        unique_points_with_pressure = [self.current_stroke[0]]
        for i in range(1, len(self.current_stroke)):
            if self.current_stroke[i][0] != self.current_stroke[i-1][0]:
                unique_points_with_pressure.append(self.current_stroke[i])
        
        if len(unique_points_with_pressure) > 3:
            # Noktaları downsample et
            downsampled_points_with_pressure = unique_points_with_pressure[::5]
            if len(downsampled_points_with_pressure) < 4:
                downsampled_points_with_pressure = unique_points_with_pressure
                
            # Sadece koordinatları al
            points_only = np.array([(p.x(), p.y()) for p, pressure in downsampled_points_with_pressure])
            
            try:
                # B-spline hesapla
                s_factor = len(points_only) * 3.0
                tck, u = splprep(points_only.T, s=s_factor, k=3)
                
                # Stroke data oluştur
                stroke_data = {
                    'type': 'bspline',  # Modüler sistem için 'type' anahtarı
                    'control_points': np.array(tck[1]).T.tolist(),  # Liste olarak kaydet
                    'knots': tck[0],
                    'degree': tck[2],
                    'u': u,
                    'original_points_with_pressure': downsampled_points_with_pressure,
                    'tool_type': 'bspline',  # Eski uyumluluk için
                    'color': self.current_color,
                    'width': self.current_width,
                    'style': self.line_style  # 'style' field'ını kullan
                }
                
                self.current_stroke = []
                self.is_drawing = False
                return stroke_data
                
            except ValueError as e:
                print(f"B-spline oluşturulamadı ({len(points_only)} nokta): {e}")
                
        else:
            print(f"Yeterli nokta yok ({len(unique_points_with_pressure)} nokta) - en az 4 gerekli.")
            
        self.current_stroke = []
        self.is_drawing = False
        return None
        
    def cancel_stroke(self):
        """Aktif çizimi iptal et"""
        self.current_stroke = []
        self.is_drawing = False
        self.selected_control_point = None
        
    def select_control_point(self, pos, strokes, tolerance=10):
        """Bir kontrol noktası seç"""
        pos_f = QPointF(pos)
        
        for stroke_index, stroke_data in enumerate(strokes):
            # Image stroke kontrolü
            if hasattr(stroke_data, 'stroke_type'):
                continue
                
            if stroke_data.get('type') != 'bspline' and stroke_data.get('tool_type') != 'bspline':
                continue
                
            control_points = stroke_data['control_points']
            for cp_index, cp in enumerate(control_points):
                cp_point = QPointF(cp[0], cp[1])
                if (pos_f - cp_point).manhattanLength() < tolerance:
                    self.selected_control_point = (stroke_index, cp_index)
                    return True
                    
        self.selected_control_point = None
        return False
        
    def move_control_point(self, new_pos, strokes):
        """Seçili kontrol noktasını taşı"""
        if self.selected_control_point is None:
            return False
            
        stroke_index, cp_index = self.selected_control_point
        if stroke_index < len(strokes):
            stroke_data = strokes[stroke_index]
            # Image stroke kontrolü
            if hasattr(stroke_data, 'stroke_type'):
                return False
                
            if stroke_data.get('type') == 'bspline' or stroke_data.get('tool_type') == 'bspline':
                stroke_data['control_points'][cp_index] = [new_pos.x(), new_pos.y()]
                return True
                
        return False
        
    def clear_selection(self):
        """Kontrol noktası seçimini temizle"""
        self.selected_control_point = None
        
    def draw_current_stroke(self, painter):
        """Aktif çizimi çiz (basınç ile)"""
        if len(self.current_stroke) > 1:
            painter.save()
            for i in range(len(self.current_stroke) - 1):
                point1, pressure1 = self.current_stroke[i]
                point2, pressure2 = self.current_stroke[i+1]
                pen_width = self.current_width + pressure1 * (self.current_width * 2)
                pen = QPen(self.current_color, pen_width, Qt.PenStyle.SolidLine, 
                          Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
                painter.setPen(pen)
                painter.drawLine(point1, point2)
            painter.restore()
            
    def draw_bspline(self, painter, stroke_data):
        """B-spline çiz"""
        # Image stroke kontrolü
        if hasattr(stroke_data, 'stroke_type'):
            return
            
        if stroke_data.get('type') != 'bspline' and stroke_data.get('tool_type') != 'bspline':
            return
            
        control_points = stroke_data['control_points']
        knots = stroke_data['knots']
        degree = stroke_data['degree']
        u = stroke_data['u']
        
        # B-spline eğrisini çiz
        painter.save()
        color = stroke_data.get('color', Qt.GlobalColor.black)
        width = stroke_data.get('width', 2)
        line_style = stroke_data.get('style', Qt.PenStyle.SolidLine)
        
        # Color string ise QColor'a çevir
        from PyQt6.QtGui import QColor
        if isinstance(color, str):
            color = QColor(color)
        if isinstance(line_style, int):
            line_style = Qt.PenStyle(line_style)
            
        pen = QPen(color, width, line_style, 
                  Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        
        # Control points'i numpy array'e çevir
        if isinstance(control_points, list):
            control_points = np.array(control_points)
        
        tck = (knots, control_points.T, degree)
        x_fine, y_fine = splev(np.linspace(0, u[-1], 200), tck)
        path = QPainterPath()
        path.moveTo(QPointF(x_fine[0], y_fine[0]))
        for i in range(1, len(x_fine)):
            path.lineTo(QPointF(x_fine[i], y_fine[i]))
        painter.drawPath(path)
        painter.restore()
        
        # Kontrol noktalarını çiz
        painter.save()
        painter.setPen(QPen(Qt.GlobalColor.red, 5, Qt.PenStyle.SolidLine))
        for cp in control_points:
            painter.drawPoint(QPointF(cp[0], cp[1]))
        painter.restore()
        
    def set_color(self, color):
        """Aktif rengi ayarla"""
        self.current_color = color
        
    def set_width(self, width):
        """Aktif çizgi kalınlığını ayarla"""
        self.current_width = width
        
    def set_line_style(self, style):
        """Çizgi stilini ayarla"""
        self.line_style = style
    
    def draw_stroke(self, painter, stroke_data):
        """Tek bir B-spline stroke çiz (modüler sistem için)"""
        self.draw_bspline(painter, stroke_data)
    
    def draw_all_bsplines(self, painter, strokes):
        """Tüm B-spline'ları çiz"""
        for stroke_data in strokes:
            # Image stroke kontrolü
            if hasattr(stroke_data, 'stroke_type'):
                continue
                
            if stroke_data.get('type') == 'bspline' or stroke_data.get('tool_type') == 'bspline':
                self.draw_bspline(painter, stroke_data) 