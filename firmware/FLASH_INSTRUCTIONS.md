# ESP32-S3 Remote ID Sniffer - Flashing Instructions

This directory contains the firmware for ESP32-S3 Remote ID Sniffer that automatically scans for Wi-Fi NAN and BLE Remote ID broadcasts.

## Firmware Features v2.0

- **Automatic Scanning**: Continuously scans Wi-Fi NAN and BLE for Remote ID broadcasts
- **Status Pins Control**: MSG, WARN, READY pins all set to LOW state always  
- **LED Status Indicator**:
  - Slow blink (1Hz): System active and scanning
  - Fast blink (5Hz): Remote ID frames detected (for 3 seconds after last frame)
- **Raw Frame Output**: Transmits all detected frames in structured format for computer processing

## Hardware Requirements

- **ESP32-S3 DevKit N8** (or compatible board)
- USB-C cable for flashing and power
- Computer with Python 3.x

## Firmware Files

- `esp32s3-remote-id-sniffer.bin` - Main firmware application
- `bootloader.bin` - ESP32-S3 bootloader 
- `partition-table.bin` - Partition table configuration

## Installation

### Option 1: Quick Flash (App Only)
```bash
# Install esptool if not already installed
pip install esptool

# Connect ESP32-S3 via USB-C and find the port
# macOS: /dev/cu.usbmodem* or /dev/cu.usbserial*
# Linux: /dev/ttyUSB* or /dev/ttyACM*
# Windows: COM3, COM4, etc.

# Flash the application only (fastest method)
esptool.py --port /dev/cu.usbmodem14101 --baud 460800 write_flash 0x10000 esp32s3-remote-id-sniffer.bin
```

### Option 2: Full Flash (Recommended)
```bash
# Erase existing flash (optional but recommended)
esptool.py --port /dev/cu.usbmodem14101 erase_flash

# Flash bootloader, partition table, and application
esptool.py --port /dev/cu.usbmodem14101 --baud 460800 write_flash \
  0x0 bootloader.bin \
  0x8000 partition-table.bin \
  0x10000 esp32s3-remote-id-sniffer.bin
```

### Option 3: Auto-detect Port
```bash
# Let esptool auto-detect the port
esptool.py --baud 460800 write_flash \
  0x0 bootloader.bin \
  0x8000 partition-table.bin \
  0x10000 esp32s3-remote-id-sniffer.bin
```

## Usage

1. **Flash the firmware** using one of the methods above
2. **Reset the ESP32-S3** (press reset button or reconnect USB)
3. **Connect via serial** at 115200 baud to see output:
   ```bash
   # macOS/Linux
   screen /dev/cu.usbmodem14101 115200
   
   # Or use the Python library
   python3 -c "from remote_id import monitor_live; monitor_live('/dev/cu.usbmodem14101')"
   ```
4. **Observe LED status**:
   - Slow blink (1 second intervals): System is active and scanning
   - Fast blink (200ms intervals): Remote ID frames are being detected

## Expected Output

The firmware will automatically start scanning and output structured data:

```
=================================================
🚁 ESP32-S3 Remote ID Sniffer v2.0
   Automatic Wi-Fi NAN & BLE Scanner  
=================================================

RID_FRAME_START
TIMESTAMP=1642678234567
TRANSPORT=BLE
MAC=84:F7:03:28:EC:1C
RSSI=-45
LENGTH=27
PAYLOAD=0D4145524F424954535F49444D450101...
RID_FRAME_END
```

## Integration with Python Library

The firmware is designed to work with the Remote ID Python library:

```bash
# Install the library
pip install git+https://github.com/JasiekMikolwjczyk/RemoteID_reader.git

# Monitor and decode in real-time
remote-id-live /dev/cu.usbmodem14101 --csv coordinates.csv

# Or use Python API
python3 -c "
from remote_id import decode_live
decoder = decode_live('/dev/cu.usbmodem14101')
"
```

## Troubleshooting

### Flash Errors
- **Permission denied**: Use `sudo` on Linux/macOS or run terminal as Administrator on Windows
- **Port not found**: Check USB connection, try different USB cable
- **Flash failed**: Try erasing flash first with `esptool.py --port PORT erase_flash`

### No Output After Flash
- Check baud rate (115200)
- Press reset button on ESP32-S3
- Verify correct port connection
- Try different terminal program

### Finding Serial Port
```bash
# macOS
ls /dev/cu.*

# Linux  
ls /dev/ttyUSB* /dev/ttyACM*

# Windows (in Command Prompt)
mode
```

### Boot Mode Issues
If ESP32-S3 doesn't enter flashing mode:
1. Hold **BOOT** button
2. Press **RESET** button  
3. Release **RESET** button
4. Release **BOOT** button
5. Try flashing again

## Additional Firmware Features

- ✅ **Automatic startup** - Begins scanning immediately on power-up
- ✅ **Dual protocol** - Scans both Wi-Fi NAN and BLE simultaneously  
- ✅ **Raw frame output** - Structured data format for computer processing
- ✅ **Real-time streaming** - Continuous output via USB serial
- ✅ **Low latency** - Optimized for fast frame detection and transmission
- ✅ **ASTM F3411 compatible** - Supports standard Remote ID message formats
- ✅ **Visual feedback** - LED indicates system status and detection activity
- ✅ **Hardware integration** - Status pins for external monitoring systems

## Technical Details

- **Target**: ESP32-S3 (dual-core, Wi-Fi + Bluetooth)
- **Flash size**: 8MB (minimum 4MB required)
- **RAM**: Uses PSRAM for packet buffers
- **Wi-Fi**: Channel 6 monitoring (configurable in source)
- **BLE**: Continuous advertisement scanning
- **Serial**: 115200 baud, 8N1
- **Power**: USB-powered, ~100mA typical

## Building from Source

If you want to modify the firmware, see the source code in the `source/` directory and follow ESP-IDF build instructions.

### GPIO Pin Configuration

Based on ESP32_S3_MINI_V1 schematic:
- **REMID_RDY_PIN**: GPIO 42 → mPCIe pin 42 (READY signal)
- **REMID_WARN_PIN**: GPIO 44 → mPCIe pin 44 (WARNING signal) 
- **REMID_MSG_PIN**: GPIO 46 → mPCIe pin 46 (MESSAGE signal)
- **STATUS_LED_PIN**: GPIO 2 → Status LED

All status pins are set to LOW state and remain LOW during operation.

## Support

For issues with the firmware or Python library:
- [GitHub Issues](https://github.com/JasiekMikolwjczyk/RemoteID_reader/issues)
- Check serial output for error messages
- Verify hardware connections