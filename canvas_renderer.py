from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QImage
from PyQt6.QtCore import Qt, QRectF, QPointF

class CanvasRenderer:
    """DrawingWidget için render işlemlerini yöneten sınıf"""
    
    def __init__(self, drawing_widget):
        self.drawing_widget = drawing_widget
        
    def paint_event(self, event):
        """Ana paintEvent metodunu işle"""
        painter = QPainter(self.drawing_widget)
        
        # Zoom manager'dan güncel zoom ve pan değerlerini al
        current_zoom = self.drawing_widget.zoom_level
        current_offset = self.drawing_widget.zoom_offset
        
        if hasattr(self.drawing_widget, 'zoom_manager'):
            current_zoom = self.drawing_widget.zoom_manager.get_zoom_level()
            current_offset = self.drawing_widget.zoom_manager.get_pan_offset()
        
        # Zoom ve pan transformasyonu uygula
        painter.scale(current_zoom, current_zoom)
        painter.translate(current_offset)
        
        # Arka planı çiz
        self.draw_background(painter)

        # Visible rect hesapla (performans için)
        visible_rect = event.rect()
        transform = painter.transform()
        inverse_transform = transform.inverted()[0]
        scene_rect = inverse_transform.mapRect(QRectF(visible_rect))
        
        # Akıllı render optimizasyonu
        total_strokes = self.drawing_widget.layer_manager.count_visible_strokes()
        use_culling = total_strokes > 100  # Moderate threshold - viewport culling
        use_lod = total_strokes > 50  # Level of Detail optimization
        
        # LOD hesaplama - zoom seviyesine göre
        zoom_level = current_zoom
        high_detail = zoom_level > 1.0  # Yakın zoom - full detail
        medium_detail = zoom_level > 0.5  # Orta zoom - reduced detail  
        low_detail = zoom_level <= 0.5  # Uzak zoom - minimal detail
        
        # Tüm tamamlanmış stroke'ları çiz
        for layer in self.drawing_widget.layer_manager.iter_layers():
            if not layer['visible']:
                continue
            for stroke_data in layer['strokes']:
                # Viewport culling kontrolü
                if use_culling:
                    try:
                        if not self.stroke_intersects_scene(stroke_data, scene_rect):
                            continue  # Görünmeyen stroke'ları atla
                    except:
                        pass  # Hata durumunda stroke'u çiz

                # Image stroke kontrolü
                if hasattr(stroke_data, 'stroke_type') and stroke_data.stroke_type == 'image':
                    # Resim stroke'ları için conditional antialiasing
                    if not stroke_data.is_loading:
                        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
                        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
                    stroke_data.render(painter)
                    continue

                # Güvenlik kontrolü - eski stroke'lar için
                if 'type' not in stroke_data:
                    continue

                # LOD bazlı rendering ayarları
                if use_lod and low_detail:
                    # Uzak zoom - minimal antialiasing, basit çizim
                    painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
                    self.draw_stroke_simple(painter, stroke_data)
                elif use_lod and medium_detail:
                    # Orta zoom - orta kalite
                    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
                    self.draw_stroke_medium(painter, stroke_data)
                else:
                    # Yakın zoom veya LOD yok - full kalite
                    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
                    self.draw_stroke_full(painter, stroke_data)

        # Seçim vurgusunu çiz
        self.drawing_widget.selection_tool.draw_selected_stroke_highlight(painter, self.drawing_widget.strokes)
        
        # Seçim dikdörtgenini çiz
        self.drawing_widget.selection_tool.draw_selection(painter)
        
        # Döndürme tutamaklarını çiz (döndürme aracı aktifse)
        if self.drawing_widget.active_tool == "rotate":
            self.drawing_widget.rotate_tool.draw_rotation_handles(painter, self.drawing_widget.strokes, self.drawing_widget.selection_tool.selected_strokes)
            
        # Boyutlandırma tutamaklarını çiz (boyutlandırma aracı aktifse)
        if self.drawing_widget.active_tool == "scale":
            self.drawing_widget.scale_tool.draw_scale_handles(painter, self.drawing_widget.strokes, self.drawing_widget.selection_tool.selected_strokes)

        # Aktif çizimi çiz
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        if self.drawing_widget.active_tool == "bspline":
            self.drawing_widget.bspline_tool.draw_current_stroke(painter)
        elif self.drawing_widget.active_tool == "freehand":
            self.drawing_widget.freehand_tool.draw_current_stroke(painter)
        elif self.drawing_widget.active_tool == "line":
            self.drawing_widget.line_tool.draw_current_stroke(painter)
        elif self.drawing_widget.active_tool == "rectangle":
            self.drawing_widget.rectangle_tool.draw_current_stroke(painter)
        elif self.drawing_widget.active_tool == "circle":
            self.drawing_widget.circle_tool.draw_current_stroke(painter)
            
    def stroke_intersects_scene(self, stroke_data, scene_rect):
        """Gelişmiş stroke-viewport intersection kontrolü"""
        try:
            # Resim stroke'ları için
            if hasattr(stroke_data, 'stroke_type') and stroke_data.stroke_type == 'image':
                stroke_rect = QRectF(stroke_data.position.x(), stroke_data.position.y(), 
                                   stroke_data.size.x(), stroke_data.size.y())
                return scene_rect.intersects(stroke_rect)
            
            # Normal stroke'lar için optimized bounds check
            if 'points' in stroke_data and stroke_data['points']:
                points = stroke_data['points']
                if not points:
                    return True
                
                # İlk ve son nokta ile hızlı pre-check
                first_point = points[0]
                last_point = points[-1]
                width = stroke_data.get('width', 2) + 5  # Biraz margin
                
                # Bounding box hesapla (vectorized)
                if len(points) == 1:
                    min_x = max_x = first_point.x()
                    min_y = max_y = first_point.y()
                elif len(points) == 2:
                    min_x = min(first_point.x(), last_point.x())
                    max_x = max(first_point.x(), last_point.x())
                    min_y = min(first_point.y(), last_point.y())
                    max_y = max(first_point.y(), last_point.y())
                else:
                    # Çok nokta varsa sampling yap (performans)
                    sample_points = points[::max(1, len(points)//10)]  # Her 10'da bir
                    x_coords = [p.x() for p in sample_points]
                    y_coords = [p.y() for p in sample_points]
                    min_x, max_x = min(x_coords), max(x_coords)
                    min_y, max_y = min(y_coords), max(y_coords)
                
                # Margin ile stroke rect
                stroke_rect = QRectF(min_x - width, min_y - width, 
                                   max_x - min_x + 2*width, max_y - min_y + 2*width)
                
                return scene_rect.intersects(stroke_rect)
                
            # Diğer stroke tipleri için
            elif stroke_data.get('type') == 'line':
                start = stroke_data['start_point']
                end = stroke_data['end_point']
                width = stroke_data.get('width', 2) + 5
                min_x = min(start[0], end[0]) - width
                max_x = max(start[0], end[0]) + width
                min_y = min(start[1], end[1]) - width
                max_y = max(start[1], end[1]) + width
                stroke_rect = QRectF(min_x, min_y, max_x - min_x, max_y - min_y)
                return scene_rect.intersects(stroke_rect)
                
            elif stroke_data.get('type') == 'rectangle':
                if 'corners' in stroke_data:
                    corners = stroke_data['corners']
                    x_coords = [c[0] for c in corners]
                    y_coords = [c[1] for c in corners]
                else:
                    tl, br = stroke_data['top_left'], stroke_data['bottom_right']
                    x_coords = [tl[0], br[0]]
                    y_coords = [tl[1], br[1]]
                
                width = stroke_data.get('width', 2) + 5
                min_x, max_x = min(x_coords) - width, max(x_coords) + width
                min_y, max_y = min(y_coords) - width, max(y_coords) + width
                stroke_rect = QRectF(min_x, min_y, max_x - min_x, max_y - min_y)
                return scene_rect.intersects(stroke_rect)
                
            elif stroke_data.get('type') == 'circle':
                center = stroke_data['center']
                radius = stroke_data['radius'] + stroke_data.get('width', 2) + 5
                stroke_rect = QRectF(center[0] - radius, center[1] - radius, 
                                   2 * radius, 2 * radius)
                return scene_rect.intersects(stroke_rect)
                
            return True  # Bilinmeyen tip - güvenli taraf
        except:
            return True  # Hata durumunda çiz
            
    def draw_background(self, painter):
        """Arka planı çiz"""
        # Arka plan rengini ayarla
        bg_color = QColor(self.drawing_widget.background_settings['background_color'])
        painter.fillRect(self.drawing_widget.rect(), QBrush(bg_color))

        if hasattr(self.drawing_widget, 'has_pdf_background') and self.drawing_widget.has_pdf_background():
            layer = self.drawing_widget.get_pdf_background_layer()
            if layer:
                try:
                    image = layer.get_current_page_image()
                except Exception:
                    image = QImage()
                if not image.isNull():
                    painter.drawImage(0, 0, image)
                    return

        # Grid/Pattern çizimi
        if self.drawing_widget.background_settings['type'] == 'grid':
            self.draw_grid_background(painter)
        elif self.drawing_widget.background_settings['type'] == 'dots':
            self.draw_dots_background(painter)
        
        # Beyaz arka planda da grid göster (snap aktifse)
        if (self.drawing_widget.background_settings['type'] == 'solid' and 
            self.drawing_widget.background_settings.get('snap_to_grid', False)):
            self.draw_snap_grid(painter)
            
    def draw_grid_background(self, painter):
        """Çizgili arka plan çiz (sadece yatay çizgiler) - Major/Minor sistem"""
        # Minor grid ayarları
        minor_color = QColor(self.drawing_widget.background_settings['grid_color'])
        major_color = QColor(self.drawing_widget.background_settings.get('major_grid_color', QColor(150, 150, 150)))
        grid_size = self.drawing_widget.background_settings['grid_size']
        minor_width = self.drawing_widget.background_settings['grid_width']
        major_width = self.drawing_widget.background_settings.get('major_grid_width', 2)
        major_interval = self.drawing_widget.background_settings.get('major_grid_interval', 5)
        grid_opacity = self.drawing_widget.background_settings.get('grid_opacity', 1.0)
        
        # Şeffaflık uygula
        minor_color.setAlphaF(grid_opacity)
        major_color.setAlphaF(grid_opacity)
        
        rect = self.drawing_widget.rect()
        width = rect.width()
        height = rect.height()
        
        # Sadece yatay çizgiler (çizgili kağıt gibi)
        y = 0
        line_count = 0
        while y <= height:
            # Her major_interval çizgide bir major grid çiz
            if line_count % major_interval == 0:
                # Major çizgi
                pen = QPen(major_color, major_width)
                painter.setPen(pen)
            else:
                # Minor çizgi
                pen = QPen(minor_color, minor_width)
                painter.setPen(pen)
            
            painter.drawLine(0, y, width, y)
            y += grid_size
            line_count += 1
             
    def draw_snap_grid(self, painter):
        """Beyaz arka planda snap için hafif grid çiz - Major/Minor sistem"""
        # Minor grid ayarları
        minor_color = QColor(self.drawing_widget.background_settings['grid_color'])
        major_color = QColor(self.drawing_widget.background_settings.get('major_grid_color', QColor(150, 150, 150)))
        grid_size = self.drawing_widget.background_settings['grid_size']
        minor_width = max(1, self.drawing_widget.background_settings['grid_width'] - 1)  # Biraz daha ince
        major_width = max(1, self.drawing_widget.background_settings.get('major_grid_width', 2) - 1)  # Biraz daha ince
        major_interval = self.drawing_widget.background_settings.get('major_grid_interval', 5)
        grid_opacity = self.drawing_widget.background_settings.get('grid_opacity', 1.0) * 0.3  # Daha şeffaf
        
        # Şeffaflık uygula
        minor_color.setAlphaF(grid_opacity)
        major_color.setAlphaF(grid_opacity)
        
        rect = self.drawing_widget.rect()
        width = rect.width()
        height = rect.height()
        
        # Dikey çizgiler
        x = 0
        line_count = 0
        while x <= width:
            # Her major_interval çizgide bir major grid çiz
            if line_count % major_interval == 0:
                # Major çizgi
                pen = QPen(major_color, major_width, Qt.PenStyle.DotLine)
                painter.setPen(pen)
            else:
                # Minor çizgi
                pen = QPen(minor_color, minor_width, Qt.PenStyle.DotLine)
                painter.setPen(pen)
            
            painter.drawLine(x, 0, x, height)
            x += grid_size
            line_count += 1
            
        # Yatay çizgiler
        y = 0
        line_count = 0
        while y <= height:
            # Her major_interval çizgide bir major grid çiz
            if line_count % major_interval == 0:
                # Major çizgi
                pen = QPen(major_color, major_width, Qt.PenStyle.DotLine)
                painter.setPen(pen)
            else:
                # Minor çizgi
                pen = QPen(minor_color, minor_width, Qt.PenStyle.DotLine)
                painter.setPen(pen)
            
            painter.drawLine(0, y, width, y)
            y += grid_size
            line_count += 1
            
    def draw_dots_background(self, painter):
        """Kareli arka plan çiz (hem yatay hem dikey çizgiler) - Major/Minor sistem"""
        # Minor grid ayarları
        minor_color = QColor(self.drawing_widget.background_settings['grid_color'])
        major_color = QColor(self.drawing_widget.background_settings.get('major_grid_color', QColor(150, 150, 150)))
        grid_size = self.drawing_widget.background_settings['grid_size']
        minor_width = self.drawing_widget.background_settings['grid_width']
        major_width = self.drawing_widget.background_settings.get('major_grid_width', 2)
        major_interval = self.drawing_widget.background_settings.get('major_grid_interval', 5)
        grid_opacity = self.drawing_widget.background_settings.get('grid_opacity', 1.0)
        
        # Şeffaflık uygula
        minor_color.setAlphaF(grid_opacity)
        major_color.setAlphaF(grid_opacity)
        
        rect = self.drawing_widget.rect()
        width = rect.width()
        height = rect.height()
        
        # Dikey çizgiler (kareli için)
        x = 0
        line_count = 0
        while x <= width:
            # Her major_interval çizgide bir major grid çiz
            if line_count % major_interval == 0:
                # Major çizgi
                pen = QPen(major_color, major_width)
                painter.setPen(pen)
            else:
                # Minor çizgi
                pen = QPen(minor_color, minor_width)
                painter.setPen(pen)
            
            painter.drawLine(x, 0, x, height)
            x += grid_size
            line_count += 1
            
        # Yatay çizgiler (kareli için)
        y = 0
        line_count = 0
        while y <= height:
            # Her major_interval çizgide bir major grid çiz
            if line_count % major_interval == 0:
                # Major çizgi
                pen = QPen(major_color, major_width)
                painter.setPen(pen)
            else:
                # Minor çizgi
                pen = QPen(minor_color, minor_width)
                painter.setPen(pen)
            
            painter.drawLine(0, y, width, y)
            y += grid_size
            line_count += 1

    def render(self, painter):
        """PDF export için özel render metodu - zoom/pan olmadan sadece içerik"""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Arka planı çiz (beyaz)
        bg_color = QColor(Qt.GlobalColor.white)
        painter.fillRect(self.drawing_widget.rect(), QBrush(bg_color))
        
        # Tüm tamamlanmış stroke'ları çiz
        for stroke_data in self.drawing_widget.strokes:
            # Image stroke kontrolü
            if hasattr(stroke_data, 'stroke_type') and stroke_data.stroke_type == 'image':
                stroke_data.render(painter)
                continue
                
            # Güvenlik kontrolü - eski stroke'lar için
            if 'type' not in stroke_data:
                continue
            if stroke_data['type'] == 'bspline':
                self.drawing_widget.bspline_tool.draw_stroke(painter, stroke_data)
            elif stroke_data['type'] == 'freehand':
                self.drawing_widget.freehand_tool.draw_stroke(painter, stroke_data)
            elif stroke_data['type'] == 'line':
                self.drawing_widget.line_tool.draw_stroke(painter, stroke_data)
            elif stroke_data['type'] == 'rectangle':
                self.drawing_widget.rectangle_tool.draw_stroke(painter, stroke_data)
            elif stroke_data['type'] == 'circle':
                self.drawing_widget.circle_tool.draw_stroke(painter, stroke_data)

    def render_with_pdf_background(self, painter):
        """PDF arka planıyla birlikte export render (zoom/pan olmadan)."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Önce PDF arka planını çizmeyi dene
        drew_pdf = False
        if hasattr(self.drawing_widget, 'has_pdf_background') and self.drawing_widget.has_pdf_background():
            layer = self.drawing_widget.get_pdf_background_layer()
            if layer:
                try:
                    image = layer.get_current_page_image()
                except Exception:
                    image = QImage()
                if not image.isNull():
                    painter.drawImage(0, 0, image)
                    drew_pdf = True
        
        # Eğer PDF arka planı yoksa beyaz doldur
        if not drew_pdf:
            bg_color = QColor(Qt.GlobalColor.white)
            painter.fillRect(self.drawing_widget.rect(), QBrush(bg_color))
        
        # Üstüne tüm stroke'ları çiz
        for stroke_data in self.drawing_widget.strokes:
            if hasattr(stroke_data, 'stroke_type') and stroke_data.stroke_type == 'image':
                stroke_data.render(painter)
                continue
            if 'type' not in stroke_data:
                continue
            if stroke_data['type'] == 'bspline':
                self.drawing_widget.bspline_tool.draw_stroke(painter, stroke_data)
            elif stroke_data['type'] == 'freehand':
                self.drawing_widget.freehand_tool.draw_stroke(painter, stroke_data)
            elif stroke_data['type'] == 'line':
                self.drawing_widget.line_tool.draw_stroke(painter, stroke_data)
            elif stroke_data['type'] == 'rectangle':
                self.drawing_widget.rectangle_tool.draw_stroke(painter, stroke_data)
            elif stroke_data['type'] == 'circle':
                self.drawing_widget.circle_tool.draw_stroke(painter, stroke_data)

    def draw_stroke_full(self, painter, stroke_data):
        """Full kalite stroke çizimi"""
        if stroke_data['type'] == 'bspline':
            self.drawing_widget.bspline_tool.draw_stroke(painter, stroke_data)
        elif stroke_data['type'] == 'freehand':
            self.drawing_widget.freehand_tool.draw_stroke(painter, stroke_data)
        elif stroke_data['type'] == 'line':
            self.drawing_widget.line_tool.draw_stroke(painter, stroke_data)
        elif stroke_data['type'] == 'rectangle':
            self.drawing_widget.rectangle_tool.draw_stroke(painter, stroke_data)
        elif stroke_data['type'] == 'circle':
            self.drawing_widget.circle_tool.draw_stroke(painter, stroke_data)
    
    def draw_stroke_medium(self, painter, stroke_data):
        """Orta kalite stroke çizimi - nokta sayısını azalt"""
        if stroke_data['type'] == 'freehand' and 'points' in stroke_data:
            # Freehand için nokta sayısını azalt (performans)
            original_points = stroke_data['points']
            if len(original_points) > 10:
                # Her 2. noktayı al
                simplified_data = stroke_data.copy()
                simplified_data['points'] = original_points[::2]
                self.drawing_widget.freehand_tool.draw_stroke(painter, simplified_data)
            else:
                self.drawing_widget.freehand_tool.draw_stroke(painter, stroke_data)
        else:
            # Diğer tipler için normal çizim
            self.draw_stroke_full(painter, stroke_data)
    
    def draw_stroke_simple(self, painter, stroke_data):
        """Basit/hızlı stroke çizimi - minimal detail"""
        # Renk ve kalınlık al
        color = stroke_data.get('color', Qt.GlobalColor.black)
        width = max(1, stroke_data.get('width', 2) * 0.7)  # İnce çiz
        
        # Basit pen oluştur
        if isinstance(color, str):
            color = QColor(color)
        
        pen = QPen(color)
        pen.setWidthF(width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        
        # Stroke tipine göre basit çizim
        if stroke_data['type'] in ['freehand', 'bspline'] and 'points' in stroke_data:
            points = stroke_data['points']
            if len(points) > 4:
                # Çok basitleştir - sadece start, mid, end
                simplified_points = [points[0], points[len(points)//2], points[-1]]
                for i in range(len(simplified_points) - 1):
                    painter.drawLine(simplified_points[i], simplified_points[i + 1])
            else:
                # Az nokta varsa normal çiz
                for i in range(len(points) - 1):
                    painter.drawLine(points[i], points[i + 1])
        elif stroke_data['type'] == 'line':
            start = stroke_data['start_point']
            end = stroke_data['end_point']
            painter.drawLine(QPointF(start[0], start[1]), QPointF(end[0], end[1]))
        elif stroke_data['type'] == 'rectangle':
            if 'corners' in stroke_data:
                corners = stroke_data['corners']
                for i in range(4):
                    p1 = QPointF(corners[i][0], corners[i][1])
                    p2 = QPointF(corners[(i+1)%4][0], corners[(i+1)%4][1])
                    painter.drawLine(p1, p2)
            else:
                tl, br = stroke_data['top_left'], stroke_data['bottom_right']
                rect = QRectF(tl[0], tl[1], br[0]-tl[0], br[1]-tl[1])
                painter.drawRect(rect)
        elif stroke_data['type'] == 'circle':
            center = stroke_data['center']
            radius = stroke_data['radius']
            rect = QRectF(center[0]-radius, center[1]-radius, 2*radius, 2*radius)
            painter.drawEllipse(rect) 