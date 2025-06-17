from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QPainter, QPen, QPainterPath, QColor
import math
from typing import List

def rgba_to_qcolor(color):
    """RGBA tuple'ını QColor'a çevir"""
    if isinstance(color, (tuple, list)) and len(color) >= 3:
        if len(color) == 3:
            return QColor(color[0], color[1], color[2])
        else:
            return QColor(color[0], color[1], color[2], color[3])
    elif isinstance(color, QColor):
        return color
    else:
        return QColor(0, 0, 0)  # Fallback

class AdvancedBrush:
    """Gelişmiş brush sistemi - performanslı çizgi stilleri"""
    
    @staticmethod
    def draw_pen_stroke(painter: QPainter, points: List[QPointF], color, width: float, line_style: str = 'solid'):
        """Optimize edilmiş pen stroke çizimi"""
        if len(points) < 2:
            return
            
        # Temel pen ayarları
        pen = QPen()
        pen.setColor(rgba_to_qcolor(color))
        pen.setWidthF(max(1.0, width))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        
        painter.save()
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        # Style'a göre farklı işlemler
        if line_style == 'zigzag':
            AdvancedBrush._draw_zigzag_optimized(painter, points, color, width)
        elif line_style == 'double':
            AdvancedBrush._draw_double_optimized(painter, points, color, width)
        else:
            # Standart stiller için optimize edilmiş path
            AdvancedBrush._draw_standard_style(painter, points, pen, line_style)
            
        painter.restore()
    
    @staticmethod
    def _draw_standard_style(painter: QPainter, points: List[QPointF], pen: QPen, line_style: str):
        """Standart çizgi stilleri - optimize edilmiş"""
        # Style ayarla
        if line_style == 'dashed':
            pen.setStyle(Qt.PenStyle.DashLine)
        elif line_style == 'dotted':
            pen.setStyle(Qt.PenStyle.DotLine)
        elif line_style == 'dashdot':
            pen.setStyle(Qt.PenStyle.DashDotLine)
        elif line_style == 'dashdotdot':
            pen.setStyle(Qt.PenStyle.DashDotDotLine)
        
        painter.setPen(pen)
        
        # Performans için: Çok nokta varsa direct line drawing
        if len(points) > 50:
            for i in range(len(points) - 1):
                painter.drawLine(points[i], points[i + 1])
        else:
            # Az nokta varsa smooth path
            path = QPainterPath()
            path.moveTo(points[0])
            for point in points[1:]:
                path.lineTo(point)
            painter.drawPath(path)
    
    @staticmethod
    def _draw_zigzag_optimized(painter: QPainter, points: List[QPointF], color, width: float, amplitude: float = 3, freq: float = 8):
        """Optimize edilmiş zigzag çizimi"""
        pen = QPen(rgba_to_qcolor(color))
        pen.setWidthF(max(1.0, width))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        
        # Sadece segment'larda zigzag yap, her nokta için değil
        for i in range(0, len(points) - 1, 3):  # 3'er atlayarak performans
            p1 = points[i]
            p2 = points[min(i + 3, len(points) - 1)]
            
            dx = p2.x() - p1.x()
            dy = p2.y() - p1.y()
            length = math.hypot(dx, dy)
            
            if length < 5:  # Çok kısa segment'leri atla
                painter.drawLine(p1, p2)
                continue
                
            steps = max(2, int(length // freq))
            if steps > 8:  # Maksimum step limit (performans)
                steps = 8
                
            zigzag_points = []
            for s in range(steps + 1):
                t = s / steps
                x = p1.x() + dx * t
                y = p1.y() + dy * t
                
                if s % 2 == 1:
                    nx = -dy / length
                    ny = dx / length
                    x += nx * amplitude
                    y += ny * amplitude
                    
                zigzag_points.append(QPointF(x, y))
            
            # Zigzag path'i çiz
            for s in range(len(zigzag_points) - 1):
                painter.drawLine(zigzag_points[s], zigzag_points[s + 1])
    
    @staticmethod
    def _draw_double_optimized(painter: QPainter, points: List[QPointF], color, width: float, offset: float = 2):
        """Optimize edilmiş double line çizimi"""
        pen = QPen(rgba_to_qcolor(color))
        pen.setWidthF(max(1.0, width * 0.7))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        
        # Her 2 nokta için offset hesapla (performans)
        for sign in [-1, 1]:
            offset_points = []
            
            for i in range(0, len(points), 2):  # 2'şer atlayarak
                point = points[i]
                
                # Normal vektör hesapla
                if i < len(points) - 1:
                    next_point = points[i + 1]
                    dx = next_point.x() - point.x()
                    dy = next_point.y() - point.y()
                else:
                    dx, dy = 0, 0
                
                length = math.hypot(dx, dy)
                if length > 1e-3:
                    nx = -dy / length
                    ny = dx / length
                    x = point.x() + sign * nx * offset
                    y = point.y() + sign * ny * offset
                    offset_points.append(QPointF(x, y))
                else:
                    offset_points.append(point)
            
            # Offset line çiz
            if len(offset_points) > 1:
                for i in range(len(offset_points) - 1):
                    painter.drawLine(offset_points[i], offset_points[i + 1])

class SimpleBrush:
    """Basit ve hızlı brush - varsayılan kullanım"""
    
    @staticmethod
    def draw_simple_stroke(painter: QPainter, points: List[QPointF], color, width: float, tablet_mode=False, line_style=Qt.PenStyle.SolidLine):
        """Ultra hızlı basit stroke çizimi"""
        if len(points) < 2:
            return
            
        pen = QPen(rgba_to_qcolor(color))
        pen.setWidthF(max(1.0, width))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        
        # Line style ayarla
        if isinstance(line_style, int):
            line_style = Qt.PenStyle(line_style)
        pen.setStyle(line_style)
        
        painter.save()
        painter.setPen(pen)
        
        # Tablet yazımı için daha iyi anti-aliasing
        if tablet_mode:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        
        # Direct line drawing - en hızlı
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])
            
        painter.restore() 