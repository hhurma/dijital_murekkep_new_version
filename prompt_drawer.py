from PyQt6.QtCore import QPointF


class PromptDrawer:
    """LLM çıktısını stroke listesine dönüştürür."""

    @staticmethod
    def _extract_axes(data: dict):
        axes = data.get('axes') or data.get('eksenler') or {}
        x_label = axes.get('x') or axes.get('yatay') or 'X'
        y_label = axes.get('y') or axes.get('dikey') or 'Y'
        return x_label, y_label

    @staticmethod
    def _extract_series(data: dict):
        # Beklenen biçimler:
        # - { series: [{ name, points: [{x,y},..] }] }
        # - { cizgiler: [{ grup_adi, veri: [{x,y},..] }] }
        series = []
        if isinstance(data, dict):
            src = data.get('series')
            if isinstance(src, list):
                for s in src:
                    name = s.get('name') if isinstance(s, dict) else None
                    # Farklı anahtar eşlemeleri: points | data
                    pts = s.get('points') if isinstance(s, dict) else None
                    if pts is None and isinstance(s, dict):
                        pts = s.get('data')
                    # line tipi verilmişse not al
                    s_type = s.get('type') if isinstance(s, dict) else None
                    if isinstance(pts, list) and pts:
                        series.append({'name': name or 'Seri', 'points': pts, 'stype': s_type})
            src = data.get('cizgiler')
            if isinstance(src, list):
                for s in src:
                    name = s.get('grup_adi') if isinstance(s, dict) else None
                    pts = s.get('veri') if isinstance(s, dict) else None
                    if isinstance(pts, list) and pts:
                        series.append({'name': name or 'Seri', 'points': pts, 'stype': None})
        return series

    @staticmethod
    def _scale_points(points, box):
        # box = (left, top, right, bottom)
        if not points:
            return []
        xs = [p.get('x') for p in points if isinstance(p, dict) and isinstance(p.get('x'), (int, float))]
        ys = [p.get('y') for p in points if isinstance(p, dict) and isinstance(p.get('y'), (int, float))]
        if not xs or not ys:
            return []
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        if max_x == min_x:
            max_x += 1.0
        if max_y == min_y:
            max_y += 1.0
        left, top, right, bottom = box
        width = max(1.0, right - left)
        height = max(1.0, bottom - top)
        scaled = []
        for p in points:
            if not isinstance(p, dict):
                continue
            x = float(p.get('x', 0.0))
            y = float(p.get('y', 0.0))
            # X sağa arttıkça sağa, Y arttıkça yukarı için canvas'ta ters yönde ölçekle
            nx = left + (x - min_x) / (max_x - min_x) * width
            ny = bottom - (y - min_y) / (max_y - min_y) * height
            scaled.append(QPointF(nx, ny))
        return scaled

    @staticmethod
    def build_axes_and_demand_curve(canvas_width: int, canvas_height: int, x_label: str, y_label: str):
        cx = canvas_width // 2
        cy = canvas_height // 2

        # Eksenler: ok uçlu çizgiler (line)
        margin = 80
        origin = (margin, canvas_height - margin)
        x_end = (canvas_width - margin, canvas_height - margin)
        y_end = (margin, margin)

        x_axis = {
            'type': 'line',
            'start_point': origin,
            'end_point': x_end,
            'color': '#000000',
            'width': 2,      # line_tool beklediği alan
            'style': 1,      # line_tool beklediği alan
            'name': x_label or 'X'
        }
        y_axis = {
            'type': 'line',
            'start_point': origin,
            'end_point': y_end,
            'color': '#000000',
            'width': 2,
            'style': 1,
            'name': y_label or 'Y'
        }

        # Talep eğrisi: negatif eğimli kavis (bspline)
        p1 = (margin + 60, margin + 40)
        p2 = (cx, cy)
        p3 = (canvas_width - margin - 40, canvas_height - margin - 20)
        # Bspline gereksinimlerinden kaçınmak için demand eğrisini freehand polyline olarak üret
        demand = {
            'type': 'freehand',
            'points': [
                QPointF(p1[0], p1[1]),
                QPointF((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2),
                QPointF(p2[0], p2[1]),
                QPointF((p2[0] + p3[0]) / 2, (p2[1] + p3[1]) / 2),
                QPointF(p3[0], p3[1]),
            ],
            'pressures': [1.0, 1.0, 1.0, 1.0, 1.0],
            'color': '#000000',
            'width': 2,
            'style': 1,
            'name': 'Talep Eğrisi'
        }

        return [x_axis, y_axis, demand]

    @staticmethod
    def strokes_from_llm_json(canvas_width: int, canvas_height: int, data: dict):
        data = data or {}
        x_label, y_label = PromptDrawer._extract_axes(data)

        # Önce veri serileri varsa onlardan çizimler üretelim
        series = PromptDrawer._extract_series(data)
        strokes = []
        # Eksenler
        margin = 80
        origin = (margin, canvas_height - margin)
        x_end = (canvas_width - margin, canvas_height - margin)
        y_end = (margin, margin)
        strokes.append({
            'type': 'line', 'start_point': origin, 'end_point': x_end,
            'color': '#000000', 'width': 2, 'style': 1, 'name': x_label or 'X'
        })
        strokes.append({
            'type': 'line', 'start_point': origin, 'end_point': y_end,
            'color': '#000000', 'width': 2, 'style': 1, 'name': y_label or 'Y'
        })

        if series:
            # Çizim alanı (eksenleri kapsayan kutu)
            left, top = margin + 20, margin + 10
            right, bottom = canvas_width - margin - 10, canvas_height - margin - 20
            for s in series:
                pts = PromptDrawer._scale_points(s.get('points'), (left, top, right, bottom))
                if len(pts) >= 2:
                    if (s.get('stype') or '').lower() == 'line':
                        # İlk ve son noktadan tek çizgi üret (kayıt dosyanızdaki format)
                        start = (pts[0].x(), pts[0].y())
                        end = (pts[-1].x(), pts[-1].y())
                        stroke = {
                            'type': 'line',
                            'start_point': start,
                            'end_point': end,
                            'color': '#000000',
                            'width': 2,
                            'style': 1,
                            'name': s.get('name') or 'Seri'
                        }
                        strokes.append(stroke)
                    else:
                        stroke = {
                            'type': 'freehand',
                            'points': pts,
                            'pressures': [1.0] * len(pts),
                            'color': '#000000',
                            'width': 2,
                            'style': 1,
                            'name': s.get('name') or 'Seri'
                        }
                        strokes.append(stroke)
            return strokes

        # Şema yoksa eski basit kurala dön
        chart = (data or {}).get('chart', '')
        if str(chart).lower() in ('talep', 'demand', 'talep eğrisi', 'demand curve'):
            return PromptDrawer.build_axes_and_demand_curve(canvas_width, canvas_height, x_label, y_label)
        if str(chart).lower() in ('arz', 'supply', 'arz eğrisi', 'supply curve'):
            # Arz için yükselen eğri üretelim
            # Basit doğrusal yükseliş
            cx = canvas_width // 2
            cy = canvas_height // 2
            margin = 80
            p1 = (margin + 40, canvas_height - margin - 40)
            p2 = (cx, cy)
            p3 = (canvas_width - margin - 40, margin + 40)
            points = [QPointF(p1[0], p1[1]), QPointF((p1[0]+p2[0])/2, (p1[1]+p2[1])/2), QPointF(p2[0], p2[1]), QPointF((p2[0]+p3[0])/2, (p2[1]+p3[1])/2), QPointF(p3[0], p3[1])]
            strokes.append({
                'type': 'freehand', 'points': points, 'pressures': [1.0]*len(points),
                'color': '#000000', 'width': 2, 'style': 1, 'name': 'Arz Eğrisi'
            })
            return strokes

        # Fallback: sadece eksenler
        return strokes


