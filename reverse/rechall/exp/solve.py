#!/usr/bin/env python3
import hashlib
from z3 import BitVec, BitVecVal, Solver, ULE, sat


def checker2_expr(x):
    eax = x & BitVecVal(0x52E3F96B, 32)
    edx = eax
    eax = edx + edx
    edx = edx + eax
    eax = x | BitVecVal(0xAD1C0694, 32)
    edx = edx - eax
    eax = edx
    eax = eax - x
    eax = eax + BitVecVal(0x5A380D28, 32)
    eax = ~eax
    return eax


def checker3_expr(x):
    eax = ~x
    eax = eax | BitVecVal(0xD68E3FE9, 32)
    edx = eax
    eax = eax << 2
    ecx = edx
    ecx = ecx - eax

    eax = x | BitVecVal(0xD68E3FE9, 32)
    eax = ~eax
    edx = eax
    eax = edx + edx
    eax = eax + edx
    edx = ecx + eax

    eax = ~x
    eax = eax & BitVecVal(0xD68E3FE9, 32)
    ecx = eax

    eax = ~x
    eax = eax | BitVecVal(0xD68E3FE9, 32)
    eax = ~eax
    eax = eax + eax
    eax = eax + ecx
    eax = eax << 2
    ecx = edx + eax

    eax = x & BitVecVal(0xD68E3FE9, 32)
    edx = eax
    eax = edx << 2
    eax = eax + edx
    eax = eax + eax
    edx = eax

    eax = x ^ BitVecVal(0xD68E3FE9, 32)
    edx = edx - eax
    eax = edx
    eax = eax + ecx
    return eax


def checker4_expr(x):
    eax = x ^ BitVecVal(0xAE7C284F, 32)
    edx = eax
    eax = edx << 2
    eax = eax + edx
    eax = eax + eax
    edx = edx + eax

    eax = x & BitVecVal(0xAE7C284F, 32)
    eax = eax << 2
    ecx = edx + eax

    eax = x & BitVecVal(0x5183D7B0, 32)
    edx = eax
    eax = edx + edx
    eax = eax + edx
    eax = eax + eax
    esi = eax

    eax = x | BitVecVal(0x5183D7B0, 32)
    eax = ~eax
    edx = eax
    eax = edx + edx
    eax = eax + edx
    eax = eax << 2
    eax = eax + esi
    ecx = ecx - eax

    edx = x
    eax = edx << 2
    eax = eax + edx
    eax = -eax

    edx = x | BitVecVal(0x4EDA6B7C, 32)
    edx = ~edx
    edx = edx + edx
    eax = eax - edx
    edx = eax

    eax = x | BitVecVal(0xB1259483, 32)
    esi = edx
    esi = esi - eax

    eax = x & BitVecVal(0x4EDA6B7C, 32)
    edx = eax
    eax = edx + edx
    eax = eax + edx
    edx = esi + eax

    eax = x & BitVecVal(0xB1259483, 32)
    esi = eax << 2

    eax = x | BitVecVal(0xB1259483, 32)
    edi = eax
    eax = BitVecVal(0, 32) - edi
    eax = eax + eax
    esi = esi - eax

    eax = esi
    eax = eax + edx
    eax = eax + ecx
    eax = eax - BitVecVal(0x5183D7B2, 32)
    return eax


def all_models(var, constraints, limit=16):
    s = Solver()
    for c in constraints:
        s.add(c)
    out = []
    while len(out) < limit and s.check() == sat:
        m = s.model()
        v = m[var].as_long()
        out.append(v)
        s.add(var != m[var])
    return out


def main():
    x1 = (0x956438B9 + 0x5294B771) & 0xFFFFFFFF

    x2 = BitVec('x2', 32)
    x2_vals = all_models(x2, [checker2_expr(x2) == BitVecVal(0xC2407EEA, 32)])

    x3 = BitVec('x3', 32)
    x3_vals = all_models(
        x3,
        [
            ULE(x3, BitVecVal(0x10000000, 32)),
            checker3_expr(x3) == BitVecVal(0x251BC4BD, 32),
        ],
    )

    x4 = BitVec('x4', 32)
    x4_vals = all_models(
        x4,
        [
            ULE(x4, BitVecVal(0x10000000, 32)),
            checker4_expr(x4) == BitVecVal(0x88637BD8, 32),
        ],
    )

    print('[+] x1 =', x1, hex(x1))
    print('[+] x2 candidates =', [hex(v) for v in x2_vals])
    print('[+] x3 candidates =', [hex(v) for v in x3_vals])
    print('[+] x4 candidates =', [hex(v) for v in x4_vals])

    target_md5 = 'f2d5f978de74c1ce7a9ff53461ca3fd2'

    print('\n[+] testing final flag candidates...')
    for a in x2_vals:
        for b in x3_vals:
            for c in x4_vals:
                flag = 'flag{%08x-%08x-%08x-%08x}' % (x1, a, b, c)
                md5 = hashlib.md5(flag.encode()).hexdigest()
                print(flag, md5)
                if md5 == target_md5:
                    print('\n[+] FOUND FLAG:', flag)
                    print('[+] decimal inputs:', x1, a, b, c)
                    return

    print('[-] no matching flag found')


if __name__ == '__main__':
    main()
