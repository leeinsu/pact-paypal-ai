"""Restricted PNG decoder for feasibility checks."""
import binascii
import struct
import zlib

_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _error(code):
    raise ValueError(code)


def decode_png(data):
    if not isinstance(data, bytes):
        _error("invalid_type")
    if len(data) > 8388608:
        _error("resource_limit")
    if not data.startswith(_SIGNATURE):
        _error("invalid_png")
    offset, chunks, seen_idat = 8, [], False
    while offset < len(data):
        if offset + 12 > len(data): _error("invalid_png")
        size = struct.unpack(">I", data[offset:offset + 4])[0]
        end = offset + 12 + size
        if end > len(data): _error("invalid_png")
        kind, body = data[offset + 4:offset + 8], data[offset + 8:offset + 8 + size]
        crc = struct.unpack(">I", data[offset + 8 + size:end])[0]
        if binascii.crc32(kind + body) & 0xffffffff != crc: _error("invalid_png")
        chunks.append((kind, body)); offset = end
    if offset != len(data) or len(chunks) < 3: _error("invalid_png")
    if chunks[0][0] != b"IHDR" or chunks[-1] != (b"IEND", b""): _error("invalid_png")
    if len(chunks[0][1]) != 13: _error("invalid_png")
    width, height, depth, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", chunks[0][1])
    if width < 64 or height < 64 or width > 1024 or height > 1024 or width * height > 1048576: _error("resource_limit")
    if depth != 8 or color not in (2, 6) or compression or filtering or interlace: _error("unsupported_format")
    idats = []
    for index, (kind, body) in enumerate(chunks[1:-1], 1):
        if kind == b"IDAT":
            seen_idat = True; idats.append(body)
        elif not seen_idat:
            _error("unsupported_format")
        else:
            _error("invalid_png")
    if not idats: _error("invalid_png")
    channels = 3 if color == 2 else 4
    expected = height * (1 + width * channels)
    raw = b""
    try:
        decoder = zlib.decompressobj()
        raw = decoder.decompress(b"".join(idats), expected + 1)
        if len(raw) > expected or decoder.unconsumed_tail or not decoder.eof or decoder.unused_data: _error("invalid_png")
    except ValueError: raise
    except Exception: _error("invalid_png")
    if len(raw) != expected: _error("invalid_png")
    rows, previous, cursor = [], bytearray(width * channels), 0
    for _ in range(height):
        kind = raw[cursor]; cursor += 1
        if kind > 4: _error("invalid_png")
        row = bytearray(raw[cursor:cursor + width * channels]); cursor += width * channels
        for i, value in enumerate(row):
            a = row[i - channels] if i >= channels else 0; b = previous[i]; c = previous[i - channels] if i >= channels else 0
            if kind == 1: value += a
            elif kind == 2: value += b
            elif kind == 3: value += (a + b) // 2
            elif kind == 4:
                p = a + b - c; value += min((abs(p-a), 0, a), (abs(p-b), 1, b), (abs(p-c), 2, c))[2]
            row[i] = value & 255
        rows.append(row); previous = row
    pixels = b"".join(rows)
    if color == 2: pixels = b"".join(pixels[i:i+3] + b"\xff" for i in range(0, len(pixels), 3))
    return width, height, pixels
