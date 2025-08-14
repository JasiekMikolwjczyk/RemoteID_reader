#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Live Decoder Module
Kombinacja monitorowania na żywo + dekodowania Remote ID w czasie rzeczywistym
"""

import binascii
from typing import Dict, List, Optional
from .live_monitor import LiveMonitor
from .decoder import RemoteIDDecoder, scan_nan_frame


class LiveDecoder:
    """Klasa łącząca monitoring na żywo z dekodowaniem Remote ID"""
    
    def __init__(self, port: str, baudrate: int = 115200):
        self.monitor = LiveMonitor(port, baudrate)
        self.decoder = RemoteIDDecoder()
        self.decoded_frames = []
        self.coordinates = []
        
        # Ustaw callbacki
        self.monitor.set_frame_callback(self._on_frame_received)
    
    def _on_frame_received(self, frame_data: Dict):
        """Callback wywoływany przy otrzymaniu ramki - dekoduje ją"""
        payload = frame_data.get('payload', '')
        if not payload:
            return
        
        try:
            # Dekoduj payload hex na bajty
            raw_bytes = binascii.unhexlify(payload)
            
            # Skanuj ramkę w poszukiwaniu bloków Remote ID
            decoded_blocks = self.decoder.scan_frame(raw_bytes)
            
            if decoded_blocks:
                # Dodaj metadane ramki
                frame_info = {
                    'timestamp': frame_data.get('timestamp', ''),
                    'transport': frame_data.get('transport', ''),
                    'mac': frame_data.get('mac', ''),
                    'rssi': frame_data.get('rssi', ''),
                    'raw_payload': payload,
                    'decoded_blocks': decoded_blocks
                }
                
                self.decoded_frames.append(frame_info)
                
                # Wyciągnij koordinaty jeśli dostępne
                coordinates = self._extract_coordinates(decoded_blocks)
                if coordinates:
                    coord_info = {
                        'timestamp': frame_data.get('timestamp', ''),
                        'mac': frame_data.get('mac', ''),
                        **coordinates
                    }
                    self.coordinates.append(coord_info)
                
        except Exception as e:
            print(f"⚠️ Błąd dekodowania ramki: {e}")
    
    def _extract_coordinates(self, blocks: List[Dict]) -> Optional[Dict]:
        """Wyciągnij współrzędne GPS z zdekodowanych bloków"""
        basic_id = None
        location = None
        
        for block in blocks:
            if block.get("msg") == "BasicID":
                basic_id = {
                    'uas_id': block.get('uas_id', ''),
                    'ua_type': block.get('ua_type_name', ''),
                    'id_type': block.get('id_type_name', '')
                }
            elif block.get("msg") == "LocationVector":
                location = {
                    'latitude': block.get('latitude_deg'),
                    'longitude': block.get('longitude_deg'),
                    'altitude': block.get('geodetic_alt_m'),
                    'speed': block.get('speed_mps'),
                    'direction': block.get('direction_deg'),
                    'vertical_speed': block.get('vertical_speed_mps')
                }
        
        # Zwróć tylko jeśli mamy kompletne dane
        if basic_id and location and location['latitude'] is not None:
            return {**basic_id, **location}
        return None
    
    def display_decoded_frame(self, frame_info: Dict):
        """Wyświetl zdekodowaną ramkę"""
        print(f"\n🎯 DECODED Remote ID Frame")
        print(f"   Time: {frame_info.get('timestamp', 'Unknown')}")
        print(f"   MAC: {frame_info.get('mac', 'Unknown')}")
        print(f"   Transport: {frame_info.get('transport', 'Unknown')}")
        print(f"   RSSI: {frame_info.get('rssi', 'Unknown')} dBm")
        
        for i, block in enumerate(frame_info.get('decoded_blocks', [])):
            msg_type = block.get('msg', 'Unknown')
            print(f"   Block {i+1}: {msg_type}")
            
            if msg_type == "BasicID":
                print(f"      UAS ID: {block.get('uas_id', 'N/A')}")
                print(f"      UA Type: {block.get('ua_type_name', 'N/A')}")
            elif msg_type == "LocationVector":
                lat = block.get('latitude_deg')
                lon = block.get('longitude_deg') 
                alt = block.get('geodetic_alt_m')
                spd = block.get('speed_mps')
                if lat is not None and lon is not None:
                    print(f"      📍 GPS: {lat:.7f}°, {lon:.7f}°")
                    print(f"      🏔️  Alt: {alt:.1f}m")
                    print(f"      🏃 Speed: {spd:.1f} m/s")
            elif msg_type == "SelfID":
                print(f"      Text: {block.get('text', 'N/A')}")
            elif msg_type == "OperatorID":
                print(f"      Op ID: {block.get('operator_id', 'N/A')}")
    
    def run(self, save_to_file: bool = True, display: bool = True, 
            decode_live: bool = True, custom_filename: Optional[str] = None) -> bool:
        """
        Uruchom dekoder na żywo
        
        Args:
            save_to_file: Zapisuj surowe dane do pliku
            display: Wyświetlaj na ekranie
            decode_live: Dekoduj i wyświetlaj zdekodowane dane
            custom_filename: Nazwa pliku (opcjonalna)
        """
        
        if decode_live and display:
            # Dodaj callback do wyświetlania zdekodowanych ramek
            original_callback = self.monitor.on_frame_callback
            def enhanced_callback(frame_data):
                if original_callback:
                    original_callback(frame_data)
                # Poczekaj chwilę na dekodowanie
                if self.decoded_frames:
                    latest = self.decoded_frames[-1]
                    if latest.get('raw_payload') == frame_data.get('payload'):
                        self.display_decoded_frame(latest)
            
            self.monitor.set_frame_callback(enhanced_callback)
        
        return self.monitor.run(save_to_file, display, custom_filename)
    
    def stop(self):
        """Zatrzymaj dekoder"""
        self.monitor.stop()
    
    def get_decoded_frames(self) -> List[Dict]:
        """Zwróć wszystkie zdekodowane ramki"""
        return self.decoded_frames.copy()
    
    def get_coordinates(self) -> List[Dict]:
        """Zwróć wszystkie wyciągnięte współrzędne"""
        return self.coordinates.copy()
    
    def save_coordinates_to_csv(self, filename: str):
        """Zapisz współrzędne do pliku CSV"""
        import csv
        
        if not self.coordinates:
            print("❌ Brak współrzędnych do zapisania")
            return
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'timestamp', 'mac', 'uas_id', 'ua_type', 'latitude', 
                'longitude', 'altitude', 'speed', 'direction'
            ])
            writer.writeheader()
            writer.writerows(self.coordinates)
        
        print(f"✅ Zapisano {len(self.coordinates)} współrzędnych do {filename}")
    
    def get_stats(self) -> Dict:
        """Zwróć statystyki"""
        monitor_stats = self.monitor.get_stats()
        decoder_stats = self.decoder.get_stats()
        
        return {
            'monitor': monitor_stats,
            'decoder': decoder_stats,
            'decoded_frames': len(self.decoded_frames),
            'coordinates_found': len(self.coordinates)
        }


# Convenience function
def decode_live(port: str, save_to_file: bool = True, display: bool = True) -> LiveDecoder:
    """Funkcja pomocnicza do dekodowania na żywo"""
    decoder = LiveDecoder(port)
    decoder.run(save_to_file, display, decode_live=True)
    return decoder