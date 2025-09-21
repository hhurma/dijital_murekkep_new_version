from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QPen, QPainter, QPainterPath, QBrush
from PyQt6.QtCore import Qt, QPointF
from scipy.interpolate import splprep, splev
import numpy as np
from shadow_renderer import ShadowRenderer

class BSplineTool:
    def __init__(self):
        self.current_stroke = []  # Aktif çizim [(QPoint, pressure)]
        self.selected_control_point = None  # (stroke_index, cp_index)
        self.hovered_control_pos = None  # (x, y) hover edilen kontrol noktası
        self.is_drawing = False
        self.edit_mode = False  # Düzenleme modunda yeni çizim başlatma
        self.current_color = Qt.GlobalColor.black
        self.current_width = 2
        self.line_style = Qt.PenStyle.SolidLine
        self.show_control_points = False  # Kontrol noktalarının görünürlüğünü kontrol eden bayrak

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
        """Yeni bir çizim başlat"""
        self.current_stroke = [(pos, pressure)]
        self.is_drawing = True
        self.selected_control_point = None
        
    def add_point(self, pos, pressure=1.0):
        """Aktif çizime nokta ekle"""
        if self.is_drawing:
            self.current_stroke.append((pos, pressure))
            
    def finish_stroke(self):
        """Çizimi tamamla ve B-spline oluştur"""
        if not self.is_drawing or len(self.current_stroke) <= 1:
            self.current_stroke = []
            self.is_drawing = False
            return None
            
        # Benzersiz noktaları filtrele
        unique_points_with_pressure = [self.current_stroke[0]]
        for i in range(1, len(self.current_stroke)):
            if self.current_stroke[i][0] != self.current_stroke[i-1][0]:
                unique_points_with_pressure.append(self.current_stroke[i])
        
        if len(unique_points_with_pressure) > 3:
            # Noktaları downsample et
            downsampled_points_with_pressure = unique_points_with_pressure[::5]
            if len(downsampled_points_with_pressure) < 4:
                downsampled_points_with_pressure = unique_points_with_pressure
                
            # Sadece koordinatları al
            points_only = np.array([(p.x(), p.y()) for p, pressure in downsampled_points_with_pressure])
            # Kapalı mı? ilk ve son nokta yakınsa kapat
            try:
                start_p = downsampled_points_with_pressure[0][0]
                end_p = downsampled_points_with_pressure[-1][0]
                dx = float(end_p.x() - start_p.x())
                dy = float(end_p.y() - start_p.y())
                closed = (dx*dx + dy*dy) ** 0.5 <= 12.0  # ~3-4px tolerans
            except Exception:
                closed = False
            
            try:
                # B-spline hesapla
                # Kapalı eğrilerde dikiş bölgesinde yinelenen son noktayı düşür
                pts_for_edit = points_only
                if closed and len(points_only) >= 2:
                    dx = points_only[-1, 0] - points_only[0, 0]
                    dy = points_only[-1, 1] - points_only[0, 1]
                    if (dx*dx + dy*dy) ** 0.5 <= 12.0:
                        pts_for_edit = points_only[:-1]
                # Kapalı eğrilerde per=True ve İNTERPOLASYON (s=0) kullan
                if closed:
                    k = 3
                    s_factor = 0.0
                    # Not: Ek sarma yapma; per=True yeterli. Son-ilk aynıysa üstte düşürdük.
                    tck, u = splprep(pts_for_edit.T, s=s_factor, k=k, per=True)
                else:
                    s_factor = 0.0
                    k = min(3, max(1, len(points_only) - 1))
                    tck, u = splprep(points_only.T, s=s_factor, k=k, per=False)
                
                # Stroke data oluştur
                stroke_data = {
                    'type': 'bspline',  # Modüler sistem için 'type' anahtarı
                    # Kontrol noktaları: DÜZENLEME için kullanıcı noktaları (interpolasyon düğümleri)
                    'edit_points': points_only.tolist(),
                    # Uyum katsayıları: eski uyumluluk için saklıyoruz
                    'control_points': np.array(tck[1]).T.tolist(),
                    # JSON uyumu için numpy -> list
                    'knots': np.array(tck[0]).tolist(),
                    'degree': int(tck[2]),
                    'u': np.array(u).tolist(),
                    'original_points_with_pressure': downsampled_points_with_pressure,
                    'tool_type': 'bspline',  # Eski uyumluluk için
                    'color': self.current_color,
                    'width': self.current_width,
                    'style': (self.line_style.value if isinstance(self.line_style, Qt.PenStyle) else self.line_style),  # 'style' field'ını kullan
                    'show_control_points': self.show_control_points,  # Kontrol noktalarının görünürlüğü
                    'closed': closed,
                    # Dolgu alanları (kapalıysa sonradan doldurulabilir)
                    'fill': False,
                    'fill_color': self.current_color,
                    'fill_opacity': 1.0,
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
                    'join_style': Qt.PenJoinStyle.RoundJoin,
                    # Düzenlenebilir düğümler (kapalıysa son-ilk çakışması düşürülmüş)
                    'edit_points': pts_for_edit.tolist() if 'pts_for_edit' in locals() else points_only.tolist()
                }
                
                self.current_stroke = []
                self.is_drawing = False
                return stroke_data
                
            except ValueError as e:
                print(f"B-spline oluşturulamadı ({len(points_only)} nokta): {e}")
                
        else:
            print(f"Yeterli nokta yok ({len(unique_points_with_pressure)} nokta) - en az 4 gerekli.")
            
        self.current_stroke = []
        self.is_drawing = False
        return None
        
    def cancel_stroke(self):
        """Aktif çizimi iptal et"""
        self.current_stroke = []
        self.is_drawing = False
        self.selected_control_point = None
        
    def select_control_point(self, pos, strokes, tolerance=10):
        """Bir kontrol noktası seç"""
        pos_f = QPointF(pos)
        
        for stroke_index, stroke_data in enumerate(strokes):
            # Image stroke kontrolü
            if hasattr(stroke_data, 'stroke_type'):
                continue
                
            if stroke_data.get('type') != 'bspline' and stroke_data.get('tool_type') != 'bspline':
                continue
                
            # Kontrol noktaları görünür değilse seçilemesin
            if not stroke_data.get('show_control_points', False):
                continue
                
            control_points = stroke_data.get('edit_points', stroke_data['control_points'])
            for cp_index, cp in enumerate(control_points):
                cp_point = QPointF(cp[0], cp[1])
                if (pos_f - cp_point).manhattanLength() < tolerance:
                    self.selected_control_point = (stroke_index, cp_index)
                    return True
                    
        self.selected_control_point = None
        return False

    def hit_test_control_point(self, pos, strokes, tolerance=10):
        """Hover için kontrol noktası çakışmasını test et ve pozisyonu kaydet"""
        pos_f = QPointF(pos)
        for stroke_data in strokes:
            # Image stroke kontrolü
            if hasattr(stroke_data, 'stroke_type'):
                continue
            if stroke_data.get('type') != 'bspline' and stroke_data.get('tool_type') != 'bspline':
                continue
            if not stroke_data.get('show_control_points', False):
                continue
            control_points = stroke_data.get('edit_points', stroke_data['control_points'])
            for cp in control_points:
                cp_point = QPointF(cp[0], cp[1])
                if (pos_f - cp_point).manhattanLength() < tolerance:
                    self.hovered_control_pos = (cp_point.x(), cp_point.y())
                    return True
        self.hovered_control_pos = None
        return False
        
    def move_control_point(self, new_pos, strokes):
        """Seçili kontrol noktasını taşı"""
        if self.selected_control_point is None:
            return False
            
        stroke_index, cp_index = self.selected_control_point
        if stroke_index < len(strokes):
            stroke_data = strokes[stroke_index]
            # Image stroke kontrolü
            if hasattr(stroke_data, 'stroke_type'):
                return False
                
            if stroke_data.get('type') == 'bspline' or stroke_data.get('tool_type') == 'bspline':
                if 'edit_points' in stroke_data:
                    stroke_data['edit_points'][cp_index] = [new_pos.x(), new_pos.y()]
                else:
                    stroke_data['control_points'][cp_index] = [new_pos.x(), new_pos.y()]
                return True
                
        return False
        
    def clear_selection(self):
        """Kontrol noktası seçimini temizle"""
        self.selected_control_point = None
        
    def draw_current_stroke(self, painter):
        """Aktif çizimi çiz (basınç ile)"""
        if len(self.current_stroke) > 1:
            preview_data = {
                'type': 'bspline',
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

            path = QPainterPath(self.current_stroke[0][0])
            for i in range(1, len(self.current_stroke)):
                point, _ = self.current_stroke[i]
                path.lineTo(point)

            ShadowRenderer.draw_shape_shadow(painter, 'path', path, preview_data)

            painter.save()
            for i in range(len(self.current_stroke) - 1):
                point1, pressure1 = self.current_stroke[i]
                point2, pressure2 = self.current_stroke[i+1]
                pen_width = self.current_width + pressure1 * (self.current_width * 2)
                pen = QPen(self.current_color, pen_width, Qt.PenStyle.SolidLine,
                          Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
                painter.setPen(pen)
                painter.drawLine(point1, point2)
            painter.restore()
            
    def draw_bspline(self, painter, stroke_data):
        """B-spline çiz"""
        # Image stroke kontrolü
        if hasattr(stroke_data, 'stroke_type'):
            return
            
        if stroke_data.get('type') != 'bspline' and stroke_data.get('tool_type') != 'bspline':
            return
            
        # Eğer edit_points varsa, her çizimde spline'ı yeniden kurarak edit sonrası
        # interpolasyonlu ve pürüzsüz kapanış elde ederiz.
        edit_points = stroke_data.get('edit_points')
        if edit_points is not None:
            pts = np.array(edit_points, dtype=float)
            closed = bool(stroke_data.get('closed', False))
            try:
                if closed and len(pts) >= 4:
                    k = 3
                    wrapped = np.vstack([pts, pts[:k]])
                    s_factor = max(0.0, len(pts) * 0.3)
                    tck, u = splprep(wrapped.T, s=s_factor, k=k, per=True)
                else:
                    s_factor = len(pts) * 3.0
                    tck, u = splprep(pts.T, s=s_factor, k=min(3, max(1, len(pts)-1)), per=False)
            except Exception:
                # Düştüğünde eski tck'yi kullan
                tck = (np.array(stroke_data['knots']), np.array(stroke_data['control_points']).T, stroke_data['degree'])
                u = np.array(stroke_data['u'])
        else:
            control_points = stroke_data['control_points']
            knots = stroke_data['knots']
            degree = stroke_data['degree']
            u = stroke_data['u']
            tck = (np.array(knots), np.array(control_points).T, degree)
        
        # B-spline eğrisini çiz
        painter.save()
        color = stroke_data.get('color', Qt.GlobalColor.black)
        width = stroke_data.get('width', 2)
        line_style = stroke_data.get('style', Qt.PenStyle.SolidLine)
        
        # Color string ise QColor'a çevir
        from PyQt6.QtGui import QColor
        if isinstance(color, str):
            color = QColor(color)
        if isinstance(line_style, int):
            line_style = Qt.PenStyle(line_style)
            
        pen = QPen(color, width, line_style, 
                  Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        
        # u dizisini numpy yap
        if isinstance(u, list):
            u = np.array(u, dtype=float)
        
        # Örnekleme: kapalı eğrilerde dikiş köşesini önlemek için endpoint=False ve daha yoğun örnekleme kullan
        num_ctrl = int(np.array(tck[1]).T.shape[0])
        # Örnek sayısını kontrol noktası sayısına bağlı, ancak sınırlı tut
        base_samples = int(max(200, min(1000, num_ctrl * 40)))
        is_closed = bool(stroke_data.get('closed', False))
        # Kapalıda endpoint=False: son==ilk örneklemesini engelleyip tek hatlık çizim yap
        ts = np.linspace(0, u[-1], base_samples, endpoint=False)
        x_fine, y_fine = splev(ts, tck)
        path = QPainterPath()
        path.moveTo(QPointF(x_fine[0], y_fine[0]))
        for i in range(1, len(x_fine)):
            path.lineTo(QPointF(x_fine[i], y_fine[i]))
        # Kapalı eğri: son noktadan ilk noktaya yumuşak (cubic) bağ kur
        if is_closed and len(x_fine) >= 4:
            p_last = QPointF(x_fine[-1], y_fine[-1])
            p_prev1 = QPointF(x_fine[-2], y_fine[-2])
            p_first = QPointF(x_fine[0], y_fine[0])
            p_next1 = QPointF(x_fine[1], y_fine[1])
            # Türev tahmini (tangent)
            t_end = QPointF(p_last.x() - p_prev1.x(), p_last.y() - p_prev1.y())
            t_start = QPointF(p_next1.x() - p_first.x(), p_next1.y() - p_first.y())
            alpha = 0.35
            c1 = QPointF(p_last.x() + t_end.x() * alpha, p_last.y() + t_end.y() * alpha)
            c2 = QPointF(p_first.x() - t_start.x() * alpha, p_first.y() - t_start.y() * alpha)
            path.cubicTo(c1, c2, p_first)

        ShadowRenderer.draw_shape_shadow(painter, 'path', path, stroke_data)

        # Dolgu varsa fırçayı ayarla ve hem doldur hem çiz
        fill_enabled = bool(stroke_data.get('fill', False)) and stroke_data.get('closed', False)
        if fill_enabled:
            from PyQt6.QtGui import QColor
            fill_color = stroke_data.get('fill_color', Qt.GlobalColor.transparent)
            if isinstance(fill_color, str):
                fill_qc = QColor(fill_color)
            else:
                fill_qc = QColor(fill_color)
            # Opaklığı uygula
            try:
                op = float(stroke_data.get('fill_opacity', 1.0))
                op = max(0.0, min(1.0, op))
                fill_qc.setAlphaF(op)
            except Exception:
                pass
            painter.setBrush(QBrush(fill_qc))
        else:
            painter.setBrush(Qt.BrushStyle.NoBrush)

        painter.drawPath(path)
        painter.restore()
        
        # Kontrol noktalarını çiz (eğer görünürlük açıksa)
        show_points = stroke_data.get('show_control_points', False)
        if show_points:
            painter.save()
            # Hangi noktalar gösterilecek? Tercihen kullanıcı düğüm noktaları (edit_points)
            if edit_points is not None:
                control_points = edit_points
            else:
                try:
                    control_points = np.array(tck[1]).T.tolist()
                except Exception:
                    control_points = stroke_data.get('control_points', [])
            # Normal noktalar için stil
            normal_pen = QPen(Qt.GlobalColor.red, 1, Qt.PenStyle.SolidLine)
            normal_brush = QBrush(Qt.GlobalColor.white)
            hover_pen = QPen(Qt.GlobalColor.red, 2, Qt.PenStyle.SolidLine)
            hover_brush = QBrush(Qt.GlobalColor.red)
            radius = 4
            hovered = self.hovered_control_pos
            for cp in control_points:
                cx, cy = cp[0], cp[1]
                center = QPointF(cx, cy)
                is_hover = hovered is not None and abs(hovered[0] - cx) < 0.001 and abs(hovered[1] - cy) < 0.001
                if is_hover:
                    painter.setPen(hover_pen)
                    painter.setBrush(hover_brush)
                    r = radius + 1
                else:
                    painter.setPen(normal_pen)
                    painter.setBrush(normal_brush)
                    r = radius
                painter.drawEllipse(center, r, r)
            painter.restore()
        
    def set_color(self, color):
        """Aktif rengi ayarla"""
        self.current_color = color
        
    def set_width(self, width):
        """Aktif çizgi kalınlığını ayarla"""
        self.current_width = width
        
    def set_line_style(self, style):
        """Çizgi stilini ayarla"""
        self.line_style = style

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
    
    def draw_stroke(self, painter, stroke_data):
        """Tek bir B-spline stroke çiz (modüler sistem için)"""
        self.draw_bspline(painter, stroke_data)
    
    def draw_all_bsplines(self, painter, strokes):
        """Tüm B-spline'ları çiz"""
        for stroke_data in strokes:
            # Image stroke kontrolü
            if hasattr(stroke_data, 'stroke_type'):
                continue
                
            if stroke_data.get('type') == 'bspline' or stroke_data.get('tool_type') == 'bspline':
                self.draw_bspline(painter, stroke_data)
                
    def set_show_control_points(self, show):
        """Kontrol noktalarının görünürlüğünü ayarla"""
        self.show_control_points = show
        
    def toggle_control_points_visibility(self, stroke_data):
        """Belirli bir stroke'un kontrol noktalarının görünürlüğünü değiştir"""
        if stroke_data.get('type') == 'bspline' or stroke_data.get('tool_type') == 'bspline':
            current = stroke_data.get('show_control_points', False)
            stroke_data['show_control_points'] = not current
            return True
        return False 