from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QPainter, QPen, QPainterPath
from PyQt6.QtCore import Qt
from grid_snap_utils import GridSnapUtils
from shadow_renderer import ShadowRenderer

class LineTool:
    def __init__(self):
        self.is_drawing = False
        self.start_point = None
        self.current_point = None
        self.line_color = Qt.GlobalColor.black
        self.line_width = 2
        self.line_style = Qt.PenStyle.SolidLine
        self.background_settings = None  # Snap için arka plan ayarları

        # Gölge ayarları
        self.has_shadow = False
        self.shadow_color = Qt.GlobalColor.black
        self.shadow_offset_x = 5
        self.shadow_offset_y = 5
        self.shadow_blur = 10
        self.shadow_size = 0
        self.shadow_opacity = 0.7
        self.inner_shadow = False
        self.shadow_quality = "medium"
        
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
                'style': self.line_style,
                'has_shadow': self.has_shadow,
                'shadow_color': self.shadow_color,
                'shadow_offset_x': self.shadow_offset_x,
                'shadow_offset_y': self.shadow_offset_y,
                'shadow_blur': self.shadow_blur,
                'shadow_size': self.shadow_size,
                'shadow_opacity': self.shadow_opacity,
                'inner_shadow': self.inner_shadow,
                'shadow_quality': self.shadow_quality,
                'cap_style': Qt.PenCapStyle.RoundCap,
                'join_style': Qt.PenJoinStyle.RoundJoin
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
        path = QPainterPath(start_point)
        path.lineTo(end_point)
        ShadowRenderer.draw_shape_shadow(painter, 'path', path, stroke_data)
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

        preview_data = {
            'type': 'line',
            'width': self.line_width,
            'has_shadow': self.has_shadow,
            'shadow_color': self.shadow_color,
            'shadow_offset_x': self.shadow_offset_x,
            'shadow_offset_y': self.shadow_offset_y,
            'shadow_blur': self.shadow_blur,
            'shadow_size': self.shadow_size,
            'shadow_opacity': self.shadow_opacity,
            'inner_shadow': self.inner_shadow,
            'shadow_quality': self.shadow_quality,
            'cap_style': Qt.PenCapStyle.RoundCap,
            'join_style': Qt.PenJoinStyle.RoundJoin
        }

        path = QPainterPath(self.start_point)
        path.lineTo(self.current_point)
        ShadowRenderer.draw_shape_shadow(painter, 'path', path, preview_data)

        painter.drawLine(self.start_point, self.current_point)
        painter.setOpacity(1.0)

    def set_shadow_enabled(self, enabled):
        """Gölge durumunu ayarla"""
        self.has_shadow = enabled

    def set_shadow_color(self, color):
        """Gölge rengini ayarla"""
        self.shadow_color = color

    def set_shadow_offset(self, x, y):
        """Gölge offsetini ayarla"""
        self.shadow_offset_x = x
        self.shadow_offset_y = y

    def set_shadow_blur(self, blur):
        """Gölge bulanıklığını ayarla"""
        self.shadow_blur = max(0, blur)

    def set_shadow_size(self, size):
        """Gölge boyutunu ayarla"""
        self.shadow_size = max(0, size)

    def set_shadow_opacity(self, opacity):
        """Gölge şeffaflığını ayarla"""
        self.shadow_opacity = max(0.0, min(1.0, opacity))

    def set_inner_shadow(self, inner):
        """İç/dış gölge durumunu ayarla"""
        self.inner_shadow = inner

    def set_shadow_quality(self, quality):
        """Gölge kalitesini ayarla"""
        self.shadow_quality = quality
