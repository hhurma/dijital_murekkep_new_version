from PyQt6.QtCore import QPointF, QRectF, QSize
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QPainterPath, QPolygonF
from PyQt6.QtCore import Qt
from grid_snap_utils import GridSnapUtils
from shadow_renderer import ShadowRenderer

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
        
        # Yuvarlak kenar özellikleri
        self.corner_radius = 0  # 0-50 px arası
        
        # Gölge özellikleri
        self.has_shadow = False
        self.shadow_color = Qt.GlobalColor.black
        self.shadow_offset_x = 5
        self.shadow_offset_y = 5
        self.shadow_blur = 10
        self.shadow_size = 0
        self.shadow_opacity = 0.7
        self.inner_shadow = False  # False=dış gölge, True=iç gölge
        self.shadow_quality = "medium"
        
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
                'is_filled': self.is_filled,  # Geriye uyumluluk için
                
                # Yuvarlak kenar ve gölge özellikleri
                'corner_radius': self.corner_radius,
                'has_shadow': self.has_shadow,
                'shadow_color': self.shadow_color,
                'shadow_offset_x': self.shadow_offset_x,
                'shadow_offset_y': self.shadow_offset_y,
                'shadow_blur': self.shadow_blur,
                'shadow_size': self.shadow_size,
                'shadow_opacity': self.shadow_opacity,
                'inner_shadow': self.inner_shadow,
                'shadow_quality': self.shadow_quality
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
        
    def set_corner_radius(self, radius):
        """Yuvarlak kenar yarıçapını ayarla (0-50)"""
        self.corner_radius = max(0, min(50, radius))
        
    def set_shadow_enabled(self, enabled):
        """Gölge durumunu ayarla"""
        self.has_shadow = enabled
        
    def set_shadow_color(self, color):
        """Gölge rengini ayarla"""
        self.shadow_color = color
        
    def set_shadow_offset(self, x, y):
        """Gölge ofsetini ayarla"""
        self.shadow_offset_x = x
        self.shadow_offset_y = y
        
    def set_shadow_blur(self, blur):
        """Gölge blur'unu ayarla"""
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
        
        # 1. Dış gölge çiz
        if stroke_data.get('has_shadow', False) and not stroke_data.get('inner_shadow', False):
            ShadowRenderer.draw_shape_shadow(painter, 'rectangle', points, stroke_data)
        
        # 2. Ana dikdörtgeni çiz (dolgu + çerçeve)
        self._draw_rectangle_shape(painter, stroke_data, points)
        
        # 3. İç gölge çiz (dolgudan sonra)
        if stroke_data.get('has_shadow', False) and stroke_data.get('inner_shadow', False):
            ShadowRenderer.draw_shape_shadow(painter, 'rectangle', points, stroke_data)
        
        painter.restore()
        
    def _draw_rectangle_shape(self, painter, stroke_data, points):
        """Ana dikdörtgen şeklini çiz"""
        painter.save()
        
        # Create a QPainterPath from the points
        path = QPainterPath()
        path.moveTo(points[0])
        for i in range(1, len(points)):
            path.lineTo(points[i])
        path.closeSubpath()

        # 1. Dolgu çiz (varsa)
        if stroke_data.get('fill_color'):
            fill_brush = QBrush(stroke_data['fill_color'])
            painter.setBrush(fill_brush)
            painter.setOpacity(stroke_data.get('fill_opacity', 1.0))
            painter.setPen(Qt.PenStyle.NoPen)
            
            # Draw the filled polygon. Rounded corners are ignored for rotated shapes.
            painter.drawPath(path)
            painter.setOpacity(1.0)
        
        # 2. Çerçeve çiz
        line_style = stroke_data.get('line_style', Qt.PenStyle.SolidLine)
        color = stroke_data.get('color', stroke_data.get('line_color', Qt.GlobalColor.black))
        width = stroke_data.get('line_width', stroke_data.get('width', 2))
        
        if isinstance(color, str):
            color = QColor(color)
        if isinstance(line_style, int):
            line_style = Qt.PenStyle(line_style)
            
        pen = QPen(color, width, line_style,
                   Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        # Draw the outline of the polygon. Rounded corners are ignored for rotated shapes.
        painter.drawPath(path)
        
        painter.restore()
        
    def draw_current_stroke(self, painter):
        """Aktif olarak çizilen dikdörtgeni çiz"""
        if not self.is_drawing or not self.start_point or not self.current_point:
            return
            
        rect = QRectF(self.start_point, self.current_point).normalized()
        
        painter.save()
        
        # Aktif dış gölge çiz
        if self.has_shadow and not self.inner_shadow:
            stroke_data = {
                'has_shadow': True,
                'shadow_color': self.shadow_color,
                'shadow_blur': self.shadow_blur,
                'shadow_size': self.shadow_size,
                'shadow_opacity': self.shadow_opacity * 0.3,  # Daha şeffaf
                'shadow_offset_x': self.shadow_offset_x,
                'shadow_offset_y': self.shadow_offset_y,
                'inner_shadow': False,
                'shadow_quality': self.shadow_quality
            }
            ShadowRenderer.draw_shape_shadow(painter, 'rectangle', rect, stroke_data)
        
        # Aktif dolgu çiz (varsa)
        if self.is_filled and self.fill_color:
            fill_brush = QBrush(self.fill_color)
            painter.setBrush(fill_brush)
            painter.setOpacity(self.fill_opacity * 0.5)  # Daha şeffaf
            painter.setPen(Qt.PenStyle.NoPen)
            
            if self.corner_radius > 0:
                painter.drawRoundedRect(rect, self.corner_radius, self.corner_radius)
            else:
                painter.drawRect(rect)
            painter.setOpacity(1.0)
        
        # Aktif iç gölge çiz (dolgudan sonra)
        if self.has_shadow and self.inner_shadow:
            stroke_data = {
                'has_shadow': True,
                'shadow_color': self.shadow_color,
                'shadow_blur': self.shadow_blur,
                'shadow_size': self.shadow_size,
                'shadow_opacity': self.shadow_opacity * 0.2,  # Daha da şeffaf
                'shadow_offset_x': self.shadow_offset_x,
                'shadow_offset_y': self.shadow_offset_y,
                'inner_shadow': True,
                'shadow_quality': self.shadow_quality
            }
            ShadowRenderer.draw_shape_shadow(painter, 'rectangle', rect, stroke_data)
        
        # Aktif çerçeve çiz
        pen = QPen(self.line_color, self.line_width, self.line_style,
                   Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setOpacity(0.7)
        
        if self.corner_radius > 0:
            painter.drawRoundedRect(rect, self.corner_radius, self.corner_radius)
        else:
            painter.drawRect(rect)
        
        painter.restore()
