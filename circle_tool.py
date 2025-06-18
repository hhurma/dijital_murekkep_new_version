from PyQt6.QtCore import QPointF, QRectF, QSize
from PyQt6.QtGui import QPainter, QPen, QBrush  
from PyQt6.QtCore import Qt
import math
from grid_snap_utils import GridSnapUtils

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
        
    def start_stroke(self, pos, pressure=1.0):
        """Yeni bir çember çizimi başlat"""
        self.is_drawing = True
        
        # Snap to grid uygulaması
        if self.background_settings and self.background_settings.get('snap_to_grid', False):
            pos = GridSnapUtils.snap_point_to_grid(pos, self.background_settings)
            
        self.start_point = pos
        self.current_point = pos
        
    def add_point(self, pos, pressure=1.0):
        """Çemberin yarıçapını güncelle"""
        if self.is_drawing:
            # Snap to grid uygulaması
            if self.background_settings and self.background_settings.get('snap_to_grid', False):
                pos = GridSnapUtils.snap_point_to_grid(pos, self.background_settings)
                
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
        
        # Çember için bounding rectangle
        rect = QRectF(center.x() - radius, center.y() - radius, 
                     radius * 2, radius * 2)
        
        painter.save()
        
        # 1. Dış gölge çiz (varsa)
        if stroke_data.get('has_shadow', False) and not stroke_data.get('inner_shadow', False):
            self._draw_circle_shadow(painter, stroke_data, rect)
        
        # 2. Ana çemberi çiz (dolgu + iç gölge + çerçeve)
        self._draw_circle_shape(painter, stroke_data, rect)
        
        painter.restore()
        
    def _draw_circle_shadow(self, painter, stroke_data, rect):
        """Çember gölgesi çiz"""
        from PyQt6.QtGui import QColor, QPixmap, QPainter
        from PyQt6.QtWidgets import QGraphicsScene, QGraphicsEllipseItem, QGraphicsBlurEffect
        
        shadow_color = stroke_data.get('shadow_color', Qt.GlobalColor.black)
        shadow_blur = stroke_data.get('shadow_blur', 10)
        shadow_size = stroke_data.get('shadow_size', 0)
        shadow_opacity = stroke_data.get('shadow_opacity', 0.7)
        shadow_offset_x = stroke_data.get('shadow_offset_x', 5)
        shadow_offset_y = stroke_data.get('shadow_offset_y', 5)
        inner_shadow = stroke_data.get('inner_shadow', False)
        shadow_quality = stroke_data.get('shadow_quality', 'medium')
        
        # Gölge rengini tam opak yap
        if isinstance(shadow_color, str):
            shadow_color = QColor(shadow_color)
        elif hasattr(shadow_color, 'name'):
            shadow_color = QColor(shadow_color)
        
        # Shadow opacity 1.0 ise color alpha'sını override et
        if shadow_opacity >= 1.0:
            shadow_color.setAlphaF(1.0)
        
        # Blur yoksa basit gölge çiz
        if shadow_blur <= 0:
            self._draw_simple_circle_shadow(painter, stroke_data, rect)
            return
        
        # Blur radius ayarla (kaliteye göre)
        blur_radius = self._get_adjusted_blur_radius(shadow_blur, shadow_quality)
        
        # Gölge pixmap boyutunu hesapla
        margin = max(25, blur_radius * 2, shadow_size * 2)
        shadow_pixmap_size = QSize(
            int(rect.width() + margin * 2 + abs(shadow_offset_x)),
            int(rect.height() + margin * 2 + abs(shadow_offset_y))
        )
        
        # Gölge pixmap oluştur
        shadow_pixmap = QPixmap(shadow_pixmap_size)
        shadow_pixmap.fill(Qt.GlobalColor.transparent)
        
        shadow_painter = QPainter(shadow_pixmap)
        shadow_painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Gölge şeklini çiz (pixmap merkezinde)
        shape_rect = QRectF(
            margin,
            margin,
            rect.width() + shadow_size * 2,
            rect.height() + shadow_size * 2
        )
        
        shadow_painter.setBrush(QBrush(shadow_color))
        shadow_painter.setPen(Qt.PenStyle.NoPen)
        shadow_painter.drawEllipse(shape_rect)
        shadow_painter.end()
        
        # İç gölge mi dış gölge mi kontrol et
        if inner_shadow:

            # İç gölge için özel işlem
            inner_shadow_pixmap = self._create_inner_shadow_pixmap(shadow_pixmap, rect, margin, blur_radius, shadow_color, shadow_offset_x, shadow_offset_y, shadow_size)
            
            # Ana painter'e iç gölgeyi çiz
            painter.save()
            painter.setOpacity(shadow_opacity)
            
            # İç gölge için clip path kullan
            from PyQt6.QtGui import QPainterPath
            clip_path = QPainterPath()
            clip_path.addEllipse(rect)
            painter.setClipPath(clip_path)
            
            # İç gölge pixmap'i ana şeklin pozisyonuna göre çiz
            shadow_pos_x = int(rect.x())
            shadow_pos_y = int(rect.y())
            painter.drawPixmap(shadow_pos_x, shadow_pos_y, inner_shadow_pixmap)
            painter.restore()
        else:
            # Dış gölge için blur efekti uygula
            if blur_radius > 0:
                blurred_shadow = self._apply_blur_to_pixmap(shadow_pixmap, blur_radius)
            else:
                blurred_shadow = shadow_pixmap
            
            # Ana painter'e dış gölgeyi çiz
            painter.save()
            painter.setOpacity(shadow_opacity)
            
            shadow_pos_x = int(rect.x() + shadow_offset_x - margin)
            shadow_pos_y = int(rect.y() + shadow_offset_y - margin)
            
            painter.drawPixmap(shadow_pos_x, shadow_pos_y, blurred_shadow)
            painter.restore()
        
    def _draw_simple_circle_shadow(self, painter, stroke_data, rect):
        """Blur olmadan basit çember gölgesi çiz"""
        shadow_color = stroke_data.get('shadow_color', Qt.GlobalColor.black)
        shadow_size = stroke_data.get('shadow_size', 0)
        shadow_opacity = stroke_data.get('shadow_opacity', 0.7)
        shadow_offset_x = stroke_data.get('shadow_offset_x', 5)
        shadow_offset_y = stroke_data.get('shadow_offset_y', 5)
        inner_shadow = stroke_data.get('inner_shadow', False)
        
        painter.save()
        
        if inner_shadow:
            # İç gölge için clip path kullan
            from PyQt6.QtGui import QPainterPath
            clip_path = QPainterPath()
            clip_path.addEllipse(rect)
            painter.setClipPath(clip_path)
            
            # İç gölge için rect'i ters offset uygula
            shadow_rect = QRectF(
                rect.x() - shadow_offset_x,
                rect.y() - shadow_offset_y,
                rect.width() + shadow_size * 2,
                rect.height() + shadow_size * 2
            )
        else:
            # Gölge rect hesapla
            shadow_rect = QRectF(
                rect.x() + shadow_offset_x,
                rect.y() + shadow_offset_y,
                rect.width() + shadow_size * 2,
                rect.height() + shadow_size * 2
            )
        
        painter.setOpacity(shadow_opacity)
        painter.setBrush(QBrush(shadow_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(shadow_rect)
        
        painter.restore()
    
    def _get_adjusted_blur_radius(self, shadow_blur, shadow_quality):
        """Performans ayarına göre blur yarıçapını ayarla"""
        base_blur = shadow_blur * 3  # 3x güçlendir
        
        if shadow_quality == "low":
            return max(3, int(base_blur * 0.5))
        elif shadow_quality == "high":
            return int(base_blur * 2.0)
        else:  # medium
            return int(base_blur * 1.2)
    
    def _apply_blur_to_pixmap(self, pixmap, radius):
        """Pixmap'e blur efekti uygula"""
        if radius <= 0:
            return pixmap
            
        from PyQt6.QtWidgets import QGraphicsScene, QGraphicsPixmapItem, QGraphicsBlurEffect
        from PyQt6.QtGui import QPixmap
        
        # QGraphicsScene kullanarak blur efekti uygula
        scene = QGraphicsScene()
        item = QGraphicsPixmapItem(pixmap)
        scene.addItem(item)
        
        # Blur efekti oluştur
        blur_effect = QGraphicsBlurEffect()
        blur_effect.setBlurRadius(radius)
        item.setGraphicsEffect(blur_effect)
        
        # Yeni pixmap oluştur
        blurred_pixmap = QPixmap(pixmap.size())
        blurred_pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(blurred_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        scene.render(painter)
        painter.end()
        
        return blurred_pixmap
        
    def _create_inner_shadow_pixmap(self, base_shadow_pixmap, rect, margin, blur_radius, shadow_color, offset_x, offset_y, shadow_size):
        """İç gölge için özel pixmap oluştur - basitleştirilmiş yaklaşım"""

        from PyQt6.QtGui import QPixmap, QPainter, QBrush, QRadialGradient, QColor
        
        # 1. Ana çember boyutunda pixmap oluştur
        inner_shadow = QPixmap(int(rect.width()), int(rect.height()))
        inner_shadow.fill(Qt.GlobalColor.transparent)
        
        inner_painter = QPainter(inner_shadow)
        inner_painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 2. Ana çemberi çiz (gölge rengi ile)
        inner_painter.setBrush(QBrush(shadow_color))
        inner_painter.setPen(Qt.PenStyle.NoPen)
        
        full_rect = QRectF(0, 0, rect.width(), rect.height())
        inner_painter.drawEllipse(full_rect)
        
        # 3. İç kısmını gradient ile temizle (iç gölge efekti için)
        inner_painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationOut)
        
        # Gölge genişliği hesapla (shadow_size kullan)
        shadow_inset = max(shadow_size, 3)  # Shadow size'ı kullan, minimum 3px
        
        # İç çemberi temizle (offset ile)
        inner_rect = QRectF(
            shadow_inset - offset_x,
            shadow_inset - offset_y,
            rect.width() - (shadow_inset * 2) + (offset_x * 2),
            rect.height() - (shadow_inset * 2) + (offset_y * 2)
        )
        
        # Geçerli alan içinde mi kontrol et
        if inner_rect.width() > 0 and inner_rect.height() > 0:
            inner_painter.setBrush(QBrush(Qt.GlobalColor.black))
            inner_painter.setPen(Qt.PenStyle.NoPen)
            inner_painter.drawEllipse(inner_rect)
        
        inner_painter.end()
        
        # 4. Blur uygula (eğer varsa)
        if blur_radius > 0:
            inner_shadow = self._apply_blur_to_pixmap(inner_shadow, int(blur_radius * 0.8))
        
        return inner_shadow
        
    def _create_tinted_pixmap(self, pixmap, color):
        """Belirtilen renkte renklendirilmiş pixmap oluştur (gölge için)"""
        from PyQt6.QtGui import QPixmap, QPainter
        tinted = QPixmap(pixmap.size())
        tinted.fill(color)
        tinted_painter = QPainter(tinted)
        tinted_painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
        tinted_painter.drawPixmap(0, 0, pixmap)
        tinted_painter.end()
        return tinted
        
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
        
        # 2. İç gölge çiz (varsa) - dolgudan sonra, çerçeveden önce
        if stroke_data.get('has_shadow', False) and stroke_data.get('inner_shadow', False):
            self._draw_circle_shadow(painter, stroke_data, rect)
        
        # 3. Çerçeve çiz
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
        
        # Aktif dolgu çiz (varsa)
        if self.is_filled and self.fill_color:
            fill_brush = QBrush(self.fill_color)
            painter.setBrush(fill_brush)
            painter.setOpacity(self.fill_opacity * 0.5)  # Daha şeffaf
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(circle_rect)
            painter.setOpacity(1.0)
        
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