from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QMouseEvent, QPainterPath, QColor, QBrush
from PyQt6.QtCore import Qt, QPoint, QPointF, QRect
from scipy.interpolate import splprep, splev
import numpy as np

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
        """Klavye tuşu basıldığında"""
        if event.key() == Qt.Key.Key_Control:
            self.selection_tool.set_ctrl_pressed(True)
        elif event.key() == Qt.Key.Key_Space and not self.is_panning:
            # Space tuşu ile pan modu
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().keyPressEvent(event)
        
    def keyReleaseEvent(self, event):
        """Klavye tuşu bırakıldığında"""
        if event.key() == Qt.Key.Key_Control:
            self.selection_tool.set_ctrl_pressed(False)
        elif event.key() == Qt.Key.Key_Space:
            # Space tuşu bırakıldığında normal cursor
            if not self.is_panning:
                self.setCursor(Qt.CursorShape.ArrowCursor)
        super().keyReleaseEvent(event)
    
    def wheelEvent(self, event):
        """Mouse wheel eventi - zoom için"""
        if self.main_window and hasattr(self.main_window, 'zoom_widget'):
            # Mouse pozisyonunu al
            mouse_pos = QPointF(event.position())
            
            # Wheel delta'ya göre zoom
            delta = event.angleDelta().y()
            if delta > 0:
                self.main_window.zoom_widget.wheel_zoom_in(mouse_pos)
            else:
                self.main_window.zoom_widget.wheel_zoom_out(mouse_pos)
        
        event.accept()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.MiddleButton:
            # Middle mouse button ile pan başlat
            self.is_panning = True
            self.pan_start_point = QPointF(event.pos())
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            return
        elif event.button() == Qt.MouseButton.LeftButton:
            pos = QPointF(event.pos())
            
            # Space tuşu basılıysa pan başlat
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier or \
               (hasattr(event, 'key') and event.key() == Qt.Key.Key_Space):
                self.is_panning = True
                self.pan_start_point = pos
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
                return
            
            # Ctrl tuşu durumunu güncelle
            self.selection_tool.set_ctrl_pressed(event.modifiers() & Qt.KeyboardModifier.ControlModifier)
            
            if self.active_tool == "bspline":
                # B-spline için özel event handling (transform içinde)
                self.handle_bspline_press(event)
            elif self.active_tool == "freehand":
                # Freehand için özel event handling (transform içinde)
                self.handle_freehand_press(event)
            elif self.active_tool == "line":
                # Line için özel event handling (transform içinde)
                self.handle_line_press(event)
            elif self.active_tool == "rectangle":
                # Rectangle için özel event handling (transform içinde)
                self.handle_rectangle_press(event)
            elif self.active_tool == "circle":
                # Circle için özel event handling (transform içinde)
                self.handle_circle_press(event)
            elif self.active_tool == "select":
                transformed_pos = self.transform_mouse_pos(pos)
                self.handle_select_press(transformed_pos)
            elif self.active_tool == "move":
                transformed_pos = self.transform_mouse_pos(pos)
                self.handle_move_press(transformed_pos)
            elif self.active_tool == "rotate":
                transformed_pos = self.transform_mouse_pos(pos)
                self.handle_rotate_press(transformed_pos)
            elif self.active_tool == "scale":
                transformed_pos = self.transform_mouse_pos(pos)
                self.handle_scale_press(transformed_pos)
            else:
                print(f"DEBUG: Bilinmeyen araç: '{self.active_tool}'")

    def mouseMoveEvent(self, event: QMouseEvent):
        pos = QPointF(event.pos())
        
        # Pan işlemi kontrol et
        if self.is_panning:
            if self.main_window and hasattr(self.main_window, 'zoom_widget'):
                # Pan delta hesapla
                delta = pos - self.pan_start_point
                current_offset = self.main_window.zoom_widget.get_pan_offset()
                new_offset = current_offset + delta
                self.main_window.zoom_widget.set_pan_offset(new_offset)
                self.pan_start_point = pos
            return
        
        if self.active_tool == "bspline":
            # B-spline için özel event handling (transform içinde)
            self.handle_bspline_move(event)
        elif self.active_tool == "freehand":
            # Freehand için özel event handling (transform içinde)
            self.handle_freehand_move(event)
        elif self.active_tool == "line":
            # Line için özel event handling (transform içinde)
            self.handle_line_move(event)
        elif self.active_tool == "rectangle":
            # Rectangle için özel event handling (transform içinde)
            self.handle_rectangle_move(event)
        elif self.active_tool == "circle":
            # Circle için özel event handling (transform içinde)
            self.handle_circle_move(event)
        elif self.active_tool == "select":
            if event.buttons() == Qt.MouseButton.LeftButton:
                transformed_pos = self.transform_mouse_pos(pos)
                self.handle_select_move(transformed_pos)
        elif self.active_tool == "move":
            if event.buttons() == Qt.MouseButton.LeftButton:
                transformed_pos = self.transform_mouse_pos(pos)
                self.handle_move_move(transformed_pos)
        elif self.active_tool == "rotate":
            # Her zaman mouse pozisyonunu güncelle (görsel feedback için)
            transformed_pos = self.transform_mouse_pos(pos)
            self.rotate_tool.set_current_mouse_pos(transformed_pos)
            if event.buttons() == Qt.MouseButton.LeftButton:
                self.handle_rotate_move(transformed_pos)
            else:
                # Sadece mouse tracking için update
                self.update()
        elif self.active_tool == "scale":
            # Her zaman mouse pozisyonunu güncelle (görsel feedback için)
            transformed_pos = self.transform_mouse_pos(pos)
            self.scale_tool.set_current_mouse_pos(transformed_pos)
            if event.buttons() == Qt.MouseButton.LeftButton:
                self.handle_scale_move(transformed_pos)
            else:
                # Sadece mouse tracking için update
                self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.MiddleButton:
            # Pan bitir
            self.is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            return
        elif event.button() == Qt.MouseButton.LeftButton:
            pos = QPointF(event.pos())
            
            if self.active_tool == "bspline":
                self.handle_bspline_release(event)
            elif self.active_tool == "freehand":
                self.handle_freehand_release(event)
            elif self.active_tool == "line":
                self.handle_line_release(event)
            elif self.active_tool == "rectangle":
                self.handle_rectangle_release(event)
            elif self.active_tool == "circle":
                self.handle_circle_release(event)
            elif self.active_tool == "select":
                transformed_pos = self.transform_mouse_pos(pos)
                self.handle_select_release(transformed_pos)
            elif self.active_tool == "move":
                transformed_pos = self.transform_mouse_pos(pos)
                self.handle_move_release(transformed_pos)
            elif self.active_tool == "rotate":
                transformed_pos = self.transform_mouse_pos(pos)
                self.handle_rotate_release(transformed_pos)
            elif self.active_tool == "scale":
                transformed_pos = self.transform_mouse_pos(pos)
                self.handle_scale_release(transformed_pos)

    # B-spline çizim aracı fonksiyonları
    def handle_bspline_press(self, event):
        clicked_point = event.pos()
        clicked_point_f = self.transform_mouse_pos(QPointF(clicked_point))
        
        # Önce kontrol noktası seçmeyi dene
        if self.bspline_tool.select_control_point(clicked_point_f, self.strokes):
            # Kontrol noktası seçildiğinde state kaydet
            self.save_current_state("Move control point")
            self.update()
            return
            
        # Kontrol noktası seçilmediyse, yeni çizim başlat
        pressure = event.pressure() if hasattr(event, 'pressure') else 1.0
        self.bspline_tool.start_stroke(clicked_point_f, pressure)
        self.update()

    def handle_bspline_move(self, event):
        # Eğer kontrol noktası seçiliyse, onu taşı
        if self.bspline_tool.selected_control_point is not None:
            new_pos = self.transform_mouse_pos(QPointF(event.pos()))
            if self.bspline_tool.move_control_point(new_pos, self.strokes):
                self.update()
        # Değilse, çizime devam et
        elif event.buttons() == Qt.MouseButton.LeftButton and self.bspline_tool.is_drawing:
            pressure = event.pressure() if hasattr(event, 'pressure') else 1.0
            transformed_pos = self.transform_mouse_pos(QPointF(event.pos()))
            self.bspline_tool.add_point(transformed_pos, pressure)
            self.update()

    def handle_bspline_release(self, event):
        # Eğer kontrol noktası taşınıyorsa, seçimi temizle
        if self.bspline_tool.selected_control_point is not None:
            self.bspline_tool.clear_selection()
            self.update()
        # Değilse, çizimi tamamla
        elif self.bspline_tool.is_drawing:
            stroke_data = self.bspline_tool.finish_stroke()
            if stroke_data is not None:
                self.strokes.append(stroke_data)
                self.save_current_state("Add B-spline")
            self.update()

    # Serbest çizim aracı fonksiyonları
    def handle_freehand_press(self, event):
        """Serbest çizim başlat"""
        pressure = event.pressure() if hasattr(event, 'pressure') else 1.0
        transformed_pos = self.transform_mouse_pos(QPointF(event.pos()))
        self.freehand_tool.start_stroke(transformed_pos, pressure)
        self.update()

    def handle_freehand_move(self, event):
        """Serbest çizim devam ettir"""
        if event.buttons() == Qt.MouseButton.LeftButton and self.freehand_tool.is_drawing:
            pressure = event.pressure() if hasattr(event, 'pressure') else 1.0
            transformed_pos = self.transform_mouse_pos(QPointF(event.pos()))
            self.freehand_tool.add_point(transformed_pos, pressure)
            self.update()

    def handle_freehand_release(self, event):
        """Serbest çizimi tamamla"""
        if self.freehand_tool.is_drawing:
            stroke_data = self.freehand_tool.finish_stroke()
            if stroke_data is not None:
                self.strokes.append(stroke_data)
                self.save_current_state("Add freehand")
            self.update()

    # Düz çizgi aracı fonksiyonları
    def handle_line_press(self, event):
        """Çizgi çizimi başlat"""
        pressure = event.pressure() if hasattr(event, 'pressure') else 1.0
        transformed_pos = self.transform_mouse_pos(QPointF(event.pos()))
        self.line_tool.start_stroke(transformed_pos, pressure)
        self.update()

    def handle_line_move(self, event):
        """Çizgi çizimi devam ettir"""
        if event.buttons() == Qt.MouseButton.LeftButton and self.line_tool.is_drawing:
            pressure = event.pressure() if hasattr(event, 'pressure') else 1.0
            transformed_pos = self.transform_mouse_pos(QPointF(event.pos()))
            self.line_tool.add_point(transformed_pos, pressure)
            self.update()

    def handle_line_release(self, event):
        """Çizgiyi tamamla"""
        if self.line_tool.is_drawing:
            stroke_data = self.line_tool.finish_stroke()
            if stroke_data is not None:
                self.strokes.append(stroke_data)
                self.save_current_state("Add line")
            self.update()

    # Dikdörtgen aracı fonksiyonları
    def handle_rectangle_press(self, event):
        """Dikdörtgen çizimi başlat"""
        pressure = event.pressure() if hasattr(event, 'pressure') else 1.0
        transformed_pos = self.transform_mouse_pos(QPointF(event.pos()))
        self.rectangle_tool.start_stroke(transformed_pos, pressure)
        self.update()

    def handle_rectangle_move(self, event):
        """Dikdörtgen çizimi devam ettir"""
        if event.buttons() == Qt.MouseButton.LeftButton and self.rectangle_tool.is_drawing:
            pressure = event.pressure() if hasattr(event, 'pressure') else 1.0
            transformed_pos = self.transform_mouse_pos(QPointF(event.pos()))
            self.rectangle_tool.add_point(transformed_pos, pressure)
            self.update()

    def handle_rectangle_release(self, event):
        """Dikdörtgeni tamamla"""
        if self.rectangle_tool.is_drawing:
            stroke_data = self.rectangle_tool.finish_stroke()
            if stroke_data is not None:
                self.strokes.append(stroke_data)
                self.save_current_state("Add rectangle")
            self.update()

    # Çember aracı fonksiyonları
    def handle_circle_press(self, event):
        """Çember çizimi başlat"""
        pressure = event.pressure() if hasattr(event, 'pressure') else 1.0
        transformed_pos = self.transform_mouse_pos(QPointF(event.pos()))
        self.circle_tool.start_stroke(transformed_pos, pressure)
        self.update()

    def handle_circle_move(self, event):
        """Çember çizimi devam ettir"""
        if event.buttons() == Qt.MouseButton.LeftButton and self.circle_tool.is_drawing:
            pressure = event.pressure() if hasattr(event, 'pressure') else 1.0
            transformed_pos = self.transform_mouse_pos(QPointF(event.pos()))
            self.circle_tool.add_point(transformed_pos, pressure)
            self.update()

    def handle_circle_release(self, event):
        """Çemberi tamamla"""
        if self.circle_tool.is_drawing:
            stroke_data = self.circle_tool.finish_stroke()
            if stroke_data is not None:
                self.strokes.append(stroke_data)
                self.save_current_state("Add circle")
            self.update()

    # Seçim aracı fonksiyonları
    def handle_select_press(self, pos):
        # Her zaman dikdörtgen seçimi başlat
        self.selection_tool.start_selection(pos)
        self.update()

    def handle_select_move(self, pos):
        if self.selection_tool.is_selecting:
            self.selection_tool.update_selection(pos)
            # Real-time seçim güncellemesi (preview)
            self.preview_selection()
            self.update()

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

    def handle_select_release(self, pos):
        if self.selection_tool.is_selecting:
            selected = self.selection_tool.finish_selection(self.strokes)
            if selected is None:
                # Dikdörtgen seçimi başarısızsa, nokta seçimi dene
                self.selection_tool.select_stroke_at_point(pos, self.strokes)
            self.update()

    # Taşıma aracı fonksiyonları
    def handle_move_press(self, pos):
        # Eğer zaten state kaydedildiyse, tekrar kaydetme
        if self._move_state_saved:
            return
        
        # Eğer zaten seçim varsa, taşımayı başlat
        if self.selection_tool.selected_strokes:
            # Move başlangıcında state kaydetme, sadece flag set et
            self._move_state_saved = True
            self.move_tool.start_move(pos)
            self.update()
        else:
            # Seçim yoksa, önce seçim yap
            selected = self.selection_tool.select_stroke_at_point(pos, self.strokes)
            if self.selection_tool.selected_strokes:
                # Move başlangıcında state kaydetme, sadece flag set et
                self._move_state_saved = True
                self.move_tool.start_move(pos)
                self.update()

    def handle_move_move(self, pos):
        selected_strokes = self.selection_tool.selected_strokes
        if self.move_tool.update_move(pos, self.strokes, selected_strokes):
            self.update()

    def handle_move_release(self, pos):
        # Move bitişinde final state'i kaydet
        if self._move_state_saved:  # Sadece move yapıldıysa
            self.save_current_state("Move end")
        
        self.move_tool.finish_move()
        self._move_state_saved = False  # Flag'i sıfırla

    # Döndürme aracı fonksiyonları
    def handle_rotate_press(self, pos):
        # Eğer zaten state kaydedildiyse, tekrar kaydetme
        if self._rotate_state_saved:
            return
            
        # Eğer zaten seçilmiş stroke'lar varsa, tutamak kontrolü yap
        if self.selection_tool.selected_strokes:
            if self.rotate_tool.start_rotate(pos, self.strokes, self.selection_tool.selected_strokes):
                # Rotate başlangıcında state kaydetme, sadece flag set et
                self._rotate_state_saved = True
                self.update()
                return
        else:
            # Seçim yoksa, önce seçim yap
            selected = self.selection_tool.select_stroke_at_point(pos, self.strokes)
            if self.selection_tool.selected_strokes:
                # Tutamakları oluştur ama döndürmeyi başlatma
                self.rotate_tool.create_rotation_handles(self.strokes, self.selection_tool.selected_strokes)
                self.update()

    def handle_rotate_move(self, pos):
        # Mouse pozisyonunu kaydet (görsel feedback için)
        self.rotate_tool.set_current_mouse_pos(pos)
        
        selected_strokes = self.selection_tool.selected_strokes
        if self.rotate_tool.update_rotate(pos, self.strokes, selected_strokes):
            self.update()

    def handle_rotate_release(self, pos):
        # Rotate bitişinde final state'i kaydet
        if self._rotate_state_saved:  # Sadece rotate yapıldıysa
            self.save_current_state("Rotate end")
        
        self.rotate_tool.finish_rotate()
        self._rotate_state_saved = False  # Flag'i sıfırla
        self.update()

    # Boyutlandırma aracı fonksiyonları
    def handle_scale_press(self, pos):
        # Eğer zaten state kaydedildiyse, tekrar kaydetme
        if self._scale_state_saved:
            return
            
        # Eğer zaten seçilmiş stroke'lar varsa, tutamak kontrolü yap
        if self.selection_tool.selected_strokes:
            if self.scale_tool.start_scale(pos, self.strokes, self.selection_tool.selected_strokes):
                # Scale başlangıcında state kaydetme, sadece flag set et
                self._scale_state_saved = True
                self.update()
                return
        else:
            # Seçim yoksa, önce seçim yap
            selected = self.selection_tool.select_stroke_at_point(pos, self.strokes)
            if self.selection_tool.selected_strokes:
                # Tutamakları oluştur ama boyutlandırmayı başlatma
                self.scale_tool.create_scale_handles(self.strokes, self.selection_tool.selected_strokes)
                self.update()

    def handle_scale_move(self, pos):
        # Mouse pozisyonunu kaydet (görsel feedback için)
        self.scale_tool.set_current_mouse_pos(pos)
        
        selected_strokes = self.selection_tool.selected_strokes
        if self.scale_tool.update_scale(pos, self.strokes, selected_strokes):
            self.update()

    def handle_scale_release(self, pos):
        # Scale bitişinde final state'i kaydet
        if self._scale_state_saved:  # Sadece scale yapıldıysa
            self.save_current_state("Scale end")
        
        self.scale_tool.finish_scale()
        self._scale_state_saved = False  # Flag'i sıfırla
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Main window'dan güncel zoom ve pan değerlerini al
        current_zoom = self.zoom_level
        current_offset = self.zoom_offset
        
        if self.main_window and hasattr(self.main_window, 'zoom_widget'):
            current_zoom = self.main_window.zoom_widget.get_zoom_level()
            current_offset = self.main_window.zoom_widget.get_pan_offset()
        
        # Zoom ve pan transformasyonu uygula
        painter.scale(current_zoom, current_zoom)
        painter.translate(current_offset)
        
        # Arka planı çiz
        self.draw_background(painter)

        # Tüm tamamlanmış stroke'ları çiz
        for stroke_data in self.strokes:
            # Image stroke kontrolü
            if hasattr(stroke_data, 'stroke_type') and stroke_data.stroke_type == 'image':
                stroke_data.render(painter)
                continue
                
            # Güvenlik kontrolü - eski stroke'lar için
            if 'type' not in stroke_data:
                continue
                
            if stroke_data['type'] == 'bspline':
                self.bspline_tool.draw_stroke(painter, stroke_data)
            elif stroke_data['type'] == 'freehand':
                self.freehand_tool.draw_stroke(painter, stroke_data)
            elif stroke_data['type'] == 'line':
                self.line_tool.draw_stroke(painter, stroke_data)
            elif stroke_data['type'] == 'rectangle':
                self.rectangle_tool.draw_stroke(painter, stroke_data)
            elif stroke_data['type'] == 'circle':
                self.circle_tool.draw_stroke(painter, stroke_data)

        # Seçim vurgusunu çiz
        self.selection_tool.draw_selected_stroke_highlight(painter, self.strokes)
        
        # Seçim dikdörtgenini çiz
        self.selection_tool.draw_selection(painter)
        
        # Döndürme tutamaklarını çiz (döndürme aracı aktifse)
        if self.active_tool == "rotate":
            self.rotate_tool.draw_rotation_handles(painter, self.strokes, self.selection_tool.selected_strokes)
            
        # Boyutlandırma tutamaklarını çiz (boyutlandırma aracı aktifse)
        if self.active_tool == "scale":
            self.scale_tool.draw_scale_handles(painter, self.strokes, self.selection_tool.selected_strokes)

        # Aktif çizimi çiz
        if self.active_tool == "bspline":
            self.bspline_tool.draw_current_stroke(painter)
        elif self.active_tool == "freehand":
            self.freehand_tool.draw_current_stroke(painter)
        elif self.active_tool == "line":
            self.line_tool.draw_current_stroke(painter)
        elif self.active_tool == "rectangle":
            self.rectangle_tool.draw_current_stroke(painter)
        elif self.active_tool == "circle":
            self.circle_tool.draw_current_stroke(painter)
            
    def draw_background(self, painter):
        """Arka planı çiz"""
        # Arka plan rengini ayarla
        bg_color = QColor(self.background_settings['background_color'])
        painter.fillRect(self.rect(), QBrush(bg_color))
        
        # Grid/Pattern çizimi
        if self.background_settings['type'] == 'grid':
            self.draw_grid_background(painter)
        elif self.background_settings['type'] == 'dots':
            self.draw_dots_background(painter)
        
        # Beyaz arka planda da grid göster (snap aktifse)
        if (self.background_settings['type'] == 'solid' and 
            self.background_settings.get('snap_to_grid', False)):
            self.draw_snap_grid(painter)
            
    def draw_grid_background(self, painter):
        """Çizgili arka plan çiz (sadece yatay çizgiler) - Major/Minor sistem"""
        # Minor grid ayarları
        minor_color = QColor(self.background_settings['grid_color'])
        major_color = QColor(self.background_settings.get('major_grid_color', QColor(150, 150, 150)))
        grid_size = self.background_settings['grid_size']
        minor_width = self.background_settings['grid_width']
        major_width = self.background_settings.get('major_grid_width', 2)
        major_interval = self.background_settings.get('major_grid_interval', 5)
        grid_opacity = self.background_settings.get('grid_opacity', 1.0)
        
        # Şeffaflık uygula
        minor_color.setAlphaF(grid_opacity)
        major_color.setAlphaF(grid_opacity)
        
        rect = self.rect()
        width = rect.width()
        height = rect.height()
        
        # Sadece yatay çizgiler (çizgili kağıt gibi)
        y = 0
        line_count = 0
        while y <= height:
            # Her major_interval çizgide bir major grid çiz
            if line_count % major_interval == 0:
                # Major çizgi
                pen = QPen(major_color, major_width)
                painter.setPen(pen)
            else:
                # Minor çizgi
                pen = QPen(minor_color, minor_width)
                painter.setPen(pen)
            
            painter.drawLine(0, y, width, y)
            y += grid_size
            line_count += 1
             
    def draw_snap_grid(self, painter):
        """Beyaz arka planda snap için hafif grid çiz - Major/Minor sistem"""
        # Minor grid ayarları
        minor_color = QColor(self.background_settings['grid_color'])
        major_color = QColor(self.background_settings.get('major_grid_color', QColor(150, 150, 150)))
        grid_size = self.background_settings['grid_size']
        minor_width = max(1, self.background_settings['grid_width'] - 1)  # Biraz daha ince
        major_width = max(1, self.background_settings.get('major_grid_width', 2) - 1)  # Biraz daha ince
        major_interval = self.background_settings.get('major_grid_interval', 5)
        grid_opacity = self.background_settings.get('grid_opacity', 1.0) * 0.3  # Daha şeffaf
        
        # Şeffaflık uygula
        minor_color.setAlphaF(grid_opacity)
        major_color.setAlphaF(grid_opacity)
        
        rect = self.rect()
        width = rect.width()
        height = rect.height()
        
        # Dikey çizgiler
        x = 0
        line_count = 0
        while x <= width:
            # Her major_interval çizgide bir major grid çiz
            if line_count % major_interval == 0:
                # Major çizgi
                pen = QPen(major_color, major_width, Qt.PenStyle.DotLine)
                painter.setPen(pen)
            else:
                # Minor çizgi
                pen = QPen(minor_color, minor_width, Qt.PenStyle.DotLine)
                painter.setPen(pen)
            
            painter.drawLine(x, 0, x, height)
            x += grid_size
            line_count += 1
            
        # Yatay çizgiler
        y = 0
        line_count = 0
        while y <= height:
            # Her major_interval çizgide bir major grid çiz
            if line_count % major_interval == 0:
                # Major çizgi
                pen = QPen(major_color, major_width, Qt.PenStyle.DotLine)
                painter.setPen(pen)
            else:
                # Minor çizgi
                pen = QPen(minor_color, minor_width, Qt.PenStyle.DotLine)
                painter.setPen(pen)
            
            painter.drawLine(0, y, width, y)
            y += grid_size
            line_count += 1
            
    def draw_dots_background(self, painter):
        """Kareli arka plan çiz (hem yatay hem dikey çizgiler) - Major/Minor sistem"""
        # Minor grid ayarları
        minor_color = QColor(self.background_settings['grid_color'])
        major_color = QColor(self.background_settings.get('major_grid_color', QColor(150, 150, 150)))
        grid_size = self.background_settings['grid_size']
        minor_width = self.background_settings['grid_width']
        major_width = self.background_settings.get('major_grid_width', 2)
        major_interval = self.background_settings.get('major_grid_interval', 5)
        grid_opacity = self.background_settings.get('grid_opacity', 1.0)
        
        # Şeffaflık uygula
        minor_color.setAlphaF(grid_opacity)
        major_color.setAlphaF(grid_opacity)
        
        rect = self.rect()
        width = rect.width()
        height = rect.height()
        
        # Dikey çizgiler (kareli için)
        x = 0
        line_count = 0
        while x <= width:
            # Her major_interval çizgide bir major grid çiz
            if line_count % major_interval == 0:
                # Major çizgi
                pen = QPen(major_color, major_width)
                painter.setPen(pen)
            else:
                # Minor çizgi
                pen = QPen(minor_color, minor_width)
                painter.setPen(pen)
            
            painter.drawLine(x, 0, x, height)
            x += grid_size
            line_count += 1
            
        # Yatay çizgiler (kareli için)
        y = 0
        line_count = 0
        while y <= height:
            # Her major_interval çizgide bir major grid çiz
            if line_count % major_interval == 0:
                # Major çizgi
                pen = QPen(major_color, major_width)
                painter.setPen(pen)
            else:
                # Minor çizgi
                pen = QPen(minor_color, minor_width)
                painter.setPen(pen)
            
            painter.drawLine(0, y, width, y)
            y += grid_size
            line_count += 1

    def render(self, painter):
        """PDF export için özel render metodu - zoom/pan olmadan sadece içerik"""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Arka planı çiz (beyaz)
        bg_color = QColor(Qt.GlobalColor.white)
        painter.fillRect(self.rect(), QBrush(bg_color))
        
        # Tüm tamamlanmış stroke'ları çiz
        for stroke_data in self.strokes:
            # Image stroke kontrolü
            if hasattr(stroke_data, 'stroke_type') and stroke_data.stroke_type == 'image':
                stroke_data.render(painter)
                continue
                
            # Güvenlik kontrolü - eski stroke'lar için
            if 'type' not in stroke_data:
                continue
            if stroke_data['type'] == 'bspline':
                self.bspline_tool.draw_stroke(painter, stroke_data)
            elif stroke_data['type'] == 'freehand':
                self.freehand_tool.draw_stroke(painter, stroke_data)
            elif stroke_data['type'] == 'line':
                self.line_tool.draw_stroke(painter, stroke_data)
            elif stroke_data['type'] == 'rectangle':
                self.rectangle_tool.draw_stroke(painter, stroke_data)
            elif stroke_data['type'] == 'circle':
                self.circle_tool.draw_stroke(painter, stroke_data)
