#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Remote ID Decoder Module
Based on rid_decoder.py - dekodowanie 25-bajtowych bloków Remote ID
"""

import argparse
import binascii
import struct
from typing import Dict, Any, List, Tuple
import string


# ------------------------------
# Helpers
# ------------------------------

def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

def _to_int8(b: bytes) -> int:
    return struct.unpack('<b', b)[0]

def _to_uint8(b: bytes) -> int:
    return b[0]

def _to_int16(b: bytes) -> int:
    return struct.unpack('<h', b)[0]

def _to_uint16(b: bytes) -> int:
    return struct.unpack('<H', b)[0]

def _to_int32(b: bytes) -> int:
    return struct.unpack('<i', b)[0]

def _to_uint32(b: bytes) -> int:
    return struct.unpack('<I', b)[0]

def _to_ascii(b: bytes) -> str:
    s = b.decode('ascii', errors='ignore')
    return s.rstrip('\x00').strip()


# ------------------------------
# Constants
# ------------------------------

BASIC_ID_TYPES = {
    0: "None",
    1: "Serial number", 
    2: "CAA registration ID",
    3: "UTM assigned UUID",
    4: "Specific Session ID",
}

UA_TYPES = {
    0: "None/Not declared",
    1: "Aeroplane (fixed wing)",
    2: "Helicopter/Multirotor", 
    3: "Gyroplane",
    4: "Hybrid lift (VTOL)",
    5: "Ornithopter",
    6: "Glider",
    7: "Kite",
    8: "Free balloon",
    9: "Captive balloon",
    10: "Airship (blimp)",
    11: "Free fall/parachute (unpowered)",
    12: "Rocket",
    13: "Tethered powered aircraft",
    14: "Ground obstacle",
    15: "Other",
}

HEIGHT_TYPE = {0: "AGL", 1: "WGS84", 2: "Reserved", 3: "Reserved"}


# ------------------------------
# Header parsing
# ------------------------------

def parse_header(b: bytes) -> Dict[str, Any]:
    if len(b) != 1:
        raise ValueError("Header must be 1 byte")
    v = b[0]
    msg_type = (v >> 4) & 0x0F
    version = v & 0x0F
    return {"type": msg_type, "version": version}


# ------------------------------
# Message decoders
# ------------------------------

def decode_basic_id(p: bytes) -> Dict[str, Any]:
    if len(p) != 24:
        raise ValueError("Basic ID payload must be 24 bytes")
    id_type = _to_uint8(p[0:1])
    ua_type = _to_uint8(p[1:2])
    uas_id = _to_ascii(p[2:22])
    return {
        "msg": "BasicID",
        "id_type": id_type,
        "id_type_name": BASIC_ID_TYPES.get(id_type, "Unknown"),
        "ua_type": ua_type,
        "ua_type_name": UA_TYPES.get(ua_type, "Unknown"),
        "uas_id": uas_id,
    }

def _decode_speed(ev: int, mult_flag: int) -> float:
    if mult_flag == 0:
        return 0.25 * ev
    else:
        return 0.25 * (ev + 255)

def decode_location_vector(p: bytes) -> Dict[str, Any]:
    if len(p) != 24:
        raise ValueError("Location/Vector payload must be 24 bytes")
    flags = _to_uint8(p[0:1])
    speed_mult = flags & 0x01
    dir_seg = (flags >> 1) & 0x01
    height_type_bits = (flags >> 2) & 0x03
    op_status = (flags >> 4) & 0x0F

    dir_raw = _to_uint8(p[1:2])
    direction = dir_raw + (180 if dir_seg else 0)

    speed_ev = _to_uint8(p[2:3])
    speed = _decode_speed(speed_ev, speed_mult)

    vs_raw = _to_int8(p[3:4])
    vert_speed = 0.5 * vs_raw

    lat_raw = _to_int32(p[4:8])
    lon_raw = _to_int32(p[8:12])
    latitude = lat_raw * 1e-7
    longitude = lon_raw * 1e-7

    p_alt_ev = _to_int16(p[12:14])
    g_alt_ev = _to_int16(p[14:16])
    pressure_alt_m = (0.5 * p_alt_ev) - 1000.0
    geodetic_alt_m = (0.5 * g_alt_ev) - 1000.0

    ts_ev = _to_uint16(p[18:20])
    timestamp_s = 0.1 * ts_ev

    tail_raw = p[20:24]

    return {
        "msg": "LocationVector",
        "op_status": op_status,
        "height_type": HEIGHT_TYPE.get(height_type_bits, "Unknown"),
        "direction_deg": float(direction),
        "speed_mps": round(speed, 2),
        "vertical_speed_mps": round(vert_speed, 2),
        "latitude_deg": round(latitude, 7),
        "longitude_deg": round(longitude, 7),
        "pressure_alt_m": round(pressure_alt_m, 1),
        "geodetic_alt_m": round(geodetic_alt_m, 1),
        "timestamp_s_in_hour": round(timestamp_s, 1),
        "tail_raw_hex": binascii.hexlify(tail_raw).decode(),
    }

def decode_self_id(p: bytes) -> Dict[str, Any]:
    if len(p) != 24:
        raise ValueError("Self ID payload must be 24 bytes")
    desc_type = _to_uint8(p[0:1])
    text = _to_ascii(p[1:24])
    return {
        "msg": "SelfID",
        "description_type": desc_type,
        "text": text,
    }

def decode_system(p: bytes) -> Dict[str, Any]:
    if len(p) != 24:
        raise ValueError("System payload must be 24 bytes")
    sys_flags = _to_uint8(p[0:1])
    out = {"msg": "System", "flags": sys_flags}
    
    try:
        op_lat = _to_int32(p[1:5]) * 1e-7
        op_lon = _to_int32(p[5:9]) * 1e-7
        op_alt_ev = _to_int16(p[9:11])
        op_alt_m = 0.5 * op_alt_ev - 1000.0
        out.update({
            "operator_lat_deg": round(op_lat, 7),
            "operator_lon_deg": round(op_lon, 7),
            "operator_alt_m": round(op_alt_m, 1),
        })
    except Exception:
        pass
    
    out["raw_tail_hex"] = binascii.hexlify(p).decode()
    return out

def decode_operator_id(p: bytes) -> Dict[str, Any]:
    if len(p) != 24:
        raise ValueError("Operator ID payload must be 24 bytes")
    op_type = _to_uint8(p[0:1])
    op_id = _to_ascii(p[1:21])
    return {
        "msg": "OperatorID",
        "operator_id_type": op_type,
        "operator_id": op_id,
    }

def decode_message_pack(p: bytes) -> Dict[str, Any]:
    if len(p) != 24:
        raise ValueError("Message Pack payload must be 24 bytes")
    return {
        "msg": "MessagePack",
        "note": "MessagePack payload is transport‑specific; returning raw for this 24‑byte fragment.",
        "raw_payload_hex": binascii.hexlify(p).decode(),
    }


# ------------------------------
# Validation functions
# ------------------------------

def _is_printable_ascii(s: str) -> bool:
    if not s:
        return False
    allowed = set(string.ascii_letters + string.digits + " -_./:+#@")
    return all(ch in allowed for ch in s)

def _is_plausible_basic(d: dict) -> bool:
    s = d.get("uas_id", "")
    return _is_printable_ascii(s) and len(s) >= 6

def _is_plausible_loc(d: dict) -> bool:
    lat = d.get("latitude_deg")
    lon = d.get("longitude_deg")
    spd = d.get("speed_mps")
    return (
        isinstance(lat, float) and -90.5 <= lat <= 90.5 and
        isinstance(lon, float) and -180.5 <= lon <= 180.5 and
        isinstance(spd, float) and 0 <= spd <= 150
    )

def _is_plausible_op(d: dict) -> bool:
    s = d.get("operator_id", "")
    return _is_printable_ascii(s) and len(s) >= 4


# ------------------------------
# Main decoder
# ------------------------------

DECODERS = {
    0x0: decode_basic_id,
    0x1: decode_location_vector,
    0x3: decode_self_id,
    0x4: decode_system,
    0x5: decode_operator_id,
    0xF: decode_message_pack,
}

def decode_block(block: bytes) -> Dict[str, Any]:
    """Dekoduj pojedynczy 25-bajtowy blok Remote ID"""
    if len(block) != 25:
        raise ValueError(f"Block must be 25 bytes, got {len(block)}")
    hdr = parse_header(block[0:1])
    payload = block[1:25]
    msg_type = hdr["type"]
    decoder = DECODERS.get(msg_type)
    out = {"header": hdr, "payload_len": len(payload)}
    
    if decoder is None:
        out["msg"] = f"UnknownType0x{msg_type:X}"
        out["raw_payload_hex"] = binascii.hexlify(payload).decode()
        return out
    
    try:
        decoded = decoder(payload)
        out.update(decoded)
        return out
    except Exception as e:
        out["msg"] = f"DecodeError(type=0x{msg_type:X})"
        out["error"] = str(e)
        out["raw_payload_hex"] = binascii.hexlify(payload).decode()
        return out

def _split_into_blocks(b: bytes) -> List[bytes]:
    """Podziel bajty na bloki 25-bajtowe"""
    n = len(b) // 25
    return [b[i*25:(i+1)*25] for i in range(n)]

def scan_nan_frame(raw: bytes) -> list[dict]:
    """Skanuj ramkę NAN/BLE w poszukiwaniu bloków Remote ID"""
    best = []
    best_score = -1
    for off in range(25):
        chunk = raw[off:]
        blocks = _split_into_blocks(chunk)
        if not blocks:
            continue
        decoded = [decode_block(b) for b in blocks]
        score = 0
        filtered = []
        for d in decoded:
            if d.get("msg", "").startswith("DecodeError"):
                continue
            t = d.get("header", {}).get("type")
            ok = False
            if t == 0x0:
                ok = _is_plausible_basic(d)
            elif t == 0x1:
                ok = _is_plausible_loc(d)
            elif t == 0x5:
                ok = _is_plausible_op(d)
            elif t in (0x3, 0x4, 0xF):
                ok = True
            if ok:
                score += 1
                filtered.append(d)
        if score > best_score:
            best_score = score
            best = filtered
    return best


# ------------------------------
# Main decoder class
# ------------------------------

class RemoteIDDecoder:
    """Główna klasa dekodera Remote ID"""
    
    def __init__(self):
        self.stats = {
            'blocks_decoded': 0,
            'frames_scanned': 0,
            'errors': 0
        }
    
    def decode_block(self, block: bytes) -> Dict[str, Any]:
        """Dekoduj pojedynczy blok"""
        try:
            result = decode_block(block)
            self.stats['blocks_decoded'] += 1
            return result
        except Exception as e:
            self.stats['errors'] += 1
            raise e
    
    def scan_frame(self, raw: bytes) -> List[Dict[str, Any]]:
        """Skanuj ramkę w poszukiwaniu bloków Remote ID"""
        try:
            result = scan_nan_frame(raw)
            self.stats['frames_scanned'] += 1
            return result
        except Exception as e:
            self.stats['errors'] += 1
            raise e
    
    def get_stats(self) -> Dict[str, int]:
        """Zwróć statystyki dekodera"""
        return self.stats.copy()
    
    def reset_stats(self):
        """Zresetuj statystyki"""
        self.stats = {
            'blocks_decoded': 0,
            'frames_scanned': 0,
            'errors': 0
        }