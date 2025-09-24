from typing import Optional, Callable

from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPen, QMouseEvent, QPainterPath, QColor, QBrush, QTabletEvent
from PyQt6.QtCore import Qt, QPoint, QPointF, QRect, QRectF, pyqtSignal
from scipy.interpolate import splprep, splev
import numpy as np
import time
import copy
from tablet_handler import TabletHandler
from event_handler import EventHandler
from canvas_renderer import CanvasRenderer
from pdf_importer import PdfBackgroundLayer
from throttle_manager import ThrottleManager

# Araç modüllerini import et
from selection_tool import SelectionTool
from move_tool import MoveTool
from rotate_tool import RotateTool
from scale_tool import ScaleTool
from bspline_tool import BSplineTool
from freehand_tool import FreehandTool
from eraser_tool import EraserTool
from line_tool import LineTool
from rectangle_tool import RectangleTool
from circle_tool import CircleTool
from stroke_handler import StrokeHandler


class LayerManager:
    """DrawingWidget içerisindeki katman yönetimini üstlenen sınıf."""

    def __init__(self, drawing_widget):
        self.drawing_widget = drawing_widget
        self.layers = {}
        self.layer_order = []
        self._id_counter = 0
        self.active_layer_id = None
        self.create_layer("Layer 1")

    # ------------------------------------------------------------------
    # Katman yardımcı metodları
    # ------------------------------------------------------------------
    def _generate_layer_id(self):
        self._id_counter += 1
        return f"layer_{self._id_counter}"

    def create_layer(self, name=None):
        layer_id = self._generate_layer_id()
        if name is None:
            name = f"Layer {len(self.layer_order) + 1}"

        self.layers[layer_id] = {
            'id': layer_id,
            'name': name,
            'visible': True,
            'locked': False,
            'strokes': []
        }
        self.layer_order.append(layer_id)

        if self.active_layer_id is None:
            self.active_layer_id = layer_id

        self._emit_changes()
        return layer_id

    def delete_layer(self, layer_id):
        if layer_id not in self.layers or len(self.layer_order) <= 1:
            return False

        was_active = layer_id == self.active_layer_id
        self.layer_order.remove(layer_id)
        self.layers.pop(layer_id, None)

        if was_active:
            self.active_layer_id = self.layer_order[-1]
            self.drawing_widget.selection_tool.clear_selection()
            self.drawing_widget.activeLayerChanged.emit(self.active_layer_id)

        self._emit_changes()
        return True

    def set_active_layer(self, layer_id):
        if layer_id in self.layers and layer_id in self.layer_order:
            if self.active_layer_id != layer_id:
                self.active_layer_id = layer_id
                self.drawing_widget.selection_tool.clear_selection()
                self.drawing_widget.activeLayerChanged.emit(layer_id)
                self._emit_changes(update_only=False)
            return True
        return False

    def get_active_layer(self):
        if self.active_layer_id is None:
            return None
        return self.layers.get(self.active_layer_id)

    def get_active_strokes(self):
        layer = self.get_active_layer()
        if not layer:
            return []
        return layer['strokes']

    def set_active_strokes(self, strokes):
        layer = self.get_active_layer()
        if layer is not None:
            layer['strokes'] = copy.deepcopy(list(strokes))
            self._emit_changes()

    def iter_layers(self):
        for layer_id in self.layer_order:
            layer = self.layers[layer_id]
            yield layer

    def iter_visible_layers(self):
        for layer in self.iter_layers():
            if layer['visible']:
                yield layer

    def is_active_layer_locked(self):
        layer = self.get_active_layer()
        return bool(layer and layer.get('locked'))

    def set_layer_visibility(self, layer_id, visible):
        if layer_id in self.layers:
            self.layers[layer_id]['visible'] = bool(visible)
            self._emit_changes()

    def set_layer_locked(self, layer_id, locked):
        if layer_id in self.layers:
            self.layers[layer_id]['locked'] = bool(locked)
            self._emit_changes()

    def rename_layer(self, layer_id, name):
        if layer_id in self.layers:
            self.layers[layer_id]['name'] = name
            self._emit_changes()

    def move_layer(self, layer_id, new_index):
        if layer_id not in self.layers:
            return False
        new_index = max(0, min(new_index, len(self.layer_order) - 1))
        current_index = self.layer_order.index(layer_id)
        if new_index == current_index:
            return False
        self.layer_order.pop(current_index)
        self.layer_order.insert(new_index, layer_id)
        self._emit_changes()
        return True

    def clear_all(self):
        for layer in self.layers.values():
            layer['strokes'].clear()
        self._emit_changes()

    def export_state(self):
        return {
            'active_layer': self.active_layer_id,
            'layer_order': list(self.layer_order),
            'layers': {
                layer_id: {
                    'id': layer_id,
                    'name': layer_data['name'],
                    'visible': layer_data['visible'],
                    'locked': layer_data['locked'],
                    'strokes': copy.deepcopy(layer_data['strokes'])
                }
                for layer_id, layer_data in self.layers.items()
            }
        }

    def import_state(self, state):
        self.layers = {}
        self.layer_order = list(state.get('layer_order', []))
        self.active_layer_id = state.get('active_layer')

        state_layers = state.get('layers', {})
        for layer_id in state_layers.keys():
            if layer_id not in self.layer_order:
                self.layer_order.append(layer_id)

        for layer_id in self.layer_order:
            layer_data = state_layers.get(layer_id, {})
            self.layers[layer_id] = {
                'id': layer_id,
                'name': layer_data.get('name', layer_id),
                'visible': layer_data.get('visible', True),
                'locked': layer_data.get('locked', False),
                'strokes': copy.deepcopy(layer_data.get('strokes', []))
            }

        if not self.layer_order:
            self.layers = {}
            self.layer_order = []
            self.active_layer_id = None
            self.create_layer("Layer 1")

        if self.active_layer_id not in self.layers:
            self.active_layer_id = self.layer_order[-1]

        # ID sayacını güncelle
        numeric_ids = []
        for layer_id in self.layer_order:
            parts = layer_id.split('_')
            if parts[-1].isdigit():
                numeric_ids.append(int(parts[-1]))
        if numeric_ids:
            self._id_counter = max(numeric_ids)
        else:
            self._id_counter = len(self.layer_order)

        # Güncelleme sinyallerini gönder
        self._emit_changes(update_only=False)
        self.drawing_widget.activeLayerChanged.emit(self.active_layer_id)

    def count_visible_strokes(self):
        count = 0
        for layer in self.iter_visible_layers():
            count += len(layer['strokes'])
        return count

    def _emit_changes(self, update_only=True):
        self.drawing_widget.layersChanged.emit()
        if not update_only:
            self.drawing_widget.activeLayerChanged.emit(self.active_layer_id)

class DrawingWidget(QWidget):
    layersChanged = pyqtSignal()
    activeLayerChanged = pyqtSignal(str)

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
        
        # PDF arka plan katmanı ve sayfa durumları (update_canvas_size öncesi gerekli)
        self.pdf_background_layer: Optional[PdfBackgroundLayer] = None
        self.pdf_page_states = {}
        self.update_canvas_size()
        
        # Katman yöneticisi
        self.layer_manager = LayerManager(self)

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
            'grid_width': 1,
            'major_grid_color': Qt.GlobalColor.gray,
            'major_grid_width': 2,
            'major_grid_interval': 5,
            'minor_grid_interval': 1.0,
            'grid_opacity': 1.0,
            'snap_to_grid': False
        }
        
        # Ayrı grid ayarları (snap grid için)
        self.grid_settings = {
            'enabled': False,
            'snap_grid_color': QColor(100, 100, 255),
            'snap_major_grid_color': QColor(50, 50, 200),
            'snap_grid_size': 20,
            'snap_grid_width': 1,
            'snap_major_grid_width': 2,
            'snap_major_grid_interval': 5,
            'snap_grid_opacity': 0.5,
            'snap_to_grid': False
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
        self.eraser_tool = EraserTool()  # Silgi aracı
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

    # ------------------------------------------------------------------
    # Katman yardımcı metodları
    # ------------------------------------------------------------------
    @property
    def strokes(self):
        return self.layer_manager.get_active_strokes()

    @strokes.setter
    def strokes(self, value):
        self.layer_manager.set_active_strokes(value)
        self.update()
        # Katman listesini güncelle
        self.layer_manager._emit_changes()

    def get_layer_overview(self):
        return list(self.layer_manager.iter_layers())

    def add_layer(self, name=None):
        self.save_current_state("Add layer")
        layer_id = self.layer_manager.create_layer(name)
        self.layer_manager.set_active_layer(layer_id)
        self.update()
        return layer_id

    def delete_layer(self, layer_id):
        if layer_id in self.layer_manager.layers and len(self.layer_manager.layer_order) > 1:
            self.save_current_state("Delete layer")
        removed = self.layer_manager.delete_layer(layer_id)
        if removed:
            self.update()
        return removed

    def set_active_layer(self, layer_id):
        if self.layer_manager.set_active_layer(layer_id):
            self.update()
            return True
        return False

    def is_active_layer_locked(self):
        return self.layer_manager.is_active_layer_locked()

    def get_active_layer_id(self):
        return self.layer_manager.active_layer_id

    def set_layer_visibility(self, layer_id, visible):
        layer = self.layer_manager.layers.get(layer_id)
        if layer and layer.get('visible') == bool(visible):
            return
        self.save_current_state("Change layer visibility")
        self.layer_manager.set_layer_visibility(layer_id, visible)
        self.update()

    def set_layer_locked(self, layer_id, locked):
        layer = self.layer_manager.layers.get(layer_id)
        if layer and layer.get('locked') == bool(locked):
            return
        self.save_current_state("Change layer lock")
        self.layer_manager.set_layer_locked(layer_id, locked)
        self.update()

    def rename_layer(self, layer_id, name):
        layer = self.layer_manager.layers.get(layer_id)
        if layer and layer.get('name') == name:
            return
        self.save_current_state("Rename layer")
        self.layer_manager.rename_layer(layer_id, name)
        self.update()

    def move_layer(self, layer_id, new_index):
        if layer_id not in self.layer_manager.layers:
            return
        current_index = self.layer_manager.layer_order.index(layer_id)
        if current_index == new_index:
            return
        self.save_current_state("Reorder layer")
        if self.layer_manager.move_layer(layer_id, new_index):
            self.update()

    def ensure_layer_editable(self):
        """Aktif katmanın düzenlenebilir olduğunu kontrol et"""
        layer = self.layer_manager.get_active_layer()
        if not layer:
            return False

        if layer.get('locked'):
            if self.main_window:
                self.main_window.show_status_message("Aktif katman kilitli")
            return False

        if not layer.get('visible', True):
            if self.main_window:
                self.main_window.show_status_message("Gizli katmanda düzenleme yapılamaz")
            return False

        return True

    def update_canvas_size(self):
        """Canvas boyutunu mevcut yönlendirmeye göre güncelle"""
        if self.pdf_background_layer and self.pdf_background_layer.has_document():
            page_size = self.pdf_background_layer.get_current_page_size()
            if page_size:
                self.setFixedSize(page_size.width(), page_size.height())
                self.update()
                return

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

    def set_eraser_radius(self, radius: float):
        if hasattr(self, 'eraser_tool'):
            self.eraser_tool.set_radius(radius)
        
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
        try:
            if self.main_window and hasattr(self.main_window, 'settings'):
                self.main_window.settings.set_fill_defaults({'enabled': filled})
        except Exception:
            pass
            
    def set_current_opacity(self, opacity):
        """Aktif opacity'yi ayarla ve araçlara bildir"""
        self.current_opacity = opacity
        
        # Şekil araçlarına opacity bildir
        if hasattr(self.rectangle_tool, 'set_fill_opacity'):
            self.rectangle_tool.set_fill_opacity(opacity)
        if hasattr(self.circle_tool, 'set_fill_opacity'):
            self.circle_tool.set_fill_opacity(opacity)
        # Varsayılan dolguya yaz
        try:
            if self.main_window and hasattr(self.main_window, 'settings'):
                self.main_window.settings.set_fill_defaults({'opacity': opacity})
        except Exception:
            pass
            
    def set_fill_opacity(self, opacity):
        """Fill opacity'yi ayarla ve araçlara bildir"""
        # Şekil araçlarına fill opacity bildir
        if hasattr(self.rectangle_tool, 'set_fill_opacity'):
            self.rectangle_tool.set_fill_opacity(opacity)
        if hasattr(self.circle_tool, 'set_fill_opacity'):
            self.circle_tool.set_fill_opacity(opacity)
        # Varsayılan dolgu opacity'ye yaz
        try:
            if self.main_window and hasattr(self.main_window, 'settings'):
                self.main_window.settings.set_fill_defaults({'opacity': opacity})
        except Exception:
            pass
            
    def set_fill_color(self, color):
        """Dolgu rengini ayarla ve araçlara bildir"""
        from PyQt6.QtGui import QColor
        self.fill_color = QColor(color)
        
        # Şekil araçlarına dolgu rengi bildir
        if hasattr(self.rectangle_tool, 'set_fill_color'):
            self.rectangle_tool.set_fill_color(self.fill_color)
        if hasattr(self.circle_tool, 'set_fill_color'):
            self.circle_tool.set_fill_color(self.fill_color)
        try:
            if self.main_window and hasattr(self.main_window, 'settings'):
                self.main_window.settings.set_fill_defaults({'color': self.fill_color})
        except Exception:
            pass
            
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
            
    def set_shadow_settings(self, shadow_settings):
        """Gölge ayarlarını şekil araçlarına bildir"""
        if hasattr(self.rectangle_tool, 'set_shadow_enabled'):
            self.rectangle_tool.set_shadow_enabled(shadow_settings.get('has_shadow', False))
        if hasattr(self.rectangle_tool, 'set_shadow_color'):
            self.rectangle_tool.set_shadow_color(shadow_settings.get('shadow_color'))
        if hasattr(self.rectangle_tool, 'set_shadow_offset'):
            self.rectangle_tool.set_shadow_offset(
                shadow_settings.get('shadow_offset_x', 0),
                shadow_settings.get('shadow_offset_y', 0)
            )
        if hasattr(self.rectangle_tool, 'set_shadow_blur'):
            self.rectangle_tool.set_shadow_blur(shadow_settings.get('shadow_blur', 5))
        if hasattr(self.rectangle_tool, 'set_shadow_size'):
            self.rectangle_tool.set_shadow_size(shadow_settings.get('shadow_size', 0))
        if hasattr(self.rectangle_tool, 'set_shadow_opacity'):
            self.rectangle_tool.set_shadow_opacity(shadow_settings.get('shadow_opacity', 0.7))
        if hasattr(self.rectangle_tool, 'set_inner_shadow'):
            self.rectangle_tool.set_inner_shadow(shadow_settings.get('inner_shadow', False))
        if hasattr(self.rectangle_tool, 'set_shadow_quality'):
            self.rectangle_tool.set_shadow_quality(shadow_settings.get('shadow_quality', 'medium'))
            
        # Circle tool için de aynı ayarları uygula
        if hasattr(self.circle_tool, 'set_shadow_enabled'):
            self.circle_tool.set_shadow_enabled(shadow_settings.get('has_shadow', False))
        if hasattr(self.circle_tool, 'set_shadow_color'):
            self.circle_tool.set_shadow_color(shadow_settings.get('shadow_color'))
        if hasattr(self.circle_tool, 'set_shadow_offset'):
            self.circle_tool.set_shadow_offset(
                shadow_settings.get('shadow_offset_x', 0),
                shadow_settings.get('shadow_offset_y', 0)
            )
        if hasattr(self.circle_tool, 'set_shadow_blur'):
            self.circle_tool.set_shadow_blur(shadow_settings.get('shadow_blur', 5))
        if hasattr(self.circle_tool, 'set_shadow_size'):
            self.circle_tool.set_shadow_size(shadow_settings.get('shadow_size', 0))
        if hasattr(self.circle_tool, 'set_shadow_opacity'):
            self.circle_tool.set_shadow_opacity(shadow_settings.get('shadow_opacity', 0.7))
        if hasattr(self.circle_tool, 'set_inner_shadow'):
            self.circle_tool.set_inner_shadow(shadow_settings.get('inner_shadow', False))
        if hasattr(self.circle_tool, 'set_shadow_quality'):
            self.circle_tool.set_shadow_quality(shadow_settings.get('shadow_quality', 'medium'))
            
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
        
    def set_grid_settings(self, settings):
        """Grid ayarlarını güncelle"""
        self.grid_settings = settings

        # Artık snap sadece grid_settings'ten okunuyor; background_settings'e yansıtma yok

        # Snap-destekli araçlara grid ayarlarını bildir
        if hasattr(self.line_tool, 'grid_settings'):
            self.line_tool.grid_settings = settings
        if hasattr(self.rectangle_tool, 'grid_settings'):
            self.rectangle_tool.grid_settings = settings
        if hasattr(self.circle_tool, 'grid_settings'):
            self.circle_tool.grid_settings = settings
        
        # Dönüştürme araçlarına da grid ayarlarını bildir
        if hasattr(self.rotate_tool, 'grid_settings'):
            self.rotate_tool.grid_settings = settings
        if hasattr(self.scale_tool, 'grid_settings'):
            self.scale_tool.grid_settings = settings
        if hasattr(self.move_tool, 'grid_settings'):
            self.move_tool.grid_settings = settings

        self.update()  # Yeniden çiz

    # ------------------------------------------------------------------
    # PDF arka planı kontrol metodları
    # ------------------------------------------------------------------
    def _initialize_pdf_page_states(self, page_count: int):
        self.pdf_page_states = {index: None for index in range(page_count)}

    def _create_blank_page_state(self):
        blank_state = self.layer_manager.export_state()
        for layer_data in blank_state.get('layers', {}).values():
            layer_data['strokes'] = []
        return blank_state

    def _save_current_pdf_page_state(self):
        if not self.pdf_background_layer or not self.pdf_background_layer.has_document():
            return
        page_index = self.pdf_background_layer.current_page
        self.pdf_page_states[page_index] = self.layer_manager.export_state()

    def _load_pdf_page_state(self, page_index: int):
        if not self.pdf_background_layer or not self.pdf_background_layer.has_document():
            return
        state = self.pdf_page_states.get(page_index)
        if state is None:
            state = self._create_blank_page_state()
            self.pdf_page_states[page_index] = state
        self.layer_manager.import_state(state)
        self.selection_tool.clear_selection()
        self.update_shape_properties()
        self.update()

    def _apply_pdf_page_change(self, change_callable: Callable[[], bool]):
        if not self.pdf_background_layer or not self.pdf_background_layer.has_document():
            return change_callable()

        previous_page = self.pdf_background_layer.current_page
        self._save_current_pdf_page_state()
        changed = change_callable()
        new_page = self.pdf_background_layer.current_page

        if changed or new_page != previous_page:
            self._load_pdf_page_state(new_page)

        return changed

    def has_pdf_background(self) -> bool:
        return bool(self.pdf_background_layer and self.pdf_background_layer.has_document())

    def set_pdf_background_layer(self, layer: Optional[PdfBackgroundLayer]):
        if self.pdf_background_layer and self.pdf_background_layer.has_document():
            self._save_current_pdf_page_state()

        current_state = self.layer_manager.export_state()

        self.pdf_background_layer = layer

        if layer and layer.has_document():
            self._initialize_pdf_page_states(layer.page_count)
            self.pdf_page_states[layer.current_page] = current_state
        else:
            self.pdf_page_states = {}

        self.selection_tool.clear_selection()
        self.update_shape_properties()
        self.update_canvas_size()
        self.update()

    def get_pdf_background_layer(self) -> Optional[PdfBackgroundLayer]:
        return self.pdf_background_layer

    def clear_pdf_background(self):
        if self.pdf_background_layer and self.pdf_background_layer.has_document():
            self._save_current_pdf_page_state()
        self.pdf_background_layer = None
        self.pdf_page_states = {}
        self.update_canvas_size()
        self.update()

    def next_pdf_page(self) -> bool:
        if not self.pdf_background_layer:
            return False
        changed = self._apply_pdf_page_change(self.pdf_background_layer.next_page)
        if changed:
            self.update_canvas_size()
        return changed

    def previous_pdf_page(self) -> bool:
        if not self.pdf_background_layer:
            return False
        changed = self._apply_pdf_page_change(self.pdf_background_layer.previous_page)
        if changed:
            self.update_canvas_size()
        return changed

    def set_pdf_dpi(self, dpi: int) -> bool:
        if not self.pdf_background_layer:
            return False
        def _set_dpi():
            return self.pdf_background_layer.set_dpi(dpi)

        changed = self._apply_pdf_page_change(_set_dpi)
        if changed:
            self.update_canvas_size()
        return changed

    def go_to_pdf_page(self, index: int) -> bool:
        """PDF arka planında belirli sayfaya git ve ilgili katman durumunu yükle."""
        if not self.pdf_background_layer:
            return False
        def _set_page():
            return self.pdf_background_layer.set_current_page(index)
        changed = self._apply_pdf_page_change(_set_page)
        if changed:
            self.update_canvas_size()
        return changed

    def export_pdf_page_states(self):
        if not self.pdf_background_layer or not self.pdf_background_layer.has_document():
            return None
        self._save_current_pdf_page_state()
        return {index: state for index, state in self.pdf_page_states.items()}

    def get_pdf_page_layer_states(self):
        if not self.has_pdf_background():
            return None

        self._save_current_pdf_page_state()

        page_states = {}
        for index, state in self.pdf_page_states.items():
            if state is None:
                continue
            page_states[index] = copy.deepcopy(state)

        return {
            'page_count': self.pdf_background_layer.page_count,
            'current_page': self.pdf_background_layer.current_page,
            'page_states': page_states
        }

    def import_pdf_page_states(self, payload):
        if not self.pdf_background_layer or not self.pdf_background_layer.has_document():
            return

        if not payload:
            self._initialize_pdf_page_states(self.pdf_background_layer.page_count)
            self._load_pdf_page_state(self.pdf_background_layer.current_page)
            return

        target_page = None
        page_states = payload

        if isinstance(payload, dict) and 'page_states' in payload:
            page_states = payload.get('page_states', {})
            target_page = payload.get('current_page')

        self._initialize_pdf_page_states(self.pdf_background_layer.page_count)

        for key, state in (page_states or {}).items():
            try:
                index = int(key)
            except (TypeError, ValueError):
                continue

            if 0 <= index < self.pdf_background_layer.page_count:
                self.pdf_page_states[index] = copy.deepcopy(state) if state is not None else None

        if isinstance(target_page, int):
            self.pdf_background_layer.set_current_page(max(0, min(target_page, self.pdf_background_layer.page_count - 1)))

        current_page = self.pdf_background_layer.current_page
        self._load_pdf_page_state(current_page)

    def export_pdf_background_state(self):
        if not self.pdf_background_layer or not self.pdf_background_layer.has_document():
            return None
        return {
            'source_path': self.pdf_background_layer.source_path,
            'page_count': self.pdf_background_layer.page_count,
            'current_page': self.pdf_background_layer.current_page,
            'dpi': self.pdf_background_layer.dpi
        }

    def import_pdf_background_state(self, state, pdf_importer=None):
        if not state or 'source_path' not in state:
            self.clear_pdf_background()
            return

        importer = pdf_importer
        if importer is None and self.main_window and hasattr(self.main_window, 'pdf_importer'):
            importer = self.main_window.pdf_importer

        if importer is None:
            return

        try:
            layer = importer.load_pdf(state['source_path'], dpi=state.get('dpi', 150))
        except Exception:
            return

        if layer:
            page_index = state.get('current_page', 0)
            layer.set_current_page(page_index)
            self.set_pdf_background_layer(layer)
            
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
        # Zoom manager'dan güncel zoom ve pan değerlerini al
        current_zoom = self.zoom_level
        current_offset = self.zoom_offset
        
        if hasattr(self, 'zoom_manager'):
            current_zoom = self.zoom_manager.get_zoom_level()
            current_offset = self.zoom_manager.get_pan_offset()
        
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
            self.undo_manager.save_state(self.layer_manager.export_state(), description)

    def undo(self):
        """Geri al"""
        if self.undo_manager:
            previous_state = self.undo_manager.undo()
            if previous_state is not None:
                self.layer_manager.import_state(previous_state)
                self.update()
                # Seçimi temizle
                self.selection_tool.clear_selection()
                self.update_shape_properties()

    def redo(self):
        """İleri al"""
        if self.undo_manager:
            next_state = self.undo_manager.redo()
            if next_state is not None:
                self.layer_manager.import_state(next_state)
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
                # Seçim var - içeriği güncelle; görünürlüğe kullanıcı kararı saygı duy
                self.main_window.shape_properties_widget.set_selected_strokes(selected_strokes, self.strokes)
                if hasattr(self.main_window, 'shape_properties_dock') and self.main_window.settings.get_shape_properties_dock_visible():
                    self.main_window.shape_properties_dock.show()
            else:
                # Seçim yok - dock'u gizle
                # Panel kullanıcı kapatmadıkça görünür kalsın; sadece içeriği boş moda al
                self.main_window.shape_properties_widget.set_no_selection()
        
        # Katman panelini de güncelle
        if self.main_window and hasattr(self.main_window, 'layer_manager_widget'):
            try:
                self.main_window.layer_manager_widget._on_canvas_selection_changed()
            except Exception:
                pass

    def send_selected_backward(self):
        """Seçili şekilleri bir basamak alta gönder (aynı katman içinde)."""
        if not self.ensure_layer_editable():
            return
        if not self.selection_tool.selected_strokes:
            return

        strokes_list = list(self.strokes)
        total = len(strokes_list)
        if total <= 1:
            return

        # Undo
        self.save_current_state("Send backward")

        # Seçili index'leri işaretle
        selected_flags = [False] * total
        for idx in self.selection_tool.selected_strokes:
            if 0 <= idx < total:
                selected_flags[idx] = True

        # Tek geçişte bir basamak geri taşı (bubble pass)
        for i in range(1, total):
            if selected_flags[i] and not selected_flags[i - 1]:
                strokes_list[i - 1], strokes_list[i] = strokes_list[i], strokes_list[i - 1]
                selected_flags[i - 1], selected_flags[i] = selected_flags[i], selected_flags[i - 1]

        # Yeni seçim index'leri
        new_selected = [i for i, flag in enumerate(selected_flags) if flag]

        # Uygula
        self.strokes = strokes_list
        self.selection_tool.selected_strokes = new_selected
        self.update_shape_properties()
        self.update()

    def send_selected_to_back(self):
        """Seçili şekilleri en alta gönder (aynı katman içinde)."""
        if not self.ensure_layer_editable():
            return
        if not self.selection_tool.selected_strokes:
            return

        strokes_list = list(self.strokes)
        total = len(strokes_list)
        if total <= 1:
            return

        # Undo
        self.save_current_state("Send to back")

        selected_set = set(i for i in self.selection_tool.selected_strokes if 0 <= i < total)
        if not selected_set:
            return

        # Sıra korumalı yeniden dizilim
        selected_items = [strokes_list[i] for i in range(total) if i in selected_set]
        non_selected_items = [strokes_list[i] for i in range(total) if i not in selected_set]
        new_order = selected_items + non_selected_items

        # Yeni seçim index'leri: 0..len(selected)-1
        new_selected = list(range(len(selected_items)))

        # Uygula
        self.strokes = new_order
        self.selection_tool.selected_strokes = new_selected
        self.update_shape_properties()
        self.update()

    def send_selected_forward(self):
        """Seçili şekilleri bir basamak üste gönder (aynı katman içinde)."""
        if not self.ensure_layer_editable():
            return
        if not self.selection_tool.selected_strokes:
            return

        strokes_list = list(self.strokes)
        total = len(strokes_list)
        if total <= 1:
            return

        # Undo
        self.save_current_state("Send forward")

        selected_flags = [False] * total
        for idx in self.selection_tool.selected_strokes:
            if 0 <= idx < total:
                selected_flags[idx] = True

        # Tersten geçişte bir basamak ileri taşı (üst)
        for i in range(total - 2, -1, -1):
            if selected_flags[i] and not selected_flags[i + 1]:
                strokes_list[i + 1], strokes_list[i] = strokes_list[i], strokes_list[i + 1]
                selected_flags[i + 1], selected_flags[i] = selected_flags[i], selected_flags[i + 1]

        new_selected = [i for i, flag in enumerate(selected_flags) if flag]

        self.strokes = strokes_list
        self.selection_tool.selected_strokes = new_selected
        self.update_shape_properties()
        self.update()

    def send_selected_to_front(self):
        """Seçili şekilleri en üste gönder (aynı katman içinde)."""
        if not self.ensure_layer_editable():
            return
        if not self.selection_tool.selected_strokes:
            return

        strokes_list = list(self.strokes)
        total = len(strokes_list)
        if total <= 1:
            return

        # Undo
        self.save_current_state("Send to front")

        selected_set = set(i for i in self.selection_tool.selected_strokes if 0 <= i < total)
        if not selected_set:
            return

        selected_items = [strokes_list[i] for i in range(total) if i in selected_set]
        non_selected_items = [strokes_list[i] for i in range(total) if i not in selected_set]
        new_order = non_selected_items + selected_items

        # Yeni seçim index'leri: son N
        start = len(non_selected_items)
        new_selected = list(range(start, start + len(selected_items)))

        self.strokes = new_order
        self.selection_tool.selected_strokes = new_selected
        self.update_shape_properties()
        self.update()

    def clear_all_strokes(self):
        """Tüm çizimleri temizle"""
        has_strokes = any(layer['strokes'] for layer in self.layer_manager.iter_layers())
        if has_strokes:  # Sadece çizim varsa kaydet
            self.save_current_state("Clear all")
        self.layer_manager.clear_all()
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
