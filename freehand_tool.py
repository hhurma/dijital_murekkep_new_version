from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QPainter, QPen, QPainterPath
import math

def ensure_qpointf(point):
    """Point'i QPointF'e dönüştür (dict'ten veya zaten QPointF'ten)"""
    if isinstance(point, dict):
        return QPointF(point['x'], point['y'])
    elif isinstance(point, QPointF):
        return point
    else:
        # Başka bir format, deneme
        return QPointF(point.x(), point.y())

class FreehandTool:
    def __init__(self):
        self.is_drawing = False
        self.current_stroke = None
        self.current_color = Qt.GlobalColor.black
        self.current_width = 2
        self.line_style = Qt.PenStyle.SolidLine
        
        # Daha güçlü smoothing ayarları (küçük iyileştirme)
        self.min_distance = 2.8  # 3.0'dan hafifçe azaltıldı
        self.smoothing_buffer = []
        self.buffer_size = 4
        
        # Adaptive smoothing için
        self.velocity_threshold = 15.0  # Hızlı çizimde daha az smoothing
        
    def start_stroke(self, pos, pressure=1.0):
        """Yeni bir serbest çizim başlat"""
        self.is_drawing = True
        self.smoothing_buffer = [pos]
        self.current_stroke = {
            'type': 'freehand',
            'points': [pos],
            'pressures': [pressure],
            'color': self.current_color,
            'width': self.current_width,
            'line_style': self.line_style
        }
        
    def add_point(self, pos, pressure=1.0):
        """Serbest çizime nokta ekle"""
        if self.is_drawing and self.current_stroke:
            # Minimum mesafe kontrolü
            if len(self.current_stroke['points']) > 0:
                last_pos = self.current_stroke['points'][-1]
                distance = math.sqrt((pos.x() - last_pos.x()) ** 2 + (pos.y() - last_pos.y()) ** 2)
                if distance < self.min_distance:
                    return
            
            # Buffer'a ekle
            self.smoothing_buffer.append(pos)
            if len(self.smoothing_buffer) > self.buffer_size:
                self.smoothing_buffer.pop(0)
            
            # Smoothing uygula
            smoothed_pos = self._calculate_smoothed_point()
            if smoothed_pos:
                self.current_stroke['points'].append(smoothed_pos)
                self.current_stroke['pressures'].append(pressure)
    
    def _calculate_smoothed_point(self):
        """Gelişmiş smoothing hesaplama"""
        if len(self.smoothing_buffer) < 2:
            return self.smoothing_buffer[-1] if self.smoothing_buffer else None
        
        # Daha güçlü smoothing (önceki iyi versiyon)
        if len(self.smoothing_buffer) == 2:
            p1, p2 = self.smoothing_buffer
            return QPointF(
                (p1.x() * 0.4 + p2.x() * 0.6),  # %60 yeni nokta
                (p1.y() * 0.4 + p2.y() * 0.6)
            )
        elif len(self.smoothing_buffer) == 3:
            p1, p2, p3 = self.smoothing_buffer
            return QPointF(
                (p1.x() * 0.2 + p2.x() * 0.5 + p3.x() * 0.3),
                (p1.y() * 0.2 + p2.y() * 0.5 + p3.y() * 0.3)
            )
        else:
            # 4 nokta için daha smooth
            p1, p2, p3, p4 = self.smoothing_buffer[-4:]
            return QPointF(
                (p1.x() * 0.1 + p2.x() * 0.3 + p3.x() * 0.4 + p4.x() * 0.2),
                (p1.y() * 0.1 + p2.y() * 0.3 + p3.y() * 0.4 + p4.y() * 0.2)
            )
            
    def finish_stroke(self):
        """Serbest çizimi tamamla"""
        if self.is_drawing and self.current_stroke and len(self.current_stroke['points']) > 1:
            # Son buffer noktalarını da ekle
            while len(self.smoothing_buffer) > 1:
                self.smoothing_buffer.pop(0)
                smoothed_pos = self._calculate_smoothed_point()
                if smoothed_pos and len(self.current_stroke['points']) > 0:
                    last_pos = self.current_stroke['points'][-1]
                    distance = math.sqrt((smoothed_pos.x() - last_pos.x()) ** 2 + (smoothed_pos.y() - last_pos.y()) ** 2)
                    if distance >= 2.0:  # Son noktalar için threshold artırıldı
                        self.current_stroke['points'].append(smoothed_pos)
                        self.current_stroke['pressures'].append(1.0)
            
            stroke_data = self.current_stroke.copy()
            self.current_stroke = None
            self.is_drawing = False
            self.smoothing_buffer = []
            return stroke_data
        else:
            self.current_stroke = None
            self.is_drawing = False
            self.smoothing_buffer = []
            return None
            
    def cancel_stroke(self):
        """Aktif çizimi iptal et"""
        self.current_stroke = None
        self.is_drawing = False
        self.smoothing_buffer = []
        
    def draw_stroke(self, painter, stroke_data):
        """Tamamlanmış serbest çizimi çiz"""
        if stroke_data['type'] != 'freehand':
            return
            
        points = stroke_data['points']
        pressures = stroke_data['pressures']
        
        if len(points) < 2:
            return
            
        # Serbest çizim için renk ve kalınlık
        color = stroke_data.get('color', Qt.GlobalColor.black)
        width = stroke_data.get('width', 2)
        line_style = stroke_data.get('line_style', Qt.PenStyle.SolidLine)
        
        # Color string ise QColor'a çevir
        from PyQt6.QtGui import QColor
        if isinstance(color, str):
            color = QColor(color)
        if isinstance(line_style, int):
            line_style = Qt.PenStyle(line_style)
            
        # Anti-aliasing'i etkinleştir
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        
        pen = QPen(color, width, line_style)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        
        # Gelişmiş Catmull-Rom spline curve
        if len(points) >= 2:
            path = QPainterPath()
            
            # Helper fonksiyonu kullan
            first_point = ensure_qpointf(points[0])
            path.moveTo(first_point)
            
            if len(points) == 2:
                second_point = ensure_qpointf(points[1])
                path.lineTo(second_point)
            elif len(points) == 3:
                p1 = ensure_qpointf(points[1])
                p2 = ensure_qpointf(points[2])
                path.quadTo(p1, p2)
            else:
                # Daha güçlü spline smoothing
                for i in range(1, len(points) - 2):
                    # Helper fonksiyonu kullan
                    p0 = ensure_qpointf(points[i - 1] if i > 0 else points[i])
                    p1 = ensure_qpointf(points[i])
                    p2 = ensure_qpointf(points[i + 1])
                    p3 = ensure_qpointf(points[i + 2] if i + 2 < len(points) else points[i + 1])
                    
                    # Daha güçlü control point hesaplama
                    cp1_x = p1.x() + (p2.x() - p0.x()) / 4.0  # Önceki iyi versiyon
                    cp1_y = p1.y() + (p2.y() - p0.y()) / 4.0
                    cp2_x = p2.x() - (p3.x() - p1.x()) / 4.0
                    cp2_y = p2.y() - (p3.y() - p1.y()) / 4.0
                    
                    path.cubicTo(
                        QPointF(cp1_x, cp1_y),
                        QPointF(cp2_x, cp2_y),
                        p2
                    )
                
                # Helper fonksiyonu kullan
                last_point = ensure_qpointf(points[-1])
                path.lineTo(last_point)
            
            painter.setPen(pen)
            painter.drawPath(path)
    
    def set_color(self, color):
        """Aktif rengi ayarla"""
        self.current_color = color
            
    def draw_current_stroke(self, painter):
        """Aktif olarak çizilen serbest çizimi çiz"""
        if not self.is_drawing or not self.current_stroke or len(self.current_stroke['points']) < 2:
            return
            
        points = self.current_stroke['points']
        
        # Anti-aliasing'i etkinleştir
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        
        pen = QPen(self.current_color, self.current_width, self.line_style)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        
        # Aktif çizim için de smooth path kullan
        path = QPainterPath()
        path.moveTo(points[0])
        
        if len(points) == 2:
            path.lineTo(points[1])
        elif len(points) > 2:
            # Aktif çizimde de smooth curves kullan
            for i in range(1, len(points)):
                if i == len(points) - 1:
                    path.lineTo(points[i])
                else:
                    # Basit smoothing için quadratic curve kullan
                    mid_x = (points[i].x() + points[i + 1].x()) / 2
                    mid_y = (points[i].y() + points[i + 1].y()) / 2
                    path.quadTo(points[i], QPointF(mid_x, mid_y))
        
        painter.setPen(pen)
        painter.drawPath(path)
    
    def set_width(self, width):
        """Aktif çizgi kalınlığını ayarla"""
        self.current_width = width
        
    def set_line_style(self, style):
        """Çizgi stilini ayarla"""
        self.line_style = style 