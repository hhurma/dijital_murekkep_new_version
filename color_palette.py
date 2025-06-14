from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QPushButton, QColorDialog, 
                            QToolTip, QApplication)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPalette, QColor
import qtawesome as qta

class ColorButton(QPushButton):
    """Renk seçim butonu - uzun basma ile renk değiştirme"""
    colorChanged = pyqtSignal(QColor)
    colorSelected = pyqtSignal(QColor)
    deleteRequested = pyqtSignal()
    
    def __init__(self, color=Qt.GlobalColor.black, can_delete=False, parent=None):
        super().__init__(parent)
        self.color = QColor(color)
        self.can_delete = can_delete
        self.long_press_timer = QTimer()
        self.long_press_timer.setSingleShot(True)
        self.long_press_timer.timeout.connect(self.show_color_dialog)
        self.is_long_press = False
        
        self.setFixedSize(32, 32)
        self.setup_style()
        
        # Tooltip
        if can_delete:
            self.setToolTip("Sol tık: rengi seç\nUzun basma: rengi değiştir\nSağ tık: sil")
        else:
            self.setToolTip("Sol tık: rengi seç\nUzun basma: rengi değiştir")
        
    def setup_style(self):
        """Buton stilini ayarla"""
        color_hex = self.color.name()
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color_hex};
                border: 2px solid #ddd;
                border-radius: 16px;
                margin: 2px;
            }}
            QPushButton:hover {{
                border: 2px solid #999;
            }}
            QPushButton:pressed {{
                border: 3px solid #666;
            }}
            QPushButton:checked {{
                border: 3px solid #000;
            }}
        """)
        
    def set_color(self, color):
        """Rengi ayarla"""
        self.color = QColor(color)
        self.setup_style()
        self.colorChanged.emit(self.color)
        
    def get_color(self):
        """Rengi al"""
        return self.color
        
    def mousePressEvent(self, event):
        """Mouse basma"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_long_press = False
            self.long_press_timer.start(500)  # 500ms uzun basma
        elif event.button() == Qt.MouseButton.RightButton and self.can_delete:
            # Sağ tık - silme
            self.deleteRequested.emit()
            return
        super().mousePressEvent(event)
        
    def mouseReleaseEvent(self, event):
        """Mouse bırakma"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.long_press_timer.stop()
            if not self.is_long_press:
                # Kısa tık - rengi seç
                self.colorSelected.emit(self.color)
        super().mouseReleaseEvent(event)
        
    def show_color_dialog(self):
        """Renk seçim dialogu göster"""
        self.is_long_press = True
        color = QColorDialog.getColor(self.color, self, "Renk Seçin")
        if color.isValid():
            self.set_color(color)

class ColorPalette(QWidget):
    """Dinamik renk paleti - başlangıçta 1 renk, + ile maksimum 5'e kadar"""
    colorSelected = pyqtSignal(QColor)
    paletteChanged = pyqtSignal()  # Palette değiştiğinde sinyal
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_color = QColor(Qt.GlobalColor.black)
        self.color_buttons = []
        self.add_button = None
        self.max_colors = 5
        self.settings_manager = None  # Ana pencere tarafından ayarlanacak
        self.loading_from_settings = False  # Ayarlardan yüklenirken sinyal gönderme
        self.setup_ui()
        
    def setup_ui(self):
        """UI bileşenlerini oluştur"""
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(2, 2, 2, 2)
        self.layout.setSpacing(2)
        
        # İlk renk butonu (siyah)
        self.add_color_button(Qt.GlobalColor.black, selected=True)
        
        # + butonu
        self.create_add_button()
        
        self.setLayout(self.layout)
        
    def create_add_button(self):
        """+ butonu oluştur"""
        self.add_button = QPushButton("+")
        self.add_button.setFixedSize(32, 32)
        self.add_button.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 2px dashed #999;
                border-radius: 16px;
                margin: 2px;
                font-size: 16px;
                font-weight: bold;
                color: #666;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border: 2px dashed #666;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)
        self.add_button.clicked.connect(self.add_new_color)
        self.add_button.setToolTip("Yeni renk ekle")
        self.layout.addWidget(self.add_button)
        
        # Maksimum renk sayısına ulaşıldıysa gizle
        if len(self.color_buttons) >= self.max_colors:
            self.add_button.hide()
    
    def add_color_button(self, color, selected=False):
        """Yeni renk butonu ekle"""
        self.add_color_button_internal(color, selected)
            
        # Ayarlara kaydet (sadece yükleme sırasında değilse)
        if not self.loading_from_settings:
            self.save_to_settings()
            self.paletteChanged.emit()
        
    def add_color_button_internal(self, color, selected=False):
        """İç kullanım için renk butonu ekle (sinyal göndermez)"""
        can_delete = len(self.color_buttons) > 0  # İlk renk silinemez
        btn = ColorButton(color, can_delete)
        btn.setCheckable(True)
        btn.colorSelected.connect(self.on_color_selected)
        btn.colorChanged.connect(self.on_color_changed)
        btn.deleteRequested.connect(lambda: self.delete_color_button(btn))
        
        if selected:
            btn.setChecked(True)
            
        # + butonundan önce ekle
        insert_pos = self.layout.count() - 1 if self.add_button else self.layout.count()
        self.layout.insertWidget(insert_pos, btn)
        self.color_buttons.append(btn)
        
        # Maksimum sayıya ulaşıldıysa + butonunu gizle
        if len(self.color_buttons) >= self.max_colors and self.add_button:
            self.add_button.hide()

    def delete_color_button(self, button):
        """Renk butonunu sil"""
        if len(self.color_buttons) <= 1:  # En az 1 renk olmalı
            return
            
        was_selected = button.isChecked()
        
        # Butonu listeden ve layout'tan kaldır
        self.color_buttons.remove(button)
        self.layout.removeWidget(button)
        button.deleteLater()
        
        # Eğer silinen buton seçiliyse, ilk butonu seç
        if was_selected and self.color_buttons:
            self.color_buttons[0].setChecked(True)
            self.current_color = self.color_buttons[0].get_color()
            self.colorSelected.emit(self.current_color)
            
        # + butonunu tekrar göster
        if len(self.color_buttons) < self.max_colors:
            self.add_button.show()
            
        # İlk butonun silinebilirliğini güncelle
        if len(self.color_buttons) == 1:
            self.color_buttons[0].can_delete = False
            self.color_buttons[0].setToolTip("Sol tık: rengi seç\nUzun basma: rengi değiştir")
            
        # Ayarlara kaydet (sadece yükleme sırasında değilse)
        if not self.loading_from_settings:
            self.save_to_settings()
            self.paletteChanged.emit()
    
    def set_settings_manager(self, settings_manager):
        """Settings manager'ı ayarla"""
        self.settings_manager = settings_manager
        
    def load_from_settings(self):
        """Ayarlardan renkleri yükle"""
        if not self.settings_manager:
            return
            
        self.loading_from_settings = True  # Yükleme modunu aç
        
        # Mevcut butonları temizle
        for btn in self.color_buttons[:]:
            self.layout.removeWidget(btn)
            btn.deleteLater()
        self.color_buttons.clear()
        
        # Ayarlardan renkleri al
        colors = self.settings_manager.get_palette_colors()
        selected_index = self.settings_manager.get_palette_selected_index()
        
        # Renk butonlarını oluştur
        for i, color in enumerate(colors):
            selected = (i == selected_index)
            self.add_color_button_internal(color, selected=selected)  # Internal fonksiyon kullan
            if selected:
                self.current_color = color
                
        # + butonunu yeniden oluştur
        if self.add_button:
            self.layout.removeWidget(self.add_button)
            self.add_button.deleteLater()
        self.create_add_button()
        
        self.loading_from_settings = False  # Yükleme modunu kapat
        
    def save_to_settings(self):
        """Renkleri ayarlara kaydet"""
        if not self.settings_manager:
            return
            
        # Renkleri topla
        colors = [btn.get_color() for btn in self.color_buttons]
        
        # Seçili index'i bul
        selected_index = 0
        for i, btn in enumerate(self.color_buttons):
            if btn.isChecked():
                selected_index = i
                break
                
        # Ayarlara kaydet
        self.settings_manager.set_palette_colors(colors)
        self.settings_manager.set_palette_selected_index(selected_index)
        self.settings_manager.save_settings()
        
    def add_new_color(self):
        """Yeni renk ekle"""
        if len(self.color_buttons) >= self.max_colors:
            return
            
        # Varsayılan renkler
        default_colors = [
            Qt.GlobalColor.red,
            Qt.GlobalColor.blue, 
            Qt.GlobalColor.green,
            Qt.GlobalColor.yellow,
            Qt.GlobalColor.cyan,
            Qt.GlobalColor.magenta
        ]
        
        # Henüz kullanılmayan rengi bul
        used_colors = [btn.get_color() for btn in self.color_buttons]
        new_color = Qt.GlobalColor.red
        
        for color in default_colors:
            if not any(QColor(color).name() == used_color.name() for used_color in used_colors):
                new_color = color
                break
        
        self.add_color_button(new_color)
        
        # İlk butonun silinebilirliğini güncelle
        if len(self.color_buttons) > 1 and not self.color_buttons[0].can_delete:
            self.color_buttons[0].can_delete = True
            self.color_buttons[0].setToolTip("Sol tık: rengi seç\nUzun basma: rengi değiştir\nSağ tık: sil")
        
    def on_color_selected(self, color):
        """Renk seçildiğinde"""
        sender = self.sender()
        
        # Diğer butonların seçimini kaldır
        for btn in self.color_buttons:
            if btn != sender:
                btn.setChecked(False)
                
        # Gönderen butonu seçili yap
        sender.setChecked(True)
        
        # Aktif rengi güncelle
        self.current_color = color
        self.colorSelected.emit(color)
        
        # Ayarlara kaydet (sadece yükleme sırasında değilse)
        if not self.loading_from_settings:
            self.save_to_settings()
        
    def on_color_changed(self, color):
        """Renk değiştirildiğinde"""
        sender = self.sender()
        if sender.isChecked():
            # Eğer değiştirilen renk şu an seçili ise, aktif rengi güncelle
            self.current_color = color
            self.colorSelected.emit(color)
            
        # Ayarlara kaydet (sadece yükleme sırasında değilse)
        if not self.loading_from_settings:
            self.save_to_settings()
            self.paletteChanged.emit()
            
    def get_current_color(self):
        """Şu anki seçili rengi al"""
        return self.current_color
        
    def set_current_color(self, color):
        """Aktif rengi ayarla"""
        self.current_color = QColor(color)
        
        # En yakın renk butonunu bul ve seç
        if self.color_buttons:
            min_distance = float('inf')
            closest_btn = self.color_buttons[0]
            
            for btn in self.color_buttons:
                btn_color = btn.get_color()
                # Basit renk mesafesi hesaplaması
                distance = (abs(btn_color.red() - color.red()) + 
                           abs(btn_color.green() - color.green()) + 
                           abs(btn_color.blue() - color.blue()))
                
                if distance < min_distance:
                    min_distance = distance
                    closest_btn = btn
                    
            # En yakın butonu seç
            for btn in self.color_buttons:
                btn.setChecked(btn == closest_btn)
                
            self.colorSelected.emit(self.current_color) 