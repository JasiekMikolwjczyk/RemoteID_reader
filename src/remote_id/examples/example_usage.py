#!/usr/bin/env python3
"""
Przykłady użycia Remote ID Complete Library
"""

import sys
sys.path.append('/Users/janmikolajczyk/nan_sniffer')

from remote_id_complete import (
    decode_from_file, 
    monitor_live, 
    decode_live,
    FileProcessor,
    LiveMonitor,
    LiveDecoder,
    RemoteIDDecoder
)

def example_1_decode_file():
    """Przykład 1: Dekodowanie z pliku"""
    print("📁 Przykład 1: Dekodowanie z pliku")
    print("-" * 40)
    
    # Prosty sposób
    results = decode_from_file(
        "/Users/janmikolajczyk/nan_sniffer/wyniki/wyniki-31.txt",
        "decoded_coordinates.csv"
    )
    
    print(f"✅ Zdekodowano {len(results)} współrzędnych")
    if results:
        print("🎯 Pierwszy wynik:")
        timestamp, uas_id, lat, lon, alt = results[0]
        print(f"   ID: {uas_id}")
        print(f"   GPS: {lat:.6f}°, {lon:.6f}°")
        print(f"   Alt: {alt:.1f}m")

def example_2_advanced_file_processing():
    """Przykład 2: Zaawansowane przetwarzanie pliku"""
    print("\n📊 Przykład 2: Zaawansowane przetwarzanie")
    print("-" * 40)
    
    processor = FileProcessor()
    
    # Przetwórz wiele plików
    files = [
        "/Users/janmikolajczyk/nan_sniffer/wyniki/wyniki-31.txt",
        # "/Users/janmikolajczyk/nan_sniffer/wyniki/wyniki-32.txt", # Dodaj więcej jeśli masz
    ]
    
    all_results = processor.process_multiple_files(files, "all_coordinates.csv")
    
    stats = processor.get_stats()
    print(f"📈 Statystyki:")
    print(f"   Plików: {stats['files_processed']}")
    print(f"   Ramek: {stats['frames_found']}")
    print(f"   Zestawów: {stats['complete_sets']}")

def example_3_live_monitor():
    """Przykład 3: Monitor na żywo (tylko wyświetlanie + zapis)"""
    print("\n🔴 Przykład 3: Monitor na żywo")
    print("-" * 40)
    print("UWAGA: To uruchomi prawdziwy monitor - użyj Ctrl+C aby zatrzymać")
    
    # Uncomment to test with real device:
    # monitor_live("/dev/ttyUSB0", save_to_file=True)

def example_4_live_decoder():
    """Przykład 4: Dekoder na żywo (wyświetlanie + zapis + dekodowanie)"""
    print("\n🎯 Przykład 4: Dekoder na żywo")
    print("-" * 40)
    print("UWAGA: To uruchomi prawdziwy dekoder - użyj Ctrl+C aby zatrzymać")
    
    # Uncomment to test with real device:
    # decoder = decode_live("/dev/ttyUSB0", save_to_file=True, display=True)
    # 
    # # Po zatrzymaniu możesz sprawdzić wyniki:
    # coordinates = decoder.get_coordinates()
    # print(f"Znaleziono {len(coordinates)} współrzędnych")
    # 
    # # Zapisz do CSV
    # if coordinates:
    #     decoder.save_coordinates_to_csv("live_coordinates.csv")

def example_5_custom_usage():
    """Przykład 5: Niestandardowe użycie"""
    print("\n⚙️ Przykład 5: Niestandardowe użycie")
    print("-" * 40)
    
    # Własny dekoder
    decoder = RemoteIDDecoder()
    
    # Przykład dekodowania pojedynczego bloku (25 bajtów)
    # Ten hex to prawdziwy blok z pliku wyniki-31.txt
    hex_block = "0D4145524F424954535F49444D4501018CDD9EFA0BBC0D89F2190602"
    
    try:
        import binascii
        raw_bytes = binascii.unhexlify(hex_block)
        if len(raw_bytes) == 25:
            result = decoder.decode_block(raw_bytes)
            print("🔍 Zdekodowany blok:")
            print(f"   Typ: {result.get('msg', 'Unknown')}")
            if 'uas_id' in result:
                print(f"   UAS ID: {result['uas_id']}")
        else:
            print(f"❌ Nieprawidłowa długość: {len(raw_bytes)} (oczekiwano 25)")
    except Exception as e:
        print(f"❌ Błąd dekodowania: {e}")
    
    # Statystyki dekodera
    stats = decoder.get_stats()
    print(f"📊 Statystyki dekodera: {stats}")

if __name__ == "__main__":
    example_1_decode_file()
    example_2_advanced_file_processing()
    example_3_live_monitor()
    example_4_live_decoder()
    example_5_custom_usage()
    
    print(f"\n🎉 Wszystkie przykłady zakończone!")