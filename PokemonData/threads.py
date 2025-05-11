import requests
from PyQt5.QtCore import QThread, pyqtSignal

class DataFetcherThread(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, fetcher, data_type):
        super().__init__()
        self.fetcher = fetcher
        self.data_type = data_type
        
    def run(self):
        try:
            if self.data_type == 'pokemon':
                response = requests.get(f"{self.fetcher.base_url}/pokemon?limit=1")
                total_count = response.json()['count']
                response = requests.get(f"{self.fetcher.base_url}/pokemon?limit={total_count}")
                self.finished.emit(response.json()['results'])
            elif self.data_type == 'hareket':
                response = requests.get(f"{self.fetcher.base_url}/move?limit=1000")
                self.finished.emit(response.json()['results'])
            elif self.data_type == 'yetenek':
                response = requests.get(f"{self.fetcher.base_url}/ability?limit=1000")
                self.finished.emit(response.json()['results'])
            elif self.data_type == 'eşya':
                response = requests.get(f"{self.fetcher.base_url}/item?limit=1025")
                self.finished.emit(response.json()['results'])
            else:
                self.finished.emit([])
        except Exception as e:
            self.error.emit(str(e)) 