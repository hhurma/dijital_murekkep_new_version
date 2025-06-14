from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QPainter, QPen
from PyQt6.QtCore import Qt
from grid_snap_utils import GridSnapUtils

class LineTool:
    def __init__(self):
        self.is_drawing = False
        self.start_point = None
        self.current_point = None
        self.line_color = Qt.GlobalColor.black
        self.line_width = 2
        self.line_style = Qt.PenStyle.SolidLine
        self.background_settings = None  # Snap için arka plan ayarları
        
    def start_stroke(self, pos, pressure=1.0):
        """Yeni bir çizgi çizimi başlat"""
        self.is_drawing = True
        
        # Snap to grid uygulaması
        if self.background_settings and self.background_settings.get('snap_to_grid', False):
            pos = GridSnapUtils.snap_point_to_grid(pos, self.background_settings)
            
        self.start_point = pos
        self.current_point = pos
        
    def add_point(self, pos, pressure=1.0):
        """Çizginin bitiş noktasını güncelle"""
        if self.is_drawing:
            # Snap to grid uygulaması
            if self.background_settings and self.background_settings.get('snap_to_grid', False):
                pos = GridSnapUtils.snap_point_to_grid(pos, self.background_settings)
                
            self.current_point = pos
            
    def finish_stroke(self):
        """Çizgiyi tamamla"""
        if self.is_drawing and self.start_point and self.current_point:
            # Çok kısa çizgileri engelle
            if (self.current_point - self.start_point).manhattanLength() < 5:
                self.cancel_stroke()
                return None
                
            stroke_data = {
                'type': 'line',
                'start_point': (self.start_point.x(), self.start_point.y()),
                'end_point': (self.current_point.x(), self.current_point.y()),
                'color': self.line_color,
                'width': self.line_width,
                'style': self.line_style
            }
            
            self.cancel_stroke()
            return stroke_data
        
        self.cancel_stroke()
        return None
        
    def cancel_stroke(self):
        """Aktif çizimi iptal et"""
        self.is_drawing = False
        self.start_point = None
        self.current_point = None
        
    def set_color(self, color):
        """Çizgi rengini ayarla"""
        self.line_color = color
        
    def set_width(self, width):
        """Çizgi kalınlığını ayarla"""
        self.line_width = max(1, width)
        
    def set_line_style(self, style):
        """Çizgi stilini ayarla"""
        self.line_style = style
        
    def set_background_settings(self, settings):
        """Arka plan ayarlarını ayarla (snap için)"""
        self.background_settings = settings
        
    def draw_stroke(self, painter, stroke_data):
        """Tamamlanmış çizgiyi çiz"""
        if stroke_data['type'] != 'line':
            return
            
        start_point = QPointF(stroke_data['start_point'][0], stroke_data['start_point'][1])
        end_point = QPointF(stroke_data['end_point'][0], stroke_data['end_point'][1])
        
        line_style = stroke_data.get('style', Qt.PenStyle.SolidLine)
        color = stroke_data['color']
        width = stroke_data['width']
        
        # Color string ise QColor'a çevir
        from PyQt6.QtGui import QColor
        if isinstance(color, str):
            color = QColor(color)
        if isinstance(line_style, int):
            line_style = Qt.PenStyle(line_style)
            
        pen = QPen(color, width, line_style,
                   Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(start_point, end_point)
        
    def draw_current_stroke(self, painter):
        """Aktif olarak çizilen çizgiyi çiz"""
        if not self.is_drawing or not self.start_point or not self.current_point:
            return
            
        # Aktif çizim için yarı şeffaf renk
        color = self.line_color
        pen = QPen(color, self.line_width, self.line_style,
                   Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setOpacity(0.7)
        painter.drawLine(self.start_point, self.current_point)
        painter.setOpacity(1.0) 