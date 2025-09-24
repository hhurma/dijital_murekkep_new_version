from PyQt6.QtCore import QPointF, QRectF
from stroke_handler import StrokeHandler
from grid_snap_utils import GridSnapUtils
import numpy as np

class MoveTool:
    def __init__(self):
        self.is_moving = False
        self.last_pos = None
        self.start_pos = None
        self.background_settings = None  # Grid snap için
        self.grid_settings = None  # Tek kaynak snap ayarları
        self.shift_constrain = False  # Shift tuşu ile snap zorlaması
        self._selection_bounds_start = None  # Başlangıçta seçimin bounding rect'i
        self._click_offset_from_topleft = None  # Tıklama noktasının bounding rect sol-üst'ünden ofseti
        
    def start_move(self, pos, strokes=None, selected_strokes=None):
        """Taşıma işlemini başlat"""
        self.is_moving = True
        self.last_pos = QPointF(pos)
        self.start_pos = QPointF(pos)
        
        # Seçimin bounding rect'ini hesapla ve tıklama ofsetini kaydet
        if strokes is not None and selected_strokes:
            bounds = self._get_selection_bounding_rect(strokes, selected_strokes)
            if bounds is not None:
                self._selection_bounds_start = bounds
                # Tıklama noktasının bounding rect sol-üst köşesinden ofseti (grup alanına KENETLE)
                raw_off_x = pos.x() - bounds.left()
                raw_off_y = pos.y() - bounds.top()
                off_x = min(max(0.0, raw_off_x), bounds.width())
                off_y = min(max(0.0, raw_off_y), bounds.height())
                self._click_offset_from_topleft = QPointF(off_x, off_y)
            else:
                self._selection_bounds_start = None
                self._click_offset_from_topleft = None
        else:
            self._selection_bounds_start = None
            self._click_offset_from_topleft = None
        
    def update_move(self, pos, strokes, selected_strokes):
        """Seçilen stroke'ları taşı"""
        if not self.is_moving or not selected_strokes:
            return False
            
        # Bounding rect tabanlı taşıma: click offset'i korunarak yeni sol-üst hesapla
        if self._click_offset_from_topleft is None:
            # Fallback: basit delta
            delta = pos - self.last_pos
            self.last_pos = QPointF(pos)
        else:
            # Yeni sol-üst pozisyonu = mouse - click_offset
            new_top_left = QPointF(
                pos.x() - self._click_offset_from_topleft.x(),
                pos.y() - self._click_offset_from_topleft.y()
            )
            
            # Snap uygula (kenetli top-left için) - tek kaynak grid_settings
            force_snap = getattr(self, 'shift_constrain', False) and not getattr(self, 'grid_settings', {}).get('snap_to_grid', False)
            snap_enabled = (
                hasattr(self, 'grid_settings') and self.grid_settings and 
                (self.grid_settings.get('snap_to_grid', False) or force_snap)
            )
            if snap_enabled:
                new_top_left = GridSnapUtils.snap_point_to_grid_precise(new_top_left, self.grid_settings)
            
            # Delta = yeni sol-üst - başlangıç sol-üst
            delta = QPointF(
                new_top_left.x() - self._selection_bounds_start.left(),
                new_top_left.y() - self._selection_bounds_start.top()
            )
            
            # 0,0 dışındaki çok küçük jitter'ları yok say
            if abs(delta.x()) < 0.25:
                delta.setX(0.0)
            if abs(delta.y()) < 0.25:
                delta.setY(0.0)

            # Başlangıç bounds'unu güncelle (bir sonraki delta için)
            self._selection_bounds_start = QRectF(
                new_top_left.x(), new_top_left.y(),
                self._selection_bounds_start.width(), self._selection_bounds_start.height()
            )
            self.last_pos = QPointF(pos)
        
        if abs(delta.x()) < 0.001 and abs(delta.y()) < 0.001:
            return False
            
        # Tüm seçili stroke'ları taşı
        for selected_stroke in selected_strokes:
            if selected_stroke < len(strokes):
                stroke_data = strokes[selected_stroke]
                
                # Image stroke kontrolü
                if hasattr(stroke_data, 'stroke_type') and stroke_data.stroke_type == 'image':
                    # Resim pozisyonunu güncelle
                    current_pos = stroke_data.position
                    new_pos = QPointF(current_pos.x() + delta.x(), current_pos.y() + delta.y())
                    stroke_data.set_position(new_pos)
                    continue
                
                # Güvenlik kontrolü - eski stroke'lar için
                if hasattr(stroke_data, 'get') and 'type' not in stroke_data:
                    continue
                elif hasattr(stroke_data, 'get'):
                    # Yeni hassas move_stroke fonksiyonunu kullan
                    self.move_stroke_precise(stroke_data, delta)
            
        return True
        
    def finish_move(self):
        """Taşıma işlemini tamamla"""
        self.is_moving = False
        self.last_pos = None
        self.start_pos = None
        self._selection_bounds_start = None
        self._click_offset_from_topleft = None
        
    def cancel_move(self, strokes, selected_strokes):
        """Taşıma işlemini iptal et - başlangıç pozisyonuna geri dön"""
        if not self.start_pos or not selected_strokes:
            return
            
        # Başlangıçtan şimdiye kadar olan toplam hareketi hesapla
        if self.last_pos:
            total_delta = self.last_pos - self.start_pos
            
            # Tüm seçili stroke'ları ters yönde hareket ettir
            for selected_stroke in selected_strokes:
                if selected_stroke < len(strokes):
                    stroke_data = strokes[selected_stroke]
                    
                    # Image stroke kontrolü
                    if hasattr(stroke_data, 'stroke_type') and stroke_data.stroke_type == 'image':
                        # Resim pozisyonunu ters yönde güncelle
                        current_pos = stroke_data.position
                        new_pos = QPointF(current_pos.x() - total_delta.x(), current_pos.y() - total_delta.y())
                        stroke_data.set_position(new_pos)
                        continue
                    
                    # Güvenlik kontrolü - eski stroke'lar için
                    if hasattr(stroke_data, 'get') and 'type' not in stroke_data:
                        continue
                    elif hasattr(stroke_data, 'get'):
                        StrokeHandler.move_stroke(stroke_data, -total_delta.x(), -total_delta.y())
                
        self.finish_move()
        
    def set_background_settings(self, settings):
        """Arka plan ayarlarını güncelle (grid snap için)"""
        self.background_settings = settings 

    def move_stroke_precise(self, stroke, delta):
        """Stroke'u belirtilen miktarda hareket ettir"""
        stroke_type = stroke.get('type', '')
        
        if stroke_type == 'freehand':
            if 'points' in stroke:
                # Serbest çizimler için her noktayı ayrı ayrı snap'leme, sadece delta'yı uygula
                for i, point in enumerate(stroke['points']):
                    # Point QPointF veya dict formatında olabilir
                    if isinstance(point, dict):
                        point['x'] += delta.x()
                        point['y'] += delta.y()
                    else:
                        # QPointF formatında
                        from stroke_handler import ensure_qpointf
                        point_qf = ensure_qpointf(point)
                        new_point = QPointF(point_qf.x() + delta.x(), point_qf.y() + delta.y())
                        stroke['points'][i] = new_point
        
        elif stroke_type == 'bspline':
            # B-spline için hem edit_points hem control_points taşınmalı
            if 'edit_points' in stroke:
                for ep in stroke['edit_points']:
                    ep[0] += delta.x()
                    ep[1] += delta.y()
            if 'control_points' in stroke:
                for cp in stroke['control_points']:
                    cp[0] += delta.x()
                    cp[1] += delta.y()
        
        elif stroke_type == 'line':
            if 'start_point' in stroke:
                start = list(stroke['start_point'])
                start[0] += delta.x()
                start[1] += delta.y()
                stroke['start_point'] = tuple(start)
            
            if 'end_point' in stroke:
                end = list(stroke['end_point'])
                end[0] += delta.x()
                end[1] += delta.y()
                stroke['end_point'] = tuple(end)
        
        elif stroke_type == 'rectangle':
            if 'corners' in stroke:
                for i, corner in enumerate(stroke['corners']):
                    corner_list = list(corner)
                    corner_list[0] += delta.x()
                    corner_list[1] += delta.y()
                    stroke['corners'][i] = tuple(corner_list)
            elif 'top_left' in stroke and 'bottom_right' in stroke:
                # Eski format desteği
                tl = list(stroke['top_left'])
                br = list(stroke['bottom_right'])
                
                tl[0] += delta.x()
                tl[1] += delta.y()
                br[0] += delta.x()
                br[1] += delta.y()
                
                stroke['top_left'] = tuple(tl)
                stroke['bottom_right'] = tuple(br)
        
        elif stroke_type == 'circle':
            if 'center' in stroke:
                center = list(stroke['center'])
                center[0] += delta.x()
                center[1] += delta.y()
                stroke['center'] = tuple(center)

    def _get_selection_bounding_rect(self, strokes, selected_strokes):
        """Seçilen stroke'ların gerçek bounding rect'ini hesapla (padding yok)"""
        if not selected_strokes:
            return None
            
        min_x = None
        max_x = None
        min_y = None
        max_y = None
        
        for stroke_index in selected_strokes:
            if stroke_index < len(strokes):
                stroke_data = strokes[stroke_index]
                
                # Image stroke kontrolü
                if hasattr(stroke_data, 'stroke_type') and stroke_data.stroke_type == 'image':
                    bounds = stroke_data.get_bounds()
                    if min_x is None:
                        min_x = bounds.left()
                        max_x = bounds.right()
                        min_y = bounds.top()
                        max_y = bounds.bottom()
                    else:
                        min_x = min(min_x, bounds.left())
                        max_x = max(max_x, bounds.right())
                        min_y = min(min_y, bounds.top())
                        max_y = max(max_y, bounds.bottom())
                    continue
                
                # Güvenlik kontrolü - eski stroke'lar için
                if 'type' not in stroke_data:
                    continue
                    
                points = StrokeHandler.get_stroke_points(stroke_data)
                for point in points:
                    x, y = point[0], point[1]
                    if min_x is None:
                        min_x = max_x = x
                        min_y = max_y = y
                    else:
                        min_x = min(min_x, x)
                        max_x = max(max_x, x)
                        min_y = min(min_y, y)
                        max_y = max(max_y, y)
                
        if min_x is None:
            return None
            
        return QRectF(min_x, min_y, max_x - min_x, max_y - min_y)