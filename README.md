# Remote ID Python

[![PyPI version](https://badge.fury.io/py/remote-id-python.svg)](https://badge.fury.io/py/remote-id-python)
[![Python versions](https://img.shields.io/pypi/pyversions/remote-id-python.svg)](https://pypi.org/project/remote-id-python/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Comprehensive Python library for Remote ID drone data decoding and monitoring**

Remote ID Python provides a complete toolkit for working with drone Remote ID broadcasts according to ASTM F3411 standard. It supports both BLE and Wi-Fi NAN transport protocols.

## Features

- 🚁 **Decode Remote ID blocks** - BasicID, Location/Vector, Self ID, System, Operator ID
- 📡 **Live monitoring** - Real-time capture from ESP32 or other hardware
- 📁 **File processing** - Batch decode from log files  
- 🎯 **Live decoding** - Real-time decode with display and logging
- 📊 **CSV export** - Export coordinates and drone data
- 🔧 **CLI tools** - Command-line utilities for common tasks

## Installation

```bash
pip install remote-id-python
```

## Quick Start

### Decode from file
```python
from remote_id import decode_from_file

# Decode Remote ID data from log file
results = decode_from_file("drone_log.txt", "coordinates.csv")
print(f"Found {len(results)} drone positions")
```

### Live monitoring
```python  
from remote_id import monitor_live

# Monitor serial port and save to file
monitor_live("/dev/ttyUSB0", save_to_file=True)
```

### Live decoding
```python
from remote_id import decode_live

# Monitor + decode + display in real-time
decoder = decode_live("/dev/ttyUSB0")
coordinates = decoder.get_coordinates()
```

### Advanced usage
```python
from remote_id import RemoteIDDecoder, FileProcessor

# Custom decoder
decoder = RemoteIDDecoder()
result = decoder.decode_block(raw_25_bytes)

# Batch file processing  
processor = FileProcessor()
results = processor.process_multiple_files(["log1.txt", "log2.txt"])
```

## CLI Tools

After installation, these commands are available:

```bash
# Decode from file
remote-id-decode input.txt --output coordinates.csv

# Monitor live data
remote-id-monitor /dev/ttyUSB0 --save wyniki.txt

# Live decode with display
remote-id-live /dev/ttyUSB0 --display --save
```

## Supported Message Types

| Type | Description | Decoded Fields |
|------|-------------|---------------|
| 0x0 | Basic ID | UAS ID, UA Type, ID Type |
| 0x1 | Location/Vector | GPS coordinates, altitude, speed, direction |  
| 0x3 | Self ID | Operator description text |
| 0x4 | System | Operator location, system status |
| 0x5 | Operator ID | Operator identification |
| 0xF | Message Pack | Multiple packed messages |

## Hardware Compatibility

- ✅ ESP32 with Remote ID sniffer firmware
- ✅ BLE receivers
- ✅ Wi-Fi NAN capable devices  
- ✅ Serial/USB connected hardware

## Data Formats

### Input formats:
- Raw 25-byte Remote ID blocks (hex)
- ESP32 serial output logs
- Structured log files with RID_FRAME_START/END markers

### Output formats:
- Python dictionaries with decoded data
- CSV files with coordinates and metadata
- Real-time display with emoji formatting

## Examples

See the `examples/` directory for complete usage examples:

- `decode_file.py` - File decoding examples
- `live_monitor.py` - Live monitoring setup  
- `custom_decoder.py` - Advanced decoder usage

## Development

```bash
# Clone repository
git clone https://github.com/janmikolajczyk/remote-id-python.git
cd remote-id-python

# Install in development mode
pip install -e .[dev]

# Run tests
pytest

# Format code
black src/ tests/
isort src/ tests/

# Type check
mypy src/
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)  
5. Open a Pull Request

## Acknowledgments

- Based on ASTM F3411 Remote ID standard
- ESP32 Remote ID sniffer community
- Original decoder implementations by the nan_sniffer project

## Support

- 📖 [Documentation](https://remote-id-python.readthedocs.io/)
- 🐛 [Bug Reports](https://github.com/janmikolajczyk/remote-id-python/issues)
- 💬 [Discussions](https://github.com/janmikolajczyk/remote-id-python/discussions)