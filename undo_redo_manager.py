from PyQt6.QtCore import QObject, pyqtSignal
import copy

class UndoRedoManager(QObject):
    """Undo/Redo işlemleri için yönetici sınıf"""
    
    # Signals
    canUndoChanged = pyqtSignal(bool)
    canRedoChanged = pyqtSignal(bool)
    stateChanged = pyqtSignal()
    
    def __init__(self, max_history=50):
        super().__init__()
        self.max_history = max_history
        self.history = []  # Geçmiş durumlar
        self.current_index = -1  # Şu anki pozisyon
        
    def save_state(self, strokes_data, description="Action"):
        """Mevcut durumu kaydet"""
        # Eğer redo geçmişindeyse, ileri durumları sil
        if self.current_index < len(self.history) - 1:
            self.history = self.history[:self.current_index + 1]
        
        # Yeni durumu ekle
        state = {
            'strokes': copy.deepcopy(strokes_data),
            'description': description,
            'timestamp': self._get_timestamp()
        }
        
        self.history.append(state)
        self.current_index += 1
        
        # Maksimum geçmiş sınırını kontrol et
        if len(self.history) > self.max_history:
            self.history.pop(0)
            self.current_index -= 1
            
        self._emit_signals()
        
    def undo(self):
        """Geri al"""
        if self.can_undo():
            self.current_index -= 1
            self._emit_signals()
            return self._get_current_state()
        return None
        
    def redo(self):
        """İleri al"""
        if self.can_redo():
            self.current_index += 1
            self._emit_signals()
            return self._get_current_state()
        return None
        
    def can_undo(self):
        """Geri alınabilir mi?"""
        return self.current_index > 0
        
    def can_redo(self):
        """İleri alınabilir mi?"""
        return self.current_index < len(self.history) - 1
        
    def clear_history(self):
        """Geçmişi temizle"""
        self.history.clear()
        self.current_index = -1
        self._emit_signals()
        
    def get_current_state(self):
        """Şu anki durumu al"""
        return self._get_current_state()
        
    def _get_current_state(self):
        """Internal: şu anki durumu al"""
        if 0 <= self.current_index < len(self.history):
            return copy.deepcopy(self.history[self.current_index]['strokes'])
        return []
        
    def _emit_signals(self):
        """Sinyalleri yayınla"""
        self.canUndoChanged.emit(self.can_undo())
        self.canRedoChanged.emit(self.can_redo())
        self.stateChanged.emit()
        
    def _get_timestamp(self):
        """Zaman damgası al"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")
        
    def get_history_info(self):
        """Geçmiş bilgilerini al (debug için)"""
        info = []
        for i, state in enumerate(self.history):
            marker = " -> " if i == self.current_index else "    "
            info.append(f"{marker}{i}: {state['description']} ({state['timestamp']})")
        return "\n".join(info)
        
    def get_undo_description(self):
        """Undo edilecek işlemin açıklamasını al"""
        if self.can_undo():
            return self.history[self.current_index]['description']
        return ""
        
    def get_redo_description(self):
        """Redo edilecek işlemin açıklamasını al"""
        if self.can_redo():
            return self.history[self.current_index + 1]['description']
        return ""

class Command:
    """Command pattern için base class"""
    def __init__(self, description="Command"):
        self.description = description
        
    def execute(self):
        """Komutu çalıştır"""
        raise NotImplementedError
        
    def undo(self):
        """Komutu geri al"""
        raise NotImplementedError

class AddStrokeCommand(Command):
    """Stroke ekleme komutu"""
    def __init__(self, drawing_widget, stroke_data):
        super().__init__(f"Add {stroke_data.get('type', 'stroke')}")
        self.drawing_widget = drawing_widget
        self.stroke_data = stroke_data
        
    def execute(self):
        """Stroke'u ekle"""
        self.drawing_widget.strokes.append(self.stroke_data)
        self.drawing_widget.update()
        
    def undo(self):
        """Stroke'u kaldır"""
        if self.stroke_data in self.drawing_widget.strokes:
            self.drawing_widget.strokes.remove(self.stroke_data)
            self.drawing_widget.update()

class ClearAllCommand(Command):
    """Tümünü temizle komutu"""
    def __init__(self, drawing_widget):
        super().__init__("Clear all")
        self.drawing_widget = drawing_widget
        self.saved_strokes = copy.deepcopy(drawing_widget.strokes)
        
    def execute(self):
        """Tümünü temizle"""
        self.drawing_widget.strokes.clear()
        self.drawing_widget.update()
        
    def undo(self):
        """Stroke'ları geri getir"""
        self.drawing_widget.strokes = copy.deepcopy(self.saved_strokes)
        self.drawing_widget.update()

class DeleteStrokeCommand(Command):
    """Stroke silme komutu"""
    def __init__(self, drawing_widget, stroke_index):
        super().__init__("Delete stroke")
        self.drawing_widget = drawing_widget
        self.stroke_index = stroke_index
        self.deleted_stroke = None
        
    def execute(self):
        """Stroke'u sil"""
        if 0 <= self.stroke_index < len(self.drawing_widget.strokes):
            self.deleted_stroke = self.drawing_widget.strokes.pop(self.stroke_index)
            self.drawing_widget.update()
            
    def undo(self):
        """Stroke'u geri ekle"""
        if self.deleted_stroke is not None:
            self.drawing_widget.strokes.insert(self.stroke_index, self.deleted_stroke)
            self.drawing_widget.update() 