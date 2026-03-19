import base64
import hashlib
from sympy import invert

KEY = bytes.fromhex('2947078587332544')
E = 65537
N = 0xB80A90BF53C6C979
P = 3533507051
Q = 3753090347
D = int(invert(E, (P - 1) * (Q - 1)))


def rc4_crypt(key: bytes, data: bytes) -> bytes:
    S = list(range(256))
    j = 0
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) & 0xFF
        S[i], S[j] = S[j], S[i]

    i = 0
    j = 0
    out = []
    for b in data:
        i = (i + 1) & 0xFF
        j = (j + S[i]) & 0xFF
        S[i], S[j] = S[j], S[i]
        out.append(b ^ S[(S[i] + S[j]) & 0xFF])
    return bytes(out)


def gen_serial(name: str) -> str:
    md5 = hashlib.md5(name.encode()).digest()
    prefix = rc4_crypt(KEY, md5[:8])
    c = int(md5[8:].hex(), 16)
    suffix = pow(c, D, N)
    raw = prefix + str(suffix).encode()
    return base64.b64encode(raw).decode()


def check(name: str, serial: str) -> bool:
    raw = base64.b64decode(serial)
    if len(raw) < 8:
        return False
    if any(not (48 <= c <= 57) for c in raw[8:]):
        return False
    md5 = hashlib.md5(name.encode()).digest()
    if rc4_crypt(KEY, raw[:8]) != md5[:8]:
        return False
    c = int(md5[8:].hex(), 16)
    suffix = int(raw[8:].decode())
    return pow(suffix, E, N) == c


if __name__ == '__main__':
    name = 'KCTF'
    serial = gen_serial(name)
    print('Name   :', name)
    print('Serial :', serial)
    print('Check  :', check(name, serial))
