from PyQt6.QtCore import QPointF, QRectF
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
        """Tamamlanmış çemberi çiz"""
        if stroke_data['type'] != 'circle':
            return
            
        center = QPointF(stroke_data['center'][0], stroke_data['center'][1])
        radius = stroke_data['radius']
        
        # Çember için bounding rectangle
        rect = QRectF(center.x() - radius, center.y() - radius, 
                     radius * 2, radius * 2)
        
        painter.save()
        
        # Dolgu çiz (varsa)
        if stroke_data.get('fill_color'):
            fill_brush = QBrush(stroke_data['fill_color'])
            painter.setBrush(fill_brush)
            painter.setOpacity(stroke_data.get('fill_opacity', 1.0))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(rect)
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