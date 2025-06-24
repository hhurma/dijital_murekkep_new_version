from PyQt6.QtCore import QSize, QRectF, Qt, QPointF
from PyQt6.QtGui import QPixmap, QPainter, QBrush, QColor, QPainterPath
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsPixmapItem, QGraphicsBlurEffect

class ShadowRenderer:
    """Tüm şekiller için ortak gölge rendering sınıfı"""
    
    @staticmethod
    def draw_shape_shadow(painter, shape_type, shape_rect, stroke_data):
        """Ana gölge çizim methodu"""
        if not stroke_data.get('has_shadow', False):
            return
            
        shadow_blur = stroke_data.get('shadow_blur', 10)
        inner_shadow = stroke_data.get('inner_shadow', False)
        
        if shadow_blur <= 0:
            ShadowRenderer._draw_simple_shadow(painter, shape_type, shape_rect, stroke_data)
        else:
            ShadowRenderer._draw_blurred_shadow(painter, shape_type, shape_rect, stroke_data)
    
    @staticmethod
    def _draw_simple_shadow(painter, shape_type, shape_rect, stroke_data):
        """Blur olmadan basit gölge"""
        shadow_color = stroke_data.get('shadow_color', Qt.GlobalColor.black)
        shadow_size = stroke_data.get('shadow_size', 0)
        shadow_opacity = stroke_data.get('shadow_opacity', 0.7)
        shadow_offset_x = stroke_data.get('shadow_offset_x', 5)
        shadow_offset_y = stroke_data.get('shadow_offset_y', 5)
        inner_shadow = stroke_data.get('inner_shadow', False)
        
        if isinstance(shadow_color, str):
            shadow_color = QColor(shadow_color)
        elif hasattr(shadow_color, 'name'):
            shadow_color = QColor(shadow_color)
            
        painter.save()
        
        if inner_shadow:
            # İç gölge için clip path
            clip_path = QPainterPath()
            if shape_type == 'circle':
                clip_path.addEllipse(shape_rect)
            else:  # rectangle
                clip_path.addRect(shape_rect)
            painter.setClipPath(clip_path)
            
            # İç gölge rect - ters offset
            shadow_rect = QRectF(
                shape_rect.x() - shadow_offset_x,
                shape_rect.y() - shadow_offset_y,
                shape_rect.width() + shadow_size * 2,
                shape_rect.height() + shadow_size * 2
            )
        else:
            # Dış gölge rect
            shadow_rect = QRectF(
                shape_rect.x() + shadow_offset_x,
                shape_rect.y() + shadow_offset_y,
                shape_rect.width() + shadow_size * 2,
                shape_rect.height() + shadow_size * 2
            )
        
        painter.setOpacity(shadow_opacity)
        painter.setBrush(QBrush(shadow_color))
        painter.setPen(Qt.PenStyle.NoPen)
        
        if shape_type == 'circle':
            painter.drawEllipse(shadow_rect)
        else:  # rectangle
            painter.drawRect(shadow_rect)
        
        painter.restore()
    
    @staticmethod
    def _draw_blurred_shadow(painter, shape_type, shape_rect, stroke_data):
        """Pixmap tabanlı blurred gölge"""
        shadow_color = stroke_data.get('shadow_color', Qt.GlobalColor.black)
        shadow_blur = stroke_data.get('shadow_blur', 10)
        shadow_size = stroke_data.get('shadow_size', 0)
        shadow_opacity = stroke_data.get('shadow_opacity', 0.7)
        shadow_offset_x = stroke_data.get('shadow_offset_x', 5)
        shadow_offset_y = stroke_data.get('shadow_offset_y', 5)
        inner_shadow = stroke_data.get('inner_shadow', False)
        shadow_quality = stroke_data.get('shadow_quality', 'medium')
        
        if isinstance(shadow_color, str):
            shadow_color = QColor(shadow_color)
        elif hasattr(shadow_color, 'name'):
            shadow_color = QColor(shadow_color)
        
        # Blur radius ayarla
        blur_radius = ShadowRenderer._get_adjusted_blur_radius(shadow_blur, shadow_quality)
        
        # Gölge pixmap boyutu
        margin = max(25, blur_radius * 2, shadow_size * 2)
        shadow_pixmap_size = QSize(
            int(shape_rect.width() + margin * 2 + abs(shadow_offset_x)),
            int(shape_rect.height() + margin * 2 + abs(shadow_offset_y))
        )
        
        # Gölge pixmap oluştur
        shadow_pixmap = QPixmap(shadow_pixmap_size)
        shadow_pixmap.fill(Qt.GlobalColor.transparent)
        
        shadow_painter = QPainter(shadow_pixmap)
        shadow_painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Gölge şeklini çiz
        shape_rect_in_pixmap = QRectF(
            margin,
            margin,
            shape_rect.width() + shadow_size * 2,
            shape_rect.height() + shadow_size * 2
        )
        
        shadow_painter.setBrush(QBrush(shadow_color))
        shadow_painter.setPen(Qt.PenStyle.NoPen)
        
        if shape_type == 'circle':
            shadow_painter.drawEllipse(shape_rect_in_pixmap)
        else:  # rectangle
            shadow_painter.drawRect(shape_rect_in_pixmap)
        
        shadow_painter.end()
        
        if inner_shadow:
            # İç gölge için özel işlem
            inner_shadow_pixmap = ShadowRenderer._create_inner_shadow_pixmap(
                shadow_pixmap, shape_rect, shape_type, margin, blur_radius, 
                shadow_color, shadow_offset_x, shadow_offset_y, shadow_size)
            
            painter.save()
            painter.setOpacity(shadow_opacity)
            
            # İç gölge için clip
            clip_path = QPainterPath()
            if shape_type == 'circle':
                clip_path.addEllipse(shape_rect)
            else:
                clip_path.addRect(shape_rect)
            painter.setClipPath(clip_path)
            
            shadow_pos_x = int(shape_rect.x())
            shadow_pos_y = int(shape_rect.y())
            painter.drawPixmap(shadow_pos_x, shadow_pos_y, inner_shadow_pixmap)
            painter.restore()
        else:
            # Dış gölge için blur uygula
            if blur_radius > 0:
                blurred_shadow = ShadowRenderer._apply_blur_to_pixmap(shadow_pixmap, blur_radius)
            else:
                blurred_shadow = shadow_pixmap
            
            painter.save()
            painter.setOpacity(shadow_opacity)
            
            shadow_pos_x = int(shape_rect.x() + shadow_offset_x - margin)
            shadow_pos_y = int(shape_rect.y() + shadow_offset_y - margin)
            
            painter.drawPixmap(shadow_pos_x, shadow_pos_y, blurred_shadow)
            painter.restore()
    
    @staticmethod
    def _get_adjusted_blur_radius(shadow_blur, shadow_quality):
        """Performans ayarına göre blur yarıçapını ayarla"""
        base_blur = shadow_blur * 3
        
        if shadow_quality == "low":
            return max(3, int(base_blur * 0.5))
        elif shadow_quality == "high":
            return int(base_blur * 2.0)
        else:  # medium
            return int(base_blur * 1.2)
    
    @staticmethod
    def _apply_blur_to_pixmap(pixmap, radius):
        """Pixmap'e blur efekti uygula"""
        if radius <= 0:
            return pixmap
            
        # QGraphicsScene kullanarak blur
        scene = QGraphicsScene()
        item = QGraphicsPixmapItem(pixmap)
        scene.addItem(item)
        
        # Blur efekti
        blur_effect = QGraphicsBlurEffect()
        blur_effect.setBlurRadius(radius)
        item.setGraphicsEffect(blur_effect)
        
        # Yeni pixmap
        blurred_pixmap = QPixmap(pixmap.size())
        blurred_pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(blurred_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        scene.render(painter)
        painter.end()
        
        return blurred_pixmap
    
    @staticmethod
    def _create_inner_shadow_pixmap(base_shadow_pixmap, shape_rect, shape_type, margin, blur_radius, shadow_color, offset_x, offset_y, shadow_size):
        """İç gölge için özel pixmap"""
        # Ana şekil boyutunda pixmap
        inner_shadow = QPixmap(int(shape_rect.width()), int(shape_rect.height()))
        inner_shadow.fill(Qt.GlobalColor.transparent)
        
        inner_painter = QPainter(inner_shadow)
        inner_painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Ana şekli çiz
        inner_painter.setBrush(QBrush(shadow_color))
        inner_painter.setPen(Qt.PenStyle.NoPen)
        
        full_rect = QRectF(0, 0, shape_rect.width(), shape_rect.height())
        if shape_type == 'circle':
            inner_painter.drawEllipse(full_rect)
        else:
            inner_painter.drawRect(full_rect)
        
        # İç kısmını temizle
        inner_painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationOut)
        
        shadow_inset = max(shadow_size, 3)
        
        inner_rect = QRectF(
            shadow_inset - offset_x,
            shadow_inset - offset_y,
            shape_rect.width() - (shadow_inset * 2) + (offset_x * 2),
            shape_rect.height() - (shadow_inset * 2) + (offset_y * 2)
        )
        
        if inner_rect.width() > 0 and inner_rect.height() > 0:
            if shape_type == 'circle':
                inner_painter.drawEllipse(inner_rect)
            else:
                inner_painter.drawRect(inner_rect)
        
        inner_painter.end()
        
        # Blur uygula
        if blur_radius > 0:
            inner_shadow = ShadowRenderer._apply_blur_to_pixmap(inner_shadow, blur_radius)
        
        return inner_shadow 