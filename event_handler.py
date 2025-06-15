from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QMouseEvent, QTabletEvent
from PyQt6.QtCore import Qt, QPointF
import time

class EventHandler:
    """DrawingWidget için event handling işlemlerini yöneten sınıf"""
    
    def __init__(self, drawing_widget):
        self.drawing_widget = drawing_widget
        
    def handle_mouse_press(self, event: QMouseEvent):
        """Mouse press event'i işle"""
        if event.button() == Qt.MouseButton.MiddleButton:
            # Middle mouse button ile pan başlat
            self.drawing_widget.is_panning = True
            self.drawing_widget.pan_start_point = QPointF(event.pos())
            self.drawing_widget.setCursor(Qt.CursorShape.ClosedHandCursor)
            return
        elif event.button() == Qt.MouseButton.LeftButton:
            pos = QPointF(event.pos())
            
            # Space tuşu basılıysa pan başlat
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier or \
               (hasattr(event, 'key') and event.key() == Qt.Key.Key_Space):
                self.drawing_widget.is_panning = True
                self.drawing_widget.pan_start_point = pos
                self.drawing_widget.setCursor(Qt.CursorShape.ClosedHandCursor)
                return
            
            # Ctrl tuşu durumunu güncelle
            self.drawing_widget.selection_tool.set_ctrl_pressed(event.modifiers() & Qt.KeyboardModifier.ControlModifier)
            
            if self.drawing_widget.active_tool == "bspline":
                self.handle_bspline_press(event)
            elif self.drawing_widget.active_tool == "freehand":
                self.handle_freehand_press(event)
            elif self.drawing_widget.active_tool == "line":
                self.handle_line_press(event)
            elif self.drawing_widget.active_tool == "rectangle":
                self.handle_rectangle_press(event)
            elif self.drawing_widget.active_tool == "circle":
                self.handle_circle_press(event)
            elif self.drawing_widget.active_tool == "select":
                transformed_pos = self.drawing_widget.transform_mouse_pos(pos)
                self.handle_select_press(transformed_pos)
            elif self.drawing_widget.active_tool == "move":
                transformed_pos = self.drawing_widget.transform_mouse_pos(pos)
                self.handle_move_press(transformed_pos)
            elif self.drawing_widget.active_tool == "rotate":
                transformed_pos = self.drawing_widget.transform_mouse_pos(pos)
                self.handle_rotate_press(transformed_pos)
            elif self.drawing_widget.active_tool == "scale":
                transformed_pos = self.drawing_widget.transform_mouse_pos(pos)
                self.handle_scale_press(transformed_pos)
            else:
                print(f"DEBUG: Bilinmeyen araç: '{self.drawing_widget.active_tool}'")

    def handle_mouse_move(self, event: QMouseEvent):
        """Mouse move event'i işle"""
        pos = QPointF(event.pos())
        
        # Pan işlemi kontrol et
        if self.drawing_widget.is_panning:
            if self.drawing_widget.main_window and hasattr(self.drawing_widget.main_window, 'zoom_widget'):
                # Pan delta hesapla
                delta = pos - self.drawing_widget.pan_start_point
                current_offset = self.drawing_widget.main_window.zoom_widget.get_pan_offset()
                new_offset = current_offset + delta
                self.drawing_widget.main_window.zoom_widget.set_pan_offset(new_offset)
                self.drawing_widget.pan_start_point = pos
            return
        
        if self.drawing_widget.active_tool == "bspline":
            self.handle_bspline_move(event)
        elif self.drawing_widget.active_tool == "freehand":
            self.handle_freehand_move(event)
        elif self.drawing_widget.active_tool == "line":
            self.handle_line_move(event)
        elif self.drawing_widget.active_tool == "rectangle":
            self.handle_rectangle_move(event)
        elif self.drawing_widget.active_tool == "circle":
            self.handle_circle_move(event)
        elif self.drawing_widget.active_tool == "select":
            if event.buttons() == Qt.MouseButton.LeftButton:
                transformed_pos = self.drawing_widget.transform_mouse_pos(pos)
                self.handle_select_move(transformed_pos)
        elif self.drawing_widget.active_tool == "move":
            if event.buttons() == Qt.MouseButton.LeftButton:
                transformed_pos = self.drawing_widget.transform_mouse_pos(pos)
                self.handle_move_move(transformed_pos)
        elif self.drawing_widget.active_tool == "rotate":
            # Her zaman mouse pozisyonunu güncelle (görsel feedback için)
            transformed_pos = self.drawing_widget.transform_mouse_pos(pos)
            self.drawing_widget.rotate_tool.set_current_mouse_pos(transformed_pos)
            if event.buttons() == Qt.MouseButton.LeftButton:
                self.handle_rotate_move(transformed_pos)
            else:
                # Throttled update - sadece mouse tracking için
                self.drawing_widget._throttled_update()
        elif self.drawing_widget.active_tool == "scale":
            # Her zaman mouse pozisyonunu güncelle (görsel feedback için)
            transformed_pos = self.drawing_widget.transform_mouse_pos(pos)
            self.drawing_widget.scale_tool.set_current_mouse_pos(transformed_pos)
            if event.buttons() == Qt.MouseButton.LeftButton:
                self.handle_scale_move(transformed_pos)
            else:
                # Throttled update - sadece mouse tracking için
                self.drawing_widget._throttled_update()

    def handle_mouse_release(self, event: QMouseEvent):
        """Mouse release event'i işle"""
        if event.button() == Qt.MouseButton.MiddleButton:
            # Pan bitir
            self.drawing_widget.is_panning = False
            self.drawing_widget.setCursor(Qt.CursorShape.ArrowCursor)
            return
        elif event.button() == Qt.MouseButton.LeftButton:
            pos = QPointF(event.pos())
            
            if self.drawing_widget.active_tool == "bspline":
                self.handle_bspline_release(event)
            elif self.drawing_widget.active_tool == "freehand":
                self.handle_freehand_release(event)
            elif self.drawing_widget.active_tool == "line":
                self.handle_line_release(event)
            elif self.drawing_widget.active_tool == "rectangle":
                self.handle_rectangle_release(event)
            elif self.drawing_widget.active_tool == "circle":
                self.handle_circle_release(event)
            elif self.drawing_widget.active_tool == "select":
                transformed_pos = self.drawing_widget.transform_mouse_pos(pos)
                self.handle_select_release(transformed_pos)
            elif self.drawing_widget.active_tool == "move":
                transformed_pos = self.drawing_widget.transform_mouse_pos(pos)
                self.handle_move_release(transformed_pos)
            elif self.drawing_widget.active_tool == "rotate":
                transformed_pos = self.drawing_widget.transform_mouse_pos(pos)
                self.handle_rotate_release(transformed_pos)
            elif self.drawing_widget.active_tool == "scale":
                transformed_pos = self.drawing_widget.transform_mouse_pos(pos)
                self.handle_scale_release(transformed_pos)

    def handle_tablet_event(self, event: QTabletEvent):
        """Tablet kalemi event'lerini işle"""
        # Tablet handler ile optimize et
        pos, pressure, should_process = self.drawing_widget.tablet_handler.handle_tablet_event(event)
        
        if not should_process:
            event.accept()
            return
            
        # Transform mouse position
        transformed_pos = self.drawing_widget.transform_mouse_pos(pos)
        
        # Event türüne göre işle
        if event.type() == QTabletEvent.Type.TabletPress:
            self._handle_tablet_press(transformed_pos, pressure)
        elif event.type() == QTabletEvent.Type.TabletMove:
            self._handle_tablet_move(transformed_pos, pressure)
        elif event.type() == QTabletEvent.Type.TabletRelease:
            self._handle_tablet_release(transformed_pos, pressure)
            
        event.accept()

    def _handle_tablet_press(self, pos, pressure):
        """Tablet press event'i işle"""
        if self.drawing_widget.active_tool == "bspline":
            if self.drawing_widget.bspline_tool.select_control_point(pos, self.drawing_widget.strokes):
                self.drawing_widget.save_current_state("Move control point")
                self.drawing_widget._throttled_update()
                return
            self.drawing_widget.bspline_tool.start_stroke(pos, pressure)
            self.drawing_widget._throttled_update()
        elif self.drawing_widget.active_tool == "freehand":
            self.drawing_widget.freehand_tool.start_stroke(pos, pressure, True)  # True = tablet
            self.drawing_widget._throttled_update()
        elif self.drawing_widget.active_tool == "line":
            self.drawing_widget.line_tool.start_stroke(pos, pressure)
            self.drawing_widget._throttled_update()
        elif self.drawing_widget.active_tool == "rectangle":
            self.drawing_widget.rectangle_tool.start_stroke(pos, pressure)
            self.drawing_widget._throttled_update()
        elif self.drawing_widget.active_tool == "circle":
            self.drawing_widget.circle_tool.start_stroke(pos, pressure)
            self.drawing_widget._throttled_update()
        elif self.drawing_widget.active_tool == "select":
            self.handle_select_press(pos)
        elif self.drawing_widget.active_tool == "move":
            self.handle_move_press(pos)
        elif self.drawing_widget.active_tool == "rotate":
            self.handle_rotate_press(pos)
        elif self.drawing_widget.active_tool == "scale":
            self.handle_scale_press(pos)

    def _handle_tablet_move(self, pos, pressure):
        """Tablet move event'i işle"""
        if self.drawing_widget.active_tool == "bspline":
            if self.drawing_widget.bspline_tool.selected_control_point is not None:
                if self.drawing_widget.bspline_tool.move_control_point(pos, self.drawing_widget.strokes):
                    self.drawing_widget._throttled_update()
            elif self.drawing_widget.bspline_tool.is_drawing:
                self.drawing_widget.bspline_tool.add_point(pos, pressure)
                self.drawing_widget._throttled_tablet_update()
        elif self.drawing_widget.active_tool == "freehand":
            if self.drawing_widget.freehand_tool.is_drawing:
                self.drawing_widget.freehand_tool.add_point(pos, pressure, True)  # True = tablet
                self.drawing_widget.update()  # INSTANT update - ASLA throttling yok
        elif self.drawing_widget.active_tool == "line":
            if self.drawing_widget.line_tool.is_drawing:
                self.drawing_widget.line_tool.add_point(pos, pressure)
                self.drawing_widget._throttled_tablet_update()
        elif self.drawing_widget.active_tool == "rectangle":
            if self.drawing_widget.rectangle_tool.is_drawing:
                self.drawing_widget.rectangle_tool.add_point(pos, pressure)
                self.drawing_widget._throttled_tablet_update()
        elif self.drawing_widget.active_tool == "circle":
            if self.drawing_widget.circle_tool.is_drawing:
                self.drawing_widget.circle_tool.add_point(pos, pressure)
                self.drawing_widget._throttled_tablet_update()
        elif self.drawing_widget.active_tool == "select":
            self.handle_select_move(pos)
        elif self.drawing_widget.active_tool == "move":
            self.handle_move_move(pos)
        elif self.drawing_widget.active_tool == "rotate":
            self.drawing_widget.rotate_tool.set_current_mouse_pos(pos)
            self.handle_rotate_move(pos)
        elif self.drawing_widget.active_tool == "scale":
            self.drawing_widget.scale_tool.set_current_mouse_pos(pos)
            self.handle_scale_move(pos)

    def _handle_tablet_release(self, pos, pressure):
        """Tablet release event'i işle"""
        if self.drawing_widget.active_tool == "bspline":
            if self.drawing_widget.bspline_tool.selected_control_point is not None:
                self.drawing_widget.bspline_tool.clear_selection()
                self.drawing_widget.update()
            elif self.drawing_widget.bspline_tool.is_drawing:
                stroke_data = self.drawing_widget.bspline_tool.finish_stroke()
                if stroke_data is not None:
                    self.drawing_widget.strokes.append(stroke_data)
                    self.drawing_widget.save_current_state("Add B-spline")
                self.drawing_widget.update()
        elif self.drawing_widget.active_tool == "freehand":
            if self.drawing_widget.freehand_tool.is_drawing:
                stroke_data = self.drawing_widget.freehand_tool.finish_stroke()
                if stroke_data is not None:
                    self.drawing_widget.strokes.append(stroke_data)
                    self.drawing_widget.save_current_state("Add freehand")
                self.drawing_widget.update()
        elif self.drawing_widget.active_tool == "line":
            if self.drawing_widget.line_tool.is_drawing:
                stroke_data = self.drawing_widget.line_tool.finish_stroke()
                if stroke_data is not None:
                    self.drawing_widget.strokes.append(stroke_data)
                    self.drawing_widget.save_current_state("Add line")
                self.drawing_widget.update()
        elif self.drawing_widget.active_tool == "rectangle":
            if self.drawing_widget.rectangle_tool.is_drawing:
                stroke_data = self.drawing_widget.rectangle_tool.finish_stroke()
                if stroke_data is not None:
                    self.drawing_widget.strokes.append(stroke_data)
                    self.drawing_widget.save_current_state("Add rectangle")
                self.drawing_widget.update()
        elif self.drawing_widget.active_tool == "circle":
            if self.drawing_widget.circle_tool.is_drawing:
                stroke_data = self.drawing_widget.circle_tool.finish_stroke()
                if stroke_data is not None:
                    self.drawing_widget.strokes.append(stroke_data)
                    self.drawing_widget.save_current_state("Add circle")
                self.drawing_widget.update()
        elif self.drawing_widget.active_tool == "select":
            self.handle_select_release(pos)
        elif self.drawing_widget.active_tool == "move":
            self.handle_move_release(pos)
        elif self.drawing_widget.active_tool == "rotate":
            self.handle_rotate_release(pos)
        elif self.drawing_widget.active_tool == "scale":
            self.handle_scale_release(pos)
            
        # Tablet işlemi bittiğinde reset
        self.drawing_widget.tablet_handler.reset_tablet_state()

    def handle_key_press(self, event):
        """Klavye tuşu basıldığında"""
        if event.key() == Qt.Key.Key_Control:
            self.drawing_widget.selection_tool.set_ctrl_pressed(True)
        elif event.key() == Qt.Key.Key_Space and not self.drawing_widget.is_panning:
            # Space tuşu ile pan modu
            self.drawing_widget.setCursor(Qt.CursorShape.OpenHandCursor)

    def handle_key_release(self, event):
        """Klavye tuşu bırakıldığında"""
        if event.key() == Qt.Key.Key_Control:
            self.drawing_widget.selection_tool.set_ctrl_pressed(False)
        elif event.key() == Qt.Key.Key_Space:
            # Space tuşu bırakıldığında normal cursor
            if not self.drawing_widget.is_panning:
                self.drawing_widget.setCursor(Qt.CursorShape.ArrowCursor)

    def handle_wheel(self, event):
        """Mouse wheel eventi - zoom için"""
        if self.drawing_widget.main_window and hasattr(self.drawing_widget.main_window, 'zoom_widget'):
            # Mouse pozisyonunu al
            mouse_pos = QPointF(event.position())
            
            # Wheel delta'ya göre zoom
            delta = event.angleDelta().y()
            if delta > 0:
                self.drawing_widget.main_window.zoom_widget.wheel_zoom_in(mouse_pos)
            else:
                self.drawing_widget.main_window.zoom_widget.wheel_zoom_out(mouse_pos)
        
        event.accept()

    # Tool-specific handlers
    def handle_bspline_press(self, event):
        """B-spline çizimi başlat"""
        pressure = event.pressure() if hasattr(event, 'pressure') else 1.0
        transformed_pos = self.drawing_widget.transform_mouse_pos(QPointF(event.pos()))
        
        # Önce mevcut kontrol noktalarını kontrol et
        if self.drawing_widget.bspline_tool.select_control_point(transformed_pos, self.drawing_widget.strokes):
            self.drawing_widget.save_current_state("Move control point")
            self.drawing_widget._throttled_update()
            return
        
        # Yeni B-spline başlat
        self.drawing_widget.bspline_tool.start_stroke(transformed_pos, pressure)
        pressure = self.drawing_widget.tablet_handler.get_optimized_pressure(event)
        self.drawing_widget._throttled_update()

    def handle_bspline_move(self, event):
        """B-spline çizimi devam ettir"""
        # Eğer kontrol noktası seçiliyse, onu taşı
        if self.drawing_widget.bspline_tool.selected_control_point is not None:
            transformed_pos = self.drawing_widget.transform_mouse_pos(QPointF(event.pos()))
            if self.drawing_widget.bspline_tool.move_control_point(transformed_pos, self.drawing_widget.strokes):
                self.drawing_widget._throttled_update()
        # B-spline çizimi devam ediyorsa
        elif event.buttons() == Qt.MouseButton.LeftButton and self.drawing_widget.bspline_tool.is_drawing:
            pressure = event.pressure() if hasattr(event, 'pressure') else 1.0
            transformed_pos = self.drawing_widget.transform_mouse_pos(QPointF(event.pos()))
            pressure = self.drawing_widget.tablet_handler.get_optimized_pressure(event)
            self.drawing_widget.bspline_tool.add_point(transformed_pos, pressure)
            self.drawing_widget._throttled_update()

    def handle_bspline_release(self, event):
        """B-spline çizimi tamamla veya seçimi temizle"""
        # Eğer kontrol noktası taşınıyorsa, seçimi temizle
        if self.drawing_widget.bspline_tool.selected_control_point is not None:
            self.drawing_widget.bspline_tool.clear_selection()
            self.drawing_widget.update()
        # B-spline çizimi tamamla
        elif self.drawing_widget.bspline_tool.is_drawing:
            stroke_data = self.drawing_widget.bspline_tool.finish_stroke()
            if stroke_data is not None:
                self.drawing_widget.strokes.append(stroke_data)
                self.drawing_widget.save_current_state("Add B-spline")
            self.drawing_widget.update()

    def handle_freehand_press(self, event):
        """Serbest çizim başlat"""
        pressure = event.pressure() if hasattr(event, 'pressure') else 1.0
        transformed_pos = self.drawing_widget.transform_mouse_pos(QPointF(event.pos()))
        pressure = self.drawing_widget.tablet_handler.get_optimized_pressure(event)
        is_tablet = self.drawing_widget.tablet_handler.is_tablet_in_use()
        self.drawing_widget.freehand_tool.start_stroke(transformed_pos, pressure, is_tablet)
        self.drawing_widget.update()

    def handle_freehand_move(self, event):
        """Serbest çizim devam ettir"""
        if event.buttons() == Qt.MouseButton.LeftButton and self.drawing_widget.freehand_tool.is_drawing:
            pressure = event.pressure() if hasattr(event, 'pressure') else 1.0
            transformed_pos = self.drawing_widget.transform_mouse_pos(QPointF(event.pos()))
            pressure = self.drawing_widget.tablet_handler.get_optimized_pressure(event)
            is_tablet = self.drawing_widget.tablet_handler.is_tablet_in_use()
            self.drawing_widget.freehand_tool.add_point(transformed_pos, pressure, is_tablet)
            
            # Tablet kullanımındaysa tablet throttling, değilse freehand throttling
            if is_tablet:
                self.drawing_widget._throttled_tablet_update()
            else:
                self.drawing_widget._throttled_freehand_update()

    def handle_freehand_release(self, event):
        """Serbest çizimi tamamla"""
        if self.drawing_widget.freehand_tool.is_drawing:
            stroke_data = self.drawing_widget.freehand_tool.finish_stroke()
            if stroke_data is not None:
                self.drawing_widget.strokes.append(stroke_data)
                self.drawing_widget.save_current_state("Add freehand")
            self.drawing_widget.update()

    def handle_line_press(self, event):
        """Çizgi çizimi başlat"""
        pressure = event.pressure() if hasattr(event, 'pressure') else 1.0
        transformed_pos = self.drawing_widget.transform_mouse_pos(QPointF(event.pos()))
        self.drawing_widget.line_tool.start_stroke(transformed_pos, pressure)
        self.drawing_widget.update()

    def handle_line_move(self, event):
        """Çizgi çizimi devam ettir"""
        if event.buttons() == Qt.MouseButton.LeftButton and self.drawing_widget.line_tool.is_drawing:
            pressure = event.pressure() if hasattr(event, 'pressure') else 1.0
            transformed_pos = self.drawing_widget.transform_mouse_pos(QPointF(event.pos()))
            self.drawing_widget.line_tool.add_point(transformed_pos, pressure)
            self.drawing_widget._throttled_freehand_update()

    def handle_line_release(self, event):
        """Çizgiyi tamamla"""
        if self.drawing_widget.line_tool.is_drawing:
            stroke_data = self.drawing_widget.line_tool.finish_stroke()
            if stroke_data is not None:
                self.drawing_widget.strokes.append(stroke_data)
                self.drawing_widget.save_current_state("Add line")
            self.drawing_widget.update()

    def handle_rectangle_press(self, event):
        """Dikdörtgen çizimi başlat"""
        pressure = event.pressure() if hasattr(event, 'pressure') else 1.0
        transformed_pos = self.drawing_widget.transform_mouse_pos(QPointF(event.pos()))
        self.drawing_widget.rectangle_tool.start_stroke(transformed_pos, pressure)
        self.drawing_widget.update()

    def handle_rectangle_move(self, event):
        """Dikdörtgen çizimi devam ettir"""
        if event.buttons() == Qt.MouseButton.LeftButton and self.drawing_widget.rectangle_tool.is_drawing:
            pressure = event.pressure() if hasattr(event, 'pressure') else 1.0
            transformed_pos = self.drawing_widget.transform_mouse_pos(QPointF(event.pos()))
            self.drawing_widget.rectangle_tool.add_point(transformed_pos, pressure)
            self.drawing_widget._throttled_freehand_update()

    def handle_rectangle_release(self, event):
        """Dikdörtgeni tamamla"""
        if self.drawing_widget.rectangle_tool.is_drawing:
            stroke_data = self.drawing_widget.rectangle_tool.finish_stroke()
            if stroke_data is not None:
                self.drawing_widget.strokes.append(stroke_data)
                self.drawing_widget.save_current_state("Add rectangle")
            self.drawing_widget.update()

    def handle_circle_press(self, event):
        """Çember çizimi başlat"""
        pressure = event.pressure() if hasattr(event, 'pressure') else 1.0
        transformed_pos = self.drawing_widget.transform_mouse_pos(QPointF(event.pos()))
        self.drawing_widget.circle_tool.start_stroke(transformed_pos, pressure)
        self.drawing_widget.update()

    def handle_circle_move(self, event):
        """Çember çizimi devam ettir"""
        if event.buttons() == Qt.MouseButton.LeftButton and self.drawing_widget.circle_tool.is_drawing:
            pressure = event.pressure() if hasattr(event, 'pressure') else 1.0
            transformed_pos = self.drawing_widget.transform_mouse_pos(QPointF(event.pos()))
            self.drawing_widget.circle_tool.add_point(transformed_pos, pressure)
            self.drawing_widget._throttled_freehand_update()

    def handle_circle_release(self, event):
        """Çemberi tamamla"""
        if self.drawing_widget.circle_tool.is_drawing:
            stroke_data = self.drawing_widget.circle_tool.finish_stroke()
            if stroke_data is not None:
                self.drawing_widget.strokes.append(stroke_data)
                self.drawing_widget.save_current_state("Add circle")
            self.drawing_widget.update()

    def handle_select_press(self, pos):
        """Seçim başlat"""
        self.drawing_widget.selection_tool.start_selection(pos)
        self.drawing_widget.update()

    def handle_select_move(self, pos):
        """Seçim güncelle"""
        if self.drawing_widget.selection_tool.is_selecting:
            self.drawing_widget.selection_tool.update_selection(pos)
            # Real-time seçim güncellemesi (preview)
            self.drawing_widget.preview_selection()
            self.drawing_widget.update()

    def handle_select_release(self, pos):
        """Seçimi tamamla"""
        if self.drawing_widget.selection_tool.is_selecting:
            selected = self.drawing_widget.selection_tool.finish_selection(self.drawing_widget.strokes)
            if selected is None:
                # Dikdörtgen seçimi başarısızsa, nokta seçimi dene
                self.drawing_widget.selection_tool.select_stroke_at_point(pos, self.drawing_widget.strokes)
            self.drawing_widget.update()

    def handle_move_press(self, pos):
        """Taşıma başlat"""
        # Eğer zaten state kaydedildiyse, tekrar kaydetme
        if self.drawing_widget._move_state_saved:
            return
        
        # Eğer zaten seçim varsa, taşımayı başlat
        if self.drawing_widget.selection_tool.selected_strokes:
            self.drawing_widget._move_state_saved = True
            self.drawing_widget.move_tool.start_move(pos)
            self.drawing_widget.update()
        else:
            # Seçim yoksa, önce seçim yap
            selected = self.drawing_widget.selection_tool.select_stroke_at_point(pos, self.drawing_widget.strokes)
            if self.drawing_widget.selection_tool.selected_strokes:
                self.drawing_widget._move_state_saved = True
                self.drawing_widget.move_tool.start_move(pos)
                self.drawing_widget.update()

    def handle_move_move(self, pos):
        """Taşıma devam ettir"""
        selected_strokes = self.drawing_widget.selection_tool.selected_strokes
        if self.drawing_widget.move_tool.update_move(pos, self.drawing_widget.strokes, selected_strokes):
            self.drawing_widget.update()

    def handle_move_release(self, pos):
        """Taşımayı tamamla"""
        # Move bitişinde final state'i kaydet
        if self.drawing_widget._move_state_saved:
            self.drawing_widget.save_current_state("Move end")
        
        self.drawing_widget.move_tool.finish_move()
        self.drawing_widget._move_state_saved = False

    def handle_rotate_press(self, pos):
        """Döndürme başlat"""
        # Eğer zaten state kaydedildiyse, tekrar kaydetme
        if self.drawing_widget._rotate_state_saved:
            return
            
        # Eğer zaten seçilmiş stroke'lar varsa, tutamak kontrolü yap
        if self.drawing_widget.selection_tool.selected_strokes:
            if self.drawing_widget.rotate_tool.start_rotate(pos, self.drawing_widget.strokes, self.drawing_widget.selection_tool.selected_strokes):
                self.drawing_widget._rotate_state_saved = True
                self.drawing_widget.update()
                return
        else:
            # Seçim yoksa, önce seçim yap
            selected = self.drawing_widget.selection_tool.select_stroke_at_point(pos, self.drawing_widget.strokes)
            if self.drawing_widget.selection_tool.selected_strokes:
                # Tutamakları oluştur ama döndürmeyi başlatma
                self.drawing_widget.rotate_tool.create_rotation_handles(self.drawing_widget.strokes, self.drawing_widget.selection_tool.selected_strokes)
                self.drawing_widget.update()

    def handle_rotate_move(self, pos):
        """Döndürme devam ettir"""
        # Mouse pozisyonunu kaydet (görsel feedback için)
        self.drawing_widget.rotate_tool.set_current_mouse_pos(pos)
        
        # Döndürme işlemi varsa güncelle
        if self.drawing_widget.rotate_tool.update_rotate(pos, self.drawing_widget.strokes, self.drawing_widget.selection_tool.selected_strokes):
            self.drawing_widget.update()

    def handle_rotate_release(self, pos):
        """Döndürmeyi tamamla"""
        # Rotate bitişinde final state'i kaydet
        if self.drawing_widget._rotate_state_saved:
            self.drawing_widget.save_current_state("Rotate end")
        
        self.drawing_widget.rotate_tool.finish_rotate()
        self.drawing_widget._rotate_state_saved = False

    def handle_scale_press(self, pos):
        """Boyutlandırma başlat"""
        # Eğer zaten state kaydedildiyse, tekrar kaydetme
        if self.drawing_widget._scale_state_saved:
            return
            
        # Eğer zaten seçilmiş stroke'lar varsa, tutamak kontrolü yap
        if self.drawing_widget.selection_tool.selected_strokes:
            if self.drawing_widget.scale_tool.start_scale(pos, self.drawing_widget.strokes, self.drawing_widget.selection_tool.selected_strokes):
                self.drawing_widget._scale_state_saved = True
                self.drawing_widget.update()
                return
        else:
            # Seçim yoksa, önce seçim yap
            selected = self.drawing_widget.selection_tool.select_stroke_at_point(pos, self.drawing_widget.strokes)
            if self.drawing_widget.selection_tool.selected_strokes:
                # Tutamakları oluştur ama boyutlandırmayı başlatma
                self.drawing_widget.scale_tool.create_scale_handles(self.drawing_widget.strokes, self.drawing_widget.selection_tool.selected_strokes)
                self.drawing_widget.update()

    def handle_scale_move(self, pos):
        """Boyutlandırma devam ettir"""
        # Mouse pozisyonunu kaydet (görsel feedback için)
        self.drawing_widget.scale_tool.set_current_mouse_pos(pos)
        
        # Boyutlandırma işlemi varsa güncelle
        if self.drawing_widget.scale_tool.update_scale(pos, self.drawing_widget.strokes, self.drawing_widget.selection_tool.selected_strokes):
            self.drawing_widget.update()

    def handle_scale_release(self, pos):
        """Boyutlandırmayı tamamla"""
        # Scale bitişinde final state'i kaydet
        if self.drawing_widget._scale_state_saved:
            self.drawing_widget.save_current_state("Scale end")
        
        self.drawing_widget.scale_tool.finish_scale()
        self.drawing_widget._scale_state_saved = False 