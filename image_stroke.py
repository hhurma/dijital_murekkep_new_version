import os
import hashlib
from PyQt6.QtGui import QPixmap, QPainter, QTransform
from PyQt6.QtCore import QPointF, QRectF
import shutil

class ImageStroke:
    """Resim stroke'u - canvas'a eklenen resimler için"""
    
    def __init__(self, image_path, position, size=None, rotation=0, opacity=1.0, cache_manager=None):
        self.stroke_type = "image"
        self.image_path = image_path
        self.position = QPointF(position)  # Sol üst köşe pozisyonu
        self.rotation = rotation  # Derece cinsinden
        self.opacity = opacity
        self.cache_manager = cache_manager
        self.is_loading = False
        self.render_pixmap = None  # Render için kullanılacak pixmap
        
        # Dosya hash'i (aynı resim kontrolü için)
        self.file_hash = self._calculate_file_hash()
        
        # Boyut ayarla (varsayılan olarak maksimum 300px genişlik/yükseklik)
        if size is None:
            self.size = self._calculate_default_size()
        else:
            self.size = size
            
        # Cache manager varsa async yükle, yoksa sync yükle
        if self.cache_manager:
            self._load_async()
        else:
            self._load_sync()
        
        # Cache'lenmiş dosya yolu
        self.cached_path = None
        
    def _load_sync(self):
        """Senkron resim yükleme (fallback)"""
        self.original_pixmap = QPixmap(self.image_path)
        if self.original_pixmap.isNull():
            raise ValueError(f"Resim yüklenemedi: {self.image_path}")
        self.render_pixmap = self._create_scaled_pixmap()
        
    def _load_async(self):
        """Asenkron resim yükleme"""
        # Cache'den kontrol et
        cached = self.cache_manager.get_cached_image(self.file_hash)
        if cached:
            self.render_pixmap = cached
            self.original_pixmap = cached
        else:
            # Placeholder pixmap oluştur
            self.render_pixmap = self._create_placeholder()
            self.is_loading = True
            # Async yükleme başlat
            self.cache_manager.imageLoaded.connect(self._on_image_loaded)
            self.cache_manager.cache_image(self.image_path, self.size)
            
    def _create_placeholder(self):
        """Yüklenirken gösterilecek placeholder"""
        from PyQt6.QtGui import QPainter, QBrush, QColor, QPen
        from PyQt6.QtCore import Qt
        
        placeholder = QPixmap(int(self.size.x()), int(self.size.y()))
        placeholder.fill(QColor(240, 240, 240))
        
        painter = QPainter(placeholder)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor(180, 180, 180), 2))
        painter.setBrush(QBrush(QColor(200, 200, 200)))
        
        # Basit loading göstergesi
        margin = 20
        painter.drawRect(margin, margin, placeholder.width() - 2*margin, placeholder.height() - 2*margin)
        painter.drawText(placeholder.rect(), Qt.AlignmentFlag.AlignCenter, "Yükleniyor...")
        painter.end()
        
        return placeholder
        
    def _on_image_loaded(self, image_hash, pixmap):
        """Resim yüklendiğinde çağrılır"""
        if image_hash == self.file_hash:
            self.render_pixmap = pixmap
            self.original_pixmap = pixmap
            self.is_loading = False
            # Disconnect to avoid memory leaks
            self.cache_manager.imageLoaded.disconnect(self._on_image_loaded)
        
    def _calculate_default_size(self):
        """Varsayılan boyutu hesapla (en fazla 250px - %200 zoom için optimize)"""
        # Sync loading için pixmap kontrolü
        if not hasattr(self, 'original_pixmap') or not self.original_pixmap:
            temp_pixmap = QPixmap(self.image_path)
            if not temp_pixmap.isNull():
                original_size = temp_pixmap.size()
            else:
                return QPointF(250, 250)  # Fallback
        else:
            original_size = self.original_pixmap.size()
            
        max_size = 250  # %200 zoom için daha küçük boyut
        
        if original_size.width() > max_size or original_size.height() > max_size:
            # Oranı koruyarak küçült
            if original_size.width() > original_size.height():
                # Genişlik daha büyük
                scale_factor = max_size / original_size.width()
            else:
                # Yükseklik daha büyük
                scale_factor = max_size / original_size.height()
            
            new_width = int(original_size.width() * scale_factor)
            new_height = int(original_size.height() * scale_factor)
            return QPointF(new_width, new_height)
        else:
            return QPointF(original_size.width(), original_size.height())
    
    def _create_scaled_pixmap(self):
        """Ölçeklenmiş pixmap oluştur"""
        from PyQt6.QtCore import Qt
        return self.original_pixmap.scaled(
            int(self.size.x()), int(self.size.y()),
            aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio,
            transformMode=Qt.TransformationMode.SmoothTransformation
        )
    
    def _calculate_file_hash(self):
        """Dosya hash'ini hesapla"""
        hash_md5 = hashlib.md5()
        with open(self.image_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def get_bounds(self):
        """Resmin sınır dikdörtgenini döndür"""
        return QRectF(self.position.x(), self.position.y(), self.size.x(), self.size.y())
    
    def set_position(self, position):
        """Pozisyonu ayarla"""
        self.position = QPointF(position)
    
    def set_size(self, size):
        """Boyutu ayarla ve pixmap'i yeniden oluştur"""
        self.size = QPointF(size)
        self.scaled_pixmap = self._create_scaled_pixmap()
    
    def set_rotation(self, rotation):
        """Dönüş açısını ayarla"""
        self.rotation = rotation
    
    def set_opacity(self, opacity):
        """Opacity'yi ayarla"""
        self.opacity = max(0.0, min(1.0, opacity))
    
    def contains_point(self, point):
        """Nokta resmin içinde mi kontrol et"""
        bounds = self.get_bounds()
        return bounds.contains(point)
    
    def render(self, painter, transform=None):
        """Resmi çiz"""
        painter.save()
        
        # Optimize render ayarları (performans için)
        if not self.is_loading:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        
        # Opacity ayarla
        painter.setOpacity(self.opacity)
        
        # Transform uygula
        if transform:
            painter.setTransform(transform, True)
        
        # Pozisyon ve dönüş
        painter.translate(self.position)
        if self.rotation != 0:
            # Resmin merkezi etrafında döndür
            center = QPointF(self.size.x() / 2, self.size.y() / 2)
            painter.translate(center)
            painter.rotate(self.rotation)
            painter.translate(-center)
        
        # Render pixmap'i çiz (async yüklenmiş veya placeholder)
        if self.render_pixmap and not self.render_pixmap.isNull():
            target_rect = QRectF(0, 0, self.size.x(), self.size.y())
            source_rect = QRectF(self.render_pixmap.rect())
            painter.drawPixmap(target_rect, self.render_pixmap, source_rect)
        
        painter.restore()
    
    def copy(self):
        """Kopyasını oluştur"""
        return ImageStroke(
            self.image_path,
            self.position,
            self.size,
            self.rotation,
            self.opacity
        )
    
    def __deepcopy__(self, memo):
        """Deep copy desteği"""
        return ImageStroke(
            self.image_path,
            QPointF(self.position),
            QPointF(self.size),
            self.rotation,
            self.opacity
        )
    
    def cache_image(self, cache_dir):
        """Resmi cache klasörüne kopyala"""
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        
        # Dosya uzantısını al
        _, ext = os.path.splitext(self.image_path)
        
        # Cache dosya yolu
        cached_filename = f"{self.file_hash}{ext}"
        self.cached_path = os.path.join(cache_dir, cached_filename)
        
        # Eğer cache'de yoksa kopyala
        if not os.path.exists(self.cached_path):
            shutil.copy2(self.image_path, self.cached_path)
        
        # Orijinal path yerine cache path kullan
        self.image_path = self.cached_path
        
        return self.cached_path
    
    def to_dict(self):
        """Seri hale getir"""
        return {
            'stroke_type': 'image',
            'image_path': self.image_path,
            'position': [self.position.x(), self.position.y()],
            'size': [self.size.x(), self.size.y()],
            'rotation': self.rotation,
            'opacity': self.opacity,
            'file_hash': self.file_hash
        }
    
    @classmethod
    def from_dict(cls, data):
        """Seri halinden oluştur"""
        position = QPointF(data['position'][0], data['position'][1])
        size = QPointF(data['size'][0], data['size'][1])
        
        image_stroke = cls(
            data['image_path'],
            position,
            size,
            data.get('rotation', 0),
            data.get('opacity', 1.0)
        )
        
        return image_stroke
    
    def get_center(self):
        """Resmin merkez noktasını döndür"""
        bounds = self.get_bounds()
        return QPointF(bounds.center()) 