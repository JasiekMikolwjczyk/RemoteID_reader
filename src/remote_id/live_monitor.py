#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Live Monitor Module  
Based on raw_data_display.py - monitoring portu szeregowego na żywo
"""

import serial
import os
import time
from datetime import datetime
from typing import Dict, Optional, Callable
from pathlib import Path


class LiveMonitor:
    """Klasa do monitorowania portu szeregowego na żywo"""
    
    def __init__(self, port: str, baudrate: int = 115200):
        self.port = port
        self.baudrate = baudrate
        self.serial_conn = None
        self.output_file = None
        self.file_counter = 1
        self.frame_count = 0
        self.running = False
        
        # Callbacks
        self.on_frame_callback = None
        self.on_data_callback = None
        
    def set_frame_callback(self, callback: Callable[[Dict], None]):
        """Ustaw callback wywoływany przy każdej ramce"""
        self.on_frame_callback = callback
    
    def set_data_callback(self, callback: Callable[[str], None]):
        """Ustaw callback wywoływany przy każdej linii danych"""
        self.on_data_callback = callback
        
    def create_output_file(self, custom_path: Optional[str] = None) -> str:
        """Utwórz plik wyjściowy z incrementalną numeracją"""
        if custom_path:
            output_path = Path(custom_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            filename = str(output_path)
        else:
            # Domyślnie tworzy w katalogu wyniki/
            os.makedirs("wyniki", exist_ok=True)
            while True:
                filename = f"wyniki/wyniki-{self.file_counter}.txt"
                if not os.path.exists(filename):
                    break
                self.file_counter += 1
        
        self.output_file = open(filename, 'w', encoding='utf-8')
        self.output_file.write("# Remote ID Raw Frames Log\n")
        self.output_file.write(f"# Created: {datetime.now().strftime('%a %b %d %H:%M:%S %Y')}\n")
        self.output_file.write("# Format: [TIMESTAMP] RAW_LINE\n")
        self.output_file.write("# Decoded coordinates will be appended at the end\n\n")
        
        return filename
    
    def connect(self) -> bool:
        """Połącz z portem szeregowym ESP32"""
        try:
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=1)
            print(f"🔌 Connected to {self.port} at {self.baudrate} baud")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to {self.port}: {e}")
            return False
    
    def display_frame_info(self, frame_data: Dict):
        """Wyświetl informacje o ramce w czasie rzeczywistym"""
        print(f"\n🚁 Remote ID Frame #{self.frame_count + 1}")
        print(f"   Transport: {frame_data.get('transport', 'Unknown')}")
        print(f"   MAC: {frame_data.get('mac', 'Unknown')}")
        print(f"   RSSI: {frame_data.get('rssi', 'Unknown')} dBm")
        print(f"   Length: {frame_data.get('length', 0)} bytes")
        
        payload = frame_data.get('payload', '')
        if payload:
            print(f"   Payload: {payload[:40]}{'...' if len(payload) > 40 else ''}")
    
    def parse_frame(self, lines: list) -> Dict:
        """Parsuj dane ramki z wyjścia ESP32"""
        frame_data = {}
        
        for line in lines:
            line = line.strip()
            if '=' in line:
                key, value = line.split('=', 1)
                if key == 'TIMESTAMP':
                    frame_data['timestamp'] = value
                elif key == 'TRANSPORT':
                    frame_data['transport'] = value
                elif key == 'MAC':
                    frame_data['mac'] = value
                elif key == 'RSSI':
                    frame_data['rssi'] = value
                elif key == 'LENGTH':
                    frame_data['length'] = value
                elif key == 'PAYLOAD':
                    frame_data['payload'] = value
        
        return frame_data
    
    def run(self, save_to_file: bool = True, display: bool = True, custom_filename: Optional[str] = None) -> bool:
        """
        Główna pętla monitorowania
        
        Args:
            save_to_file: Czy zapisywać do pliku
            display: Czy wyświetlać na ekranie  
            custom_filename: Nazwa pliku (opcjonalna)
        """
        if not self.connect():
            return False
        
        filename = None
        if save_to_file:
            filename = self.create_output_file(custom_filename)
            if display:
                print(f"📁 Created output file: {filename}")
        
        if display:
            print(f"🎯 Live Monitor - Monitoring {self.port}")
            print("📊 Press Ctrl+C to stop")
            print("💡 Waiting for Remote ID devices...\n")
        
        frame_lines = []
        in_frame = False
        self.running = True
        
        try:
            while self.running:
                try:
                    line = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                    
                    if not line:
                        continue
                    
                    # Callback na surowe dane
                    if self.on_data_callback:
                        self.on_data_callback(line)
                    
                    # Zapisz do pliku z timestampem
                    if save_to_file and self.output_file:
                        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        self.output_file.write(f"[{timestamp}] {line}\n")
                        self.output_file.flush()
                    
                    # Parsuj ramki Remote ID
                    if line == "RID_FRAME_START":
                        in_frame = True
                        frame_lines = []
                        if display:
                            print(f"🔍 Detecting Remote ID frame...", end="", flush=True)
                    elif line == "RID_FRAME_END" and in_frame:
                        in_frame = False
                        frame_data = self.parse_frame(frame_lines)
                        
                        if display:
                            print(" ✅")  # Complete the detection line
                            self.display_frame_info(frame_data)
                            print(f"   RAW: {frame_data.get('payload', 'No payload')}")
                        
                        # Callback na ramkę
                        if self.on_frame_callback:
                            self.on_frame_callback(frame_data)
                        
                        self.frame_count += 1
                        frame_lines = []
                    elif in_frame:
                        frame_lines.append(line)
                    elif display and ("Remote ID detected" in line or "RID" in line):
                        # Pokaż wiadomości ESP32 związane z Remote ID
                        print(f"🚁 {line}")
                    elif display and any(keyword in line.lower() for keyword in ['error', 'warning', 'failed']):
                        print(f"⚠️  {line}")
                
                except UnicodeDecodeError:
                    continue
                except KeyboardInterrupt:
                    break
        
        except Exception as e:
            if display:
                print(f"❌ Error: {e}")
            return False
        
        finally:
            self.running = False
            if display:
                print(f"\n📊 Total frames captured: {self.frame_count}")
                if filename:
                    print(f"📁 Data saved to: {filename}")
            
            if self.output_file:
                self.output_file.close()
                self.output_file = None
            if self.serial_conn:
                self.serial_conn.close()
                self.serial_conn = None
        
        return True
    
    def stop(self):
        """Zatrzymaj monitoring"""
        self.running = False
    
    def get_stats(self) -> Dict[str, int]:
        """Zwróć statystyki monitorowania"""
        return {
            'frames_captured': self.frame_count,
            'is_running': self.running
        }


# Convenience function
def monitor_live(port: str, save_to_file: bool = True, display: bool = True) -> bool:
    """Funkcja pomocnicza do monitorowania na żywo"""
    monitor = LiveMonitor(port)
    return monitor.run(save_to_file, display)