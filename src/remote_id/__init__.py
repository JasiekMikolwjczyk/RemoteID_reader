"""
Remote ID Complete Library
Kompletna biblioteka do dekodowania, wyświetlania i zapisywania danych Remote ID

Główne komponenty:
- RemoteIDDecoder: Dekodowanie ramek Remote ID
- LiveMonitor: Monitoring na żywo z portu szeregowego  
- FileProcessor: Przetwarzanie zapisanych plików
- LiveDecoder: Dekodowanie na żywo z wyświetlaniem
"""

from .decoder import RemoteIDDecoder, decode_block, scan_nan_frame
from .live_monitor import LiveMonitor
from .file_processor import FileProcessor
from .live_decoder import LiveDecoder

__version__ = "1.0.0"
__all__ = [
    'RemoteIDDecoder',
    'LiveMonitor', 
    'FileProcessor',
    'LiveDecoder',
    'decode_block',
    'scan_nan_frame'
]

# Convenience functions
def decode_from_file(filepath, output_csv=None):
    """Dekoduj dane z pliku logu"""
    processor = FileProcessor()
    return processor.process_file(filepath, output_csv)

def monitor_live(port, save_to_file=True):
    """Monitoruj port szeregowy na żywo"""
    monitor = LiveMonitor(port)
    return monitor.run(save_to_file)

def decode_live(port, save_to_file=True, display=True):
    """Dekoduj i wyświetlaj dane na żywo"""
    decoder = LiveDecoder(port)
    return decoder.run(save_to_file, display)