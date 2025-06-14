import json
import os
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QListWidget, QListWidgetItem, QLineEdit, QLabel,
                            QComboBox, QMessageBox, QInputDialog, QFileDialog,
                            QSplitter, QTextEdit, QGroupBox, QScrollArea, QCheckBox,
                            QGridLayout, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal, QStandardPaths, QSize, QRect, QRectF
from PyQt6.QtGui import QPixmap, QPainter, QIcon, QPen, QBrush, QColor
import qtawesome as qta

class ShapeLibraryManager:
    """Şekil havuzu yönetimi"""
    
    def __init__(self):
        self.library_dir = self.get_library_directory()
        self.ensure_library_directory()
        self.library_file = os.path.join(self.library_dir, "shape_library.json")
        self.shapes_data = self.load_library()
        
    def get_library_directory(self):
        """Şekil havuzu için dizin yolunu al"""
        documents_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
        return os.path.join(documents_path, "Dijital Mürekkep Şekil Havuzu")
        
    def ensure_library_directory(self):
        """Şekil havuzu dizininin var olduğundan emin ol"""
        if not os.path.exists(self.library_dir):
            os.makedirs(self.library_dir)
            
    def load_library(self):
        """Şekil havuzunu yükle"""
        if os.path.exists(self.library_file):
            try:
                with open(self.library_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Eski şekilleri yeni formata güncelle
                self.migrate_old_shapes(data)
                return data
            except Exception as e:
                print(f"Şekil havuzu yüklenemedi: {e}")
                
        # Varsayılan yapı
        return {
            'version': '1.0',
            'categories': {
                'Genel': {
                    'name': 'Genel',
                    'description': 'Genel şekiller',
                    'shapes': {}
                }
            }
        }
        
    def migrate_old_shapes(self, data):
        """Eski şekilleri yeni formata güncelle"""
        try:
            for category_name, category_data in data.get('categories', {}).items():
                for shape_id, shape_info in category_data.get('shapes', {}).items():
                    # Eksik alanları ekle
                    if 'favorite' not in shape_info:
                        shape_info['favorite'] = False
                    if 'usage_count' not in shape_info:
                        shape_info['usage_count'] = 0
                    if 'thumbnail' not in shape_info:
                        shape_info['thumbnail'] = None
                        
            # Güncellenmiş veriyi kaydet
            self.save_library_data(data)
        except Exception as e:
            print(f"Migration hatası: {e}")
            
    def save_library_data(self, data):
        """Veriyi doğrudan kaydet"""
        try:
            with open(self.library_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Veri kaydedilemedi: {e}")
        
    def save_library(self):
        """Şekil havuzunu kaydet"""
        try:
            with open(self.library_file, 'w', encoding='utf-8') as f:
                json.dump(self.shapes_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Şekil havuzu kaydedilemedi: {e}")
            return False
            
    def add_category(self, category_name, description=""):
        """Yeni kategori ekle"""
        if category_name not in self.shapes_data['categories']:
            self.shapes_data['categories'][category_name] = {
                'name': category_name,
                'description': description,
                'shapes': {}
            }
            self.save_library()
            return True
        return False
        
    def remove_category(self, category_name):
        """Kategori sil"""
        if category_name in self.shapes_data['categories'] and category_name != 'Genel':
            del self.shapes_data['categories'][category_name]
            self.save_library()
            return True
        return False
        
    def add_shape(self, category_name, shape_name, shape_data, description="", drawing_widget=None, selected_strokes=None):
        """Şekil ekle"""
        if category_name not in self.shapes_data['categories']:
            self.add_category(category_name)
            
        shape_id = f"{category_name}_{shape_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Şekil verilerini serialize et
        from session_manager import SessionManager
        session_manager = SessionManager()
        serialized_strokes = session_manager.serialize_strokes(shape_data)
        
        # Canvas'tan thumbnail al (öncelikli)
        thumbnail_data = None
        if drawing_widget and selected_strokes:
            thumbnail_data = self.create_thumbnail_from_canvas(drawing_widget, selected_strokes)
        
        # Canvas thumbnail alınamazsa eski yöntemi dene
        if not thumbnail_data:
            thumbnail_data = self.create_thumbnail(shape_data)
        
        self.shapes_data['categories'][category_name]['shapes'][shape_id] = {
            'name': shape_name,
            'description': description,
            'strokes': serialized_strokes,
            'created': datetime.now().isoformat(),
            'thumbnail': thumbnail_data,
            'favorite': False,
            'usage_count': 0
        }
        
        self.save_library()
        return shape_id
        
    def remove_shape(self, category_name, shape_id):
        """Şekil sil"""
        if (category_name in self.shapes_data['categories'] and 
            shape_id in self.shapes_data['categories'][category_name]['shapes']):
            del self.shapes_data['categories'][category_name]['shapes'][shape_id]
            self.save_library()
            return True
        return False
        
    def get_shape(self, category_name, shape_id):
        """Şekil verilerini al"""
        if (category_name in self.shapes_data['categories'] and 
            shape_id in self.shapes_data['categories'][category_name]['shapes']):
            shape_info = self.shapes_data['categories'][category_name]['shapes'][shape_id]
            
            # Stroke'ları deserialize et
            from session_manager import SessionManager
            session_manager = SessionManager()
            strokes = session_manager.deserialize_strokes(shape_info['strokes'])
            
            return {
                'name': shape_info['name'],
                'description': shape_info['description'],
                'strokes': strokes,
                'created': shape_info['created']
            }
        return None
        
    def get_categories(self):
        """Tüm kategorileri al"""
        return list(self.shapes_data['categories'].keys())
        
    def get_shapes_in_category(self, category_name):
        """Kategorideki şekilleri al"""
        if category_name in self.shapes_data['categories']:
            return self.shapes_data['categories'][category_name]['shapes']
        return {}
        
    def export_library(self, filename):
        """Şekil havuzunu dışa aktar"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.shapes_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Şekil havuzu dışa aktarılamadı: {e}")
            return False
            
    def import_library(self, filename, merge=True):
        """Şekil havuzunu içe aktar"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                imported_data = json.load(f)
                
            if merge:
                # Mevcut havuzla birleştir
                for cat_name, cat_data in imported_data.get('categories', {}).items():
                    if cat_name not in self.shapes_data['categories']:
                        self.shapes_data['categories'][cat_name] = cat_data
                    else:
                        # Şekilleri birleştir
                        self.shapes_data['categories'][cat_name]['shapes'].update(cat_data['shapes'])
            else:
                # Tamamen değiştir
                self.shapes_data = imported_data
                
            self.save_library()
            return True
        except Exception as e:
            print(f"Şekil havuzu içe aktarılamadı: {e}")
            return False
            
    def create_thumbnail_from_canvas(self, drawing_widget, selected_strokes, size=64):
        """Canvas'tan seçili şekillerin ekran görüntüsünü al"""
        try:
            if not selected_strokes or not drawing_widget:
                return None
            
            # Seçim aracının bounding rect metodunu kullan
            bounding_rect = drawing_widget.selection_tool.get_selection_bounding_rect(drawing_widget.strokes)
            if not bounding_rect:
                return None
            
            # Widget sınırları içinde kalmasını sağla
            widget_rect = drawing_widget.rect()
            widget_rectf = QRectF(widget_rect)
            capture_rect = bounding_rect.intersected(widget_rectf)
            
            if capture_rect.width() <= 0 or capture_rect.height() <= 0:
                return None
            
            # Canvas'tan bu alanı yakala
            grab_rect = QRect(int(capture_rect.x()), int(capture_rect.y()), 
                            int(capture_rect.width()), int(capture_rect.height()))
            canvas_pixmap = drawing_widget.grab(grab_rect)
            
            if canvas_pixmap.isNull():
                return None
            
            # Thumbnail boyutuna ölçekle (aspect ratio korunarak)
            scaled_pixmap = canvas_pixmap.scaled(
                size, size, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            
            # Kare bir thumbnail oluştur (merkezde)
            final_pixmap = QPixmap(size, size)
            final_pixmap.fill(QColor(255, 255, 255, 0))  # Şeffaf arka plan
            
            painter = QPainter(final_pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Tam merkeze yerleştir
            x_offset = (size - scaled_pixmap.width()) / 2
            y_offset = (size - scaled_pixmap.height()) / 2
            painter.drawPixmap(int(x_offset), int(y_offset), scaled_pixmap)
            
            painter.end()
            
            # Base64'e çevir
            from PyQt6.QtCore import QBuffer, QIODevice
            import base64
            
            buffer = QBuffer()
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            success = final_pixmap.save(buffer, "PNG")
            
            if success and buffer.size() > 0:
                encoded = base64.b64encode(buffer.data()).decode('utf-8')
                return encoded
            else:
                return None
                
        except Exception as e:
            print(f"Canvas thumbnail oluşturulamadı: {e}")
            return None
            
    def create_thumbnail(self, strokes, size=64):
        """Eski thumbnail oluşturma metodu - geriye dönük uyumluluk için"""
        # Bu metod artık kullanılmayacak ama eski şekiller için gerekli
        return None
            
    def toggle_favorite(self, category_name, shape_id):
        """Şekli favorilere ekle/çıkar"""
        if (category_name in self.shapes_data['categories'] and 
            shape_id in self.shapes_data['categories'][category_name]['shapes']):
            shape = self.shapes_data['categories'][category_name]['shapes'][shape_id]
            shape['favorite'] = not shape.get('favorite', False)
            self.save_library()
            return shape['favorite']
        return False
        
    def increment_usage(self, category_name, shape_id):
        """Şekil kullanım sayısını artır"""
        if (category_name in self.shapes_data['categories'] and 
            shape_id in self.shapes_data['categories'][category_name]['shapes']):
            shape = self.shapes_data['categories'][category_name]['shapes'][shape_id]
            shape['usage_count'] = shape.get('usage_count', 0) + 1
            self.save_library()
            
    def search_shapes(self, query, category_name=None):
        """Şekillerde arama yap"""
        results = []
        query_lower = query.lower()
        
        categories_to_search = [category_name] if category_name else self.get_categories()
        
        for cat_name in categories_to_search:
            if cat_name in self.shapes_data['categories']:
                shapes = self.shapes_data['categories'][cat_name]['shapes']
                for shape_id, shape_info in shapes.items():
                    if (query_lower in shape_info['name'].lower() or 
                        query_lower in shape_info.get('description', '').lower()):
                        results.append({
                            'category': cat_name,
                            'shape_id': shape_id,
                            'shape_info': shape_info
                        })
        
        return results
        
    def get_favorite_shapes(self):
        """Favori şekilleri al"""
        favorites = []
        for cat_name in self.get_categories():
            if cat_name in self.shapes_data['categories']:
                shapes = self.shapes_data['categories'][cat_name]['shapes']
                for shape_id, shape_info in shapes.items():
                    if shape_info.get('favorite', False):
                        favorites.append({
                            'category': cat_name,
                            'shape_id': shape_id,
                            'shape_info': shape_info
                        })
        
        # Kullanım sayısına göre sırala
        favorites.sort(key=lambda x: x['shape_info'].get('usage_count', 0), reverse=True)
        return favorites
        
    def regenerate_thumbnails(self, force=False):
        """Mevcut şekiller için thumbnail'ları yeniden oluştur"""
        from session_manager import SessionManager
        session_manager = SessionManager()
        
        updated = False
        total_shapes = 0
        processed_shapes = 0
        
        for cat_name, cat_data in self.shapes_data.get('categories', {}).items():
            for shape_id, shape_info in cat_data.get('shapes', {}).items():
                total_shapes += 1
                print(f"İşleniyor: {shape_info['name']} - Force: {force}, Mevcut thumbnail: {bool(shape_info.get('thumbnail'))}")
                
                # Force=True ise tüm thumbnail'ları yeniden oluştur
                if force or not shape_info.get('thumbnail'):
                    processed_shapes += 1
                    print(f"Thumbnail oluşturuluyor: {shape_info['name']}")
                    
                    # Stroke'ları deserialize et
                    strokes = session_manager.deserialize_strokes(shape_info['strokes'])
                    print(f"Deserialize edilen stroke sayısı: {len(strokes)}")
                    
                    # Thumbnail oluştur
                    thumbnail_data = self.create_thumbnail(strokes)
                    print(f"Thumbnail oluşturuldu: {bool(thumbnail_data)}")
                    
                    if thumbnail_data:
                        shape_info['thumbnail'] = thumbnail_data
                        updated = True
                        print(f"Başarılı: {shape_info['name']}")
                    else:
                        print(f"Başarısız: {shape_info['name']}")
        
        print(f"Toplam şekil: {total_shapes}, İşlenen: {processed_shapes}, Güncellenen: {updated}")
        
        if updated:
            self.save_library()
        
        return updated


class ShapeLibraryWidget(QWidget):
    """Şekil havuzu widget'ı"""
    
    shapeSelected = pyqtSignal(list)  # Seçilen şekil stroke'ları
    
    def __init__(self):
        super().__init__()
        self.library_manager = ShapeLibraryManager()
        self.setup_ui()
        self.refresh_categories()
        
    def setup_ui(self):
        """UI'yi oluştur"""
        layout = QVBoxLayout(self)
        
        # Başlık
        title_label = QLabel("Şekil Havuzu")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        layout.addWidget(title_label)
        
        # Arama kutusu
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Şekil ara...")
        self.search_input.textChanged.connect(self.on_search_changed)
        search_layout.addWidget(QLabel("Ara:"))
        search_layout.addWidget(self.search_input)
        
        # Favori filtresi
        self.favorites_only_cb = QCheckBox("Sadece Favoriler")
        self.favorites_only_cb.toggled.connect(self.refresh_shapes)
        search_layout.addWidget(self.favorites_only_cb)
        
        layout.addLayout(search_layout)
        
        # Kategori yönetimi
        category_group = QGroupBox("Kategoriler")
        category_layout = QVBoxLayout(category_group)
        
        # Kategori seçimi
        cat_select_layout = QHBoxLayout()
        self.category_combo = QComboBox()
        self.category_combo.currentTextChanged.connect(self.on_category_changed)
        cat_select_layout.addWidget(QLabel("Kategori:"))
        cat_select_layout.addWidget(self.category_combo)
        category_layout.addLayout(cat_select_layout)
        
        # Kategori butonları
        cat_buttons_layout = QHBoxLayout()
        
        add_cat_btn = QPushButton(qta.icon('fa5s.plus', color='#4CAF50'), "")
        add_cat_btn.setToolTip("Yeni kategori ekle")
        add_cat_btn.clicked.connect(self.add_category)
        cat_buttons_layout.addWidget(add_cat_btn)
        
        remove_cat_btn = QPushButton(qta.icon('fa5s.trash', color='#F44336'), "")
        remove_cat_btn.setToolTip("Kategori sil")
        remove_cat_btn.clicked.connect(self.remove_category)
        cat_buttons_layout.addWidget(remove_cat_btn)
        
        cat_buttons_layout.addStretch()
        category_layout.addLayout(cat_buttons_layout)
        
        layout.addWidget(category_group)
        
        # Şekil listesi
        shapes_group = QGroupBox("Şekiller")
        shapes_layout = QVBoxLayout(shapes_group)
        
        # Custom grid widget ile scroll area
        self.shapes_scroll = QScrollArea()
        self.shapes_widget = QWidget()
        self.shapes_grid_layout = QGridLayout(self.shapes_widget)
        self.shapes_grid_layout.setSpacing(5)
        
        self.shapes_scroll.setWidget(self.shapes_widget)
        self.shapes_scroll.setWidgetResizable(True)
        self.shapes_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.shapes_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        shapes_layout.addWidget(self.shapes_scroll)
        
        # Şekil butonları için storage
        self.shape_buttons = []
        
        # Şekil butonları
        shape_buttons_layout = QHBoxLayout()
        
        add_shape_btn = QPushButton(qta.icon('fa5s.plus', color='#4CAF50'), "Ekle")
        add_shape_btn.setToolTip("Seçili şekilleri havuza ekle")
        add_shape_btn.clicked.connect(self.add_selected_shapes)
        shape_buttons_layout.addWidget(add_shape_btn)
        
        remove_shape_btn = QPushButton(qta.icon('fa5s.trash', color='#F44336'), "Sil")
        remove_shape_btn.setToolTip("Şekli havuzdan sil")
        remove_shape_btn.clicked.connect(self.remove_shape)
        shape_buttons_layout.addWidget(remove_shape_btn)
        
        shapes_layout.addLayout(shape_buttons_layout)
        layout.addWidget(shapes_group)
        
        # İçe/Dışa aktarma
        io_group = QGroupBox("İçe/Dışa Aktarma")
        io_layout = QHBoxLayout(io_group)
        
        export_btn = QPushButton(qta.icon('fa5s.download', color='#2196F3'), "Dışa Aktar")
        export_btn.clicked.connect(self.export_library)
        io_layout.addWidget(export_btn)
        
        import_btn = QPushButton(qta.icon('fa5s.upload', color='#FF9800'), "İçe Aktar")
        import_btn.clicked.connect(self.import_library)
        io_layout.addWidget(import_btn)
        
        layout.addWidget(io_group)
        
        layout.addStretch()
        
    def create_shape_button(self, shape_id, shape_info):
        """Şekil için custom button oluştur"""
        
        # Ana frame
        frame = QFrame()
        frame.setFixedSize(80, 80)
        frame.setFrameStyle(QFrame.Shape.Box)
        frame.setStyleSheet("""
            QFrame {
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: white;
            }
            QFrame:hover {
                border: 2px solid #007acc;
                background-color: #f0f8ff;
            }
        """)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Thumbnail label
        thumbnail_label = QLabel()
        thumbnail_label.setFixedSize(80, 60)  # Frame boyutuna yakın
        thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thumbnail_label.setStyleSheet("border: none; background-color: transparent;")
        thumbnail_label.setScaledContents(False)
        
        # Thumbnail yükle
        thumbnail_data = shape_info.get('thumbnail')
        if thumbnail_data:
            try:
                import base64
                from PyQt6.QtCore import QBuffer, QIODevice
                
                # Base64'ten pixmap oluştur
                image_data = base64.b64decode(thumbnail_data)
                buffer = QBuffer()
                buffer.setData(image_data)
                buffer.open(QIODevice.OpenModeFlag.ReadOnly)
                
                pixmap = QPixmap()
                success = pixmap.loadFromData(buffer.data(), "PNG")
                
                if not pixmap.isNull():
                    # Pixmap'i ölçekle ve ortalı yerleştir
                    scaled_pixmap = pixmap.scaled(75, 55, Qt.AspectRatioMode.KeepAspectRatio, 
                                                 Qt.TransformationMode.SmoothTransformation)
                    thumbnail_label.setPixmap(scaled_pixmap)
                    
            except Exception as e:
                print(f"Thumbnail yüklenemedi: {e}")
                # Varsayılan icon
                default_pixmap = qta.icon('fa5s.image', color='#999').pixmap(64, 64)
                thumbnail_label.setPixmap(default_pixmap)
        else:
            # Varsayılan icon
            default_pixmap = qta.icon('fa5s.image', color='#999').pixmap(64, 64)
            thumbnail_label.setPixmap(default_pixmap)
        
        # İsim label
        name_label = QLabel(shape_info['name'])
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("border: none; font-size: 8px; color: #333;")
        name_label.setWordWrap(True)
        name_label.setMaximumHeight(12)
        
        layout.addWidget(thumbnail_label)
        layout.addWidget(name_label)
        
        # Mouse events
        frame.shape_id = shape_id
        frame.shape_info = shape_info
        frame.mousePressEvent = lambda event: self.on_shape_clicked(frame, event)
        frame.mouseDoubleClickEvent = lambda event: self.on_shape_double_clicked_custom(frame)
        frame.contextMenuEvent = lambda event: self.show_context_menu_custom(frame, event)
        
        # Favori vurgusu
        if shape_info.get('favorite', False):
            frame.setStyleSheet(frame.styleSheet() + """
                QFrame {
                    background-color: #fff9c4;
                }
            """)
        
        return frame
        
    def refresh_categories(self):
        """Kategori listesini yenile"""
        current_text = self.category_combo.currentText()
        self.category_combo.clear()
        
        categories = self.library_manager.get_categories()
        self.category_combo.addItems(categories)
        
        # Önceki seçimi geri yükle
        if current_text in categories:
            self.category_combo.setCurrentText(current_text)
        elif categories:
            self.category_combo.setCurrentIndex(0)
            
        self.refresh_shapes()
        
    def refresh_shapes(self):
        """Şekil listesini yenile"""
        # Eski butonları temizle
        for button in self.shape_buttons:
            button.setParent(None)
        self.shape_buttons.clear()
        
        current_category = self.category_combo.currentText()
        if not current_category:
            return
        
        # Arama terimi
        search_query = self.search_input.text().strip()
        favorites_only = self.favorites_only_cb.isChecked()
        
        if search_query:
            # Arama sonuçlarını göster
            results = self.library_manager.search_shapes(search_query, current_category)
            shapes_to_show = {r['shape_id']: r['shape_info'] for r in results}
        else:
            # Kategorideki tüm şekilleri göster
            shapes_to_show = self.library_manager.get_shapes_in_category(current_category)
        
        # Favori filtresi
        if favorites_only:
            shapes_to_show = {k: v for k, v in shapes_to_show.items() if v.get('favorite', False)}
        
        # Şekilleri kullanım sayısına göre sırala
        sorted_shapes = sorted(shapes_to_show.items(), 
                              key=lambda x: x[1].get('usage_count', 0), reverse=True)
        
        # Grid layout'a şekilleri ekle
        columns = 4  # 4 sütunlu grid
        for i, (shape_id, shape_info) in enumerate(sorted_shapes):
            row = i // columns
            col = i % columns
            
            # Custom shape button oluştur
            shape_button = self.create_shape_button(shape_id, shape_info)
            self.shapes_grid_layout.addWidget(shape_button, row, col)
            self.shape_buttons.append(shape_button)
            
    def on_category_changed(self):
        """Kategori değiştiğinde"""
        self.refresh_shapes()
        
    def on_search_changed(self):
        """Arama terimi değiştiğinde"""
        self.refresh_shapes()
        
    def on_shape_clicked(self, frame, event):
        """Custom shape button'a tıklandığında"""
        # Seçim işaretleme için
        pass
        
    def on_shape_double_clicked_custom(self, frame):
        """Custom shape button'a çift tıklandığında"""
        shape_id = frame.shape_id
        current_category = self.category_combo.currentText()
        
        shape_data = self.library_manager.get_shape(current_category, shape_id)
        if shape_data:
            # Kullanım sayısını artır
            self.library_manager.increment_usage(current_category, shape_id)
            # Şekil stroke'larını emit et
            self.shapeSelected.emit(shape_data['strokes'])
            # Listeyi yenile (kullanım sayısı değişti)
            self.refresh_shapes()
            
    def show_context_menu_custom(self, frame, event):
        """Custom shape button için context menu"""
        from PyQt6.QtWidgets import QMenu
        
        menu = QMenu(self)
        shape_id = frame.shape_id
        shape_info = frame.shape_info
        current_category = self.category_combo.currentText()
        
        # Favori toggle
        is_favorite = shape_info.get('favorite', False)
        fav_text = "Favorilerden Çıkar" if is_favorite else "Favorilere Ekle"
        fav_icon = qta.icon('fa5s.star', color='#FFD700') if is_favorite else qta.icon('fa5s.star', color='#666')
        fav_action = menu.addAction(fav_icon, fav_text)
        fav_action.triggered.connect(lambda: self.toggle_favorite(current_category, shape_id))
        
        menu.addSeparator()
        
        # Şekli kullan
        use_action = menu.addAction(qta.icon('fa5s.plus', color='#4CAF50'), "Canvas'a Ekle")
        use_action.triggered.connect(lambda: self.on_shape_double_clicked_custom(frame))
        
        menu.addSeparator()
        
        # Şekil bilgileri
        info_action = menu.addAction(qta.icon('fa5s.info-circle', color='#2196F3'), "Bilgiler")
        info_action.triggered.connect(lambda: self.show_shape_info(current_category, shape_id))
        
        # Şekli sil
        delete_action = menu.addAction(qta.icon('fa5s.trash', color='#F44336'), "Sil")
        delete_action.triggered.connect(lambda: self.remove_shape_by_id(current_category, shape_id))
        
        menu.exec(event.globalPos())
        
    def add_category(self):
        """Yeni kategori ekle"""
        name, ok = QInputDialog.getText(self, "Yeni Kategori", "Kategori adı:")
        if ok and name.strip():
            description, ok2 = QInputDialog.getText(self, "Kategori Açıklaması", "Açıklama (isteğe bağlı):")
            if ok2:
                if self.library_manager.add_category(name.strip(), description.strip()):
                    self.refresh_categories()
                    self.category_combo.setCurrentText(name.strip())
                else:
                    QMessageBox.warning(self, "Hata", "Bu kategori zaten mevcut!")
                    
    def remove_category(self):
        """Kategori sil"""
        current_category = self.category_combo.currentText()
        if not current_category:
            return
            
        if current_category == "Genel":
            QMessageBox.warning(self, "Hata", "Genel kategorisi silinemez!")
            return
            
        reply = QMessageBox.question(self, "Kategori Sil", 
                                   f"'{current_category}' kategorisini ve içindeki tüm şekilleri silmek istediğinizden emin misiniz?")
        if reply == QMessageBox.StandardButton.Yes:
            if self.library_manager.remove_category(current_category):
                self.refresh_categories()
                
    def add_selected_shapes(self):
        """Seçili şekilleri havuza ekle"""
        # Ana pencereden seçili şekilleri al
        main_window = self.get_main_window()
        if not main_window:
            QMessageBox.warning(self, "Hata", "Ana pencere bulunamadı!")
            return
            
        current_widget = main_window.get_current_drawing_widget()
        if not current_widget or not current_widget.selection_tool.selected_strokes:
            QMessageBox.information(self, "Bilgi", "Önce şekil seçin!")
            return
            
        # Seçili stroke'ları al
        selected_strokes = []
        for stroke_index in current_widget.selection_tool.selected_strokes:
            if stroke_index < len(current_widget.strokes):
                selected_strokes.append(current_widget.strokes[stroke_index])
                
        if not selected_strokes:
            QMessageBox.information(self, "Bilgi", "Seçili şekil bulunamadı!")
            return
            
        # Şekil adı sor
        name, ok = QInputDialog.getText(self, "Şekil Adı", "Şekil adı:")
        if not ok or not name.strip():
            return
            
        description, ok2 = QInputDialog.getText(self, "Şekil Açıklaması", "Açıklama (isteğe bağlı):")
        if not ok2:
            return
            
        # Kategori seç
        current_category = self.category_combo.currentText()
        if not current_category:
            current_category = "Genel"
            
        # Şekli havuza ekle (canvas widget ve seçili stroke indeksleriyle)
        shape_id = self.library_manager.add_shape(current_category, name.strip(), 
                                                 selected_strokes, description.strip(),
                                                 current_widget, current_widget.selection_tool.selected_strokes)
        if shape_id:
            self.refresh_shapes()
            QMessageBox.information(self, "Başarılı", f"Şekil '{name}' havuza eklendi!")
        else:
            QMessageBox.warning(self, "Hata", "Şekil eklenemedi!")
            
    def remove_shape(self):
        """Şekli sil - artık kullanılmıyor"""
        QMessageBox.information(self, "Bilgi", "Şekil silmek için sağ tıklayıp 'Sil' seçin!")
        
    def toggle_favorite(self, category_name, shape_id):
        """Favori durumunu değiştir"""
        self.library_manager.toggle_favorite(category_name, shape_id)
        self.refresh_shapes()
        
    def show_shape_info(self, category_name, shape_id):
        """Şekil bilgilerini göster"""
        shapes = self.library_manager.get_shapes_in_category(category_name)
        if shape_id not in shapes:
            return
            
        shape_info = shapes[shape_id]
        
        info_text = f"""
Şekil Adı: {shape_info['name']}
Açıklama: {shape_info.get('description', 'Yok')}
Kategori: {category_name}
Oluşturulma: {shape_info['created']}
Kullanım Sayısı: {shape_info.get('usage_count', 0)}
Favori: {'Evet' if shape_info.get('favorite', False) else 'Hayır'}
        """.strip()
        
        QMessageBox.information(self, "Şekil Bilgileri", info_text)
        
    def remove_shape_by_id(self, category_name, shape_id):
        """Şekli ID ile sil"""
        shapes = self.library_manager.get_shapes_in_category(category_name)
        if shape_id not in shapes:
            return
            
        shape_name = shapes[shape_id]['name']
        
        reply = QMessageBox.question(self, "Şekil Sil", 
                                   f"'{shape_name}' şeklini silmek istediğinizden emin misiniz?")
        if reply == QMessageBox.StandardButton.Yes:
            if self.library_manager.remove_shape(category_name, shape_id):
                self.refresh_shapes()
                QMessageBox.information(self, "Başarılı", "Şekil silindi!")
            else:
                QMessageBox.warning(self, "Hata", "Şekil silinemedi!")
            
    def export_library(self):
        """Şekil havuzunu dışa aktar"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Şekil Havuzunu Dışa Aktar",
            f"sekil_havuzu_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON Dosyaları (*.json);;Tüm Dosyalar (*)"
        )
        
        if filename:
            if self.library_manager.export_library(filename):
                QMessageBox.information(self, "Başarılı", f"Şekil havuzu dışa aktarıldı:\n{filename}")
            else:
                QMessageBox.warning(self, "Hata", "Şekil havuzu dışa aktarılamadı!")
                
    def import_library(self):
        """Şekil havuzunu içe aktar"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Şekil Havuzunu İçe Aktar", "",
            "JSON Dosyaları (*.json);;Tüm Dosyalar (*)"
        )
        
        if filename:
            reply = QMessageBox.question(self, "İçe Aktarma Modu", 
                                       "Mevcut şekil havuzuyla birleştirmek istiyor musunuz?\n\n"
                                       "Evet: Mevcut havuzla birleştir\n"
                                       "Hayır: Mevcut havuzu değiştir")
            
            merge = reply == QMessageBox.StandardButton.Yes
            
            if self.library_manager.import_library(filename, merge):
                self.refresh_categories()
                QMessageBox.information(self, "Başarılı", "Şekil havuzu içe aktarıldı!")
            else:
                QMessageBox.warning(self, "Hata", "Şekil havuzu içe aktarılamadı!")
                
    def regenerate_thumbnails(self):
        """Thumbnail'ları yeniden oluştur"""
        # Tüm thumbnail'ları zorla yeniden oluştur
        if self.library_manager.regenerate_thumbnails(force=True):
            self.refresh_shapes()
            QMessageBox.information(self, "Başarılı", "Tüm önizlemeler yenilendi!")
        else:
            QMessageBox.information(self, "Bilgi", "Önizleme bulunamadı.")
                
    def get_main_window(self):
        """Ana pencereyi bul"""
        parent = self.parent()
        while parent:
            if hasattr(parent, 'get_current_drawing_widget'):
                return parent
            parent = parent.parent()
        return None 