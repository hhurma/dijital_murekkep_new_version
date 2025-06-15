import json
import os
from datetime import datetime
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from PyQt6.QtCore import QStandardPaths

class SessionManager:
    """Oturum kaydetme ve açma işlemleri"""
    
    def __init__(self):
        self.sessions_dir = self.get_sessions_directory()
        self.ensure_sessions_directory()
        
    def get_sessions_directory(self):
        """Oturumlar için dizin yolunu al"""
        documents_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
        return os.path.join(documents_path, "Dijital Mürekkep Oturumları")
        
    def ensure_sessions_directory(self):
        """Oturumlar dizininin var olduğundan emin ol"""
        if not os.path.exists(self.sessions_dir):
            os.makedirs(self.sessions_dir)
            
    def save_session(self, main_window, filename=None):
        """Mevcut oturumu kaydet"""
        try:
            # Eğer dosya adı verilmemişse, kullanıcıdan iste
            if not filename:
                filename, _ = QFileDialog.getSaveFileName(
                    main_window,
                    "Oturumu Kaydet",
                    os.path.join(self.sessions_dir, f"oturum_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sdm"),
                    "Dijital Mürekkep Oturum Dosyaları (*.sdm);;Tüm Dosyalar (*)"
                )
                
            if not filename:
                return None
                
            # Oturum verilerini topla
            session_data = {
                'version': '1.0',
                'created': datetime.now().isoformat(),
                'tabs': [],
                'active_tab': main_window.tab_manager.get_current_index(),
                'window_size': {
                    'width': main_window.width(),
                    'height': main_window.height()
                },
                'settings': self.serialize_settings(main_window.settings.get_all_settings())
            }
            
            # Her tab'ın verilerini kaydet
            for i in range(main_window.tab_manager.get_tab_count()):
                tab_widget = main_window.tab_manager.get_tab_widget_at_index(i)
                tab_name = main_window.tab_manager.get_tab_text(i)
                
                if tab_widget and hasattr(tab_widget, 'strokes'):
                    tab_data = {
                        'name': tab_name,
                        'strokes': self.serialize_strokes(tab_widget.strokes),
                        'background_settings': self.serialize_background_settings(tab_widget.background_settings)
                    }
                    session_data['tabs'].append(tab_data)
                    
            # JSON dosyasına kaydet
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
                
            # Status bar'da mesaj göster
            if hasattr(main_window, 'show_status_message'):
                file_name = os.path.basename(filename)
                main_window.show_status_message(f"Oturum kaydedildi: {file_name}")
            return filename
            
        except Exception as e:
            # Status bar'da hata mesajı göster
            if hasattr(main_window, 'show_status_message'):
                main_window.show_status_message(f"Oturum kaydedilemedi: {str(e)}")
            return None
            
    def load_session(self, main_window, filename=None):
        """Kaydedilmiş oturumu aç"""
        try:
            # Eğer dosya adı verilmemişse, kullanıcıdan iste
            if not filename:
                filename, _ = QFileDialog.getOpenFileName(
                    main_window,
                    "Oturum Aç",
                    self.sessions_dir,
                    "Dijital Mürekkep Oturum Dosyaları (*.sdm);;Tüm Dosyalar (*)"
                )
                
            if not filename or not os.path.exists(filename):
                return None
                
            # JSON dosyasından oku
            with open(filename, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
                
            # Mevcut tab'ları temizle
            main_window.tab_manager.clear_all_tabs()
                
            # Ayarları yükle
            if 'settings' in session_data:
                deserialized_settings = self.deserialize_settings(session_data['settings'])
                main_window.settings.load_from_dict(deserialized_settings)
                
            # Tab'ları yeniden oluştur
            for tab_data in session_data.get('tabs', []):
                # Yeni tab oluştur
                tab_name = tab_data.get('name', f'Çizim {main_window.tab_manager.get_tab_count() + 1}')
                current_widget = main_window.tab_manager.create_new_tab(tab_name)
                
                # Tab adını ayarla (create_new_tab zaten ayarlıyor ama emin olmak için)
                tab_index = main_window.tab_manager.get_current_index()
                main_window.tab_manager.set_tab_text(tab_index, tab_name)
                
                # Stroke'ları yükle
                if current_widget and 'strokes' in tab_data:
                    current_widget.strokes = self.deserialize_strokes(tab_data['strokes'])
                    
                # Arka plan ayarlarını yükle
                if 'background_settings' in tab_data:
                    bg_settings = self.deserialize_background_settings(tab_data['background_settings'])
                    current_widget.set_background_settings(bg_settings)
                    
                current_widget.update()
                
            # Aktif tab'ı ayarla
            active_tab = session_data.get('active_tab', 0)
            if 0 <= active_tab < main_window.tab_manager.get_tab_count():
                main_window.tab_manager.set_current_index(active_tab)
                
            # Pencere boyutunu ayarla
            if 'window_size' in session_data:
                size = session_data['window_size']
                main_window.resize(size.get('width', 800), size.get('height', 600))
                
            # UI'yi güncelle
            main_window.load_settings_to_tab(main_window.get_current_drawing_widget())
                
            # Status bar'da mesaj göster
            if hasattr(main_window, 'show_status_message'):
                file_name = os.path.basename(filename)
                main_window.show_status_message(f"Oturum yüklendi: {file_name}")
            return filename
            
        except Exception as e:
            # Status bar'da hata mesajı göster
            if hasattr(main_window, 'show_status_message'):
                main_window.show_status_message(f"Oturum yüklenemedi: {str(e)}")
            return None
            
    def serialize_strokes(self, strokes):
        """Stroke'ları JSON'a dönüştürülebilir formata çevir"""
        from PyQt6.QtGui import QColor
        from PyQt6.QtCore import Qt, QPointF
        
        serialized = []
        for i, stroke in enumerate(strokes):
            try:
                # ImageStroke kontrolü
                if hasattr(stroke, 'stroke_type') and stroke.stroke_type == 'image':
                    # ImageStroke'u serialize et
                    stroke_copy = stroke.to_dict()
                else:
                    # Normal stroke verilerini kopyala
                    stroke_copy = stroke.copy()
                
                # Points listesini özel olarak handle et
                if 'points' in stroke_copy:
                    points = stroke_copy['points']
                    serialized_points = []
                    
                    for point in points:
                        if isinstance(point, QPointF):
                            # QPointF'i dict'e çevir
                            serialized_points.append({'x': point.x(), 'y': point.y()})
                        elif hasattr(point, 'x') and hasattr(point, 'y'):
                            # x() ve y() metodları olan objeler
                            serialized_points.append({'x': point.x(), 'y': point.y()})
                        elif isinstance(point, dict):
                            # Zaten dict formatında
                            serialized_points.append(point)
                        else:
                            # Diğer durumlar için string'e çevir
                            print(f"Bilinmeyen point tipi: {type(point)}")
                            continue
                    
                    stroke_copy['points'] = serialized_points
                
                # Diğer değerleri kontrol et ve serialize et
                for key, value in stroke_copy.items():
                    if key == 'points':
                        continue  # Zaten yukarıda handle ettik
                    elif isinstance(value, QColor):
                        stroke_copy[key] = value.name()
                    elif hasattr(value, 'name') and callable(getattr(value, 'name')):
                        # QColor benzeri objeler
                        stroke_copy[key] = value.name()
                    elif hasattr(value, 'value'):
                        # Qt enum'ları
                        stroke_copy[key] = value.value
                    elif isinstance(value, Qt.PenStyle):
                        stroke_copy[key] = int(value)
                    elif isinstance(value, QPointF):
                        # Tek QPointF objesi
                        stroke_copy[key] = {'x': value.x(), 'y': value.y()}
                    elif not isinstance(value, (str, int, float, bool, list, tuple, dict, type(None))):
                        # JSON serializable olmayan diğer tipler
                        stroke_copy[key] = str(value)
                
                serialized.append(stroke_copy)
                
            except Exception as e:
                print(f"Stroke {i} serialize edilemedi: {e}")
                print(f"Stroke içeriği: {stroke}")
                # Hatalı stroke'u atla
                continue
            
        return serialized
        
    def deserialize_strokes(self, serialized_strokes):
        """JSON'dan stroke'ları geri yükle"""
        from PyQt6.QtGui import QColor
        from PyQt6.QtCore import Qt
        
        strokes = []
        for i, stroke_data in enumerate(serialized_strokes):
            try:
                # ImageStroke kontrolü
                if stroke_data.get('stroke_type') == 'image':
                    # ImageStroke'u deserialize et
                    from image_stroke import ImageStroke
                    image_stroke = ImageStroke.from_dict(stroke_data)
                    strokes.append(image_stroke)
                else:
                    # Normal stroke verilerini kopyala
                    stroke = stroke_data.copy()
                    
                    # String'leri QColor'a çevir
                    if 'color' in stroke and isinstance(stroke['color'], str):
                        stroke['color'] = QColor(stroke['color'])
                    if 'fill_color' in stroke and isinstance(stroke['fill_color'], str):
                        stroke['fill_color'] = QColor(stroke['fill_color'])
                        
                    # Integer'ları Qt enum'larına çevir
                    if 'style' in stroke and isinstance(stroke['style'], int):
                        stroke['style'] = Qt.PenStyle(stroke['style'])
                    if 'line_style' in stroke and isinstance(stroke['line_style'], int):
                        stroke['line_style'] = Qt.PenStyle(stroke['line_style'])
                        
                    strokes.append(stroke)
                    
            except Exception as e:
                print(f"Stroke {i} deserialize edilemedi: {e}")
                continue
            
        return strokes
        
    def get_recent_sessions(self, limit=10):
        """Son oturumları listele"""
        try:
            files = []
            for filename in os.listdir(self.sessions_dir):
                if filename.endswith('.sdm'):
                    filepath = os.path.join(self.sessions_dir, filename)
                    mtime = os.path.getmtime(filepath)
                    files.append((filepath, mtime, filename))
                    
            # Tarihe göre sırala (en yeni önce)
            files.sort(key=lambda x: x[1], reverse=True)
            
            return [(filepath, filename) for filepath, _, filename in files[:limit]]
            
        except Exception:
            return []
            
    def auto_save_session(self, main_window):
        """Otomatik oturum kaydetme"""
        try:
            auto_save_path = os.path.join(self.sessions_dir, "auto_save.sdm")
            result = self.save_session(main_window, auto_save_path)
            if result and hasattr(main_window, 'show_status_message'):
                main_window.show_status_message("Otomatik kayıt tamamlandı")
            return result
        except Exception as e:
            if hasattr(main_window, 'show_status_message'):
                main_window.show_status_message(f"Otomatik kayıt başarısız: {str(e)}")
            return False
            
    def serialize_background_settings(self, bg_settings):
        """Background settings'i JSON'a dönüştürülebilir formata çevir"""
        if not bg_settings:
            return None
            
        from PyQt6.QtGui import QColor
        
        serialized = bg_settings.copy()
        
        # QColor nesnelerini string'e çevir
        if 'background_color' in serialized:
            if isinstance(serialized['background_color'], QColor):
                serialized['background_color'] = serialized['background_color'].name()
        if 'grid_color' in serialized:
            if isinstance(serialized['grid_color'], QColor):
                serialized['grid_color'] = serialized['grid_color'].name()
        if 'major_grid_color' in serialized:
            if isinstance(serialized['major_grid_color'], QColor):
                serialized['major_grid_color'] = serialized['major_grid_color'].name()
                
        return serialized
        
    def deserialize_background_settings(self, serialized_bg_settings):
        """JSON'dan background settings'i geri yükle"""
        if not serialized_bg_settings:
            return None
            
        from PyQt6.QtGui import QColor
        
        bg_settings = serialized_bg_settings.copy()
        
        # String'leri QColor'a çevir
        if 'background_color' in bg_settings and isinstance(bg_settings['background_color'], str):
            bg_settings['background_color'] = QColor(bg_settings['background_color'])
        if 'grid_color' in bg_settings and isinstance(bg_settings['grid_color'], str):
            bg_settings['grid_color'] = QColor(bg_settings['grid_color'])
        if 'major_grid_color' in bg_settings and isinstance(bg_settings['major_grid_color'], str):
            bg_settings['major_grid_color'] = QColor(bg_settings['major_grid_color'])
            
        return bg_settings
        
    def serialize_settings(self, settings_dict):
        """Settings dictionary'sini JSON'a dönüştürülebilir formata çevir"""
        if not settings_dict:
            return {}
            
        from PyQt6.QtGui import QColor
        
        serialized = {}
        for section_name, section_data in settings_dict.items():
            serialized[section_name] = {}
            for key, value in section_data.items():
                # QColor string'lerini kontrol et (hex format)
                if isinstance(value, str) and value.startswith('#') and len(value) == 7:
                    # Zaten string format, olduğu gibi bırak
                    serialized[section_name][key] = value
                else:
                    # Diğer değerler string olarak saklanıyor zaten
                    serialized[section_name][key] = str(value)
                    
        return serialized
        
    def deserialize_settings(self, serialized_settings):
        """JSON'dan settings dictionary'sini geri yükle"""
        if not serialized_settings:
            return {}
            
        # Settings zaten string formatında saklanıyor, direkt döndür
        return serialized_settings 