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
            printer.setPageMargins(QMarginsF(20, 20, 20, 20), QPageLayout.Unit.Millimeter)
            
            painter = QPainter()
            painter.begin(printer)
            
            # Her sekmeyi ayrı sayfa olarak ekle
            for i in range(self.main_window.tab_widget.count()):
                if i > 0:
                    printer.newPage()  # Yeni sayfa
                
                # Tab widget'ını al
                drawing_widget = self.main_window.tab_widget.widget(i)
                if drawing_widget:
                    self._render_page(painter, drawing_widget, i)
            
            painter.end()
            
            QMessageBox.information(self.main_window, "Başarılı", f"PDF başarıyla oluşturuldu:\n{filename}")
            
        except Exception as e:
            QMessageBox.critical(self.main_window, "Hata", f"PDF oluşturulamadı:\n{str(e)}")
    
    def _render_page(self, painter, drawing_widget, page_index):
        """Tek sayfa çiz"""
        # Drawing widget'ını PDF'e çiz
        widget_rect = drawing_widget.rect()
        page_rect = painter.viewport()
        
        # Ölçekleme hesapla (sayfa boyutuna sığdır)
        scale_x = page_rect.width() / widget_rect.width()
        scale_y = page_rect.height() / widget_rect.height()
        scale = min(scale_x, scale_y) * 0.9  # %90 boyut (margin için)
        
        # Merkeze hizala
        scaled_width = widget_rect.width() * scale
        scaled_height = widget_rect.height() * scale
        x_offset = (page_rect.width() - scaled_width) / 2
        y_offset = (page_rect.height() - scaled_height) / 2
        
        painter.save()
        painter.translate(x_offset, y_offset)
        painter.scale(scale, scale)
        
        # Widget'ı çiz
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
        text_y = page_rect.height() - 50
        
        painter.drawText(int(text_x), int(text_y), page_info)
        painter.restore() 