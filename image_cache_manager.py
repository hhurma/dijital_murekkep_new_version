import os
import hashlib
import threading
from PyQt6.QtCore import QObject, pyqtSignal, QThread, QMutex
from PyQt6.QtGui import QPixmap
from concurrent.futures import ThreadPoolExecutor
import queue

class ImageCacheManager(QObject):
    """Threaded resim cache yöneticisi"""
    imageLoaded = pyqtSignal(str, QPixmap)  # hash, pixmap
    
    def __init__(self, cache_dir, max_workers=3):
        super().__init__()
        self.cache_dir = cache_dir
        self.cache = {}  # hash -> QPixmap
        self.loading_queue = queue.Queue()
        self.mutex = QMutex()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.is_shutdown = False
        
        # Cache directory oluştur
        os.makedirs(cache_dir, exist_ok=True)
        
    def get_image_hash(self, image_path):
        """Resim dosyası hash'ini hesapla"""
        try:
            hash_md5 = hashlib.md5()
            with open(image_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except:
            return None
            
    def get_cached_image(self, image_hash):
        """Cache'den resim al (thread-safe)"""
        self.mutex.lock()
        try:
            return self.cache.get(image_hash)
        finally:
            self.mutex.unlock()
            
    def cache_image(self, image_path, target_size=None):
        """Resmi async olarak cache'le"""
        if self.is_shutdown:
            return None
            
        image_hash = self.get_image_hash(image_path)
        if not image_hash:
            return None
            
        # Zaten cache'de varsa direkt döndür
        cached = self.get_cached_image(image_hash)
        if cached:
            return image_hash
            
        # Async olarak yükle
        future = self.executor.submit(self._load_image_worker, image_path, image_hash, target_size)
        return image_hash
        
    def _load_image_worker(self, image_path, image_hash, target_size):
        """Worker thread'de resim yükleme"""
        try:
            # Resmi yükle
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                return
                
            # Boyutlandır
            if target_size:
                from PyQt6.QtCore import Qt
                pixmap = pixmap.scaled(
                    target_size.x(), target_size.y(),
                    aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio,
                    transformMode=Qt.TransformationMode.SmoothTransformation
                )
            
            # Cache'e ekle (thread-safe)
            self.mutex.lock()
            try:
                self.cache[image_hash] = pixmap
            finally:
                self.mutex.unlock()
                
            # Sinyal gönder
            self.imageLoaded.emit(image_hash, pixmap)
            
        except Exception as e:
            print(f"Resim yükleme hatası: {e}")
            
    def preload_images(self, image_paths):
        """Birden fazla resmi önceden yükle"""
        for path in image_paths:
            self.cache_image(path)
            
    def clear_cache(self):
        """Cache'i temizle"""
        self.mutex.lock()
        try:
            self.cache.clear()
        finally:
            self.mutex.unlock()
            
    def shutdown(self):
        """Thread pool'u kapat"""
        self.is_shutdown = True
        self.executor.shutdown(wait=True)
        
    def get_cache_size(self):
        """Cache boyutunu döndür"""
        self.mutex.lock()
        try:
            return len(self.cache)
        finally:
            self.mutex.unlock() 