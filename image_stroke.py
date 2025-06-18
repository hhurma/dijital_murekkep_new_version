import os
import hashlib
from PyQt6.QtGui import QPixmap, QPainter, QTransform, QColor
from PyQt6.QtCore import QPointF, QRectF, QRect, QSize, Qt
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
        self.group_id = None  # Grup ID'si
        
        # Kenarlık özellikleri
        self.has_border = False
        self.border_color = QColor(0, 0, 0)  # Siyah
        self.border_width = 2
        self.border_style = Qt.PenStyle.SolidLine
        
        # Gölge özellikleri
        self.has_shadow = False
        self.shadow_color = QColor(0, 0, 0, 128)  # Yarı şeffaf siyah
        self.shadow_blur = 5
        self.shadow_offset_x = 3
        self.shadow_offset_y = 3
        self.shadow_size = 0  # Gölge boyutu (piksel cinsinden genişletme)
        self.inner_shadow = False  # İç gölge (true) veya dış gölge (false)
        self.shadow_quality = "medium"  # "low", "medium", "high" - performans ayarı
        self.shadow_opacity = 1.0  # Gölge şeffaflığı (0.0-1.0)
        
        # Filtre özellikleri
        self.filter_type = "none"  # "none", "grayscale", "sepia", "invert", "blur"
        self.filter_intensity = 1.0  # 0.0-1.0 arası
        
        # Şeffaflık ve bulanıklık
        self.transparency = 1.0  # Resim için ekstra şeffaflık (opacity'ye ek)
        self.blur_radius = 0  # Bulanıklık yarıçapı (0 = blur yok)
        self.corner_radius = 0  # Kenar yuvarlama yarıçapı (0 = keskin kenarlar)
        
        # Dosya hash'i (aynı resim kontrolü için)
        self.file_hash = self._calculate_file_hash()
        
        # Boyut ayarla (varsayılan olarak maksimum 300px genişlik/yükseklik)
        if size is None:
            self.size = self._calculate_default_size()
        else:
            self.size = size
            
        # Cache manager varsa async yükle, yoksa sync yükle
        if self.cache_manager:
            try:
                self._load_async()
            except Exception as e:
                print(f"Async yükleme hatası, sync'e geçiliyor: {e}")
                self._load_sync()
        else:
            self._load_sync()
        
        # Cache'lenmiş dosya yolu
        self.cached_path = None
        
    def _load_sync(self):
        """Senkron resim yükleme (fallback)"""
        try:
            self.original_pixmap = QPixmap(self.image_path)
            if self.original_pixmap.isNull():
                print(f"Resim yüklenemedi: {self.image_path}")
                self.render_pixmap = self._create_placeholder()
                return
            self.render_pixmap = self._create_scaled_pixmap()
        except Exception as e:
            print(f"Resim yükleme hatası: {e}")
            self.render_pixmap = self._create_placeholder()
        
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
        
        # Size değerlerini güvenli şekilde int'e çevir
        width = max(1, int(round(self.size.x())))
        height = max(1, int(round(self.size.y())))
        
        placeholder = QPixmap(width, height)
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
        if hasattr(self, 'original_pixmap') and self.original_pixmap and not self.original_pixmap.isNull():
            # Size değerlerini güvenli şekilde int'e çevir
            width = max(1, int(round(self.size.x())))
            height = max(1, int(round(self.size.y())))
            return self.original_pixmap.scaled(
                width, height,
                aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio,
                transformMode=Qt.TransformationMode.SmoothTransformation
            )
        return None
    
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
        self.render_pixmap = self._create_scaled_pixmap()
    
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
        
        # Opacity ve transparency ayarla
        total_opacity = self.opacity * self.transparency
        painter.setOpacity(total_opacity)
        
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
        
        target_rect = QRectF(0, 0, self.size.x(), self.size.y())
        
        # Dış gölge çiz (resmin altında)
        if self.has_shadow and not self.inner_shadow and self.render_pixmap and not self.render_pixmap.isNull():
            self._render_outer_shadow(painter, total_opacity)
        
        # Ana resmi çiz (filtre ve blur ile)
        if self.render_pixmap and not self.render_pixmap.isNull():
            # Filtreleri uygula
            processed_pixmap = self._apply_all_effects(self.render_pixmap)
            source_rect = QRectF(processed_pixmap.rect())
            
            # İç gölge varsa, önce resmi çiz sonra gölgeyi üstüne ekle
            painter.drawPixmap(target_rect, processed_pixmap, source_rect)
            
            # İç gölge çiz (resmin üstünde, ama içinde)
            if self.has_shadow and self.inner_shadow:
                self._render_inner_shadow(painter, target_rect, total_opacity)
        
        # Kenarlık çiz (resmin üstünde)
        if self.has_border:
            painter.save()
            
            # Kenarlık pen'i ayarla
            from PyQt6.QtGui import QPen
            pen = QPen(self.border_color, self.border_width, self.border_style)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            
            # Kenarlığı çiz
            painter.drawRect(target_rect)
            
            painter.restore()
        
        painter.restore()
    
    def _render_outer_shadow(self, painter, total_opacity):
        """Dış gölgeyi render et"""
        painter.save()
        
        # Gölge rengi ve opacity ayarla - tam opak için shadow_color alpha'sını override et
        base_opacity = 1.0 if self.shadow_opacity == 1.0 else self.shadow_color.alphaF()
        shadow_opacity = base_opacity * total_opacity * self.shadow_opacity
        painter.setOpacity(shadow_opacity)
        
        # Gölge pozisyon ve boyut hesapla
        shadow_offset_x = self.shadow_offset_x
        shadow_offset_y = self.shadow_offset_y
        shadow_width = self.size.x()
        shadow_height = self.size.y()
        
        # Gölge boyutu varsa offset ve boyutları ayarla - 2x güçlendir
        if self.shadow_size > 0:
            enhanced_size = self.shadow_size * 2
            shadow_offset_x -= enhanced_size
            shadow_offset_y -= enhanced_size
            shadow_width += (2 * enhanced_size)
            shadow_height += (2 * enhanced_size)
        
        # Eğer offset ve blur her ikisi de 0 ise gölgeyi biraz aşağı kaydır
        if self.shadow_offset_x == 0 and self.shadow_offset_y == 0 and self.shadow_blur <= 1:
            shadow_offset_y += 2  # Minimal görünürlük için
        
        shadow_rect = QRectF(
            shadow_offset_x, 
            shadow_offset_y, 
            shadow_width, 
            shadow_height
        )
        
        # Gölge pixmap'i oluştur (boyut ve blur ile)
        shadow_pixmap = self._create_shadow_pixmap(self.render_pixmap)
        source_rect = QRectF(shadow_pixmap.rect())
        painter.drawPixmap(shadow_rect, shadow_pixmap, source_rect)
        
        painter.restore()
    
    def _render_inner_shadow(self, painter, target_rect, total_opacity):
        """İç gölgeyi render et"""
        painter.save()
        
        # İç gölge pixmap'i oluştur
        inner_shadow_pixmap = self._create_inner_shadow_pixmap(self.render_pixmap)
        
        if inner_shadow_pixmap and not inner_shadow_pixmap.isNull():
            # Gölge opacity'yi ayarla - tam opak için shadow_color alpha'sını override et
            color_alpha = 1.0 if self.shadow_opacity == 1.0 else self.shadow_color.alphaF()
            base_opacity = 1.0 if (self.shadow_offset_x == 0 and self.shadow_offset_y == 0) else 0.8
            shadow_opacity = color_alpha * total_opacity * base_opacity * self.shadow_opacity
            painter.setOpacity(shadow_opacity)
            
            # Normal composition mode kullan
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            
            # İç gölge için offset (kenarlardan içe doğru)
            shadow_rect = QRectF(
                self.shadow_offset_x,
                self.shadow_offset_y,
                target_rect.width(),
                target_rect.height()
            )
            
            source_rect = QRectF(inner_shadow_pixmap.rect())
            painter.drawPixmap(shadow_rect, inner_shadow_pixmap, source_rect)
        
        painter.restore()
    
    def _create_tinted_pixmap(self, pixmap, color):
        """Belirtilen renkte renklendirilmiş pixmap oluştur (gölge için)"""
        tinted = QPixmap(pixmap.size())
        tinted.fill(color)
        tinted_painter = QPainter(tinted)
        tinted_painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
        tinted_painter.drawPixmap(0, 0, pixmap)
        tinted_painter.end()
        return tinted
    
    def _create_shadow_pixmap(self, pixmap):
        """Gölge pixmap'i oluştur (boyut, blur ve renk ile)"""
        shadow_pixmap = pixmap
        
        # Önce yuvarlak kenar uygula (gölge için)
        if self.corner_radius > 0:
            shadow_pixmap = self._apply_rounded_corners(shadow_pixmap)
        
        # Gölge boyutu varsa pixmap'i genişlet - 2x güçlendir
        if self.shadow_size > 0:
            enhanced_size = self.shadow_size * 2
            shadow_pixmap = self._expand_pixmap(shadow_pixmap, enhanced_size)
        
        # Blur uygula (performans ayarına göre)
        if self.shadow_blur > 0:
            blur_radius = self._get_adjusted_blur_radius()
            shadow_pixmap = self._apply_blur(shadow_pixmap, blur_radius)
        
        # Renklendirme uygula
        tinted = self._create_tinted_pixmap(shadow_pixmap, self.shadow_color)
        return tinted
    
    def _create_inner_shadow_pixmap(self, pixmap):
        """İç gölge pixmap'i oluştur - dış kenardan içe doğru gölge"""
        if not pixmap or pixmap.isNull():
            return None
            
        # Önce yuvarlak kenar uygula (eğer varsa)
        working_pixmap = pixmap
        if self.corner_radius > 0:
            working_pixmap = self._apply_rounded_corners(pixmap)
            
        # 1. Genişletilmiş boyutta çalış (blur için) - güçlendirilmiş
        # Offset 0 olduğunda bile gölgenin görünmesi için minimum margin ekle
        min_margin = 25 if (self.shadow_offset_x == 0 and self.shadow_offset_y == 0) else 15
        blur_margin = max(min_margin, int(self.shadow_blur * 5), (self.shadow_size * 2) + 20)
        expanded_size = QSize(
            working_pixmap.width() + blur_margin * 2,
            working_pixmap.height() + blur_margin * 2
        )
        
        # 2. Orijinal resmin tersini oluştur (kenar bölgeler)
        mask = QPixmap(expanded_size)
        mask.fill(Qt.GlobalColor.black)  # Tamamen siyah başla
        
        mask_painter = QPainter(mask)
        mask_painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        # Merkeze yuvarlak resmi koy ve temizle (orijinal kısım şeffaf olur)
        mask_painter.drawPixmap(blur_margin, blur_margin, working_pixmap)
        mask_painter.end()
        
        # 3. Maskeyi blur'la (kenar geçişi için)
        if self.shadow_blur > 0:
            blur_radius = self._get_adjusted_blur_radius()
            blurred_mask = self._apply_blur(mask, blur_radius)
        else:
            blurred_mask = mask
            
        # 4. İç gölge oluştur - sadece orijinal resmin içinde kalan kısmı al
        inner_shadow = QPixmap(working_pixmap.size())
        inner_shadow.fill(Qt.GlobalColor.transparent)
        
        inner_painter = QPainter(inner_shadow)
        
        # Blur'lanmış maskeyi çiz (merkeze hizala)
        inner_painter.drawPixmap(-blur_margin, -blur_margin, blurred_mask)
        
        # Sadece orijinal resmin içinde kalan kısmı bırak
        inner_painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
        inner_painter.drawPixmap(0, 0, working_pixmap)
        
        inner_painter.end()
        
        # 5. Gölge rengini uygula
        tinted_shadow = self._create_tinted_pixmap(inner_shadow, self.shadow_color)
        
        return tinted_shadow
    
    def _expand_pixmap(self, pixmap, expand_size):
        """Pixmap'i belirtilen boyutta genişletir (gölge boyutu için)"""
        if expand_size <= 0:
            return pixmap
            
        # Yeni boyutları hesapla
        new_width = pixmap.width() + (2 * expand_size)
        new_height = pixmap.height() + (2 * expand_size)
        
        # Yeni pixmap oluştur
        expanded = QPixmap(new_width, new_height)
        expanded.fill(Qt.GlobalColor.transparent)
        
        # Painter ile orijinal pixmap'i merkeze çiz
        painter = QPainter(expanded)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawPixmap(expand_size, expand_size, pixmap)
        painter.end()
        
        return expanded
    
    def _get_adjusted_blur_radius(self):
        """Performans ayarına göre blur yarıçapını ayarla - güçlendirilmiş"""
        base_blur = self.shadow_blur * 3  # 3x güçlendir
        
        if self.shadow_quality == "low":
            return max(3, int(base_blur * 0.5))
        elif self.shadow_quality == "high":
            return int(base_blur * 2.0)
        else:  # medium
            return int(base_blur * 1.2)
    
    def _apply_blur(self, pixmap, radius):
        """Pixmap'e blur efekti uygula"""
        if radius <= 0:
            return pixmap
            
        from PyQt6.QtWidgets import QGraphicsScene, QGraphicsPixmapItem, QGraphicsBlurEffect
        from PyQt6.QtGui import QPixmap
        
        # QGraphicsScene kullanarak blur efekti uygula
        scene = QGraphicsScene()
        item = QGraphicsPixmapItem(pixmap)
        scene.addItem(item)
        
        # Blur efekti oluştur
        blur_effect = QGraphicsBlurEffect()
        blur_effect.setBlurRadius(radius)
        item.setGraphicsEffect(blur_effect)
        
        # Yeni pixmap oluştur
        blurred_pixmap = QPixmap(pixmap.size())
        blurred_pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(blurred_pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        scene.render(painter)
        painter.end()
        
        return blurred_pixmap
    
    def _apply_all_effects(self, pixmap):
        """Tüm efektleri uygula (blur + filtreler + yuvarlak kenarlar)"""
        processed_pixmap = pixmap
        
        # Önce blur uygula
        if self.blur_radius > 0:
            processed_pixmap = self._apply_blur(processed_pixmap, self.blur_radius)
        
        # Sonra filtreleri uygula
        processed_pixmap = self._apply_filter(processed_pixmap)
        
        # Son olarak yuvarlak kenarları uygula
        if self.corner_radius > 0:
            processed_pixmap = self._apply_rounded_corners(processed_pixmap)
        
        return processed_pixmap
    
    def _apply_rounded_corners(self, pixmap):
        """Pixmap'e yuvarlak kenarlar uygula"""
        if not pixmap or pixmap.isNull() or self.corner_radius <= 0:
            return pixmap
            
        # Yeni pixmap oluştur
        rounded = QPixmap(pixmap.size())
        rounded.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Yuvarlak maske oluştur
        from PyQt6.QtGui import QPainterPath
        path = QPainterPath()
        rect = QRectF(0, 0, pixmap.width(), pixmap.height())
        path.addRoundedRect(rect, self.corner_radius, self.corner_radius)
        
        # Maskeyi uygula
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()
        
        return rounded
    
    def _apply_filter(self, pixmap):
        """Pixmap'e filtre uygula"""
        if self.filter_type == "none" or self.filter_intensity <= 0.0:
            return pixmap
            
        # QImage'e çevir (pixel manipülasyonu için)
        image = pixmap.toImage()
        if image.isNull():
            return pixmap
            
        # RGBA format'a çevir
        image = image.convertToFormat(image.Format.Format_RGBA8888)
        
        width = image.width()
        height = image.height()
        
        for y in range(height):
            for x in range(width):
                pixel = image.pixelColor(x, y)
                r, g, b, a = pixel.red(), pixel.green(), pixel.blue(), pixel.alpha()
                
                if self.filter_type == "grayscale":
                    # Gri tonlama: luminance hesabı
                    gray = int(0.299 * r + 0.587 * g + 0.114 * b)
                    new_r = int(r + (gray - r) * self.filter_intensity)
                    new_g = int(g + (gray - g) * self.filter_intensity)
                    new_b = int(b + (gray - b) * self.filter_intensity)
                    
                elif self.filter_type == "sepia":
                    # Sepia efekti
                    sepia_r = min(255, int(r * 0.393 + g * 0.769 + b * 0.189))
                    sepia_g = min(255, int(r * 0.349 + g * 0.686 + b * 0.168))
                    sepia_b = min(255, int(r * 0.272 + g * 0.534 + b * 0.131))
                    new_r = int(r + (sepia_r - r) * self.filter_intensity)
                    new_g = int(g + (sepia_g - g) * self.filter_intensity)
                    new_b = int(b + (sepia_b - b) * self.filter_intensity)
                    
                elif self.filter_type == "invert":
                    # Renk tersçevirme
                    inv_r = 255 - r
                    inv_g = 255 - g
                    inv_b = 255 - b
                    new_r = int(r + (inv_r - r) * self.filter_intensity)
                    new_g = int(g + (inv_g - g) * self.filter_intensity)
                    new_b = int(b + (inv_b - b) * self.filter_intensity)
                    
                else:
                    new_r, new_g, new_b = r, g, b
                
                # Yeni rengi ayarla
                new_color = QColor(
                    max(0, min(255, new_r)),
                    max(0, min(255, new_g)), 
                    max(0, min(255, new_b)),
                    a
                )
                image.setPixelColor(x, y, new_color)
        
        # QPixmap'e geri çevir
        return QPixmap.fromImage(image)
    
    def copy(self):
        """Kopyasını oluştur"""
        new_stroke = ImageStroke(
            self.image_path,
            self.position,
            self.size,
            self.rotation,
            self.opacity
        )
        new_stroke.group_id = self.group_id
        new_stroke.has_border = self.has_border
        new_stroke.border_color = QColor(self.border_color)
        new_stroke.border_width = self.border_width
        new_stroke.border_style = self.border_style
        new_stroke.has_shadow = self.has_shadow
        new_stroke.shadow_color = QColor(self.shadow_color)
        new_stroke.shadow_blur = self.shadow_blur
        new_stroke.shadow_offset_x = self.shadow_offset_x
        new_stroke.shadow_offset_y = self.shadow_offset_y
        new_stroke.shadow_size = self.shadow_size
        new_stroke.inner_shadow = self.inner_shadow
        new_stroke.shadow_quality = self.shadow_quality
        new_stroke.shadow_opacity = self.shadow_opacity
        new_stroke.filter_type = self.filter_type
        new_stroke.filter_intensity = self.filter_intensity
        new_stroke.transparency = self.transparency
        new_stroke.blur_radius = self.blur_radius
        new_stroke.corner_radius = self.corner_radius
        return new_stroke
    
    def __deepcopy__(self, memo):
        """Deep copy desteği"""
        new_stroke = ImageStroke(
            self.image_path,
            QPointF(self.position),
            QPointF(self.size),
            self.rotation,
            self.opacity
        )
        new_stroke.group_id = self.group_id
        new_stroke.has_border = self.has_border
        new_stroke.border_color = QColor(self.border_color)
        new_stroke.border_width = self.border_width
        new_stroke.border_style = self.border_style
        new_stroke.has_shadow = self.has_shadow
        new_stroke.shadow_color = QColor(self.shadow_color)
        new_stroke.shadow_blur = self.shadow_blur
        new_stroke.shadow_offset_x = self.shadow_offset_x
        new_stroke.shadow_offset_y = self.shadow_offset_y
        new_stroke.shadow_size = self.shadow_size
        new_stroke.inner_shadow = self.inner_shadow
        new_stroke.shadow_quality = self.shadow_quality
        new_stroke.shadow_opacity = self.shadow_opacity
        new_stroke.filter_type = self.filter_type
        new_stroke.filter_intensity = self.filter_intensity
        new_stroke.transparency = self.transparency
        new_stroke.blur_radius = self.blur_radius
        new_stroke.corner_radius = self.corner_radius
        return new_stroke
    
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
            'file_hash': self.file_hash,
            'group_id': self.group_id,
            'has_border': self.has_border,
            'border_color': self.border_color.name(),
            'border_width': self.border_width,
            'border_style': int(self.border_style.value),
            'has_shadow': self.has_shadow,
            'shadow_color': self.shadow_color.name(),
            'shadow_blur': self.shadow_blur,
            'shadow_offset_x': self.shadow_offset_x,
            'shadow_offset_y': self.shadow_offset_y,
            'shadow_size': self.shadow_size,
            'inner_shadow': self.inner_shadow,
            'shadow_quality': self.shadow_quality,
            'shadow_opacity': self.shadow_opacity,
            'filter_type': self.filter_type,
            'filter_intensity': self.filter_intensity,
            'transparency': self.transparency,
            'blur_radius': self.blur_radius,
            'corner_radius': self.corner_radius
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
        
        image_stroke.group_id = data.get('group_id', None)
        
        # Kenarlık özellikleri
        image_stroke.has_border = data.get('has_border', False)
        image_stroke.border_color = QColor(data.get('border_color', '#000000'))
        image_stroke.border_width = data.get('border_width', 2)
        image_stroke.border_style = Qt.PenStyle(data.get('border_style', Qt.PenStyle.SolidLine))
        
        # Gölge özellikleri  
        image_stroke.has_shadow = data.get('has_shadow', False)
        image_stroke.shadow_color = QColor(data.get('shadow_color', '#80000000'))
        image_stroke.shadow_blur = data.get('shadow_blur', 5)
        image_stroke.shadow_offset_x = data.get('shadow_offset_x', 3)
        image_stroke.shadow_offset_y = data.get('shadow_offset_y', 3)
        image_stroke.shadow_size = data.get('shadow_size', 0)
        image_stroke.inner_shadow = data.get('inner_shadow', False)
        image_stroke.shadow_quality = data.get('shadow_quality', 'medium')
        image_stroke.shadow_opacity = data.get('shadow_opacity', 1.0)
        
        # Filtre özellikleri
        image_stroke.filter_type = data.get('filter_type', 'none')
        image_stroke.filter_intensity = data.get('filter_intensity', 1.0)
        
        # Şeffaflık ve bulanıklık
        image_stroke.transparency = data.get('transparency', 1.0)
        image_stroke.blur_radius = data.get('blur_radius', 0)
        image_stroke.corner_radius = data.get('corner_radius', 0)
        
        return image_stroke
    
    def get_center(self):
        """Resmin merkez noktasını döndür"""
        bounds = self.get_bounds()
        return QPointF(bounds.center()) 