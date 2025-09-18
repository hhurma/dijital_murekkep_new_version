from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QListWidget,
    QListWidgetItem,
    QHBoxLayout,
    QToolButton,
    QLineEdit,
    QPushButton
)
from PyQt6.QtCore import Qt


class LayerItemWidget(QWidget):
    """Katman satırı için özel widget."""

    def __init__(self, layer_id, name, visible, locked, callbacks, parent=None):
        super().__init__(parent)
        self.layer_id = layer_id
        self._callbacks = callbacks

        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 0, 2, 0)
        layout.setSpacing(6)

        self.visibility_button = QToolButton(self)
        self.visibility_button.setCheckable(True)
        self.visibility_button.setAutoRaise(True)
        self.visibility_button.setToolTip("Katmanı görünür yap/gizle")
        self.visibility_button.setChecked(bool(visible))
        self._update_visibility_icon()
        self.visibility_button.toggled.connect(self._on_visibility_toggled)
        layout.addWidget(self.visibility_button)

        self.lock_button = QToolButton(self)
        self.lock_button.setCheckable(True)
        self.lock_button.setAutoRaise(True)
        self.lock_button.setToolTip("Katmanı kilitle/aç")
        self.lock_button.setChecked(bool(locked))
        self._update_lock_icon()
        self.lock_button.toggled.connect(self._on_lock_toggled)
        layout.addWidget(self.lock_button)

        self.name_edit = QLineEdit(name, self)
        self.name_edit.setFrame(False)
        self.name_edit.setToolTip("Katman adını düzenle")
        self.name_edit.editingFinished.connect(self._on_name_changed)
        layout.addWidget(self.name_edit, 1)

    def _on_visibility_toggled(self, checked):
        self._update_visibility_icon()
        callback = self._callbacks.get('visibility')
        if callback:
            callback(self.layer_id, checked)

    def _on_lock_toggled(self, checked):
        self._update_lock_icon()
        callback = self._callbacks.get('lock')
        if callback:
            callback(self.layer_id, checked)

    def _on_name_changed(self):
        callback = self._callbacks.get('rename')
        if callback:
            name = self.name_edit.text().strip() or "Layer"
            self.name_edit.setText(name)
            callback(self.layer_id, name)

    def _update_visibility_icon(self):
        if self.visibility_button.isChecked():
            self.visibility_button.setText("👁")
        else:
            self.visibility_button.setText("🚫")

    def _update_lock_icon(self):
        if self.lock_button.isChecked():
            self.lock_button.setText("🔒")
        else:
            self.lock_button.setText("🔓")


class LayerManagerWidget(QWidget):
    """Katmanları listeleyen ve yöneten panel."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.drawing_widget = None
        self._updating = False

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(6)

        self.layer_list = QListWidget(self)
        self.layer_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.layer_list.currentItemChanged.connect(self._on_selection_changed)
        main_layout.addWidget(self.layer_list, 1)

        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(4)

        self.add_button = QPushButton("+")
        self.add_button.setToolTip("Yeni katman ekle")
        self.add_button.clicked.connect(self._on_add_layer)
        controls_layout.addWidget(self.add_button)

        self.remove_button = QPushButton("-")
        self.remove_button.setToolTip("Seçili katmanı sil")
        self.remove_button.clicked.connect(self._on_remove_layer)
        controls_layout.addWidget(self.remove_button)

        self.up_button = QToolButton(self)
        self.up_button.setText("⬆")
        self.up_button.setToolTip("Katmanı yukarı taşı")
        self.up_button.clicked.connect(lambda: self._move_layer(direction=1))
        controls_layout.addWidget(self.up_button)

        self.down_button = QToolButton(self)
        self.down_button.setText("⬇")
        self.down_button.setToolTip("Katmanı aşağı taşı")
        self.down_button.clicked.connect(lambda: self._move_layer(direction=-1))
        controls_layout.addWidget(self.down_button)

        main_layout.addLayout(controls_layout)

    # ------------------------------------------------------------------
    # Drawing widget bağlantısı
    # ------------------------------------------------------------------
    def set_drawing_widget(self, drawing_widget):
        if self.drawing_widget is drawing_widget:
            return

        if self.drawing_widget:
            try:
                self.drawing_widget.layersChanged.disconnect(self.refresh_layers)
            except Exception:
                pass
            try:
                self.drawing_widget.activeLayerChanged.disconnect(self._on_active_layer_changed)
            except Exception:
                pass

        self.drawing_widget = drawing_widget

        if self.drawing_widget:
            self.drawing_widget.layersChanged.connect(self.refresh_layers)
            self.drawing_widget.activeLayerChanged.connect(self._on_active_layer_changed)

        self.refresh_layers()

    # ------------------------------------------------------------------
    # UI güncellemeleri
    # ------------------------------------------------------------------
    def refresh_layers(self):
        self._updating = True
        self.layer_list.clear()

        if not self.drawing_widget:
            self._updating = False
            self._update_controls()
            return

        layers = list(self.drawing_widget.get_layer_overview())
        active_id = self.drawing_widget.get_active_layer_id()

        # Görüntüde üstte olan layer listenin en üstünde görünsün
        display_layers = list(reversed(layers))

        for layer in display_layers:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, layer['id'])
            widget = LayerItemWidget(
                layer['id'],
                layer['name'],
                layer['visible'],
                layer['locked'],
                {
                    'visibility': self._on_visibility_changed,
                    'lock': self._on_lock_changed,
                    'rename': self._on_rename_layer
                },
                self.layer_list
            )
            item.setSizeHint(widget.sizeHint())
            self.layer_list.addItem(item)
            self.layer_list.setItemWidget(item, widget)

        self._updating = False
        self._select_layer(active_id)
        self._update_controls()

    def _select_layer(self, layer_id):
        if layer_id is None:
            self.layer_list.clearSelection()
            return

        for row in range(self.layer_list.count()):
            item = self.layer_list.item(row)
            if item.data(Qt.ItemDataRole.UserRole) == layer_id:
                self.layer_list.setCurrentRow(row)
                return

    def _update_controls(self):
        count = self.layer_list.count()
        has_selection = self.layer_list.currentRow() >= 0

        self.remove_button.setEnabled(count > 1 and has_selection)
        self.up_button.setEnabled(has_selection)
        self.down_button.setEnabled(has_selection)

        if has_selection and self.drawing_widget:
            item = self.layer_list.currentItem()
            layer_id = item.data(Qt.ItemDataRole.UserRole)
            order = [layer['id'] for layer in self.drawing_widget.layer_manager.iter_layers()]
            index = order.index(layer_id)
            self.up_button.setEnabled(index < len(order) - 1)
            self.down_button.setEnabled(index > 0)

    # ------------------------------------------------------------------
    # Kullanıcı etkileşimleri
    # ------------------------------------------------------------------
    def _on_selection_changed(self, current, previous):
        if self._updating or not self.drawing_widget or current is None:
            self._update_controls()
            return

        layer_id = current.data(Qt.ItemDataRole.UserRole)
        if layer_id:
            self.drawing_widget.set_active_layer(layer_id)
        self._update_controls()

    def _on_active_layer_changed(self, layer_id):
        if self._updating:
            return
        self._select_layer(layer_id)
        self._update_controls()

    def _on_visibility_changed(self, layer_id, visible):
        if not self.drawing_widget:
            return
        self.drawing_widget.set_layer_visibility(layer_id, visible)

    def _on_lock_changed(self, layer_id, locked):
        if not self.drawing_widget:
            return
        self.drawing_widget.set_layer_locked(layer_id, locked)

    def _on_rename_layer(self, layer_id, name):
        if not self.drawing_widget:
            return
        self.drawing_widget.rename_layer(layer_id, name)

    def _on_add_layer(self):
        if not self.drawing_widget:
            return
        self.drawing_widget.add_layer()
        self.refresh_layers()

    def _on_remove_layer(self):
        if not self.drawing_widget:
            return
        current_item = self.layer_list.currentItem()
        if not current_item:
            return
        layer_id = current_item.data(Qt.ItemDataRole.UserRole)
        if not layer_id:
            return

        removed = self.drawing_widget.delete_layer(layer_id)
        if not removed and hasattr(self.drawing_widget, 'main_window') and self.drawing_widget.main_window:
            self.drawing_widget.main_window.show_status_message("Son katman silinemez")
        self.refresh_layers()

    def _move_layer(self, direction):
        if not self.drawing_widget:
            return
        current_item = self.layer_list.currentItem()
        if not current_item:
            return
        layer_id = current_item.data(Qt.ItemDataRole.UserRole)
        if not layer_id:
            return

        order = [layer['id'] for layer in self.drawing_widget.layer_manager.iter_layers()]
        index = order.index(layer_id)
        new_index = index + direction
        new_index = max(0, min(new_index, len(order) - 1))

        if new_index != index:
            self.drawing_widget.move_layer(layer_id, new_index)
            self.refresh_layers()
            self._select_layer(layer_id)

