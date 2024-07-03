from ..graph import BaseNode
import dearpygui.dearpygui as dpg
import time

class ProgressNode(BaseNode):
    def __init__(self):
        super().__init__()
        self._last_update = None
        self._execution_times = []
        self._progress = None
        self._last_current = -1
        self._last_total = -1

    def init(self):
        self.set_progress(-1, -1)
        pass

    def set_progress(self, current, total, show_eta=True):
        if self._progress == None:
            return
        
        if current == self._last_current and total == self._last_total:
            return
        
        self._last_current = current
        self._last_total = total
        
        if not dpg.does_item_exist(self._progress):
            return

        if current == -1 or total == -1:
            if dpg.does_item_exist(self._progress):
                dpg.hide_item(self._progress)
            self._last_update = None
            self._execution_times = []
            return
        
        if self._progress != None and  dpg.does_item_exist(self._progress) and not dpg.is_item_shown(self._progress):
            dpg.show_item(self._progress)

        progress_float = (float(current) / float(total)) if total != 0 else 0

        if self._last_update is None:
            self._last_update = time.time()
            if not show_eta:
                dpg.configure_item(self._progress, overlay=f"{current}/{total}")
            else:
                dpg.configure_item(self._progress, overlay=f"{current}/{total} ETA: N/A")
            dpg.set_value(self._progress, progress_float)
        else:
            self._execution_times.append(time.time() - self._last_update)
            self._execution_times = self._execution_times[-10:]
            eta = sum(self._execution_times) / len(self._execution_times) * (total - current)
            if not show_eta:
                dpg.configure_item(self._progress, overlay=f"{current}/{total}")
            else:
                dpg.configure_item(self._progress, overlay=f"{current}/{total} ETA: {eta:.1f}s")
            dpg.set_value(self._progress, progress_float)
            self._last_update = time.time()

    def show_custom_ui(self, parent):
        self._progress = dpg.add_progress_bar(default_value=0, overlay="0/0 ETA: 0s", parent=parent, width=150, show=False)
