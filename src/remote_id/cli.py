#!/usr/bin/env python3
"""
Command Line Interface for Remote ID Python Library
"""

import argparse
import sys
from pathlib import Path
from .file_processor import decode_from_file
from .live_monitor import monitor_live
from .live_decoder import decode_live


def decode_command():
    """CLI command for decoding files"""
    parser = argparse.ArgumentParser(description='Decode Remote ID data from file')
    parser.add_argument('input', help='Input log file path')
    parser.add_argument('--output', '-o', help='Output CSV file path')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        print(f"📁 Decoding file: {args.input}")
    
    try:
        results = decode_from_file(args.input, args.output)
        
        if args.verbose:
            print(f"✅ Decoded {len(results)} coordinate sets")
            if results:
                print("🎯 Sample results:")
                for i, (timestamp, uas_id, lat, lon, alt) in enumerate(results[:3]):
                    print(f"   {i+1}. {uas_id} - {lat:.6f}°, {lon:.6f}° ({alt:.1f}m)")
        else:
            print(f"Decoded {len(results)} coordinate sets")
            
        if args.output:
            print(f"Saved to: {args.output}")
            
    except FileNotFoundError:
        print(f"❌ File not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


def monitor_command():
    """CLI command for live monitoring"""
    parser = argparse.ArgumentParser(description='Monitor Remote ID data from serial port')
    parser.add_argument('port', help='Serial port (e.g., /dev/ttyUSB0)')
    parser.add_argument('--baudrate', '-b', type=int, default=115200, help='Baud rate (default: 115200)')
    parser.add_argument('--save', '-s', help='Save to file (default: wyniki/wyniki-N.txt)')
    parser.add_argument('--no-display', action='store_true', help='Disable display output')
    
    args = parser.parse_args()
    
    print(f"🔌 Monitoring {args.port} at {args.baudrate} baud")
    print("Press Ctrl+C to stop")
    
    try:
        from .live_monitor import LiveMonitor
        monitor = LiveMonitor(args.port, args.baudrate)
        save_file = args.save if args.save else True
        display = not args.no_display
        monitor.run(save_to_file=save_file, display=display)
        
    except KeyboardInterrupt:
        print("\n📊 Monitoring stopped")
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


def live_command():
    """CLI command for live decoding"""
    parser = argparse.ArgumentParser(description='Live decode Remote ID data from serial port')
    parser.add_argument('port', help='Serial port (e.g., /dev/ttyUSB0)')
    parser.add_argument('--baudrate', '-b', type=int, default=115200, help='Baud rate (default: 115200)')
    parser.add_argument('--save', '-s', help='Save raw data to file')
    parser.add_argument('--csv', '-c', help='Save coordinates to CSV file')
    parser.add_argument('--no-display', action='store_true', help='Disable display output')
    
    args = parser.parse_args()
    
    print(f"🎯 Live decoding from {args.port} at {args.baudrate} baud")
    print("Press Ctrl+C to stop")
    
    try:
        from .live_decoder import LiveDecoder
        decoder = LiveDecoder(args.port, args.baudrate)
        
        save_file = args.save if args.save else True
        display = not args.no_display
        
        decoder.run(save_to_file=save_file, display=display, decode_live=True)
        
        # Save coordinates if requested
        if args.csv:
            coordinates = decoder.get_coordinates()
            if coordinates:
                decoder.save_coordinates_to_csv(args.csv)
            else:
                print("❌ No coordinates found to save")
        
        # Show stats
        stats = decoder.get_stats()
        print(f"\n📊 Statistics:")
        print(f"   Frames captured: {stats['monitor']['frames_captured']}")
        print(f"   Decoded frames: {stats['decoded_frames']}")
        print(f"   Coordinates found: {stats['coordinates_found']}")
        
    except KeyboardInterrupt:
        print("\n📊 Live decoding stopped")
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    print("Use specific commands:")
    print("  remote-id-decode   - Decode from file")
    print("  remote-id-monitor  - Monitor live data") 
    print("  remote-id-live     - Live decode with display")