from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QPen, QBrush
from PyQt6.QtCore import Qt
from grid_snap_utils import GridSnapUtils
from shadow_renderer import ShadowRenderer

class CircleTool:
    def __init__(self):
        self.is_drawing = False
        self.start_point = None  # İlk tıklanan nokta (dikdörtgen gibi)
        self.current_point = None
        self.line_color = Qt.GlobalColor.black
        self.line_width = 2
        self.fill_color = None  # None = doldurma yok
        self.fill_opacity = 1.0  # 0.0-1.0 arası şeffaflık
        self.is_filled = False  # Fill aktif mi
        self.line_style = Qt.PenStyle.SolidLine  # Çizgi stili
        self.background_settings = None  # Snap için arka plan ayarları
        
        # Gölge özellikleri
        self.has_shadow = False
        self.shadow_color = Qt.GlobalColor.black
        self.shadow_offset_x = 5
        self.shadow_offset_y = 5
        self.shadow_blur = 10
        self.shadow_size = 0
        self.shadow_opacity = 0.7
        self.inner_shadow = False
        self.shadow_quality = 'medium'
        self.shift_constrain = False
        
    def start_stroke(self, pos, pressure=1.0):
        """Yeni bir çember çizimi başlat"""
        self.is_drawing = True
        
        # Snap to grid uygulaması: grid açık veya Shift basılıysa
        if self.background_settings:
            force_snap = getattr(self, 'shift_constrain', False) and not self.background_settings.get('snap_to_grid', False)
            if self.background_settings.get('snap_to_grid', False) or force_snap:
                pos = GridSnapUtils.snap_point_to_grid_precise(pos, self.background_settings, force_snap=True)
            
        self.start_point = pos
        self.current_point = pos
        
    def add_point(self, pos, pressure=1.0):
        """Çemberin yarıçapını güncelle"""
        if self.is_drawing:
            # Snap to grid uygulaması: grid açık veya Shift basılıysa
            if self.background_settings:
                force_snap = getattr(self, 'shift_constrain', False) and not self.background_settings.get('snap_to_grid', False)
                if self.background_settings.get('snap_to_grid', False) or force_snap:
                    pos = GridSnapUtils.snap_point_to_grid_precise(pos, self.background_settings, force_snap=True)
                
            self.current_point = pos
            
    def finish_stroke(self):
        """Çemberi tamamla"""
        if self.is_drawing and self.start_point and self.current_point:
            # Bounding rectangle oluştur (dikdörtgen gibi)
            rect = QRectF(self.start_point, self.current_point).normalized()
            
            # Çok küçük çemberleri engelle
            if rect.width() < 5 or rect.height() < 5:
                self.cancel_stroke()
                return None
            
            # Merkez ve yarıçapı hesapla (elips için en/boy oranını koruyacağız)
            center_x = rect.center().x()
            center_y = rect.center().y()
            radius_x = rect.width() / 2
            radius_y = rect.height() / 2
            # Daire için ortalama yarıçap kullan
            radius = (radius_x + radius_y) / 2
                
            stroke_data = {
                'type': 'circle',
                'center': (center_x, center_y),
                'radius': radius,
                'color': self.line_color,
                'line_width': self.line_width,
                'line_style': self.line_style,
                'fill': self.is_filled,
                'fill_color': self.fill_color if self.is_filled and self.fill_color else None,
                'fill_opacity': self.fill_opacity,
                'is_filled': self.is_filled,  # Geriye uyumluluk için
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
        """Tamamlanmış çemberi çiz"""
        if stroke_data['type'] != 'circle':
            return

        center = QPointF(stroke_data['center'][0], stroke_data['center'][1])
        radius = stroke_data['radius']

        # Çember için bounding rectangle ve ShadowRenderer için nokta listesi
        rect = QRectF(center.x() - radius, center.y() - radius,
                      radius * 2, radius * 2)
        points = [
            QPointF(center.x(), center.y() - radius),  # Üst
            QPointF(center.x(), center.y() + radius),  # Alt
            QPointF(center.x() - radius, center.y()),  # Sol
            QPointF(center.x() + radius, center.y())   # Sağ
        ]

        painter.save()

        # 1. Dış gölge çiz (varsa)
        if stroke_data.get('has_shadow', False) and not stroke_data.get('inner_shadow', False):
            ShadowRenderer.draw_shape_shadow(painter, 'circle', points, stroke_data)

        # 2. Ana çemberi çiz (dolgu + çerçeve)
        self._draw_circle_shape(painter, stroke_data, rect)

        # 3. İç gölge çiz (varsa)
        if stroke_data.get('has_shadow', False) and stroke_data.get('inner_shadow', False):
            ShadowRenderer.draw_shape_shadow(painter, 'circle', points, stroke_data)

        painter.restore()
        
    def _draw_circle_shape(self, painter, stroke_data, rect):
        """Ana çember şeklini çiz"""
        from PyQt6.QtGui import QColor
        
        painter.save()
        
        # 1. Dolgu çiz (varsa)
        if stroke_data.get('fill_color'):
            fill_brush = QBrush(stroke_data['fill_color'])
            painter.setBrush(fill_brush)
            painter.setOpacity(stroke_data.get('fill_opacity', 1.0))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(rect)
            painter.setOpacity(1.0)

        # 2. Çerçeve çiz
        line_style = stroke_data.get('line_style', Qt.PenStyle.SolidLine)
        # Geriye uyumluluk için hem 'color' hem 'line_color' kontrol et
        color = stroke_data.get('color', stroke_data.get('line_color', Qt.GlobalColor.black))
        width = stroke_data.get('line_width', stroke_data.get('width', 2))
        
        # Color string ise QColor'a çevir
        if isinstance(color, str):
            color = QColor(color)
        if isinstance(line_style, int):
            line_style = Qt.PenStyle(line_style)
            
        pen = QPen(color, width, line_style,
                   Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(rect)
        
        painter.restore()
        
    def draw_current_stroke(self, painter):
        """Aktif olarak çizilen çemberi çiz"""
        if not self.is_drawing or not self.start_point or not self.current_point:
            return
            
        # Bounding rectangle oluştur (dikdörtgen gibi)
        rect = QRectF(self.start_point, self.current_point).normalized()
        
        # Daire için ortalama yarıçap hesapla
        radius_x = rect.width() / 2
        radius_y = rect.height() / 2
        avg_radius = (radius_x + radius_y) / 2
        
        # Merkez noktası
        center = rect.center()
        
        # Daire için kare bounding rect oluştur
        circle_rect = QRectF(center.x() - avg_radius, center.y() - avg_radius,
                           avg_radius * 2, avg_radius * 2)
        
        painter.save()

        # Aktif dış gölge çiz (varsa)
        if self.has_shadow and not self.inner_shadow:
            stroke_data = {
                'has_shadow': True,
                'shadow_color': self.shadow_color,
                'shadow_blur': self.shadow_blur,
                'shadow_size': self.shadow_size,
                'shadow_opacity': self.shadow_opacity * 0.3,
                'shadow_offset_x': self.shadow_offset_x,
                'shadow_offset_y': self.shadow_offset_y,
                'inner_shadow': False,
                'shadow_quality': self.shadow_quality
            }
            ShadowRenderer.draw_shape_shadow(painter, 'circle', circle_rect, stroke_data)

        # Aktif dolgu çiz (varsa)
        if self.is_filled and self.fill_color:
            fill_brush = QBrush(self.fill_color)
            painter.setBrush(fill_brush)
            painter.setOpacity(self.fill_opacity * 0.5)  # Daha şeffaf
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(circle_rect)
            painter.setOpacity(1.0)

        # Aktif iç gölge çiz (varsa)
        if self.has_shadow and self.inner_shadow:
            stroke_data = {
                'has_shadow': True,
                'shadow_color': self.shadow_color,
                'shadow_blur': self.shadow_blur,
                'shadow_size': self.shadow_size,
                'shadow_opacity': self.shadow_opacity * 0.2,
                'shadow_offset_x': self.shadow_offset_x,
                'shadow_offset_y': self.shadow_offset_y,
                'inner_shadow': True,
                'shadow_quality': self.shadow_quality
            }
            ShadowRenderer.draw_shape_shadow(painter, 'circle', circle_rect, stroke_data)

        # Aktif çerçeve çiz
        pen = QPen(self.line_color, self.line_width, self.line_style,
                   Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setOpacity(0.7)
        painter.drawEllipse(circle_rect)
        
        # Yardımcı çizgiler - bounding rectangle
        painter.setOpacity(0.3)
        painter.setPen(QPen(self.line_color, 1, Qt.PenStyle.DotLine))
        painter.drawRect(rect)
        
        painter.restore() 