from PyQt6.QtWidgets import QSplashScreen, QApplication
from PyQt6.QtGui import QPixmap, QFont, QColor
from PyQt6.QtCore import Qt, QTimer
import os

class SplashScreen(QSplashScreen):
    """Uygulama açılış ekranı"""
    
    def __init__(self):
        super().__init__()
        self.setup_splash()
        
    def setup_splash(self):
        """Splash screen'i ayarla"""
        # Splash resmi yükle
        splash_path = os.path.join(os.path.dirname(__file__), "@splash.png")
        
        if os.path.exists(splash_path):
            pixmap = QPixmap(splash_path)
            # Resmi uygun boyuta ölçekle
            if not pixmap.isNull():
                # Maksimum 600x400 boyutunda tut
                if pixmap.width() > 600 or pixmap.height() > 400:
                    pixmap = pixmap.scaled(600, 400, Qt.AspectRatioMode.KeepAspectRatio, 
                                         Qt.TransformationMode.SmoothTransformation)
        else:
            # Eğer resim yoksa varsayılan splash oluştur
            pixmap = QPixmap(400, 300)
            pixmap.fill(Qt.GlobalColor.white)
            
        self.setPixmap(pixmap)
        
        # Splash screen özelliklerini ayarla
        self.setWindowFlags(Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Merkeze hizala
        self.show()
        
        # Font ayarla
        font = QFont()
        font.setFamily("Arial")
        font.setPointSize(16)
        font.setBold(True)
        self.setFont(font)
        
        # Yükleme mesajı göster (resme uygun navy blue renk)
        navy_color = QColor(35, 47, 94)  # Resimle uyumlu navy blue
        self.showMessage("Yükleniyor...", 
                        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter,
                        navy_color)
        
    def show_for_duration(self, duration_ms=2000):
        """Belirtilen süre boyunca splash screen göster"""
        self.show()
        
        # Timer ile otomatik kapanma
        self.timer = QTimer()
        self.timer.timeout.connect(self.close)
        self.timer.setSingleShot(True)
        self.timer.start(duration_ms)
        
        # Uygulama event'lerini işle
        QApplication.processEvents()
        
    def update_message(self, message):
        """Yükleme mesajını güncelle"""
        navy_color = QColor(35, 47, 94)  # Resimle uyumlu navy blue
        self.showMessage(message, 
                        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter,
                        navy_color)
        QApplication.processEvents()
        
    def finish_splash(self, main_window):
        """Splash screen'i kapat ve ana pencereyi göster"""
        if hasattr(self, 'timer'):
            self.timer.stop()
        self.finish(main_window)
        
def show_splash_screen():
    """Splash screen göster ve referansını döndür"""
    splash = SplashScreen()
    splash.show_for_duration(2000)  # 2 saniye
    return splash 