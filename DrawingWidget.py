from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QMouseEvent, QPainterPath, QColor, QBrush, QTabletEvent
from PyQt6.QtCore import Qt, QPoint, QPointF, QRect, QRectF
from scipy.interpolate import splprep, splev
import numpy as np
import time
from tablet_handler import TabletHandler
from event_handler import EventHandler
from canvas_renderer import CanvasRenderer
from throttle_manager import ThrottleManager

# Araç modüllerini import et
from selection_tool import SelectionTool
from move_tool import MoveTool
from rotate_tool import RotateTool
from scale_tool import ScaleTool
from bspline_tool import BSplineTool
from freehand_tool import FreehandTool
from line_tool import LineTool
from rectangle_tool import RectangleTool
from circle_tool import CircleTool
from stroke_handler import StrokeHandler

class DrawingWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        # A4 boyutları (100 DPI'da piksel cinsinden - daha küçük)
        # A4: 210x297 mm = 8.27x11.69 inch
        # Portrait: 827x1169, Landscape: 1169x827
        self.a4_width_portrait = 827
        self.a4_height_portrait = 1169
        self.a4_width_landscape = 1169
        self.a4_height_landscape = 827
        
        # Varsayılan olarak yatay (landscape)
        self.canvas_orientation = 'landscape'
        self.update_canvas_size()
        
        self.strokes = [] # Stores all stroke data (farklı araç türleri)
        self.setMouseTracking(True) # Enable tracking even when no button is pressed
        
        # Aktif araç
        self.active_tool = "bspline"  # "bspline", "freehand", "select", "move", "rotate", "scale"
        
        # Aktif renk
        from PyQt6.QtCore import Qt
        self.current_color = Qt.GlobalColor.black
        self.current_width = 2
        self.current_fill = False
        self.current_opacity = 1.0
        self.fill_color = Qt.GlobalColor.white  # Dolgu rengi
        self.line_style = Qt.PenStyle.SolidLine  # Çizgi stili
        self.undo_manager = None
        
        # Arka plan ayarları
        self.background_settings = {
            'type': 'solid',
            'background_color': Qt.GlobalColor.white,
            'grid_color': Qt.GlobalColor.lightGray,
            'grid_size': 20,
            'grid_width': 1
        }
        
        # Araç örnekleri
        self.selection_tool = SelectionTool()
        self.move_tool = MoveTool()
        self._move_state_saved = False  # Move için state kaydedildi mi
        self.rotate_tool = RotateTool()
        self._rotate_state_saved = False  # Rotate için state kaydedildi mi
        self.scale_tool = ScaleTool()
        self._scale_state_saved = False  # Scale için state kaydedildi mi
        self.bspline_tool = BSplineTool()  # B-spline aracı
        self.freehand_tool = FreehandTool()  # Serbest çizim aracı
        self.line_tool = LineTool()  # Düz çizgi aracı
        self.rectangle_tool = RectangleTool()  # Dikdörtgen aracı
        self.circle_tool = CircleTool()  # Çember aracı
        
        # Ana pencere referansı
        self.main_window = None
        
        # Zoom ayarları - varsayılan %200
        self.zoom_level = 2.0
        self.zoom_offset = QPointF(0, 0)  # Pan offset
        
        # Pan ayarları
        self.is_panning = False
        self.pan_start_point = QPointF(0, 0)
        
        # Tablet handler
        self.tablet_handler = TabletHandler()
        self.setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, False)  # Touch events'i devre dışı bırak
        
        # Event handler
        self.event_handler = EventHandler(self)
        
        # Canvas renderer
        self.canvas_renderer = CanvasRenderer(self)
        
        # Throttle manager
        self.throttle_manager = ThrottleManager(self)
        
        # Eski stroke'ları temizle ve yeni formatla başla
        self.clear_all_strokes()
        
    def set_main_window(self, main_window):
        """Ana pencere referansını ayarla"""
        self.main_window = main_window
        
    def update_canvas_size(self):
        """Canvas boyutunu mevcut yönlendirmeye göre güncelle"""
        if self.canvas_orientation == 'landscape':
            self.setFixedSize(self.a4_width_landscape, self.a4_height_landscape)
        else:
            self.setFixedSize(self.a4_width_portrait, self.a4_height_portrait)
        self.update()
        
    def set_canvas_orientation(self, orientation):
        """Canvas yönünü ayarla (portrait/landscape)"""
        if orientation in ['portrait', 'landscape']:
            self.canvas_orientation = orientation
            self.update_canvas_size()
            
    def get_canvas_orientation(self):
        """Canvas yönünü döndür"""
        return self.canvas_orientation
        
    def set_active_tool(self, tool_name):
        """Aktif aracı ayarla"""
        self.active_tool = tool_name
        
        # Araç değiştikten sonra ilgili tutamakları oluştur
        if tool_name == "rotate" and self.selection_tool.selected_strokes:
            self.rotate_tool.create_rotation_handles(self.strokes, self.selection_tool.selected_strokes)
        elif tool_name == "scale" and self.selection_tool.selected_strokes:
            self.scale_tool.create_scale_handles(self.strokes, self.selection_tool.selected_strokes)
            
        self.update()
        
    def set_current_color(self, color):
        """Aktif rengi ayarla ve araçlara bildir"""
        self.current_color = color
        
        # Tüm çizim araçlarına rengi bildir
        if hasattr(self.bspline_tool, 'set_color'):
            self.bspline_tool.set_color(color)
        if hasattr(self.freehand_tool, 'set_color'):
            self.freehand_tool.set_color(color)
        if hasattr(self.line_tool, 'set_color'):
            self.line_tool.set_color(color)
        if hasattr(self.rectangle_tool, 'set_line_color'):
            self.rectangle_tool.set_line_color(color)
        if hasattr(self.circle_tool, 'set_line_color'):
            self.circle_tool.set_line_color(color)
            
    def set_current_width(self, width):
        """Aktif çizgi kalınlığını ayarla ve araçlara bildir"""
        self.current_width = width
        
        # Tüm çizim araçlarına kalınlığı bildir
        if hasattr(self.bspline_tool, 'set_width'):
            self.bspline_tool.set_width(width)
        if hasattr(self.freehand_tool, 'set_width'):
            self.freehand_tool.set_width(width)
        if hasattr(self.line_tool, 'set_width'):
            self.line_tool.set_width(width)
        if hasattr(self.rectangle_tool, 'set_line_width'):
            self.rectangle_tool.set_line_width(width)
        if hasattr(self.circle_tool, 'set_line_width'):
            self.circle_tool.set_line_width(width)
            
    def set_current_fill(self, filled):
        """Aktif fill durumunu ayarla ve araçlara bildir"""
        self.current_fill = filled
        
        # Şekil araçlarına fill durumunu bildir
        if hasattr(self.rectangle_tool, 'set_filled'):
            self.rectangle_tool.set_filled(filled)
        if hasattr(self.circle_tool, 'set_filled'):
            self.circle_tool.set_filled(filled)
            
    def set_current_opacity(self, opacity):
        """Aktif opacity'yi ayarla ve araçlara bildir"""
        self.current_opacity = opacity
        
        # Şekil araçlarına opacity bildir
        if hasattr(self.rectangle_tool, 'set_fill_opacity'):
            self.rectangle_tool.set_fill_opacity(opacity)
        if hasattr(self.circle_tool, 'set_fill_opacity'):
            self.circle_tool.set_fill_opacity(opacity)
            
    def set_fill_color(self, color):
        """Dolgu rengini ayarla ve araçlara bildir"""
        from PyQt6.QtGui import QColor
        self.fill_color = QColor(color)
        
        # Şekil araçlarına dolgu rengi bildir
        if hasattr(self.rectangle_tool, 'set_fill_color'):
            self.rectangle_tool.set_fill_color(self.fill_color)
        if hasattr(self.circle_tool, 'set_fill_color'):
            self.circle_tool.set_fill_color(self.fill_color)
            
    def set_line_style(self, style):
        """Çizgi stilini ayarla ve araçlara bildir"""
        self.line_style = style
        
        # Tüm çizim araçlarına stili bildir
        if hasattr(self.bspline_tool, 'set_line_style'):
            self.bspline_tool.set_line_style(style)
        if hasattr(self.freehand_tool, 'set_line_style'):
            self.freehand_tool.set_line_style(style)
        if hasattr(self.line_tool, 'set_line_style'):
            self.line_tool.set_line_style(style)
        if hasattr(self.rectangle_tool, 'set_line_style'):
            self.rectangle_tool.set_line_style(style)
        if hasattr(self.circle_tool, 'set_line_style'):
            self.circle_tool.set_line_style(style)
            
    def set_background_settings(self, settings):
        """Arka plan ayarlarını güncelle"""
        self.background_settings = settings
        
        # Snap-destekli araçlara arka plan ayarlarını bildir
        if hasattr(self.line_tool, 'set_background_settings'):
            self.line_tool.set_background_settings(settings)
        if hasattr(self.rectangle_tool, 'set_background_settings'):
            self.rectangle_tool.set_background_settings(settings)
        if hasattr(self.circle_tool, 'set_background_settings'):
            self.circle_tool.set_background_settings(settings)
        
        # Dönüştürme araçlarına da arka plan ayarlarını bildir
        if hasattr(self.rotate_tool, 'set_background_settings'):
            self.rotate_tool.set_background_settings(settings)
        if hasattr(self.scale_tool, 'set_background_settings'):
            self.scale_tool.set_background_settings(settings)
        if hasattr(self.move_tool, 'set_background_settings'):
            self.move_tool.set_background_settings(settings)
            
        self.update()  # Yeniden çiz
            
    def set_undo_manager(self, undo_manager):
        """Undo/Redo manager'ı ayarla"""
        self.undo_manager = undo_manager
        # İlk durumu kaydet
        self.save_current_state("Initial state")
    
    def set_zoom_level(self, zoom_level):
        """Zoom seviyesini ayarla"""
        self.zoom_level = zoom_level
        self.update()
    
    def get_zoom_level(self):
        """Mevcut zoom seviyesini döndür"""
        return self.zoom_level
    
    def set_pan_offset(self, offset):
        """Pan offset'ini ayarla"""
        self.zoom_offset = QPointF(offset)
        self.update()
    
    def get_pan_offset(self):
        """Pan offset'ini döndür"""
        return self.zoom_offset
    
    def transform_mouse_pos(self, pos):
        """Mouse pozisyonunu zoom ve pan'e göre dönüştür"""
        # Main window'dan güncel zoom ve pan değerlerini al
        current_zoom = self.zoom_level
        current_offset = self.zoom_offset
        
        if self.main_window and hasattr(self.main_window, 'zoom_widget'):
            current_zoom = self.main_window.zoom_widget.get_zoom_level()
            current_offset = self.main_window.zoom_widget.get_pan_offset()
        
        # Önce pan offset'ini çıkar, sonra zoom'u tersine çevir
        transformed_x = (pos.x() - current_offset.x()) / current_zoom
        transformed_y = (pos.y() - current_offset.y()) / current_zoom
        return QPointF(transformed_x, transformed_y)
    
    def set_zoom_level(self, zoom_level):
        """Zoom seviyesini ayarla"""
        self.zoom_level = zoom_level
        self.update()
    
    def set_pan_offset(self, pan_offset):
        """Pan offset'ini ayarla"""
        self.zoom_offset = pan_offset
        self.update()
        
    def save_current_state(self, description="Action"):
        """Mevcut durumu undo manager'a kaydet"""
        if self.undo_manager:
            self.undo_manager.save_state(self.strokes, description)
            
    def undo(self):
        """Geri al"""
        if self.undo_manager:
            previous_state = self.undo_manager.undo()
            if previous_state is not None:
                self.strokes = previous_state
                self.update()
                # Seçimi temizle
                self.selection_tool.clear_selection()

    def redo(self):
        """İleri al"""
        if self.undo_manager:
            next_state = self.undo_manager.redo()
            if next_state is not None:
                self.strokes = next_state
                self.update()
                        # Seçimi temizle
        self.selection_tool.clear_selection()
        # Shape properties dock'unu kapat
        self.update_shape_properties()

    def update_shape_properties(self):
        """Seçim değiştiğinde shape properties dock'unu güncelle"""
        if self.main_window and hasattr(self.main_window, 'shape_properties_widget'):
            selected_strokes = self.selection_tool.selected_strokes
            
            if selected_strokes:
                # Seçim var - dock'u göster ve güncelle
                self.main_window.shape_properties_widget.set_selected_strokes(selected_strokes, self.strokes)
                if hasattr(self.main_window, 'shape_properties_dock'):
                    self.main_window.shape_properties_dock.show()
            else:
                # Seçim yok - dock'u gizle
                self.main_window.shape_properties_widget.set_no_selection()
                if hasattr(self.main_window, 'shape_properties_dock'):
                    self.main_window.shape_properties_dock.hide()

    def clear_all_strokes(self):
        """Tüm çizimleri temizle"""
        if self.strokes:  # Sadece çizim varsa kaydet
            self.save_current_state("Clear all")
        self.strokes = []
        self.bspline_tool.cancel_stroke()  # Aktif B-spline çizimi de temizle
        self.freehand_tool.cancel_stroke()  # Aktif serbest çizimi de temizle
        self.line_tool.cancel_stroke()  # Aktif çizgi çizimi de temizle
        self.rectangle_tool.cancel_stroke()  # Aktif dikdörtgen çizimi de temizle
        self.circle_tool.cancel_stroke()  # Aktif çember çizimi de temizle
        self.selection_tool.clear_selection()
        self.update()

    def keyPressEvent(self, event):
        """Klavye olayını event handler'a yönlendir"""
        self.event_handler.handle_key_press(event)
        super().keyPressEvent(event)
        
    def keyReleaseEvent(self, event):
        """Klavye olayını event handler'a yönlendir"""
        self.event_handler.handle_key_release(event)
        super().keyReleaseEvent(event)
    
    def wheelEvent(self, event):
        """Mouse wheel olayını event handler'a yönlendir"""
        self.event_handler.handle_wheel(event)

    def mousePressEvent(self, event: QMouseEvent):
        """Mouse press olayını event handler'a yönlendir"""
        self.event_handler.handle_mouse_press(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        """Mouse move olayını event handler'a yönlendir"""
        self.event_handler.handle_mouse_move(event)
                
    def _throttled_update(self):
        """Akıllı throttling - ThrottleManager'a yönlendir"""
        self.throttle_manager.throttled_update()
            
    def _throttled_freehand_update(self):
        """Freehand için minimal throttling - ThrottleManager'a yönlendir"""
        self.throttle_manager.throttled_freehand_update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Mouse release olayını event handler'a yönlendir"""
        self.event_handler.handle_mouse_release(event)
                
    def tabletEvent(self, event: QTabletEvent):
        """Tablet olayını event handler'a yönlendir"""
        self.event_handler.handle_tablet_event(event)
        
    # Tablet handle metodları EventHandler'a taşındı
        
    def _throttled_tablet_update(self):
        """Tablet için akıllı throttling - ThrottleManager'a yönlendir"""
        self.throttle_manager.throttled_tablet_update()

    # Tool handle metodları EventHandler'a taşındı

    def preview_selection(self):
        """Seçim dikdörtgeni sırasında preview göster"""
        if not self.selection_tool.is_selecting or not self.selection_tool.selection_rect:
            return
            
        # Geçici seçim listesi oluştur (asıl seçimi değiştirmez)
        temp_selected = list(self.selection_tool.selected_strokes) if self.selection_tool.ctrl_pressed else []
        
        for stroke_index, stroke_data in enumerate(self.strokes):
            if stroke_index in temp_selected:
                continue
                
            # Image stroke kontrolü
            if hasattr(stroke_data, 'stroke_type') and stroke_data.stroke_type == 'image':
                # Resim için basit bounding rect kontrolü
                bounds = stroke_data.get_bounds()
                if self.selection_tool.selection_rect.intersects(bounds):
                    temp_selected.append(stroke_index)
                continue
                
            # Güvenlik kontrolü - eski stroke'lar için
            if hasattr(stroke_data, 'get') and 'type' not in stroke_data:
                continue
            elif hasattr(stroke_data, 'get'):
                # Modüler stroke seçim kontrolü
                stroke_selected = StrokeHandler.is_stroke_in_rect(stroke_data, self.selection_tool.selection_rect)
                
                # B-spline için eğri kesişimi de kontrol et
                if not stroke_selected and stroke_data['type'] == 'bspline':
                    stroke_selected = self.selection_tool.check_curve_intersection(stroke_data, self.selection_tool.selection_rect)
                    
                if stroke_selected:
                    temp_selected.append(stroke_index)
                 
        # Preview listesini güncelle
        self.selection_tool.set_preview_strokes(temp_selected)

    # Geri kalan handle metodları EventHandler'a taşındı

    def paintEvent(self, event):
        """Paint olayını canvas renderer'a yönlendir"""
        self.canvas_renderer.paint_event(event)
            
    # Render metodları CanvasRenderer'a taşındı
            
    # Background render metodları CanvasRenderer'a taşındı
             
    def render(self, painter):
        """PDF export için özel render metodu - CanvasRenderer'a yönlendir"""
        self.canvas_renderer.render(painter)
