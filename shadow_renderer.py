import math

from PyQt6.QtCore import QSize, QRectF, Qt, QPointF
from PyQt6.QtGui import QPixmap, QPainter, QBrush, QColor, QPainterPath, QPainterPathStroker
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsPixmapItem, QGraphicsBlurEffect

class ShadowRenderer:
    """Tüm şekiller için ortak gölge rendering sınıfı"""
    
    @staticmethod
    def draw_shape_shadow(painter, shape_type, shape_rect_or_points, stroke_data):
        """Ana gölge çizim methodu - rect veya points array alabilir"""
        if not stroke_data.get('has_shadow', False):
            return

        shadow_blur = stroke_data.get('shadow_blur', 10)
        inner_shadow = stroke_data.get('inner_shadow', False)

        if shape_type == 'path':
            ShadowRenderer._draw_path_shadow(painter, shape_rect_or_points, stroke_data, shadow_blur)
            return

        if shadow_blur <= 0:
            ShadowRenderer._draw_simple_shadow(painter, shape_type, shape_rect_or_points, stroke_data)
        else:
            ShadowRenderer._draw_blurred_shadow(painter, shape_type, shape_rect_or_points, stroke_data)

    @staticmethod
    def _draw_simple_shadow(painter, shape_type, shape_rect_or_points, stroke_data):
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
        
        # Points array mi yoksa QRect mi?
        if isinstance(shape_rect_or_points, list):
            # Döndürülmüş şekil - points kullan
            points = shape_rect_or_points
            shape_path = QPainterPath()
            if shape_type == 'circle':
                # Circle için center ve radius hesapla
                center_x = sum(p.x() for p in points) / len(points)
                center_y = sum(p.y() for p in points) / len(points)
                # Yaklaşık radius hesapla
                radius = ((points[1].x() - points[0].x())**2 + (points[1].y() - points[0].y())**2)**0.5 / 2
                shape_path.addEllipse(center_x - radius, center_y - radius, radius*2, radius*2)
            else:  # rectangle
                shape_path.moveTo(points[0])
                for i in range(1, len(points)):
                    shape_path.lineTo(points[i])
                shape_path.closeSubpath()
            
            if inner_shadow:
                # İç gölge için clip
                painter.setClipPath(shape_path)
                
                # Shadow offset için points'leri kaydır
                shadow_points = []
                for p in points:
                    shadow_points.append(QPointF(p.x() - shadow_offset_x, p.y() - shadow_offset_y))
            else:
                # Dış gölge için points'leri kaydır
                shadow_points = []
                for p in points:
                    shadow_points.append(QPointF(p.x() + shadow_offset_x, p.y() + shadow_offset_y))
            
            # Shadow path oluştur
            shadow_path = QPainterPath()
            if shape_type == 'circle':
                center_x = sum(p.x() for p in shadow_points) / len(shadow_points)
                center_y = sum(p.y() for p in shadow_points) / len(shadow_points)
                radius = ((shadow_points[1].x() - shadow_points[0].x())**2 + (shadow_points[1].y() - shadow_points[0].y())**2)**0.5 / 2
                shadow_path.addEllipse(center_x - radius - shadow_size, center_y - radius - shadow_size, 
                                     (radius + shadow_size)*2, (radius + shadow_size)*2)
            else:  # rectangle
                shadow_path.moveTo(shadow_points[0])
                for i in range(1, len(shadow_points)):
                    shadow_path.lineTo(shadow_points[i])
                shadow_path.closeSubpath()
            
            painter.setOpacity(shadow_opacity)
            painter.setBrush(QBrush(shadow_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawPath(shadow_path)
            
        else:
            # Normal QRectF - eski kod
            shape_rect = shape_rect_or_points
            
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
    def _draw_blurred_shadow(painter, shape_type, shape_rect_or_points, stroke_data):
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
        
        # Points mi QRect mi kontrol et
        if isinstance(shape_rect_or_points, list):
            # Döndürülmüş şekil için bounding box hesapla
            points = shape_rect_or_points
            min_x = min(p.x() for p in points)
            max_x = max(p.x() for p in points)
            min_y = min(p.y() for p in points)
            max_y = max(p.y() for p in points)
            bounding_rect = QRectF(min_x, min_y, max_x - min_x, max_y - min_y)
            
            # Gölge pixmap boyutu
            margin = max(25, blur_radius * 2, shadow_size * 2)
            shadow_pixmap_size = QSize(
                int(bounding_rect.width() + margin * 2 + abs(shadow_offset_x)),
                int(bounding_rect.height() + margin * 2 + abs(shadow_offset_y))
            )
            
            # Points'leri pixmap koordinatlarına çevir
            pixmap_points = []
            for p in points:
                pixmap_points.append(QPointF(
                    p.x() - min_x + margin,
                    p.y() - min_y + margin
                ))
        else:
            # Normal QRectF
            shape_rect = shape_rect_or_points
            bounding_rect = shape_rect
            
            # Gölge pixmap boyutu
            margin = max(25, blur_radius * 2, shadow_size * 2)
            shadow_pixmap_size = QSize(
                int(shape_rect.width() + margin * 2 + abs(shadow_offset_x)),
                int(shape_rect.height() + margin * 2 + abs(shadow_offset_y))
            )
            pixmap_points = None
        
        # Gölge pixmap oluştur
        shadow_pixmap = QPixmap(shadow_pixmap_size)
        shadow_pixmap.fill(Qt.GlobalColor.transparent)
        
        shadow_painter = QPainter(shadow_pixmap)
        shadow_painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Gölge şeklini çiz
        shadow_painter.setBrush(QBrush(shadow_color))
        shadow_painter.setPen(Qt.PenStyle.NoPen)
        
        # Corner radius kontrolü
        corner_radius = stroke_data.get('corner_radius', 0)
        
        if pixmap_points is not None:
            # Döndürülmüş şekil - points kullan
            shadow_path = QPainterPath()
            if shape_type == 'circle':
                # Circle için center ve radius hesapla
                center_x = sum(p.x() for p in pixmap_points) / len(pixmap_points)
                center_y = sum(p.y() for p in pixmap_points) / len(pixmap_points)
                radius = ((pixmap_points[1].x() - pixmap_points[0].x())**2 + (pixmap_points[1].y() - pixmap_points[0].y())**2)**0.5 / 2
                shadow_path.addEllipse(center_x - radius - shadow_size, center_y - radius - shadow_size, 
                                     (radius + shadow_size)*2, (radius + shadow_size)*2)
            else:  # rectangle
                if corner_radius > 0:
                    # Döndürülmüş yuvarlak kenar rectangle için path oluştur
                    shadow_path = ShadowRenderer._create_rounded_rectangle_shadow_path(pixmap_points, corner_radius, shadow_size)
                else:
                    # Normal köşeli rectangle
                    shadow_path.moveTo(pixmap_points[0])
                    for i in range(1, len(pixmap_points)):
                        shadow_path.lineTo(pixmap_points[i])
                    shadow_path.closeSubpath()
            
            shadow_painter.drawPath(shadow_path)
        else:
            # Normal QRectF
            shape_rect_in_pixmap = QRectF(
                margin,
                margin,
                bounding_rect.width() + shadow_size * 2,
                bounding_rect.height() + shadow_size * 2
            )
            
            if shape_type == 'circle':
                shadow_painter.drawEllipse(shape_rect_in_pixmap)
            else:  # rectangle
                if corner_radius > 0:
                    # Yuvarlak kenar rectangle
                    shadow_painter.drawRoundedRect(shape_rect_in_pixmap, corner_radius, corner_radius)
                else:
                    # Normal köşeli rectangle
                    shadow_painter.drawRect(shape_rect_in_pixmap)
        
        shadow_painter.end()
        
        if inner_shadow:
            # İç gölge için özel işlem
            inner_shadow_pixmap = ShadowRenderer._create_inner_shadow_pixmap(
                shadow_pixmap, bounding_rect, shape_type, margin, blur_radius, 
                shadow_color, shadow_offset_x, shadow_offset_y, shadow_size, 
                pixmap_points if pixmap_points is not None else None, corner_radius)
            
            painter.save()
            painter.setOpacity(shadow_opacity)
            
            # İç gölge için clip
            clip_path = QPainterPath()
            if pixmap_points is not None:
                # Döndürülmüş şekil için points kullan
                if shape_type == 'circle':
                    center_x = sum(p.x() for p in points) / len(points)
                    center_y = sum(p.y() for p in points) / len(points)
                    radius = ((points[1].x() - points[0].x())**2 + (points[1].y() - points[0].y())**2)**0.5 / 2
                    clip_path.addEllipse(center_x - radius, center_y - radius, radius*2, radius*2)
                else:  # rectangle
                    if corner_radius > 0:
                        # Döndürülmüş yuvarlak kenar rectangle için clip path
                        clip_path = ShadowRenderer._create_rounded_rectangle_path_for_clip(points, corner_radius)
                    else:
                        # Normal köşeli rectangle
                        clip_path.moveTo(points[0])
                        for i in range(1, len(points)):
                            clip_path.lineTo(points[i])
                        clip_path.closeSubpath()
            else:
                # Normal QRectF
                if shape_type == 'circle':
                    clip_path.addEllipse(bounding_rect)
                else:
                    if corner_radius > 0:
                        # Yuvarlak kenar rectangle
                        clip_path.addRoundedRect(bounding_rect, corner_radius, corner_radius)
                    else:
                        # Normal köşeli rectangle
                        clip_path.addRect(bounding_rect)
            painter.setClipPath(clip_path)
            
            # İç gölge pixmap pozisyonunu düzelt
            if pixmap_points is not None:
                # Döndürülmüş şekil için min koordinatları kullan
                shadow_pos_x = int(min_x)
                shadow_pos_y = int(min_y)
            else:
                shadow_pos_x = int(bounding_rect.x())
                shadow_pos_y = int(bounding_rect.y())
            
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
            
            shadow_pos_x = int(bounding_rect.x() + shadow_offset_x - margin)
            shadow_pos_y = int(bounding_rect.y() + shadow_offset_y - margin)
            
            painter.drawPixmap(shadow_pos_x, shadow_pos_y, blurred_shadow)
            painter.restore()

    @staticmethod
    def _draw_path_shadow(painter, path_or_points, stroke_data, shadow_blur):
        """QPainterPath tabanlı gölge çizimi"""
        path = ShadowRenderer._ensure_path(path_or_points)
        if path is None or path.isEmpty():
            return

        shadow_color = stroke_data.get('shadow_color', Qt.GlobalColor.black)
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

        base_width = ShadowRenderer._get_path_width(stroke_data)
        expanded_width = max(0.1, base_width + shadow_size * 2)

        base_path = ShadowRenderer._create_stroke_area_path(path, base_width, stroke_data)
        shadow_path = ShadowRenderer._create_stroke_area_path(path, expanded_width, stroke_data)

        if shadow_blur <= 0:
            painter.save()
            painter.setOpacity(shadow_opacity)
            painter.setBrush(QBrush(shadow_color))
            painter.setPen(Qt.PenStyle.NoPen)

            draw_path = QPainterPath(shadow_path)
            if inner_shadow:
                painter.setClipPath(base_path)
                draw_path.translate(-shadow_offset_x, -shadow_offset_y)
            else:
                draw_path.translate(shadow_offset_x, shadow_offset_y)

            painter.drawPath(draw_path)
            painter.restore()
            return

        blur_radius = ShadowRenderer._get_adjusted_blur_radius(shadow_blur, shadow_quality)

        bounding_rect = shadow_path.boundingRect()
        margin = max(25, blur_radius * 2, shadow_size * 2, int(base_width) + 5)
        shadow_pixmap_size = QSize(
            int(bounding_rect.width() + margin * 2 + abs(shadow_offset_x)),
            int(bounding_rect.height() + margin * 2 + abs(shadow_offset_y))
        )

        shadow_pixmap = QPixmap(shadow_pixmap_size)
        shadow_pixmap.fill(Qt.GlobalColor.transparent)

        shadow_painter = QPainter(shadow_pixmap)
        shadow_painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        shadow_painter.setBrush(QBrush(shadow_color))
        shadow_painter.setPen(Qt.PenStyle.NoPen)

        path_in_pixmap = QPainterPath(shadow_path)
        path_in_pixmap.translate(-bounding_rect.x() + margin, -bounding_rect.y() + margin)
        shadow_painter.drawPath(path_in_pixmap)
        shadow_painter.end()

        if blur_radius > 0:
            blurred_shadow = ShadowRenderer._apply_blur_to_pixmap(shadow_pixmap, blur_radius)
        else:
            blurred_shadow = shadow_pixmap

        painter.save()
        painter.setOpacity(shadow_opacity)

        draw_x = bounding_rect.x() + ( -shadow_offset_x if inner_shadow else shadow_offset_x) - margin
        draw_y = bounding_rect.y() + ( -shadow_offset_y if inner_shadow else shadow_offset_y) - margin

        if inner_shadow:
            painter.setClipPath(base_path)

        painter.drawPixmap(int(draw_x), int(draw_y), blurred_shadow)
        painter.restore()

    @staticmethod
    def _ensure_path(path_or_points):
        """QPainterPath veya nokta listesini path'e dönüştür"""
        if isinstance(path_or_points, QPainterPath):
            return QPainterPath(path_or_points)

        if isinstance(path_or_points, (list, tuple)) and path_or_points:
            points = [ShadowRenderer._ensure_point(p) for p in path_or_points]
            points = [p for p in points if p is not None]
            if len(points) < 2:
                return None
            path = QPainterPath(points[0])
            for point in points[1:]:
                path.lineTo(point)
            return path

        return None

    @staticmethod
    def _ensure_point(point):
        """Verilen noktayı QPointF'e çevir"""
        if point is None:
            return None
        if isinstance(point, QPointF):
            return QPointF(point)
        if isinstance(point, dict):
            x = point.get('x')
            y = point.get('y')
            if x is not None and y is not None:
                return QPointF(float(x), float(y))
            return None
        if isinstance(point, (tuple, list)) and len(point) >= 2:
            return QPointF(float(point[0]), float(point[1]))
        if hasattr(point, 'x') and hasattr(point, 'y'):
            return QPointF(float(point.x()), float(point.y()))
        return None

    @staticmethod
    def _get_path_width(stroke_data):
        """Stroke verisinden çizgi kalınlığını al"""
        width = stroke_data.get('shadow_path_width')
        if width is None:
            width = stroke_data.get('width', stroke_data.get('line_width', 1))
        try:
            return max(0.1, float(width))
        except (TypeError, ValueError):
            return 1.0

    @staticmethod
    def _create_stroke_area_path(path, width, stroke_data):
        """Stroke genişliğine göre dolu path oluştur"""
        stroker = QPainterPathStroker()
        stroker.setWidth(max(0.1, float(width)))

        cap_style = stroke_data.get('cap_style', Qt.PenCapStyle.RoundCap)
        join_style = stroke_data.get('join_style', Qt.PenJoinStyle.RoundJoin)
        miter_limit = stroke_data.get('miter_limit', 4)

        try:
            if isinstance(cap_style, int):
                cap_style = Qt.PenCapStyle(cap_style)
        except Exception:
            cap_style = Qt.PenCapStyle.RoundCap

        try:
            if isinstance(join_style, int):
                join_style = Qt.PenJoinStyle(join_style)
        except Exception:
            join_style = Qt.PenJoinStyle.RoundJoin

        stroker.setCapStyle(cap_style)
        stroker.setJoinStyle(join_style)
        try:
            stroker.setMiterLimit(max(0.1, float(miter_limit)))
        except Exception:
            stroker.setMiterLimit(4.0)

        return stroker.createStroke(path)
    
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
    def _create_inner_shadow_pixmap(base_shadow_pixmap, shape_rect, shape_type, margin, blur_radius, shadow_color, offset_x, offset_y, shadow_size, points, corner_radius):
        """İç gölge için özel pixmap"""
        
        if points is not None:
            # Döndürülmüş şekil için büyük pixmap kullan
            inner_shadow = QPixmap(int(shape_rect.width()), int(shape_rect.height()))
        else:
            # Normal şekil için standard boyut
            inner_shadow = QPixmap(int(shape_rect.width()), int(shape_rect.height()))
        
        inner_shadow.fill(Qt.GlobalColor.transparent)
        
        inner_painter = QPainter(inner_shadow)
        inner_painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        if points is not None:
            # Döndürülmüş şekil - points'leri shape_rect içindeki relatif pozisyonlara çevir
            min_x = min(p.x() for p in points)
            min_y = min(p.y() for p in points)
            
            # Points'leri pixmap koordinatlarına çevir
            inner_points = []
            for p in points:
                inner_points.append(QPointF(p.x() - min_x, p.y() - min_y))
            
            # Ana şekli çiz
            inner_painter.setBrush(QBrush(shadow_color))
            inner_painter.setPen(Qt.PenStyle.NoPen)
            
            outer_path = QPainterPath()
            if shape_type == 'circle':
                center_x = sum(p.x() for p in inner_points) / len(inner_points)
                center_y = sum(p.y() for p in inner_points) / len(inner_points)
                radius = ((inner_points[1].x() - inner_points[0].x())**2 + (inner_points[1].y() - inner_points[0].y())**2)**0.5 / 2
                outer_path.addEllipse(center_x - radius, center_y - radius, radius*2, radius*2)
            else:
                if corner_radius > 0:
                    # Döndürülmüş yuvarlak kenar rectangle
                    outer_path = ShadowRenderer._create_rounded_rectangle_path_for_clip(inner_points, corner_radius)
                else:
                    # Normal köşeli rectangle
                    outer_path.moveTo(inner_points[0])
                    for i in range(1, len(inner_points)):
                        outer_path.lineTo(inner_points[i])
                    outer_path.closeSubpath()
            
            inner_painter.drawPath(outer_path)
            
            # İç kısmını temizle
            inner_painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationOut)
            
            # İç şekil için offset ve inset hesapla
            shadow_inset = max(shadow_size, 3)
            
            inner_path = QPainterPath()
            if shape_type == 'circle':
                inner_center_x = center_x + offset_x
                inner_center_y = center_y + offset_y
                inner_radius = max(1, radius - shadow_inset)
                inner_path.addEllipse(inner_center_x - inner_radius, inner_center_y - inner_radius,
                                      inner_radius * 2, inner_radius * 2)
            else:
                inset_points = None
                axis_aligned = len(inner_points) >= 4 and ShadowRenderer._is_axis_aligned_rectangle(inner_points)

                if axis_aligned:
                    inner_rect = QRectF(
                        shadow_inset,
                        shadow_inset,
                        shape_rect.width() - (shadow_inset * 2),
                        shape_rect.height() - (shadow_inset * 2)
                    )

                    if inner_rect.width() > 0 and inner_rect.height() > 0:
                        inner_rect.translate(offset_x, offset_y)
                        if corner_radius > 0:
                            inner_radius = max(0, corner_radius - shadow_inset)
                            inner_path.addRoundedRect(inner_rect, inner_radius, inner_radius)
                        else:
                            inner_path.addRect(inner_rect)
                else:
                    if len(inner_points) >= 4:
                        inset_points = ShadowRenderer._inset_rotated_rectangle_points(inner_points, shadow_inset)

                    if inset_points:
                        if offset_x != 0 or offset_y != 0:
                            inset_points = [QPointF(p.x() + offset_x, p.y() + offset_y) for p in inset_points]

                        if corner_radius > 0:
                            inner_radius = max(0, corner_radius - shadow_inset)
                            inner_path = ShadowRenderer._create_rounded_rectangle_path_for_clip(inset_points, inner_radius)
                        else:
                            inner_path = QPainterPath()
                            inner_path.moveTo(inset_points[0])
                            for i in range(1, len(inset_points)):
                                inner_path.lineTo(inset_points[i])
                            inner_path.closeSubpath()
                    else:
                        # Fallback: eski merkez tabanlı yaklaşım, offset uygulanmış şekilde
                        center_x = sum(p.x() for p in inner_points) / len(inner_points)
                        center_y = sum(p.y() for p in inner_points) / len(inner_points)

                        fallback_points = []
                        for p in inner_points:
                            direction_x = center_x - p.x()
                            direction_y = center_y - p.y()
                            length = (direction_x ** 2 + direction_y ** 2) ** 0.5
                            if length > 0:
                                direction_x /= length
                                direction_y /= length
                                new_x = p.x() + direction_x * shadow_inset + offset_x
                                new_y = p.y() + direction_y * shadow_inset + offset_y
                                fallback_points.append(QPointF(new_x, new_y))
                            else:
                                fallback_points.append(QPointF(p.x() + offset_x, p.y() + offset_y))

                        if fallback_points:
                            if corner_radius > 0:
                                inner_radius = max(0, corner_radius - shadow_inset)
                                inner_path = ShadowRenderer._create_rounded_rectangle_path_for_clip(fallback_points, inner_radius)
                            else:
                                inner_path = QPainterPath()
                                inner_path.moveTo(fallback_points[0])
                                for i in range(1, len(fallback_points)):
                                    inner_path.lineTo(fallback_points[i])
                                inner_path.closeSubpath()
            
            inner_painter.drawPath(inner_path)
            
        else:
            # Normal rectangular/circular şekil
            # Ana şekli çiz
            inner_painter.setBrush(QBrush(shadow_color))
            inner_painter.setPen(Qt.PenStyle.NoPen)
            
            full_rect = QRectF(0, 0, shape_rect.width(), shape_rect.height())
            if shape_type == 'circle':
                inner_painter.drawEllipse(full_rect)
            else:
                if corner_radius > 0:
                    # Yuvarlak kenar rectangle
                    inner_painter.drawRoundedRect(full_rect, corner_radius, corner_radius)
                else:
                    # Normal köşeli rectangle
                    inner_painter.drawRect(full_rect)
            
            # İç kısmını temizle - offset'i dikkate al
            inner_painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationOut)
            
            shadow_inset = max(shadow_size, 3)
            
            inner_rect = QRectF(
                shadow_inset + offset_x,
                shadow_inset + offset_y,
                shape_rect.width() - (shadow_inset * 2),
                shape_rect.height() - (shadow_inset * 2)
            )
            
            if inner_rect.width() > 0 and inner_rect.height() > 0:
                if shape_type == 'circle':
                    inner_painter.drawEllipse(inner_rect)
                else:
                    if corner_radius > 0:
                        # Yuvarlak kenar rectangle - inner radius hesapla
                        inner_radius = max(0, corner_radius - shadow_inset)
                        inner_painter.drawRoundedRect(inner_rect, inner_radius, inner_radius)
                    else:
                        # Normal köşeli rectangle
                        inner_painter.drawRect(inner_rect)
        
        inner_painter.end()
        
        # Blur uygula
        if blur_radius > 0:
            return ShadowRenderer._apply_blur_to_pixmap(inner_shadow, blur_radius)
        else:
            return inner_shadow

    @staticmethod
    def _is_axis_aligned_rectangle(points, tolerance=1e-3):
        """Points dizisinin eksen hizalı bir dikdörtgen olup olmadığını kontrol et"""
        if len(points) != 4:
            return False

        for i in range(4):
            p_curr = points[i]
            p_next = points[(i + 1) % 4]
            dx = p_next.x() - p_curr.x()
            dy = p_next.y() - p_curr.y()
            if math.isclose(dx, 0.0, abs_tol=tolerance) and math.isclose(dy, 0.0, abs_tol=tolerance):
                return False
            if not (math.isclose(dx, 0.0, abs_tol=tolerance) or math.isclose(dy, 0.0, abs_tol=tolerance)):
                return False

        return True

    @staticmethod
    def _inset_rotated_rectangle_points(points, inset_distance):
        """Döndürülmüş dikdörtgenin kenarlarını belirli mesafede içeri al"""
        if len(points) != 4 or inset_distance <= 0:
            return None

        area = 0.0
        for i in range(4):
            p_curr = points[i]
            p_next = points[(i + 1) % 4]
            area += p_curr.x() * p_next.y() - p_next.x() * p_curr.y()

        if math.isclose(area, 0.0, abs_tol=1e-6):
            return None

        orientation = 1 if area > 0 else -1
        inset_lines = []

        for i in range(4):
            p_curr = points[i]
            p_next = points[(i + 1) % 4]
            edge_vector = QPointF(p_next.x() - p_curr.x(), p_next.y() - p_curr.y())
            length = math.hypot(edge_vector.x(), edge_vector.y())

            if math.isclose(length, 0.0, abs_tol=1e-6):
                return None

            normal_x = -edge_vector.y() / length
            normal_y = edge_vector.x() / length

            if orientation < 0:
                normal_x = -normal_x
                normal_y = -normal_y

            offset_point = QPointF(
                p_curr.x() + normal_x * inset_distance,
                p_curr.y() + normal_y * inset_distance
            )

            inset_lines.append((offset_point, edge_vector))

        inset_points = []
        for i in range(4):
            prev_point, prev_dir = inset_lines[i - 1]
            curr_point, curr_dir = inset_lines[i]
            intersection = ShadowRenderer._intersect_lines(prev_point, prev_dir, curr_point, curr_dir)
            if intersection is None:
                return None
            inset_points.append(intersection)

        return inset_points

    @staticmethod
    def _intersect_lines(point1, direction1, point2, direction2):
        """İki doğruyu kesiştir"""
        cross = direction1.x() * direction2.y() - direction1.y() * direction2.x()
        if math.isclose(cross, 0.0, abs_tol=1e-6):
            return None

        diff_x = point2.x() - point1.x()
        diff_y = point2.y() - point1.y()

        t = (diff_x * direction2.y() - diff_y * direction2.x()) / cross

        return QPointF(
            point1.x() + direction1.x() * t,
            point1.y() + direction1.y() * t
        )
    
    @staticmethod
    def _create_rounded_rectangle_shadow_path(points, corner_radius, shadow_size):
        """Döndürülmüş yuvarlak kenar rectangle için gölge path oluştur"""
        if len(points) != 4:
            # Fallback: normal path
            path = QPainterPath()
            if points:
                path.moveTo(points[0])
                for i in range(1, len(points)):
                    path.lineTo(points[i])
                path.closeSubpath()
            return path
        
        # Shadow için points'leri genişlet
        expanded_points = []
        
        # Merkez hesapla
        center_x = sum(p.x() for p in points) / len(points)
        center_y = sum(p.y() for p in points) / len(points)
        
        # Her noktayı merkezden uzaklaştır (shadow_size kadar)
        for p in points:
            direction_x = p.x() - center_x
            direction_y = p.y() - center_y
            length = (direction_x**2 + direction_y**2)**0.5
            
            if length > 0:
                # Normalize ve genişlet
                direction_x /= length
                direction_y /= length
                expanded_x = p.x() + direction_x * shadow_size
                expanded_y = p.y() + direction_y * shadow_size
                expanded_points.append(QPointF(expanded_x, expanded_y))
            else:
                expanded_points.append(QPointF(p.x(), p.y()))
        
        # Yuvarlak kenar path oluştur
        path = QPainterPath()
        
        for i in range(4):
            p_prev = expanded_points[(i - 1) % 4]
            p_curr = expanded_points[i]
            p_next = expanded_points[(i + 1) % 4]
            
            # Kenar vektörleri
            edge_in = QPointF(p_curr.x() - p_prev.x(), p_curr.y() - p_prev.y())
            edge_out = QPointF(p_next.x() - p_curr.x(), p_next.y() - p_curr.y())
            
            # Kenar uzunlukları
            len_in = (edge_in.x()**2 + edge_in.y()**2)**0.5
            len_out = (edge_out.x()**2 + edge_out.y()**2)**0.5
            
            if len_in > 0 and len_out > 0:
                # Normalize
                edge_in = QPointF(edge_in.x() / len_in, edge_in.y() / len_in)
                edge_out = QPointF(edge_out.x() / len_out, edge_out.y() / len_out)
                
                # Radius'u kenar uzunluğuna göre sınırla
                actual_radius = min(corner_radius, len_in / 2, len_out / 2)
                
                # Yuvarlak başlangıç ve bitiş noktaları
                start_point = QPointF(p_curr.x() - edge_in.x() * actual_radius,
                                    p_curr.y() - edge_in.y() * actual_radius)
                end_point = QPointF(p_curr.x() + edge_out.x() * actual_radius,
                                   p_curr.y() + edge_out.y() * actual_radius)
                
                if i == 0:
                    path.moveTo(start_point)
                else:
                    path.lineTo(start_point)
                
                # Yuvarlak köşe (quadratic curve)
                path.quadTo(p_curr, end_point)
        
        path.closeSubpath()
        return path
    
    @staticmethod
    def _create_rounded_rectangle_path_for_clip(points, corner_radius):
        """Döndürülmüş yuvarlak kenar rectangle için clipping path oluştur"""
        if len(points) != 4:
            # Fallback: normal path
            path = QPainterPath()
            if points:
                path.moveTo(points[0])
                for i in range(1, len(points)):
                    path.lineTo(points[i])
                path.closeSubpath()
            return path
        
        path = QPainterPath()
        
        # Her köşede yuvarlak kenar ekle (shadow_size expansion olmadan)
        for i in range(4):
            p_prev = points[(i - 1) % 4]
            p_curr = points[i]
            p_next = points[(i + 1) % 4]
            
            # Kenar vektörleri
            edge_in = QPointF(p_curr.x() - p_prev.x(), p_curr.y() - p_prev.y())
            edge_out = QPointF(p_next.x() - p_curr.x(), p_next.y() - p_curr.y())
            
            # Kenar uzunlukları
            len_in = (edge_in.x()**2 + edge_in.y()**2)**0.5
            len_out = (edge_out.x()**2 + edge_out.y()**2)**0.5
            
            if len_in > 0 and len_out > 0:
                # Normalize
                edge_in = QPointF(edge_in.x() / len_in, edge_in.y() / len_in)
                edge_out = QPointF(edge_out.x() / len_out, edge_out.y() / len_out)
                
                # Radius'u kenar uzunluğuna göre sınırla
                actual_radius = min(corner_radius, len_in / 2, len_out / 2)
                
                # Yuvarlak başlangıç ve bitiş noktaları
                start_point = QPointF(p_curr.x() - edge_in.x() * actual_radius,
                                    p_curr.y() - edge_in.y() * actual_radius)
                end_point = QPointF(p_curr.x() + edge_out.x() * actual_radius,
                                   p_curr.y() + edge_out.y() * actual_radius)
                
                if i == 0:
                    path.moveTo(start_point)
                else:
                    path.lineTo(start_point)
                
                # Yuvarlak köşe (quadratic curve)
                path.quadTo(p_curr, end_point)
        
        path.closeSubpath()
        return path 