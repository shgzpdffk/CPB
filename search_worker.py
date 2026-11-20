from PySide6.QtCore import QThread, Signal

from search_client import fetch_recipes


class SearchWorker(QThread):
    succeeded = Signal(dict)
    failed = Signal(str)

    def __init__(self, request):
        super().__init__()
        self.request = request

    def run(self):
        try:
            response = fetch_recipes(self.request)
        except Exception as error:
            self.failed.emit(str(error))
        else:
            self.succeeded.emit(response)
