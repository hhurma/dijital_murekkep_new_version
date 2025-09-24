from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QPainter, QPen
from stroke_handler import ensure_qpointf


class EraserTool:
    """Silgi aracı: fırça benzeri dairesel silme.

    Mantık:
    - Canvas vektör tabanlı. Silme, vuruş (stroke) noktalarını silgi dairesiyle
      kesişen kısımlardan kırparak yapılır.
    - İlk sürüm: Silgi yarıçapı içinde kalan noktaları kaldırır.
      Çok seyrekleşen stroke (<=1 nokta) tamamen silinir.
    - Performans için sade bir yaklaşım.
    """

    def __init__(self):
        self.is_erasing = False
        self.radius = 16.0
        self.hardness = 1.0  # Gelecekte yumuşak silgi için
        self.current_pos = None
        self._to_remove = set()
        self._pending_compact = False

    def set_radius(self, radius: float):
        try:
            r = float(radius)
        except Exception:
            return
        self.radius = max(1.0, r)

    def start_erase(self, pos: QPointF):
        self.is_erasing = True
        self.current_pos = QPointF(pos)

    def update_erase(self, pos: QPointF, drawing_widget):
        """Silme işlemini sürdür. Aktif katmandaki stroke'ları düzenler.

        Nokta-tabanlı stroke'larda (freehand/bspline) silgi dairesi içinde kalan
        noktaları kaldırır. Çizgi/şekiller için basit bir yakınlık kontrolü ile
        tümü kaldırılır (ilk sürümde basitleştirilmiş davranış).
        """
        if not self.is_erasing:
            return False

        self.current_pos = QPointF(pos)

        changed = False
        # Aktif katman stroke listesini yerinde (in-place) düzenle
        strokes = drawing_widget.strokes

        from PyQt6.QtCore import QPointF as QPF, QRectF
        try:
            from stroke_handler import StrokeHandler
        except Exception:
            StrokeHandler = None

        r = float(self.radius)
        r2 = r * r
        erase_rect = QRectF(self.current_pos.x() - r, self.current_pos.y() - r, 2 * r, 2 * r)

        def point_inside(qp: QPF) -> bool:
            dx = qp.x() - self.current_pos.x()
            dy = qp.y() - self.current_pos.y()
            return (dx * dx + dy * dy) <= r2

        for idx, s in enumerate(list(strokes)):
            # Image stroke'ları silgi ile işlemiyoruz (ileri sürümde maske olabilir)
            if hasattr(s, 'stroke_type') and getattr(s, 'stroke_type', None) == 'image':
                continue

            if not hasattr(s, 'get') or 'type' not in s:
                continue

            stype = s.get('type')
            # Hızlı bounding kontrolü (varsa)
            if StrokeHandler is not None:
                try:
                    bounds = StrokeHandler.get_stroke_bounds(s)
                    if bounds is not None:
                        # Bir miktar margin ekle (yarıçap)
                        inflated = bounds.adjusted(-r, -r, r, r)
                        if not inflated.intersects(erase_rect):
                            continue
                except Exception:
                    pass

            if stype in ('freehand', 'bspline') and 'points' in s:
                points = s['points']
                kept = []
                # In-place filtreleme (kopya listeyi oluşturup atayacağız)
                for p in points:
                    q = ensure_qpointf(p)
                    if not point_inside(q):
                        kept.append(q)
                if len(kept) > 1:
                    if len(kept) != len(points):
                        s['points'] = kept
                        changed = True
                else:
                    # Çok az nokta kaldıysa stroke'u tamamen kaldır (release'te compact edilir)
                    self._to_remove.add(idx)
                    self._pending_compact = True
                    changed = True
            elif stype in ('line', 'rectangle', 'circle'):
                # Basit: silgi merkezine yakınsa tüm şekli kaldır
                # Daha iyi: kenar-segment yakınlık testi (ileride)
                if StrokeHandler is not None:
                    try:
                        if StrokeHandler.is_point_near_stroke(s, self.current_pos, tolerance=max(8, int(self.radius))):
                            self._to_remove.add(idx)
                            self._pending_compact = True
                            changed = True
                            continue
                    except Exception:
                        pass
            else:
                continue

        # In-place değişiklikler yapıldı; anlık ek maliyet olmadan ekranda güncellenecek
        return changed

    def finish_erase(self):
        self.is_erasing = False
        # Kaldırılacaklar varsa, listeyi sıkıştır ve setter ile yaz (undo noktası sonrası)
        if self._pending_compact and hasattr(self, '_to_remove') and self._to_remove:
            # Mevcut aktif katman stroke listesi
            try:
                # drawing_widget'a erişim yok; kompakt işlemi EventHandler'da setter ile yapılacak
                # Bu nedenle burada sadece bayrakları temizle
                pass
            finally:
                self._to_remove.clear()
                self._pending_compact = False

    def draw_cursor(self, painter: QPainter):
        if self.current_pos is None:
            return
        painter.save()
        pen = QPen(Qt.GlobalColor.red)
        pen.setWidth(1)
        pen.setStyle(Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        r = self.radius
        painter.drawEllipse(self.current_pos, r, r)
        painter.restore()


