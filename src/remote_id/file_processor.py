#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
File Processor Module
Based on loging.py - przetwarzanie plików logów Remote ID
"""

import binascii
import csv
from pathlib import Path
from typing import Generator, Tuple, Dict, List, Optional
from .decoder import scan_nan_frame


class FileProcessor:
    """Klasa do przetwarzania plików logów Remote ID"""
    
    def __init__(self):
        self.stats = {
            'files_processed': 0,
            'frames_found': 0,
            'complete_sets': 0,
            'errors': 0
        }
    
    def parse_log_file(self, path: Path) -> Generator[Tuple[Dict, str], None, None]:
        """Generator zwracający (meta, payload_hex) dla każdej ramki"""
        current_meta = {}
        payload_hex = None
        inside_frame = False

        try:
            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if "RID_FRAME_START" in line:
                        inside_frame = True
                        current_meta = {}
                        payload_hex = None
                        continue
                    if "RID_FRAME_END" in line:
                        if inside_frame and payload_hex:
                            yield current_meta, payload_hex
                            self.stats['frames_found'] += 1
                        inside_frame = False
                        continue
                    if not inside_frame:
                        continue

                    if "TIMESTAMP=" in line:
                        current_meta["timestamp"] = line.split("TIMESTAMP=")[1]
                    elif "PAYLOAD=" in line:
                        payload_hex = line.split("PAYLOAD=")[1]
        except Exception as e:
            self.stats['errors'] += 1
            raise e

    def extract_full_set(self, decoded_blocks: List[Dict]) -> Optional[Tuple[str, float, float, float]]:
        """Zwraca (uas_id, lat, lon, alt) tylko jeśli w tej samej ramce jest BasicID i LocationVector"""
        uas_id = None
        lat = None
        lon = None
        alt = None

        for block in decoded_blocks:
            if block.get("msg") == "BasicID":
                uas_id = block.get("uas_id")
            elif block.get("msg") == "LocationVector":
                lat = block.get("latitude_deg")
                lon = block.get("longitude_deg")
                alt = block.get("geodetic_alt_m")

        # Zwracamy tylko jeśli oba są dostępne i dane są w normalnym zakresie
        if uas_id and lat is not None and lon is not None and alt is not None:
            if -90 <= lat <= 90 and -180 <= lon <= 180 and -500 <= alt <= 10000:
                self.stats['complete_sets'] += 1
                return uas_id, lat, lon, alt
        return None

    def process_file(self, input_path: str, output_path: Optional[str] = None) -> List[Tuple[str, str, float, float, float]]:
        """
        Przetwórz plik logu i wyciągnij pełne zestawy danych Remote ID
        
        Args:
            input_path: Ścieżka do pliku wejściowego
            output_path: Ścieżka do pliku CSV (opcjonalne)
            
        Returns:
            Lista krotek (timestamp, uas_id, lat, lon, alt)
        """
        in_path = Path(input_path)
        results = []
        
        if not in_path.exists():
            raise FileNotFoundError(f"Plik {input_path} nie istnieje")
        
        # Przetwórz plik
        for meta, payload_hex in self.parse_log_file(in_path):
            try:
                raw = binascii.unhexlify(payload_hex)
                decoded = scan_nan_frame(raw)
                full_set = self.extract_full_set(decoded)
                if full_set:
                    uas_id, lat, lon, alt = full_set
                    timestamp = meta.get('timestamp', '')
                    results.append((timestamp, uas_id, lat, lon, alt))
            except Exception as e:
                self.stats['errors'] += 1
                continue
        
        self.stats['files_processed'] += 1
        
        # Zapisz do CSV jeśli podano ścieżkę
        if output_path:
            self.save_to_csv(results, output_path)
        
        return results
    
    def save_to_csv(self, results: List[Tuple], output_path: str):
        """Zapisz wyniki do pliku CSV"""
        out_path = Path(output_path)
        
        with out_path.open("w", encoding="utf-8", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "uas_id", "latitude_deg", "longitude_deg", "geodetic_alt_m"])
            for row in results:
                writer.writerow(row)
        
        print(f"Zapisano {len(results)} pełnych zestawów danych do {output_path}")
    
    def process_multiple_files(self, file_paths: List[str], output_path: Optional[str] = None) -> List[Tuple]:
        """Przetwórz wiele plików logów"""
        all_results = []
        
        for file_path in file_paths:
            try:
                results = self.process_file(file_path)
                all_results.extend(results)
                print(f"Przetworzono {file_path}: {len(results)} zestawów")
            except Exception as e:
                print(f"Błąd przy przetwarzaniu {file_path}: {e}")
                continue
        
        if output_path and all_results:
            self.save_to_csv(all_results, output_path)
        
        return all_results
    
    def get_stats(self) -> Dict[str, int]:
        """Zwróć statystyki przetwarzania"""
        return self.stats.copy()
    
    def reset_stats(self):
        """Zresetuj statystyki"""
        self.stats = {
            'files_processed': 0,
            'frames_found': 0,
            'complete_sets': 0,
            'errors': 0
        }


# Convenience functions
def decode_from_file(filepath: str, output_csv: Optional[str] = None) -> List[Tuple]:
    """Funkcja pomocnicza do dekodowania z pliku"""
    processor = FileProcessor()
    return processor.process_file(filepath, output_csv)