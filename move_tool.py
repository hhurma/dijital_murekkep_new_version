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
            
        # Grid snap uygula
        if (self.background_settings and 
            self.background_settings.get('snap_to_grid', False)):
            pos = GridSnapUtils.snap_point_to_grid(pos, self.background_settings)
            
        # Hareket vektörü
        delta = pos - self.last_pos
        
        # Tüm seçili stroke'ları taşı
        for selected_stroke in selected_strokes:
            if selected_stroke < len(strokes):
                stroke_data = strokes[selected_stroke]
                # Güvenlik kontrolü - eski stroke'lar için
                if 'type' not in stroke_data:
                    continue
                StrokeHandler.move_stroke(stroke_data, delta.x(), delta.y())
            
        self.last_pos = pos
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