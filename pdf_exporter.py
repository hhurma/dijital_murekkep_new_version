import errno
import os

from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtGui import QPainter, QColor, QPageSize, QPageLayout
from PyQt6.QtCore import QMarginsF
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from datetime import datetime

class PDFExporter:
    """PDF dışa aktarma işlemlerini yöneten sınıf"""
    
    def __init__(self, main_window):
        self.main_window = main_window
    
    def export_to_pdf(self):
        """Tüm sekmeleri PDF olarak dışa aktar"""
        if self.main_window.tab_widget.count() == 0:
            QMessageBox.warning(self.main_window, "Uyarı", "Dışa aktarılacak sekme yok!")
            return
        
        # PDF dosya adı sor
        filename, _ = QFileDialog.getSaveFileName(
            self.main_window, "PDF Olarak Dışa Aktar",
            f"oturum_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            "PDF Dosyaları (*.pdf);;Tüm Dosyalar (*)"
        )
        
        if not filename:
            return
            
        try:
            # PDF printer oluştur
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(filename)
            printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
            
            # Sayfa yönünü canvas yönüne göre otomatik belirle
            # İlk tab'ın canvas yönünü al
            first_drawing_widget = self.main_window.tab_manager.get_tab_widget_at_index(0)
            if first_drawing_widget and hasattr(first_drawing_widget, 'get_canvas_orientation'):
                canvas_orientation = first_drawing_widget.get_canvas_orientation()
                if canvas_orientation == 'landscape':
                    printer.setPageOrientation(QPageLayout.Orientation.Landscape)
                else:
                    printer.setPageOrientation(QPageLayout.Orientation.Portrait)
            else:
                # Fallback: Settings'den PDF yönünü al
                orientation = self.main_window.settings.get_pdf_orientation()
                if orientation == 'landscape':
                    printer.setPageOrientation(QPageLayout.Orientation.Landscape)
                else:
                    printer.setPageOrientation(QPageLayout.Orientation.Portrait)
            
            printer.setPageMargins(QMarginsF(5, 5, 5, 5), QPageLayout.Unit.Millimeter)
            
            painter = QPainter()
            painter.begin(printer)
            
            # Her sekmeyi ayrı sayfa olarak ekle
            for i in range(self.main_window.tab_widget.count()):
                if i > 0:
                    printer.newPage()  # Yeni sayfa
                
                # Drawing widget'ı tab manager'dan al
                drawing_widget = self.main_window.tab_manager.get_tab_widget_at_index(i)
                if drawing_widget:
                    self._render_page(painter, drawing_widget, i)
            
            painter.end()
            
            QMessageBox.information(self.main_window, "Başarılı", f"PDF başarıyla oluşturuldu:\n{filename}")
            
        except Exception as e:
            QMessageBox.critical(self.main_window, "Hata", f"PDF oluşturulamadı:\n{str(e)}")
    
    def export_current_tab_with_pdf_pages(self):
        """Geçerli sekmenin PDF arka planındaki TÜM sayfalarını tek PDF'e dışa aktar."""
        drawing_widget = self.main_window.get_current_drawing_widget()
        if not drawing_widget:
            QMessageBox.warning(self.main_window, "Uyarı", "Açık çizim sekmesi bulunmuyor.")
            return
        if not hasattr(drawing_widget, 'has_pdf_background') or not drawing_widget.has_pdf_background():
            QMessageBox.warning(self.main_window, "Uyarı", "Bu sekmede PDF arka planı yok.")
            return

        layer = drawing_widget.get_pdf_background_layer()
        if not layer:
            QMessageBox.warning(self.main_window, "Uyarı", "PDF arka planı bulunamadı.")
            return

        # Dosya adı
        filename, _ = QFileDialog.getSaveFileName(
            self.main_window, "PDF'ye Kaydet (Tüm PDF Sayfaları)",
            f"pdf_aktar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            "PDF Dosyaları (*.pdf);;Tüm Dosyalar (*)"
        )
        if not filename:
            return

        try:
            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
            printer.setOutputFileName(filename)
            printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))

            # Yönlendirme: canvas yönü
            if hasattr(drawing_widget, 'get_canvas_orientation') and drawing_widget.get_canvas_orientation() == 'landscape':
                printer.setPageOrientation(QPageLayout.Orientation.Landscape)
            else:
                printer.setPageOrientation(QPageLayout.Orientation.Portrait)

            printer.setPageMargins(QMarginsF(5, 5, 5, 5), QPageLayout.Unit.Millimeter)

            painter = QPainter()
            painter.begin(printer)

            # Orijinal sayfayı hatırla
            original_page = layer.current_page

            for page_index in range(layer.page_count):
                if page_index > 0:
                    printer.newPage()

                # Sayfayı değiştir ve PDF arka planıyla birlikte çiz
                if hasattr(drawing_widget, 'go_to_pdf_page'):
                    drawing_widget.go_to_pdf_page(page_index)
                else:
                    layer.set_current_page(page_index)

                widget_rect = drawing_widget.rect()
                page_rect = painter.viewport()
                scale_x = page_rect.width() / widget_rect.width()
                scale_y = page_rect.height() / widget_rect.height()
                base_scale = min(scale_x, scale_y) * 0.98

                scaled_width = widget_rect.width() * base_scale
                scaled_height = widget_rect.height() * base_scale
                x_offset = (page_rect.width() - scaled_width) / 2
                y_offset = (page_rect.height() - scaled_height) / 2

                painter.save()
                painter.translate(x_offset, y_offset)
                painter.scale(base_scale, base_scale)

                # PDF arka planını da içeren render
                if hasattr(drawing_widget, 'canvas_renderer') and hasattr(drawing_widget.canvas_renderer, 'render_with_pdf_background'):
                    drawing_widget.canvas_renderer.render_with_pdf_background(painter)
                else:
                    drawing_widget.render(painter)

                painter.restore()

            # Orijinal sayfaya geri dön
            layer.set_current_page(original_page)

            painter.end()

            QMessageBox.information(self.main_window, "Başarılı", f"PDF kaydedildi:\n{filename}")
        except Exception as e:
            QMessageBox.critical(self.main_window, "Hata", f"PDF kaydedilemedi:\n{str(e)}")

    def save_current_pdf_to_source(self) -> bool:
        """Aktif sekmedeki PDF arka planını kaynağın üzerine yazmaya çalış."""
        drawing_widget = self.main_window.get_current_drawing_widget()
        if not drawing_widget:
            QMessageBox.warning(self.main_window, "Uyarı", "Açık çizim sekmesi bulunmuyor.")
            return False

        if not hasattr(drawing_widget, 'has_pdf_background') or not drawing_widget.has_pdf_background():
            QMessageBox.warning(self.main_window, "Uyarı", "Bu sekmede PDF arka planı yok.")
            return False

        layer = drawing_widget.get_pdf_background_layer()
        if not layer or not getattr(layer, 'source_path', None):
            QMessageBox.warning(self.main_window, "Uyarı", "PDF kaynağı bulunamadı.")
            return False

        target_path = layer.source_path
        target_exists = os.path.exists(target_path)
        if target_exists:
            reply = QMessageBox.question(
                self.main_window,
                "PDF'nin Üzerine Yaz",
                f"{os.path.basename(target_path)} dosyasının mevcut içeriği üzerine yazılacak. Devam etmek istiyor musunuz?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return False

        parent_dir = os.path.dirname(target_path) or os.getcwd()
        if target_exists:
            writable = os.access(target_path, os.W_OK)
        else:
            writable = os.access(parent_dir, os.W_OK)

        if not writable:
            prompt = QMessageBox.question(
                self.main_window,
                "Yazma İzni Yok",
                "PDF dosyasına yazma izni bulunamadı. İçeriği farklı bir dosyaya kaydetmek ister misiniz?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if prompt == QMessageBox.StandardButton.Yes:
                self.export_current_tab_with_pdf_pages()
            return False

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(target_path)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))

        orientation = None
        if hasattr(drawing_widget, 'get_canvas_orientation'):
            orientation = drawing_widget.get_canvas_orientation()

        if orientation == 'landscape':
            printer.setPageOrientation(QPageLayout.Orientation.Landscape)
        elif orientation == 'portrait':
            printer.setPageOrientation(QPageLayout.Orientation.Portrait)
        else:
            fallback_orientation = self.main_window.settings.get_pdf_orientation()
            if fallback_orientation == 'landscape':
                printer.setPageOrientation(QPageLayout.Orientation.Landscape)
            else:
                printer.setPageOrientation(QPageLayout.Orientation.Portrait)

        printer.setPageMargins(QMarginsF(5, 5, 5, 5), QPageLayout.Unit.Millimeter)

        painter = QPainter()
        original_page = layer.current_page

        try:
            if not painter.begin(printer):
                raise RuntimeError("PDF yazıcısı başlatılamadı.")
            for page_index in range(layer.page_count):
                if page_index > 0:
                    printer.newPage()

                if hasattr(drawing_widget, 'go_to_pdf_page'):
                    drawing_widget.go_to_pdf_page(page_index)
                else:
                    layer.set_current_page(page_index)

                widget_rect = drawing_widget.rect()
                page_rect = painter.viewport()
                if widget_rect.width() == 0 or widget_rect.height() == 0:
                    continue

                scale_x = page_rect.width() / widget_rect.width()
                scale_y = page_rect.height() / widget_rect.height()
                base_scale = min(scale_x, scale_y) * 0.98

                scaled_width = widget_rect.width() * base_scale
                scaled_height = widget_rect.height() * base_scale
                x_offset = (page_rect.width() - scaled_width) / 2
                y_offset = (page_rect.height() - scaled_height) / 2

                painter.save()
                painter.translate(x_offset, y_offset)
                painter.scale(base_scale, base_scale)

                if hasattr(drawing_widget, 'canvas_renderer') and hasattr(drawing_widget.canvas_renderer, 'render_with_pdf_background'):
                    drawing_widget.canvas_renderer.render_with_pdf_background(painter)
                else:
                    drawing_widget.render(painter)

                painter.restore()

        except OSError as exc:
            if exc.errno in (errno.EACCES, errno.EPERM):
                QMessageBox.warning(self.main_window, "Yazma Hatası", "PDF dosyası üzerine yazılamadı. Lütfen farklı kaydedin.")
                self.export_current_tab_with_pdf_pages()
            else:
                QMessageBox.critical(self.main_window, "Hata", f"PDF kaydedilemedi:\n{str(exc)}")
            return False
        except Exception as exc:
            QMessageBox.critical(self.main_window, "Hata", f"PDF kaydedilemedi:\n{str(exc)}")
            return False
        finally:
            if hasattr(drawing_widget, 'go_to_pdf_page'):
                drawing_widget.go_to_pdf_page(original_page)
            else:
                layer.set_current_page(original_page)
            painter.end()

        QMessageBox.information(self.main_window, "Başarılı", f"PDF kaydedildi:\n{target_path}")
        return True

    def _render_page(self, painter, drawing_widget, page_index):
        """Tek sayfa çiz"""
        # Drawing widget'ının boyutları (A4)
        widget_rect = drawing_widget.rect()
        page_rect = painter.viewport()
        
        # PDF export için %200 zoom (canvas küçük olduğu için)
        export_zoom = 1.0  # %200 zoom
        
        # A4 boyutu zaten doğru, sadece sayfa boyutuna göre ölçekle
        scale_x = page_rect.width() / widget_rect.width()
        scale_y = page_rect.height() / widget_rect.height()
        base_scale = min(scale_x, scale_y) * 0.98  # %98 boyut (minimal margin için)
        
        # Export zoom ile birleştir
        final_scale = base_scale * export_zoom
        
        # Merkeze hizala
        scaled_width = widget_rect.width() * final_scale
        scaled_height = widget_rect.height() * final_scale
        x_offset = (page_rect.width() - scaled_width) / 2
        y_offset = (page_rect.height() - scaled_height) / 2
        
        painter.save()
        painter.translate(x_offset, y_offset)
        painter.scale(final_scale, final_scale)
        
        # Drawing widget'ını render et (sadece çizim içeriği)
        drawing_widget.render(painter)
        
        painter.restore()
        
        # Sayfa numarası ve tab adı ekle
        self._add_page_info(painter, page_index, page_rect)
    
    def _add_page_info(self, painter, page_index, page_rect):
        """Sayfa bilgilerini ekle"""
        painter.save()
        painter.setPen(QColor(0, 0, 0))
        font = painter.font()
        font.setPointSize(12)
        painter.setFont(font)
        
        tab_title = self.main_window.tab_widget.tabText(page_index)
        page_info = f"Sayfa {page_index + 1}/{self.main_window.tab_widget.count()} - {tab_title}"
        
        # Alt merkeze yazı
        text_rect = painter.fontMetrics().boundingRect(page_info)
        text_x = (page_rect.width() - text_rect.width()) / 2
        text_y = page_rect.height() - 20
        
        painter.drawText(int(text_x), int(text_y), page_info)
        painter.restore() 