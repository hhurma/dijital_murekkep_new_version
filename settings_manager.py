import configparser
import os
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt

class SettingsManager:
    """Uygulama ayarlarını yöneten sınıf"""
    
    def __init__(self, config_file="settings.ini"):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.load_settings()
        
    def load_settings(self):
        """Ayarları dosyadan yükle"""
        if os.path.exists(self.config_file):
            self.config.read(self.config_file)
        else:
            self.create_default_settings()
            
    def create_default_settings(self):
        """Varsayılan ayarları oluştur"""
        # Çizim ayarları
        self.config['Drawing'] = {
            'current_color': '#000000',
            'line_width': '2',
            'fill_enabled': 'False',
            'fill_color': '#FFFFFF',
            'opacity': '1.0',
            'line_style': '1'  # Qt.PenStyle.SolidLine
        }
        
        # Color palette ayarları
        self.config['ColorPalette'] = {
            'colors': '#000000',  # Virgülle ayrılmış renk listesi
            'selected_index': '0'
        }
        
        # Arka plan ayarları
        self.config['Background'] = {
            'type': 'solid',
            'background_color': '#FFFFFF',
            'grid_color': '#C8C8C8',
            'grid_size': '20',
            'grid_width': '1',
            'grid_opacity': '1.0',
            'snap_to_grid': 'False'
        }
        
        # Araç ayarları
        self.config['Tools'] = {
            'active_tool': 'bspline'
        }
        
        # Pencere ayarları
        self.config['Window'] = {
            'width': '1200',
            'height': '800',
            'background_dock_visible': 'False'
        }
        
        # PDF ayarları
        self.config['PDF'] = {
            'orientation': 'landscape'  # portrait veya landscape
        }
        
        # Canvas ayarları
        self.config['Canvas'] = {
            'orientation': 'landscape',  # portrait veya landscape
            'size': 'small',
            'custom_width': '1200',
            'custom_height': '800'
        }

        # Gölge varsayılanları (tüm araçlar için ortak)
        self.config['ShadowDefaults'] = {
            'enabled': 'False',
            'color': '#000000',
            'offset_x': '5',
            'offset_y': '5',
            'blur': '10',
            'size': '0',
            'opacity': '0.7',
            'inner': 'False',
            'quality': 'medium'
        }
        
        self.save_settings()
        
    def save_settings(self):
        """Ayarları dosyaya kaydet"""
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)
            
    # Çizim ayarları
    def get_drawing_color(self):
        """Çizim rengini al"""
        color_str = self.config.get('Drawing', 'current_color', fallback='#000000')
        return QColor(color_str)
        
    def set_drawing_color(self, color):
        """Çizim rengini kaydet"""
        self.config.set('Drawing', 'current_color', color.name())
        
    def get_line_width(self):
        """Çizgi kalınlığını al"""
        return self.config.getint('Drawing', 'line_width', fallback=2)
        
    def set_line_width(self, width):
        """Çizgi kalınlığını kaydet"""
        self.config.set('Drawing', 'line_width', str(width))
        
    def get_fill_enabled(self):
        """Dolgu durumunu al"""
        return self.config.getboolean('Drawing', 'fill_enabled', fallback=False)
        
    def set_fill_enabled(self, enabled):
        """Dolgu durumunu kaydet"""
        self.config.set('Drawing', 'fill_enabled', str(enabled))
        
    def get_fill_color(self):
        """Dolgu rengini al"""
        color_str = self.config.get('Drawing', 'fill_color', fallback='#FFFFFF')
        return QColor(color_str)
        
    def set_fill_color(self, color):
        """Dolgu rengini kaydet"""
        self.config.set('Drawing', 'fill_color', color.name())
        
    def get_opacity(self):
        """Opacity'yi al"""
        return self.config.getfloat('Drawing', 'opacity', fallback=1.0)
        
    def set_opacity(self, opacity):
        """Opacity'yi kaydet"""
        self.config.set('Drawing', 'opacity', str(opacity))
        
    def get_line_style(self):
        """Çizgi stilini al"""
        style_int = self.config.getint('Drawing', 'line_style', fallback=1)
        return Qt.PenStyle(style_int)
        
    def set_line_style(self, style):
        """Çizgi stilini kaydet"""
        # Qt.PenStyle enum'ından integer değeri al
        if hasattr(style, 'value'):
            style_value = style.value
        else:
            style_value = int(style)
        self.config.set('Drawing', 'line_style', str(style_value))
        
    # Color palette ayarları
    def get_palette_colors(self):
        """Color palette renklerini al"""
        colors_str = self.config.get('ColorPalette', 'colors', fallback='#000000')
        color_names = colors_str.split(',')
        colors = []
        for color_name in color_names:
            color_name = color_name.strip()
            if color_name:
                colors.append(QColor(color_name))
        return colors if colors else [QColor('#000000')]
        
    def set_palette_colors(self, colors):
        """Color palette renklerini kaydet"""
        # ColorPalette section'ının var olduğundan emin ol
        if not self.config.has_section('ColorPalette'):
            self.config.add_section('ColorPalette')
            
        color_names = [color.name() for color in colors]
        colors_str = ','.join(color_names)
        self.config.set('ColorPalette', 'colors', colors_str)
        
    def get_palette_selected_index(self):
        """Color palette seçili index'i al"""
        return self.config.getint('ColorPalette', 'selected_index', fallback=0)
        
    def set_palette_selected_index(self, index):
        """Color palette seçili index'i kaydet"""
        # ColorPalette section'ının var olduğundan emin ol
        if not self.config.has_section('ColorPalette'):
            self.config.add_section('ColorPalette')
            
        self.config.set('ColorPalette', 'selected_index', str(index))
        
    # Arka plan ayarları
    def get_background_type(self):
        """Arka plan tipini al"""
        return self.config.get('Background', 'type', fallback='solid')
        
    def set_background_type(self, bg_type):
        """Arka plan tipini kaydet"""
        self.config.set('Background', 'type', bg_type)
        
    def get_background_color(self):
        """Arka plan rengini al"""
        color_str = self.config.get('Background', 'background_color', fallback='#FFFFFF')
        return QColor(color_str)
        
    def set_background_color(self, color):
        """Arka plan rengini kaydet"""
        self.config.set('Background', 'background_color', color.name())
        
    def get_grid_color(self):
        """Minor grid rengini al"""
        color_str = self.config.get('Background', 'grid_color', fallback='#C8C8C8')
        return QColor(color_str)
        
    def set_grid_color(self, color):
        """Minor grid rengini kaydet"""
        self.config.set('Background', 'grid_color', color.name())
        
    def get_major_grid_color(self):
        """Major grid rengini al"""
        color_str = self.config.get('Background', 'major_grid_color', fallback='#969696')
        return QColor(color_str)
        
    def set_major_grid_color(self, color):
        """Major grid rengini kaydet"""
        self.config.set('Background', 'major_grid_color', color.name())
        
    def get_grid_size(self):
        """Grid boyutunu al"""
        return self.config.getint('Background', 'grid_size', fallback=20)
        
    def set_grid_size(self, size):
        """Grid boyutunu kaydet"""
        self.config.set('Background', 'grid_size', str(size))
        
    def get_grid_width(self):
        """Minor grid kalınlığını al"""
        return self.config.getint('Background', 'grid_width', fallback=1)
        
    def set_grid_width(self, width):
        """Minor grid kalınlığını kaydet"""
        self.config.set('Background', 'grid_width', str(width))
        
    def get_major_grid_width(self):
        """Major grid kalınlığını al"""
        return self.config.getint('Background', 'major_grid_width', fallback=2)
        
    def set_major_grid_width(self, width):
        """Major grid kalınlığını kaydet"""
        self.config.set('Background', 'major_grid_width', str(width))
        
    def get_major_grid_interval(self):
        """Major grid aralığını al"""
        return self.config.getint('Background', 'major_grid_interval', fallback=5)
        
    def set_major_grid_interval(self, interval):
        """Major grid aralığını kaydet"""
        self.config.set('Background', 'major_grid_interval', str(interval))
        
    def get_grid_opacity(self):
        """Grid şeffaflığını al"""
        return self.config.getfloat('Background', 'grid_opacity', fallback=1.0)
        
    def set_grid_opacity(self, opacity):
        """Grid şeffaflığını kaydet"""
        self.config.set('Background', 'grid_opacity', str(opacity))
        
    def get_snap_to_grid(self):
        """Snap to grid durumunu al"""
        return self.config.getboolean('Background', 'snap_to_grid', fallback=False)
        
    def set_snap_to_grid(self, enabled):
        """Snap to grid durumunu kaydet"""
        self.config.set('Background', 'snap_to_grid', str(enabled))
        
    def get_background_settings(self):
        """Tüm arka plan ayarlarını al"""
        return {
            'type': self.get_background_type(),
            'background_color': self.get_background_color(),
            'grid_color': self.get_grid_color(),
            'major_grid_color': self.get_major_grid_color(),
            'grid_size': self.get_grid_size(),
            'grid_width': self.get_grid_width(),
            'major_grid_width': self.get_major_grid_width(),
            'major_grid_interval': self.get_major_grid_interval(),
            'grid_opacity': self.get_grid_opacity(),
            'snap_to_grid': self.get_snap_to_grid()
        }
        
    def set_background_settings(self, settings):
        """Tüm arka plan ayarlarını kaydet"""
        self.set_background_type(settings.get('type', 'solid'))
        self.set_background_color(settings.get('background_color', QColor(255, 255, 255)))
        self.set_grid_color(settings.get('grid_color', QColor(200, 200, 200)))
        self.set_major_grid_color(settings.get('major_grid_color', QColor(150, 150, 150)))
        self.set_grid_size(settings.get('grid_size', 20))
        self.set_grid_width(settings.get('grid_width', 1))
        self.set_major_grid_width(settings.get('major_grid_width', 2))
        self.set_major_grid_interval(settings.get('major_grid_interval', 5))
        self.set_grid_opacity(settings.get('grid_opacity', 1.0))
        self.set_snap_to_grid(settings.get('snap_to_grid', False))
        
    # Araç ayarları
    def get_active_tool(self):
        """Aktif aracı al"""
        return self.config.get('Tools', 'active_tool', fallback='bspline')
        
    def set_active_tool(self, tool):
        """Aktif aracı kaydet"""
        self.config.set('Tools', 'active_tool', tool)

    # Gölge varsayılanları
    def get_shadow_defaults(self):
        from PyQt6.QtGui import QColor
        sec = 'ShadowDefaults'
        enabled = self.config.getboolean(sec, 'enabled', fallback=False)
        color = QColor(self.config.get(sec, 'color', fallback='#000000'))
        offset_x = self.config.getint(sec, 'offset_x', fallback=5)
        offset_y = self.config.getint(sec, 'offset_y', fallback=5)
        blur = self.config.getint(sec, 'blur', fallback=10)
        size = self.config.getint(sec, 'size', fallback=0)
        opacity = self.config.getfloat(sec, 'opacity', fallback=0.7)
        inner = self.config.getboolean(sec, 'inner', fallback=False)
        quality = self.config.get(sec, 'quality', fallback='medium')
        return {
            'has_shadow': enabled,
            'shadow_color': color,
            'shadow_offset_x': offset_x,
            'shadow_offset_y': offset_y,
            'shadow_blur': blur,
            'shadow_size': size,
            'shadow_opacity': opacity,
            'inner_shadow': inner,
            'shadow_quality': quality,
        }

    def set_shadow_defaults(self, payload):
        sec = 'ShadowDefaults'
        if not self.config.has_section(sec):
            self.config.add_section(sec)
        if 'has_shadow' in payload:
            self.config.set(sec, 'enabled', str(bool(payload['has_shadow'])))
        if 'shadow_color' in payload:
            self.config.set(sec, 'color', payload['shadow_color'].name())
        if 'shadow_offset_x' in payload:
            self.config.set(sec, 'offset_x', str(int(payload['shadow_offset_x'])))
        if 'shadow_offset_y' in payload:
            self.config.set(sec, 'offset_y', str(int(payload['shadow_offset_y'])))
        if 'shadow_blur' in payload:
            self.config.set(sec, 'blur', str(int(payload['shadow_blur'])))
        if 'shadow_size' in payload:
            self.config.set(sec, 'size', str(int(payload['shadow_size'])))
        if 'shadow_opacity' in payload:
            self.config.set(sec, 'opacity', str(float(payload['shadow_opacity'])))
        if 'inner_shadow' in payload:
            self.config.set(sec, 'inner', str(bool(payload['inner_shadow'])))
        if 'shadow_quality' in payload:
            self.config.set(sec, 'quality', str(payload['shadow_quality']))
        
    # Pencere ayarları
    def get_window_size(self):
        """Pencere boyutunu al"""
        width = self.config.getint('Window', 'width', fallback=1200)
        height = self.config.getint('Window', 'height', fallback=800)
        return (width, height)
        
    def set_window_size(self, width, height):
        """Pencere boyutunu kaydet"""
        self.config.set('Window', 'width', str(width))
        self.config.set('Window', 'height', str(height))
        
    def get_background_dock_visible(self):
        """Arka plan dock'ının görünürlüğünü al"""
        return self.config.getboolean('Window', 'background_dock_visible', fallback=False)
        
    def set_background_dock_visible(self, visible):
        """Arka plan dock'ının görünürlüğünü kaydet"""
        self.config.set('Window', 'background_dock_visible', str(visible))
        
    def get_all_settings(self):
        """Tüm ayarları dictionary olarak döndür"""
        settings_dict = {}
        for section_name in self.config.sections():
            settings_dict[section_name] = dict(self.config[section_name])
        return settings_dict
        
    def load_from_dict(self, settings_dict):
        """Dictionary'den ayarları yükle"""
        try:
            # Mevcut ayarları temizle
            for section in self.config.sections():
                self.config.remove_section(section)
                
            # Yeni ayarları yükle
            for section_name, section_data in settings_dict.items():
                if not self.config.has_section(section_name):
                    self.config.add_section(section_name)
                for key, value in section_data.items():
                    self.config.set(section_name, key, str(value))
                    
            self.save_settings()
        except Exception as e:
            print(f"Ayarlar yüklenemedi: {e}")
    
    # PDF ayarları
    def get_pdf_orientation(self):
        """PDF sayfa yönünü al"""
        return self.config.get('PDF', 'orientation', fallback='landscape')
        
    def set_pdf_orientation(self, orientation):
        """PDF sayfa yönünü kaydet"""
        if not self.config.has_section('PDF'):
            self.config.add_section('PDF')
        self.config.set('PDF', 'orientation', orientation)
        
    # Canvas ayarları
    def get_canvas_orientation(self):
        """Canvas yönünü al"""
        return self.config.get('Canvas', 'orientation', fallback='landscape')
        
    def set_canvas_orientation(self, orientation):
        """Canvas yönünü kaydet"""
        if not self.config.has_section('Canvas'):
            self.config.add_section('Canvas')
        self.config.set('Canvas', 'orientation', orientation) 

    def get_canvas_size_key(self):
        return self.config.get('Canvas', 'size', fallback='small')

    def set_canvas_size_key(self, size_key):
        if not self.config.has_section('Canvas'):
            self.config.add_section('Canvas')
        self.config.set('Canvas', 'size', size_key)

    def get_custom_canvas_size(self):
        w = self.config.getint('Canvas', 'custom_width', fallback=1200)
        h = self.config.getint('Canvas', 'custom_height', fallback=800)
        return w, h

    def set_custom_canvas_size(self, width, height):
        if not self.config.has_section('Canvas'):
            self.config.add_section('Canvas')
        self.config.set('Canvas', 'custom_width', str(int(width)))
        self.config.set('Canvas', 'custom_height', str(int(height)))