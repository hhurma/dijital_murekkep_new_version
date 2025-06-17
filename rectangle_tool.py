from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QPainter, QPen, QBrush
from PyQt6.QtCore import Qt
from grid_snap_utils import GridSnapUtils

class RectangleTool:
    def __init__(self):
        self.is_drawing = False
        self.start_point = None
        self.current_point = None
        self.line_color = Qt.GlobalColor.black
        self.line_width = 2
        self.fill_color = None  # None = doldurma yok
        self.fill_opacity = 1.0  # 0.0-1.0 arası şeffaflık
        self.is_filled = False  # Fill aktif mi
        self.line_style = Qt.PenStyle.SolidLine  # Çizgi stili
        self.background_settings = None  # Snap için arka plan ayarları
        
    def start_stroke(self, pos, pressure=1.0):
        """Yeni bir dikdörtgen çizimi başlat"""
        self.is_drawing = True
        
        # Snap to grid uygulaması
        if self.background_settings and self.background_settings.get('snap_to_grid', False):
            pos = GridSnapUtils.snap_point_to_grid(pos, self.background_settings)
            
        self.start_point = pos
        self.current_point = pos
        
    def add_point(self, pos, pressure=1.0):
        """Dikdörtgenin karşı köşesini güncelle"""
        if self.is_drawing:
            # Snap to grid uygulaması
            if self.background_settings and self.background_settings.get('snap_to_grid', False):
                pos = GridSnapUtils.snap_point_to_grid(pos, self.background_settings)
                
            self.current_point = pos
            
    def finish_stroke(self):
        """Dikdörtgeni tamamla"""
        if self.is_drawing and self.start_point and self.current_point:
            # Çok küçük dikdörtgenleri engelle
            rect = QRectF(self.start_point, self.current_point).normalized()
            if rect.width() < 5 or rect.height() < 5:
                self.cancel_stroke()
                return None
                
            stroke_data = {
                'type': 'rectangle',
                'corners': [
                    (rect.topLeft().x(), rect.topLeft().y()),      # Sol üst
                    (rect.topRight().x(), rect.topRight().y()),   # Sağ üst
                    (rect.bottomRight().x(), rect.bottomRight().y()), # Sağ alt
                    (rect.bottomLeft().x(), rect.bottomLeft().y())     # Sol alt
                ],
                'color': self.line_color,
                'line_width': self.line_width,
                'line_style': self.line_style,
                'fill': self.is_filled,
                'fill_color': self.fill_color if self.is_filled and self.fill_color else None,
                'fill_opacity': self.fill_opacity,
                'is_filled': self.is_filled  # Geriye uyumluluk için
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
        
    def set_line_color(self, color):
        """Çizgi rengini ayarla"""
        self.line_color = color
        
    def set_line_width(self, width):
        """Çizgi kalınlığını ayarla"""
        self.line_width = max(1, width)
        
    def set_fill_color(self, color):
        """Dolgu rengini ayarla (None = doldurma yok)"""
        self.fill_color = color
        
    def set_fill_opacity(self, opacity):
        """Dolgu şeffaflığını ayarla (0.0-1.0)"""
        self.fill_opacity = max(0.0, min(1.0, opacity))
        
    def set_filled(self, filled):
        """Fill durumunu ayarla"""
        self.is_filled = filled
        
    def set_line_style(self, style):
        """Çizgi stilini ayarla"""
        self.line_style = style
        
    def set_background_settings(self, settings):
        """Arka plan ayarlarını ayarla (snap için)"""
        self.background_settings = settings
        
    def draw_stroke(self, painter, stroke_data):
        """Tamamlanmış dikdörtgeni çiz"""
        if stroke_data['type'] != 'rectangle':
            return
            
        # Geriye uyumluluk için eski format kontrolü
        if 'corners' in stroke_data:
            corners = stroke_data['corners']
            points = [QPointF(corner[0], corner[1]) for corner in corners]
        else:
            # Eski format - top_left ve bottom_right
            top_left = QPointF(stroke_data['top_left'][0], stroke_data['top_left'][1])
            bottom_right = QPointF(stroke_data['bottom_right'][0], stroke_data['bottom_right'][1])
            rect = QRectF(top_left, bottom_right).normalized()
            points = [rect.topLeft(), rect.topRight(), rect.bottomRight(), rect.bottomLeft()]
        
        painter.save()
        
        # Dolgu çiz (varsa)
        if stroke_data.get('fill_color'):
            from PyQt6.QtGui import QPolygonF
            polygon = QPolygonF(points)
            fill_brush = QBrush(stroke_data['fill_color'])
            painter.setBrush(fill_brush)
            painter.setOpacity(stroke_data.get('fill_opacity', 1.0))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPolygon(polygon)
            painter.setOpacity(1.0)
        
        # Çerçeve çiz
        line_style = stroke_data.get('line_style', Qt.PenStyle.SolidLine)
        # Geriye uyumluluk için hem 'color' hem 'line_color' kontrol et
        color = stroke_data.get('color', stroke_data.get('line_color', Qt.GlobalColor.black))
        width = stroke_data.get('line_width', stroke_data.get('width', 2))
        
        # Color string ise QColor'a çevir
        from PyQt6.QtGui import QColor
        if isinstance(color, str):
            color = QColor(color)
        if isinstance(line_style, int):
            line_style = Qt.PenStyle(line_style)
            
        pen = QPen(color, width, line_style,
                   Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        # Köşeleri birleştirerek dikdörtgeni çiz
        for i in range(len(points)):
            start_point = points[i]
            end_point = points[(i + 1) % len(points)]
            painter.drawLine(start_point, end_point)
        
        painter.restore()
        
    def draw_current_stroke(self, painter):
        """Aktif olarak çizilen dikdörtgeni çiz"""
        if not self.is_drawing or not self.start_point or not self.current_point:
            return
            
        rect = QRectF(self.start_point, self.current_point).normalized()
        
        painter.save()
        
        # Aktif dolgu çiz (varsa)
        if self.is_filled and self.fill_color:
            fill_brush = QBrush(self.fill_color)
            painter.setBrush(fill_brush)
            painter.setOpacity(self.fill_opacity * 0.5)  # Daha şeffaf
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(rect)
            painter.setOpacity(1.0)
        
        # Aktif çerçeve çiz
        pen = QPen(self.line_color, self.line_width, self.line_style,
                   Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setOpacity(0.7)
        painter.drawRect(rect)
        
        painter.restore() 