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
        """Grid rengini al"""
        color_str = self.config.get('Background', 'grid_color', fallback='#C8C8C8')
        return QColor(color_str)
        
    def set_grid_color(self, color):
        """Grid rengini kaydet"""
        self.config.set('Background', 'grid_color', color.name())
        
    def get_grid_size(self):
        """Grid boyutunu al"""
        return self.config.getint('Background', 'grid_size', fallback=20)
        
    def set_grid_size(self, size):
        """Grid boyutunu kaydet"""
        self.config.set('Background', 'grid_size', str(size))
        
    def get_grid_width(self):
        """Grid kalınlığını al"""
        return self.config.getint('Background', 'grid_width', fallback=1)
        
    def set_grid_width(self, width):
        """Grid kalınlığını kaydet"""
        self.config.set('Background', 'grid_width', str(width))
        
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
            'grid_size': self.get_grid_size(),
            'grid_width': self.get_grid_width(),
            'grid_opacity': self.get_grid_opacity(),
            'snap_to_grid': self.get_snap_to_grid()
        }
        
    def set_background_settings(self, settings):
        """Tüm arka plan ayarlarını kaydet"""
        self.set_background_type(settings.get('type', 'solid'))
        self.set_background_color(settings.get('background_color', QColor(255, 255, 255)))
        self.set_grid_color(settings.get('grid_color', QColor(200, 200, 200)))
        self.set_grid_size(settings.get('grid_size', 20))
        self.set_grid_width(settings.get('grid_width', 1))
        self.set_grid_opacity(settings.get('grid_opacity', 1.0))
        self.set_snap_to_grid(settings.get('snap_to_grid', False))
        
    # Araç ayarları
    def get_active_tool(self):
        """Aktif aracı al"""
        return self.config.get('Tools', 'active_tool', fallback='bspline')
        
    def set_active_tool(self, tool):
        """Aktif aracı kaydet"""
        self.config.set('Tools', 'active_tool', tool)
        
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