from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QPainter, QPen, QPainterPath
import math
import time
from advanced_brush import AdvancedBrush, SimpleBrush
from shadow_renderer import ShadowRenderer

def ensure_qpointf(point):
    """Point'i QPointF'e dönüştür (dict'ten veya zaten QPointF'ten)"""
    if isinstance(point, dict):
        return QPointF(point['x'], point['y'])
    elif isinstance(point, QPointF):
        return point
    else:
        # Başka bir format, deneme
        return QPointF(point.x(), point.y())

class FreehandTool:
    def __init__(self):
        self.is_drawing = False
        self.current_stroke = None
        self.current_color = Qt.GlobalColor.black
        self.current_width = 2
        self.line_style = Qt.PenStyle.SolidLine

        # Tablet yazımı için optimize edilmiş ayarlar
        self.min_distance = 1.0  # Mouse için küçük minimum mesafe
        self.tablet_min_distance = 0.3  # Tablet için çok küçük mesafe (real-time)
        self.smoothing_buffer = []
        self.buffer_size = 3  # Buffer boyutu azaltıldı
        
        # Throttling devre dışı
        
        # Adaptive smoothing için
        self.velocity_threshold = 20.0  # Hızlı çizimde daha az smoothing

        # Brush mode ayarları
        self.brush_mode = 'simple'  # 'simple', 'advanced'
        self.advanced_style = 'solid'  # 'solid', 'dashed', 'dotted', 'zigzag', 'double'

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
        
    def start_stroke(self, pos, pressure=1.0, is_tablet=False):
        """Yeni bir serbest çizim başlat"""
        self.is_drawing = True
        self.smoothing_buffer = [pos]
        self.current_stroke = {
            'type': 'freehand',
            'points': [pos],
            'pressures': [pressure],
            'color': self.current_color,
            'width': self.current_width,
            'style': self.line_style,  # 'style' field'ını kullan
            'brush_mode': self.brush_mode,
            'advanced_style': self.advanced_style,
            'tablet_mode': is_tablet,
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
        self._last_update_time = time.time()
        
    def add_point(self, pos, pressure=1.0, is_tablet=False):
        """Serbest çizime nokta ekle (tablet yazımı optimize)"""
        if not self.is_drawing or not self.current_stroke:
            return
            
        # Tablet için daha hassas minimum mesafe kontrolü
        min_dist = self.tablet_min_distance if is_tablet else self.min_distance
        
        if len(self.current_stroke['points']) > 0:
            last_pos = self.current_stroke['points'][-1]
            distance = math.sqrt((pos.x() - last_pos.x()) ** 2 + (pos.y() - last_pos.y()) ** 2)
            if distance < min_dist:
                return
        
        # Tablet yazımında smoothing'i azalt (daha net harfler)
        if is_tablet:
            # Tablet için minimal smoothing - sadece jitter azaltma
            if len(self.current_stroke['points']) > 0:
                last_pos = self.current_stroke['points'][-1]
                # Çok hafif smoothing (%20 eski, %80 yeni)
                smoothed_pos = QPointF(
                    last_pos.x() * 0.2 + pos.x() * 0.8,
                    last_pos.y() * 0.2 + pos.y() * 0.8
                )
                self.current_stroke['points'].append(smoothed_pos)
            else:
                self.current_stroke['points'].append(pos)
        else:
            # Mouse için normal smoothing
            if len(self.current_stroke['points']) > 0:
                last_pos = self.current_stroke['points'][-1]
                smoothed_pos = QPointF(
                    (last_pos.x() + pos.x()) * 0.5,
                    (last_pos.y() + pos.y()) * 0.5
                )
                self.current_stroke['points'].append(smoothed_pos)
            else:
                self.current_stroke['points'].append(pos)
            
        self.current_stroke['pressures'].append(pressure)
    
    def _should_update(self):
        """Her zaman güncelle - throttling YOK"""
        return True
            
    def finish_stroke(self):
        """Serbest çizimi tamamla (optimized)"""
        if self.is_drawing and self.current_stroke and len(self.current_stroke['points']) > 1:
            stroke_data = self.current_stroke.copy()
            self.current_stroke = None
            self.is_drawing = False
            self.smoothing_buffer = []
            return stroke_data
        else:
            self.current_stroke = None
            self.is_drawing = False
            self.smoothing_buffer = []
            return None
            
    def cancel_stroke(self):
        """Aktif çizimi iptal et"""
        self.current_stroke = None
        self.is_drawing = False
        self.smoothing_buffer = []
        
    def draw_stroke(self, painter, stroke_data):
        """Tamamlanmış serbest çizimi çiz (optimized)"""
        if stroke_data['type'] != 'freehand':
            return
            
        points = stroke_data['points']
        
        if len(points) < 2:
            return
            
        # Serbest çizim için renk ve kalınlık
        color = stroke_data.get('color', Qt.GlobalColor.black)
        width = stroke_data.get('width', 2)
        brush_mode = stroke_data.get('brush_mode', 'simple')
        advanced_style = stroke_data.get('advanced_style', 'solid')
        
        # Color string ise QColor'a çevir
        from PyQt6.QtGui import QColor
        if isinstance(color, str):
            color = QColor(color)
            
        # QPointF listesine çevir
        qpoint_list = [ensure_qpointf(p) for p in points]

        if len(qpoint_list) >= 2:
            path = QPainterPath(qpoint_list[0])
            for qp in qpoint_list[1:]:
                path.lineTo(qp)
            ShadowRenderer.draw_shape_shadow(painter, 'path', path, stroke_data)

        # Brush mode'a göre çiz
        if brush_mode == 'advanced':
            AdvancedBrush.draw_pen_stroke(painter, qpoint_list, color, width, advanced_style)
        else:
            # Varsayılan hızlı çizim - tablet mode bilgisini stroke'tan al
            tablet_mode = stroke_data.get('tablet_mode', False)
            line_style = stroke_data.get('style', Qt.PenStyle.SolidLine)
            if isinstance(line_style, int):
                line_style = Qt.PenStyle(line_style)
            SimpleBrush.draw_simple_stroke(painter, qpoint_list, color, width, tablet_mode, line_style)
    
    def set_color(self, color):
        """Aktif rengi ayarla"""
        self.current_color = color
            
    def draw_current_stroke(self, painter):
        """Aktif olarak çizilen serbest çizimi çiz (optimized)"""
        if not self.is_drawing or not self.current_stroke or len(self.current_stroke['points']) < 2:
            return

        points = self.current_stroke['points']

        qpoint_list = [ensure_qpointf(p) for p in points]
        if len(qpoint_list) >= 2:
            preview_data = {
                'type': 'freehand',
                'width': self.current_width,
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
            path = QPainterPath(qpoint_list[0])
            for qp in qpoint_list[1:]:
                path.lineTo(qp)
            ShadowRenderer.draw_shape_shadow(painter, 'path', path, preview_data)

        # Aktif çizim için her zaman simple brush kullan (performans)
        tablet_mode = self.current_stroke.get('tablet_mode', False)
        SimpleBrush.draw_simple_stroke(painter, points, self.current_color, self.current_width, tablet_mode, self.line_style)
    
    def set_width(self, width):
        """Aktif çizgi kalınlığını ayarla"""
        self.current_width = width
        
    def set_line_style(self, style):
        """Çizgi stilini ayarla"""
        self.line_style = style
        
    def set_brush_mode(self, mode):
        """Brush mode ayarla: 'simple' veya 'advanced'"""
        if mode in ['simple', 'advanced']:
            self.brush_mode = mode
            
    def set_advanced_style(self, style):
        """Advanced brush style ayarla"""
        if style in ['solid', 'dashed', 'dotted', 'dashdot', 'zigzag', 'double']:
            self.advanced_style = style

    def get_brush_mode(self):
        """Aktif brush mode'unu döndür"""
        return self.brush_mode

    def get_advanced_style(self):
        """Aktif advanced style'ı döndür"""
        return self.advanced_style

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