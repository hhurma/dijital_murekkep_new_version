from PyQt6.QtCore import QPointF
from stroke_handler import StrokeHandler
from grid_snap_utils import GridSnapUtils
import numpy as np

class MoveTool:
    def __init__(self):
        self.is_moving = False
        self.last_pos = None
        self.start_pos = None
        self.background_settings = None  # Grid snap için
        
    def start_move(self, pos):
        """Taşıma işlemini başlat"""
        self.is_moving = True
        self.last_pos = pos
        self.start_pos = pos
        
    def update_move(self, pos, strokes, selected_strokes):
        """Seçilen stroke'ları taşı"""
        if not self.is_moving or not selected_strokes:
            return False
            
        # Grid snap uygula - daha hassas snap kullan
        snapped_pos = pos
        if (self.background_settings and 
            self.background_settings.get('snap_to_grid', False)):
            snapped_pos = GridSnapUtils.snap_point_to_grid_precise(pos, self.background_settings)
            
        # Hareket vektörü - snapped pozisyondan hesapla
        delta = snapped_pos - self.last_pos
        
        # Grid snap aktifse minimum hareket kontrolü
        if (self.background_settings and 
            self.background_settings.get('snap_to_grid', False)):
            # Çok küçük hareketleri atla
            if abs(delta.x()) < 1.0 and abs(delta.y()) < 1.0:
                return False
            
            # Delta'yı grid boyutuna göre ayarla
            grid_size = self.background_settings.get('grid_size', 20)
            delta_x = round(delta.x() / grid_size) * grid_size
            delta_y = round(delta.y() / grid_size) * grid_size
            delta = QPointF(delta_x, delta_y)
            
            # Sıfır hareket varsa çık
            if delta.x() == 0 and delta.y() == 0:
                return False
            
        # Tüm seçili stroke'ları taşı
        for selected_stroke in selected_strokes:
            if selected_stroke < len(strokes):
                stroke_data = strokes[selected_stroke]
                # Güvenlik kontrolü - eski stroke'lar için
                if 'type' not in stroke_data:
                    continue
                
                # Yeni hassas move_stroke fonksiyonunu kullan
                self.move_stroke_precise(stroke_data, delta)
            
        self.last_pos = snapped_pos  # Snapped pozisyonu kaydet
        return True
        
    def finish_move(self):
        """Taşıma işlemini tamamla"""
        self.is_moving = False
        self.last_pos = None
        self.start_pos = None
        
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
                    # Güvenlik kontrolü - eski stroke'lar için
                    if 'type' not in stroke_data:
                        continue
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
            if 'control_points' in stroke:
                for cp in stroke['control_points']:
                    cp[0] += delta.x()
                    cp[1] += delta.y()
                    
                    # Grid snap aktifse control point'i snap'le
                    if self.background_settings and self.background_settings.get('snap_to_grid', False):
                        snapped = GridSnapUtils.snap_point_to_grid_precise(
                            QPointF(cp[0], cp[1]), self.background_settings
                        )
                        cp[0] = snapped.x()
                        cp[1] = snapped.y()
        
        elif stroke_type == 'line':
            if 'start_point' in stroke:
                start = list(stroke['start_point'])
                start[0] += delta.x()
                start[1] += delta.y()
                
                # Grid snap aktifse endpoint'i snap'le
                if self.background_settings and self.background_settings.get('snap_to_grid', False):
                    snapped = GridSnapUtils.snap_point_to_grid_precise(
                        QPointF(start[0], start[1]), self.background_settings
                    )
                    start[0] = snapped.x()
                    start[1] = snapped.y()
                
                stroke['start_point'] = tuple(start)
            
            if 'end_point' in stroke:
                end = list(stroke['end_point'])
                end[0] += delta.x()
                end[1] += delta.y()
                
                # Grid snap aktifse endpoint'i snap'le
                if self.background_settings and self.background_settings.get('snap_to_grid', False):
                    snapped = GridSnapUtils.snap_point_to_grid_precise(
                        QPointF(end[0], end[1]), self.background_settings
                    )
                    end[0] = snapped.x()
                    end[1] = snapped.y()
                
                stroke['end_point'] = tuple(end)
        
        elif stroke_type == 'rectangle':
            if 'corners' in stroke:
                for i, corner in enumerate(stroke['corners']):
                    corner_list = list(corner)
                    corner_list[0] += delta.x()
                    corner_list[1] += delta.y()
                    
                    # Grid snap aktifse corner'ı snap'le
                    if self.background_settings and self.background_settings.get('snap_to_grid', False):
                        snapped = GridSnapUtils.snap_point_to_grid_precise(
                            QPointF(corner_list[0], corner_list[1]), self.background_settings
                        )
                        corner_list[0] = snapped.x()
                        corner_list[1] = snapped.y()
                    
                    stroke['corners'][i] = tuple(corner_list)
            elif 'top_left' in stroke and 'bottom_right' in stroke:
                # Eski format desteği
                tl = list(stroke['top_left'])
                br = list(stroke['bottom_right'])
                
                tl[0] += delta.x()
                tl[1] += delta.y()
                br[0] += delta.x()
                br[1] += delta.y()
                
                # Grid snap aktifse corner'ları snap'le
                if self.background_settings and self.background_settings.get('snap_to_grid', False):
                    snapped_tl = GridSnapUtils.snap_point_to_grid_precise(
                        QPointF(tl[0], tl[1]), self.background_settings
                    )
                    snapped_br = GridSnapUtils.snap_point_to_grid_precise(
                        QPointF(br[0], br[1]), self.background_settings
                    )
                    tl[0], tl[1] = snapped_tl.x(), snapped_tl.y()
                    br[0], br[1] = snapped_br.x(), snapped_br.y()
                
                stroke['top_left'] = tuple(tl)
                stroke['bottom_right'] = tuple(br)
        
        elif stroke_type == 'circle':
            if 'center' in stroke:
                center = list(stroke['center'])
                center[0] += delta.x()
                center[1] += delta.y()
                
                # Grid snap aktifse center'ı snap'le
                if self.background_settings and self.background_settings.get('snap_to_grid', False):
                    snapped = GridSnapUtils.snap_point_to_grid_precise(
                        QPointF(center[0], center[1]), self.background_settings
                    )
                    center[0] = snapped.x()
                    center[1] = snapped.y()
                
                stroke['center'] = tuple(center) 