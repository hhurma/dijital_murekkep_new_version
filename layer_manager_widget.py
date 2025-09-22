from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QListWidgetItem,
    QHBoxLayout,
    QToolButton,
    QLineEdit,
    QPushButton
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QHeaderView


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

        self.layer_tree = QTreeWidget(self)
        self.layer_tree.setHeaderHidden(True)
        self.layer_tree.setColumnCount(2)
        # Basit kolon düzeni - şekil isimleri tamamen görünsün
        self.layer_tree.setColumnWidth(0, 150)  # Şekil isimleri için
        self.layer_tree.setColumnWidth(1, 120)  # Kontroller için
        self.layer_tree.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
        self.layer_tree.currentItemChanged.connect(self._on_selection_changed)
        self.layer_tree.itemClicked.connect(self._on_item_clicked)
        main_layout.addWidget(self.layer_tree, 1)

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
            # Canvas seçimi değiştiğinde paneli güncelle
            if hasattr(self.drawing_widget, 'selection_tool'):
                try:
                    # Seçim değişimi sinyali varsa bağla
                    if hasattr(self.drawing_widget.selection_tool, 'selectionChanged'):
                        self.drawing_widget.selection_tool.selectionChanged.connect(self._on_canvas_selection_changed)
                except Exception:
                    pass

        self.refresh_layers()
        # UI stabilize olsun diye bir sonraki event döngüsünde tekrar yenile
        QTimer.singleShot(0, self.refresh_layers)

    # ------------------------------------------------------------------
    # UI güncellemeleri
    # ------------------------------------------------------------------
    def refresh_layers(self):
        self._updating = True
        
        # Basit yenileme - expand durumunu koruma
        was_expanded = False
        if self.layer_tree.topLevelItemCount() > 0:
            was_expanded = self.layer_tree.topLevelItem(0).isExpanded()

        self.layer_tree.clear()

        if not self.drawing_widget:
            self._updating = False
            self._update_controls()
            return

        layers = list(self.drawing_widget.get_layer_overview())
        active_id = self.drawing_widget.get_active_layer_id()

        # Görüntüde üstte olan layer listenin en üstünde görünsün
        display_layers = list(reversed(layers))

        for layer in display_layers:
            # Katman üst düğümü
            layer_item = QTreeWidgetItem(self.layer_tree)
            layer_item.setText(0, layer['name'])
            layer_item.setData(0, Qt.ItemDataRole.UserRole, layer['id'])
            layer_item.setData(0, Qt.ItemDataRole.UserRole + 1, 'layer')

            # Katman satırı için custom widget (görünür/kilit/ad)
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
                self.layer_tree
            )
            # Widget'ı ikinci kolona koy ki expand oku ve isim korunabilsin
            self.layer_tree.setItemWidget(layer_item, 1, widget)

            # Şekilleri (strokeleri) ekle - üstte olan önce gözüksün
            strokes = layer.get('strokes', [])
            self._populate_shapes_for_layer(layer_item, strokes)

        # İlk katmanı aç
        if self.layer_tree.topLevelItemCount() > 0:
            self.layer_tree.topLevelItem(0).setExpanded(True)

        self._updating = False
        self._select_layer(active_id)
        self._update_controls()

    def _select_layer(self, layer_id):
        if layer_id is None:
            self.layer_tree.clearSelection()
            return

        for i in range(self.layer_tree.topLevelItemCount()):
            item = self.layer_tree.topLevelItem(i)
            if item.data(0, Qt.ItemDataRole.UserRole) == layer_id:
                self.layer_tree.setCurrentItem(item)
                return

    def _update_controls(self):
        count = self.layer_tree.topLevelItemCount()
        has_selection = self.layer_tree.currentItem() is not None

        self.remove_button.setEnabled(count > 1 and has_selection)
        self.up_button.setEnabled(has_selection)
        self.down_button.setEnabled(has_selection)

        if has_selection and self.drawing_widget:
            current = self.layer_tree.currentItem()
            # Eğer bir alt öğe seçiliyse üst katmanını al
            layer_item = current
            while layer_item and layer_item.parent() is not None:
                layer_item = layer_item.parent()
            layer_id = layer_item.data(0, Qt.ItemDataRole.UserRole) if layer_item else None
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

        # Geçerli item bilgilerini hemen oku ve uygulamayı event döngüsüne ertele
        try:
            node_type = current.data(0, Qt.ItemDataRole.UserRole + 1)
        except RuntimeError:
            node_type = None

        if node_type not in ('layer', 'stroke', 'group'):
            self._update_controls()
            return

        # Gerekli değerleri kopyala
        layer_id_val = None
        selection_payload = None
        try:
            if node_type == 'layer':
                layer_id_val = current.data(0, Qt.ItemDataRole.UserRole)
            else:
                parent = current.parent()
                layer_id_val = parent.data(0, Qt.ItemDataRole.UserRole) if parent else None
                selection_payload = current.data(0, Qt.ItemDataRole.UserRole)
        except RuntimeError:
            layer_id_val = None
            selection_payload = None

        # Çoklu seçim desteği
        selected_items = self.layer_tree.selectedItems()
        if not selected_items:
            return

        # Tüm seçili stroke/grup indekslerini topla
        all_selected_indices = []
        active_layer_id = None

        for item in selected_items:
            try:
                item_node_type = item.data(0, Qt.ItemDataRole.UserRole + 1)
                if item_node_type == 'layer':
                    layer_id = item.data(0, Qt.ItemDataRole.UserRole)
                    if layer_id and not active_layer_id:
                        active_layer_id = layer_id
                elif item_node_type in ('stroke', 'group'):
                    parent = item.parent()
                    layer_id = parent.data(0, Qt.ItemDataRole.UserRole) if parent else None
                    if layer_id and not active_layer_id:
                        active_layer_id = layer_id
                    
                    item_payload = item.data(0, Qt.ItemDataRole.UserRole)
                    if item_node_type == 'stroke' and isinstance(item_payload, int):
                        if item_payload not in all_selected_indices:
                            all_selected_indices.append(item_payload)
                    elif item_node_type == 'group' and isinstance(item_payload, list):
                        for idx in item_payload:
                            if idx not in all_selected_indices:
                                all_selected_indices.append(idx)
            except RuntimeError:
                continue

        # Aktif katmanı ayarla
        if active_layer_id:
            self.drawing_widget.set_active_layer(active_layer_id)

        # Seçimi uygula
        if all_selected_indices:
            self.drawing_widget.selection_tool.selected_strokes = all_selected_indices
            self.drawing_widget.set_active_tool('select')
            self.drawing_widget.update_shape_properties()
            self.drawing_widget.update()

        self._update_controls()

    def _on_item_clicked(self, item, column):
        # Aynı davranışı tıklamada da uygula (çift yönlü güvence)
        self._on_selection_changed(item, None)

    def _on_active_layer_changed(self, layer_id):
        if self._updating:
            return
        self._select_layer(layer_id)
        self._update_controls()

    def _on_canvas_selection_changed(self):
        """Canvas'ta seçim değiştiğinde katman panelinde vurgula"""
        if self._updating or not self.drawing_widget:
            return
        
        selected_strokes = self.drawing_widget.selection_tool.selected_strokes
        if not selected_strokes:
            self.layer_tree.clearSelection()
            return
        
        # Seçili stroke'ları ağaçta bul ve vurgula
        self._updating = True
        self.layer_tree.clearSelection()
        
        for i in range(self.layer_tree.topLevelItemCount()):
            layer_item = self.layer_tree.topLevelItem(i)
            self._select_strokes_in_tree(layer_item, selected_strokes)
        
        self._updating = False

    def _select_strokes_in_tree(self, parent_item, selected_strokes):
        """Ağaçta belirtilen stroke'ları seç"""
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            node_type = child.data(0, Qt.ItemDataRole.UserRole + 1)
            
            if node_type == 'stroke':
                stroke_idx = child.data(0, Qt.ItemDataRole.UserRole)
                if stroke_idx in selected_strokes:
                    child.setSelected(True)
            elif node_type == 'group':
                group_indices = child.data(0, Qt.ItemDataRole.UserRole)
                if isinstance(group_indices, list) and any(idx in selected_strokes for idx in group_indices):
                    child.setSelected(True)
                # Grup alt öğelerini de kontrol et
                self._select_strokes_in_tree(child, selected_strokes)

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
        current_item = self.layer_tree.currentItem()
        if not current_item:
            return
        # Alt öğe seçiliyse üst katmanı al
        while current_item and current_item.parent() is not None:
            current_item = current_item.parent()
        layer_id = current_item.data(0, Qt.ItemDataRole.UserRole)
        if not layer_id:
            return

        removed = self.drawing_widget.delete_layer(layer_id)
        if not removed and hasattr(self.drawing_widget, 'main_window') and self.drawing_widget.main_window:
            self.drawing_widget.main_window.show_status_message("Son katman silinemez")
        self.refresh_layers()

    def _move_layer(self, direction):
        if not self.drawing_widget:
            return
        current_item = self.layer_tree.currentItem()
        if not current_item:
            return
        # Alt öğe seçiliyse üst katmanı al
        while current_item and current_item.parent() is not None:
            current_item = current_item.parent()
        layer_id = current_item.data(0, Qt.ItemDataRole.UserRole)
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

    # ------------------------------------------------------------------
    # Yardımcılar: şekil listesi oluşturma ve grup tespiti
    # ------------------------------------------------------------------
    def _populate_shapes_for_layer(self, layer_item, strokes):
        visited_indices = set()

        # Z üstte olan önce görünsün: sondan başa
        for idx in range(len(strokes) - 1, -1, -1):
            if idx in visited_indices:
                continue
            stroke = strokes[idx]

            group_id = self._get_stroke_group_id(stroke)
            if group_id:
                members = self._find_group_members_indices(strokes, group_id)
                print(f"DEBUG: Found group {group_id} with {len(members)} members: {members}")
                # Tüm üyeleri visited işaretle
                for m in members:
                    visited_indices.add(m)

                text = f"Grup ({len(members)} öğe)"
                group_item = QTreeWidgetItem(layer_item)
                group_item.setText(0, text)
                group_item.setData(0, Qt.ItemDataRole.UserRole, members)
                group_item.setData(0, Qt.ItemDataRole.UserRole + 1, 'group')
                
                # Grup üyelerini alt düğümler olarak ekle
                for member_idx in members:
                    if member_idx < len(strokes):
                        member_stroke = strokes[member_idx]
                        member_type = self._get_stroke_type(member_stroke)
                        member_text = f"{member_type} #{member_idx}"
                        member_item = QTreeWidgetItem(group_item)
                        member_item.setText(0, member_text)
                        member_item.setData(0, Qt.ItemDataRole.UserRole, member_idx)
                        member_item.setData(0, Qt.ItemDataRole.UserRole + 1, 'stroke')
            else:
                visited_indices.add(idx)
                stroke_type = self._get_stroke_type(stroke)
                text = f"{stroke_type} #{idx}"
                stroke_item = QTreeWidgetItem(layer_item)
                stroke_item.setText(0, text)
                stroke_item.setData(0, Qt.ItemDataRole.UserRole, idx)
                stroke_item.setData(0, Qt.ItemDataRole.UserRole + 1, 'stroke')

    def _get_stroke_group_id(self, stroke):
        try:
            group_id = None
            if hasattr(stroke, 'group_id'):
                group_id = getattr(stroke, 'group_id', None)
            elif isinstance(stroke, dict):
                group_id = stroke.get('group_id')
            
            if group_id:
                print(f"DEBUG: Stroke has group_id: {group_id}")
            return group_id
        except Exception:
            return None

    def _find_group_members_indices(self, strokes, group_id):
        members = []
        for i, s in enumerate(strokes):
            gid = self._get_stroke_group_id(s)
            if gid == group_id:
                members.append(i)
        return members

    def _get_stroke_type(self, stroke):
        try:
            if hasattr(stroke, 'stroke_type'):
                stroke_type = getattr(stroke, 'stroke_type', 'şekil')
            elif isinstance(stroke, dict):
                stroke_type = stroke.get('type', 'şekil')
            else:
                stroke_type = 'şekil'
            
            # Kısa isimlere çevir (kolon genişliği için)
            type_names = {
                'line': 'Çizgi',
                'rectangle': 'Dikdörtgen', 
                'circle': 'Çember',
                'bspline': 'Eğri',
                'freehand': 'Kalem',
                'image': 'Resim',
                'text': 'Metin'
            }
            return type_names.get(stroke_type, stroke_type.title() if stroke_type else 'Şekil')
        except Exception:
            return 'Şekil'

