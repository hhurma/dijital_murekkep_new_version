import json
import os
import tempfile
from datetime import datetime
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from PyQt6.QtCore import QStandardPaths

class SessionManager:
    """Oturum kaydetme ve açma işlemleri"""
    
    def __init__(self):
        self.sessions_dir = self.get_sessions_directory()
        self.ensure_sessions_directory()
        self.pdf_importer = None

    def set_pdf_importer(self, importer):
        self.pdf_importer = importer
        
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
                'version': '1.1',
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

                if tab_widget:
                    tab_data = {
                        'name': tab_name,
                        'background_settings': self.serialize_background_settings(tab_widget.background_settings)
                    }

                    if hasattr(tab_widget, 'export_pdf_background_state'):
                        pdf_state = tab_widget.export_pdf_background_state()
                        if pdf_state:
                            tab_data['pdf_background'] = pdf_state

                    if hasattr(tab_widget, 'layer_manager'):
                        tab_data['layers'] = self.serialize_layers(tab_widget)
                        if hasattr(tab_widget, 'has_pdf_background') and hasattr(tab_widget, 'export_pdf_page_states'):
                            if tab_widget.has_pdf_background():
                                page_states = tab_widget.export_pdf_page_states()
                                if page_states:
                                    serialized_pages = self.serialize_pdf_page_states(page_states)
                                    if serialized_pages:
                                        tab_data['pdf_page_layers'] = serialized_pages
                    elif hasattr(tab_widget, 'strokes'):
                        # Eski sürümler için geri uyumluluk
                        tab_data['strokes'] = self.serialize_strokes(tab_widget.strokes)

                    session_data['tabs'].append(tab_data)
                    
            target_directory = os.path.dirname(filename)
            if target_directory and not os.path.exists(target_directory):
                os.makedirs(target_directory, exist_ok=True)

            temp_file = None
            temp_path = None
            try:
                temp_file = tempfile.NamedTemporaryFile(
                    'w',
                    encoding='utf-8',
                    delete=False,
                    dir=target_directory if target_directory else None,
                    prefix='.tmp_session_',
                    suffix='.sdm'
                )
                temp_path = temp_file.name
                json.dump(session_data, temp_file, indent=2, ensure_ascii=False)
                temp_file.flush()
                os.fsync(temp_file.fileno())
            finally:
                if temp_file is not None:
                    temp_file.close()

            try:
                os.replace(temp_path, filename)
            finally:
                if temp_path and os.path.exists(temp_path):
                    # os.replace başarılıysa temp_path artık filename oldu;
                    # başarısız olduysa geçici dosyayı temizle.
                    try:
                        os.remove(temp_path)
                    except FileNotFoundError:
                        pass
                    except Exception:
                        pass
                
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

            return self._load_session_from_path(main_window, filename)

        except Exception as e:
            # Status bar'da hata mesajı göster
            if hasattr(main_window, 'show_status_message'):
                main_window.show_status_message(f"Oturum yüklenemedi: {str(e)}")
            return None

    def _load_session_from_path(self, main_window, filename):
        """Verilen dosya yolundan oturumu yükle"""
        # JSON dosyasından oku
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
        except json.JSONDecodeError as decode_error:
            message = (
                "Oturum dosyası okunamadı. Dosya eksik ya da bozulmuş görünüyor. "
                "Lütfen farklı bir yedek seçmeyi deneyin."
            )
            raise json.JSONDecodeError(message, decode_error.doc, decode_error.pos) from decode_error

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

            if 'pdf_background' in tab_data and hasattr(current_widget, 'import_pdf_background_state'):
                importer = self.pdf_importer or getattr(main_window, 'pdf_importer', None)
                current_widget.import_pdf_background_state(tab_data['pdf_background'], importer)

            # Stroke'ları veya katmanları yükle
            if current_widget and 'layers' in tab_data:
                self.deserialize_layers(current_widget, tab_data['layers'])
            elif current_widget and 'strokes' in tab_data:
                current_widget.strokes = self.deserialize_strokes(tab_data['strokes'])

            # Arka plan ayarlarını yükle
            if 'background_settings' in tab_data:
                bg_settings = self.deserialize_background_settings(tab_data['background_settings'])
                current_widget.set_background_settings(bg_settings)

            if (
                'pdf_page_layers' in tab_data
                and hasattr(current_widget, 'import_pdf_page_states')
            ):
                page_states = self.deserialize_pdf_page_states(tab_data['pdf_page_layers'])
                if page_states:
                    current_widget.import_pdf_page_states(page_states)

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
            
    def serialize_strokes(self, strokes):
        """Stroke'ları JSON'a dönüştürülebilir formata çevir"""
        from PyQt6.QtGui import QColor
        from PyQt6.QtCore import Qt, QPointF
        try:
            import numpy as np
        except ImportError:  # pragma: no cover - numpy is an optional dependency
            np = None

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
                    elif np is not None and isinstance(value, np.ndarray):
                        stroke_copy[key] = value.tolist()
                    elif (
                        np is not None
                        and isinstance(value, (np.generic,))
                    ):
                        stroke_copy[key] = value.item()
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

    def serialize_layers(self, drawing_widget):
        """DrawingWidget katmanlarını serileştir"""
        if not hasattr(drawing_widget, 'layer_manager'):
            return {
                'order': [],
                'active_layer': None,
                'layers': []
            }

        state = drawing_widget.layer_manager.export_state()
        serialized_state = self.serialize_layer_state(state)

        if (
            hasattr(drawing_widget, 'has_pdf_background')
            and callable(getattr(drawing_widget, 'has_pdf_background'))
            and drawing_widget.has_pdf_background()
            and callable(getattr(drawing_widget, 'get_pdf_page_layer_states', None))
        ):
            pdf_payload = drawing_widget.get_pdf_page_layer_states()
            serialized_pdf = self.serialize_pdf_layers_payload(pdf_payload)
            if serialized_pdf:
                serialized_state['pdf_layers'] = serialized_pdf

        return serialized_state

    def serialize_layer_state(self, state):
        if not state:
            return {
                'order': [],
                'active_layer': None,
                'layers': []
            }

        layers_dict = state.get('layers', {})
        ordered_ids = list(state.get('layer_order', []))
        for layer_id in layers_dict.keys():
            if layer_id not in ordered_ids:
                ordered_ids.append(layer_id)

        serialized_layers = []
        for layer_id in ordered_ids:
            layer_data = layers_dict.get(layer_id, {})
            serialized_layers.append({
                'id': layer_id,
                'name': layer_data.get('name', layer_id),
                'visible': layer_data.get('visible', True),
                'locked': layer_data.get('locked', False),
                'strokes': self.serialize_strokes(layer_data.get('strokes', []))
            })

        return {
            'order': ordered_ids,
            'active_layer': state.get('active_layer'),
            'layers': serialized_layers
        }

    def serialize_pdf_page_states(self, page_states):
        serialized = {}
        for page_index, state in page_states.items():
            if state is None:
                continue
            serialized[str(page_index)] = self.serialize_layer_state(state)
        return serialized

    def serialize_pdf_layers_payload(self, payload):
        if not payload or not isinstance(payload, dict):
            return None

        serialized_payload = {}

        page_states = payload.get('page_states')
        if isinstance(page_states, dict):
            serialized_pages = {}
            for page_index, state in page_states.items():
                if state is None:
                    continue
                serialized_pages[str(page_index)] = self.serialize_layer_state(state)
            serialized_payload['page_states'] = serialized_pages
        else:
            serialized_payload['page_states'] = {}

        if 'current_page' in payload:
            try:
                serialized_payload['current_page'] = int(payload['current_page'])
            except (TypeError, ValueError):
                pass

        if 'page_count' in payload:
            try:
                serialized_payload['page_count'] = int(payload['page_count'])
            except (TypeError, ValueError):
                pass

        for key in payload.keys():
            if key in {'page_states', 'current_page', 'page_count'}:
                continue
            value = payload[key]
            if isinstance(value, (str, int, float, bool)) or value is None:
                serialized_payload[key] = value

        return serialized_payload
        
    def deserialize_strokes(self, serialized_strokes):
        """JSON'dan stroke'ları geri yükle"""
        from PyQt6.QtGui import QColor
        from PyQt6.QtCore import Qt
        try:
            import numpy as np
        except ImportError:  # pragma: no cover - numpy is an optional dependency
            np = None
        
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
                        
                    if np is not None:
                        is_bspline = (
                            stroke.get('type') == 'bspline'
                            or stroke.get('tool_type') == 'bspline'
                        )

                        if is_bspline:
                            for key in ('knots', 'u'):
                                if key not in stroke:
                                    continue

                                value = stroke[key]
                                if isinstance(value, list):
                                    stroke[key] = np.array(value, dtype=float)
                                elif isinstance(value, tuple):
                                    stroke[key] = np.array(list(value), dtype=float)
                                elif isinstance(value, str):
                                    try:
                                        parsed = json.loads(value)
                                    except (TypeError, json.JSONDecodeError):
                                        continue
                                    stroke[key] = np.array(parsed, dtype=float)

                    strokes.append(stroke)
                    
            except Exception as e:
                print(f"Stroke {i} deserialize edilemedi: {e}")
                continue
            
        return strokes

    def deserialize_layers(self, drawing_widget, serialized_layers):
        """Serileştirilmiş katmanları DrawingWidget'a yükle"""
        if not hasattr(drawing_widget, 'layer_manager'):
            return

        state = self.deserialize_layer_state(serialized_layers)
        drawing_widget.layer_manager.import_state(state)

        if (
            isinstance(serialized_layers, dict)
            and 'pdf_layers' in serialized_layers
            and hasattr(drawing_widget, 'import_pdf_page_states')
        ):
            pdf_payload = self.deserialize_pdf_layers_payload(serialized_layers.get('pdf_layers'))
            if pdf_payload is not None and (
                not hasattr(drawing_widget, 'has_pdf_background')
                or drawing_widget.has_pdf_background()
            ):
                drawing_widget.import_pdf_page_states(pdf_payload)

    def deserialize_layer_state(self, serialized_layers):
        if not serialized_layers:
            return {
                'active_layer': None,
                'layer_order': [],
                'layers': {}
            }

        layer_list = serialized_layers.get('layers', [])
        ordered_ids = list(serialized_layers.get('order', []))

        state = {
            'active_layer': serialized_layers.get('active_layer'),
            'layer_order': [],
            'layers': {}
        }

        for index, layer in enumerate(layer_list):
            layer_id = layer.get('id') or f"layer_{index + 1}"
            state['layers'][layer_id] = {
                'id': layer_id,
                'name': layer.get('name', layer_id),
                'visible': layer.get('visible', True),
                'locked': layer.get('locked', False),
                'strokes': self.deserialize_strokes(layer.get('strokes', []))
            }
            if layer_id not in ordered_ids:
                ordered_ids.append(layer_id)

        state['layer_order'] = ordered_ids
        return state

    def deserialize_pdf_page_states(self, serialized_page_states):
        page_states = {}
        for key, value in serialized_page_states.items():
            try:
                index = int(key)
            except (TypeError, ValueError):
                continue

            state = self.deserialize_layer_state(value)
            page_states[index] = state

        return page_states

    def deserialize_pdf_layers_payload(self, payload):
        if not payload or not isinstance(payload, dict):
            return None

        page_states_data = payload.get('page_states', {})
        deserialized_states = {}

        if isinstance(page_states_data, dict):
            for key, value in page_states_data.items():
                try:
                    index = int(key)
                except (TypeError, ValueError):
                    continue
                state = self.deserialize_layer_state(value)
                deserialized_states[index] = state

        result = {'page_states': deserialized_states}

        if 'current_page' in payload:
            try:
                result['current_page'] = int(payload['current_page'])
            except (TypeError, ValueError):
                pass

        if 'page_count' in payload:
            try:
                result['page_count'] = int(payload['page_count'])
            except (TypeError, ValueError):
                pass

        for key in payload.keys():
            if key in {'page_states', 'current_page', 'page_count'}:
                continue
            value = payload[key]
            if isinstance(value, (str, int, float, bool)) or value is None:
                result[key] = value

        return result
        
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

    def get_auto_save_path(self):
        """Otomatik kayıt dosyasının yolunu döndür"""
        return os.path.join(self.sessions_dir, "auto_save.sdm")

    def has_auto_save(self):
        """Otomatik kayıt dosyası mevcut mu?"""
        auto_save_path = self.get_auto_save_path()
        return os.path.exists(auto_save_path) and os.path.getsize(auto_save_path) > 0

    def load_auto_save(self, main_window):
        """Otomatik kaydedilen oturumu yükle"""
        auto_save_path = self.get_auto_save_path()
        if not os.path.exists(auto_save_path):
            return None

        try:
            return self._load_session_from_path(main_window, auto_save_path)
        except json.JSONDecodeError as decode_error:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f"{auto_save_path}.corrupt_{timestamp}"
            cleanup_message = ""

            try:
                os.replace(auto_save_path, backup_path)
                cleanup_message = (
                    f" Bozuk dosya yedek olarak '{os.path.basename(backup_path)}' adına taşındı."
                )
            except OSError:
                backup_path = None
                try:
                    os.remove(auto_save_path)
                    cleanup_message = " Bozuk dosya silindi."
                except OSError:
                    cleanup_message = (
                        " Bozuk dosya otomatik olarak temizlenemedi; lütfen dosyayı manuel olarak silin."
                    )

            user_message = (
                "Otomatik kayıt dosyası bozulduğu için yüklenemedi." + cleanup_message
            )
            technical_details = (
                f"Teknik detay: {decode_error.msg} (satır {decode_error.lineno}, sütun {decode_error.colno})."
            )

            if hasattr(main_window, 'show_status_message'):
                main_window.show_status_message(user_message)

            try:
                QMessageBox.warning(
                    main_window,
                    "Otomatik Kayıt Hatası",
                    f"{user_message}\n\n{technical_details}"
                )
            except Exception:
                # GUI henüz hazır değilse sessizce devam et
                pass

            return None
        except Exception as e:
            if hasattr(main_window, 'show_status_message'):
                main_window.show_status_message(f"Otomatik kayıt yüklenemedi: {str(e)}")
            return None

    def clear_auto_save(self):
        """Otomatik kayıt dosyasını sil"""
        auto_save_path = self.get_auto_save_path()
        try:
            if os.path.exists(auto_save_path):
                os.remove(auto_save_path)
                return True
            return False
        except Exception as e:
            print(f"Otomatik kayıt dosyası silinemedi: {e}")
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
