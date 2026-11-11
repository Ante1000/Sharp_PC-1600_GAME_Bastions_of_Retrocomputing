#!/usr/bin/env python3
"""pc1600_bas2wav.py - BASIC text file -> tape recording (WAV) for LOAD "CAS:" on a Sharp PC-1600.

Usage:  python3 pc1600_bas2wav.py program.txt out.wav [NAME] [--rate 44100] [--eol crlf|cr|lf]
                                  [--ext BAS] [--invert]
        python3 pc1600_bas2wav.py --check in.wav       (decode a recording: header, checksums, text)

The program is recorded as an ASCII BASIC file (the format written by SAVE "CAS:name",A in
MODE 0, the PC-1600 mode), so no token table is needed: the PC-1600 tokenizes the text itself
when it loads it.  Load it in MODE 0 with   LOAD "CAS:NAME"   (or LOAD "CAS:" for the first file).
Format source: PC-1600 Technical Reference, section 3.11.1 "PC-1600 Mode (Mode 0)" and 3.11.3.
NOT yet verified on a real PC-1600: the only check made here is the decoder below, which
reads back what this tool writes (header, both checksums, the text).

Tape format (default 44100 Hz, 8 bit mono)
  bit "0" = SHORT = one cycle: high 163 us, low 164 us      (about 3.06 kHz)
  bit "1" = LONG  = one cycle: high 409 us, low 409 us      (about 1.22 kHz)
  byte    = LONG (start bit) + bit 7 ... bit 0
  checksum = the number of "1" bits in the data bytes (the start bits are not counted), lower
             16 bits, written as two bytes, high byte first, then one LONG bit.
  file:   8 s of silence, header gap (SHORT x10000, LONG x40, SHORT x40, LONG x1), the 48 header
          bytes, checksum, LONG, 2 s of silence, then the ASCII data in blocks of 256 bytes:
          data gap (SHORT x11000, LONG x20, SHORT x20, LONG x1), 256 bytes, checksum, LONG,
          4 s of silence.  The text ends with the EOF code 1AH, the last block is padded with 00H.
  header (48 bytes): 00 = 04H (ASCII), 01-0D file name (20H fill), 0E-10 extension, 11 = 0DH,
          18 = 04H (MODE 2 file format: ASCII), 19-1C month (1-12), day, hour, minute (BCD),
          all other bytes 00H.
"""
import argparse, sys, wave

SHORT_HI, SHORT_LO = 163.0, 164.0      # microseconds (PC-1600 Technical Reference, 3.11.1 [2])
LONG_HI, LONG_LO = 409.0, 409.0
HDR_SHORT1, HDR_LONG, HDR_SHORT2 = 10000, 40, 40
DAT_SHORT1, DAT_LONG, DAT_SHORT2 = 11000, 20, 20
LEADER_S, HDR_SPACE_S, DATA_SPACE_S = 8.0, 2.0, 4.0
BLOCK = 256
EOF = 0x1A


class Synth:
    def __init__(self, rate, invert=False):
        self.rate = rate
        self.buf = bytearray()
        self.pos = 0.0                 # position in samples (float), edges are rounded
        lo, hi = 30, 226
        self.hi, self.lo = (lo, hi) if invert else (hi, lo)

    def _seg(self, us, level):
        end = self.pos + us * self.rate / 1e6
        a, b = int(round(self.pos)), int(round(end))
        self.buf.extend(bytes([level]) * (b - a))
        self.pos = end

    def silence(self, seconds):
        end = self.pos + seconds * self.rate
        a, b = int(round(self.pos)), int(round(end))
        self.buf.extend(bytes([128]) * (b - a))
        self.pos = end

    def bit(self, v):
        if v:
            self._seg(LONG_HI, self.hi); self._seg(LONG_LO, self.lo)
        else:
            self._seg(SHORT_HI, self.hi); self._seg(SHORT_LO, self.lo)

    def bits(self, v, n):
        for _ in range(n):
            self.bit(v)

    def byte(self, b):
        self.bit(1)                                    # start bit (LONG)
        for i in range(7, -1, -1):
            self.bit((b >> i) & 1)

    def block(self, data, gap):
        """gap = (short1, long, short2); sync, data, checksum, LONG."""
        s1, l1, s2 = gap
        self.bits(0, s1); self.bits(1, l1); self.bits(0, s2); self.bit(1)
        total = 0
        for b in data:
            self.byte(b); total += bin(b).count('1')
        total &= 0xFFFF
        self.byte(total >> 8); self.byte(total & 0xFF)
        self.bit(1)


def header_bytes(name, ext, date):
    h = bytearray(48)
    h[0] = 0x04                                        # MODE 1 file format: ASCII
    h[1:14] = name.upper().encode('ascii')[:8].ljust(13, b' ')
    h[14:17] = ext.upper().encode('ascii')[:3].ljust(3, b' ')
    h[17] = 0x0D
    h[24] = 0x04                                       # MODE 2 file format: ASCII
    mo, da, hr, mi = date
    h[25] = mo
    h[26], h[27], h[28] = [((v // 10) << 4) | (v % 10) for v in (da, hr, mi)]
    return bytes(h)


def ascii_blocks(path, eol):
    text = open(path, 'rb').read().decode('latin1')
    lines = [l.rstrip() for l in text.replace('\r\n', '\n').replace('\r', '\n').split('\n')]
    while lines and not lines[-1]:
        lines.pop()
    for l in lines:
        if not l or not l[0].isdigit():
            sys.exit('every line must start with a line number: %r' % l[:30])
        if len(l) > 80:
            sys.exit('line longer than 80 characters: %r' % l[:30])
    data = (eol.join(lines) + eol).encode('ascii') + bytes([EOF])
    pad = (-len(data)) % BLOCK
    data += bytes(pad)
    return data, [data[i:i + BLOCK] for i in range(0, len(data), BLOCK)]


def build(path, name, ext, rate, eol, invert, date):
    data, blocks = ascii_blocks(path, eol)
    s = Synth(rate, invert)
    s.silence(LEADER_S)
    s.bits(0, HDR_SHORT1); s.bits(1, HDR_LONG); s.bits(0, HDR_SHORT2); s.bit(1)
    total = 0
    for b in header_bytes(name, ext, date):
        s.byte(b); total += bin(b).count('1')
    total &= 0xFFFF
    s.byte(total >> 8); s.byte(total & 0xFF); s.bit(1)
    s.silence(HDR_SPACE_S)
    for blk in blocks:
        s.block(blk, (DAT_SHORT1, DAT_LONG, DAT_SHORT2))
        s.silence(DATA_SPACE_S)
    return bytes(s.buf), len(blocks), len(data)


def write_wav(path, data, rate):
    w = wave.open(path, 'wb'); w.setnchannels(1); w.setsampwidth(1); w.setframerate(rate)
    w.writeframes(data); w.close()


# ---------------------------------------------------------------- decoder (self check)
def pulses(path):
    """returns (rate, list of (period in microseconds)) from the rising edges of the signal"""
    w = wave.open(path)
    rate, width, ch = w.getframerate(), w.getsampwidth(), w.getnchannels()
    raw = w.readframes(w.getnframes())
    if width == 2:
        import array
        a = array.array('h'); a.frombytes(raw)
        d = [(v >> 8) + 128 for v in a[::ch]]
    else:
        d = list(raw[::ch])
    rising = []
    prev = d[0] >= 128
    for i, v in enumerate(d):
        s = v >= 128
        if s and not prev:
            rising.append(i)
        prev = s
    return rate, [(b - a) * 1e6 / rate for a, b in zip(rising, rising[1:])]


def bursts(per):
    """split the periods at gaps (> 5 ms) into bursts of bits: 0 = SHORT, 1 = LONG"""
    out, cur = [], []
    for p in per:
        if p > 5000:
            if cur:
                out.append(cur)
            cur = []
        else:
            cur.append(1 if p > 520 else 0)
    if cur:
        out.append(cur)
    return out


def parse_burst(bits, sync):
    """sync = (short1, long, short2) minimum counts; returns (bytes, checksum ok, text of problems)"""
    i, n = 0, len(bits)
    s1 = 0
    while i < n and bits[i] == 0:
        i += 1; s1 += 1
    l1 = 0
    while i < n and bits[i] == 1:
        i += 1; l1 += 1
    s2 = 0
    while i < n and bits[i] == 0:
        i += 1; s2 += 1
    if s1 < sync[0] * 0.9 or l1 < sync[1] * 0.9 or s2 < sync[2] * 0.9:
        return None, False, 'sync %d/%d/%d is not %s' % (s1, l1, s2, sync)
    i += 1                                              # the single LONG after the second SHORT run
    rest = n - i - 1                                    # without the final LONG
    count = rest // 9
    out = []
    for _ in range(count):
        if bits[i] != 1:
            return None, False, 'missing start bit'
        v = 0
        for b in bits[i + 1:i + 9]:
            v = (v << 1) | b
        out.append(v); i += 9
    data, chk = out[:-2], out[-2] * 256 + out[-1]
    calc = sum(bin(b).count('1') for b in data) & 0xFFFF
    return data, calc == chk, '' if calc == chk else 'checksum %04X, expected %04X' % (chk, calc)


def decode(path):
    rate, per = pulses(path)
    bs = bursts(per)
    if not bs:
        sys.exit('no signal found')
    hdr, ok, msg = parse_burst(bs[0], (HDR_SHORT1, HDR_LONG, HDR_SHORT2))
    if hdr is None or len(hdr) != 48:
        sys.exit('no header: ' + msg)
    print('header: %s  checksum %s' % (' '.join('%02X' % b for b in hdr[:18]), 'OK' if ok else 'BAD ' + msg))
    print('file name: %r  extension: %r  format: %02X/%02X' % (
        bytes(hdr[1:14]).decode('latin1').rstrip(), bytes(hdr[14:17]).decode('latin1'), hdr[0], hdr[24]))
    data = b''
    for k, b in enumerate(bs[1:], 1):
        d, ok, msg = parse_burst(b, (DAT_SHORT1, DAT_LONG, DAT_SHORT2))
        if d is None:
            print('block %d: %s' % (k, msg)); continue
        if not ok or len(d) != BLOCK:
            print('block %d: %d bytes, %s' % (k, len(d), msg or 'checksum OK'))
        data += bytes(d)
    n = data.find(bytes([EOF]))
    print('%d blocks, %d bytes of text, EOF %s' % (len(bs) - 1, n, 'found' if n >= 0 else 'MISSING'))
    return hdr, data[:n] if n >= 0 else data


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument('--check'); ap.add_argument('--rate', type=int, default=44100)
    ap.add_argument('--eol', default='crlf', choices=['crlf', 'cr', 'lf'])
    ap.add_argument('--ext', default='BAS'); ap.add_argument('--invert', action='store_true')
    ap.add_argument('files', nargs='*')
    a = ap.parse_args()
    if a.check:
        hdr, text = decode(a.check)
        for l in text.decode('latin1').replace('\r', '').split('\n')[:5]:
            print('  ', l)
        print('   ...')
        return
    if len(a.files) not in (2, 3):
        print(__doc__); return
    src, out = a.files[0], a.files[1]
    import re
    name = a.files[2] if len(a.files) == 3 else re.sub(r'[^A-Za-z0-9]', '', src.split('/')[-1].split('.')[0])[:8]
    eol = {'crlf': '\r\n', 'cr': '\r', 'lf': '\n'}[a.eol]
    data, nblocks, nbytes = build(src, name, a.ext, a.rate, eol, a.invert, (1, 1, 0, 0))
    write_wav(out, data, a.rate)
    print('%s: %d bytes of text in %d blocks, tape name %s.%s, %.0f s' % (
        out, nbytes, nblocks, name.upper(), a.ext.upper(), len(data) / a.rate))


if __name__ == '__main__':
    main()
