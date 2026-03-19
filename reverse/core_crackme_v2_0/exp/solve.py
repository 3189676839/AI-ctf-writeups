import struct
from pathlib import Path

import pefile


EXE_PATH = Path('/tmp/core_unipacker_out/unpacked_CRACKME3.EXE')
TARGET = (0xBAB8150D, 0x57308F2C, 0xAEA9D86B)


def read_dwords(pe: pefile.PE, va: int, count: int = 64):
    off = pe.get_offset_from_rva(va - pe.OPTIONAL_HEADER.ImageBase)
    data = pe.__data__[off:off + 4 * count]
    return list(struct.unpack('<%dI' % count, data))


def build_key_matrix(mask1, mask2):
    matrix = [[0] * 64 for _ in range(64)]
    for i in range(32):
        key1 = ((mask2[31 - i] & 0xFFFFFFFF) << 32) | (mask1[31 - i] & 0xFFFFFFFF)
        key2 = ((mask2[63 - i] & 0xFFFFFFFF) << 32) | (mask1[63 - i] & 0xFFFFFFFF)
        for j in range(64):
            matrix[i][j] = (key1 >> j) & 1
            matrix[i + 32][j] = (key2 >> j) & 1
    return matrix


def invert_matrix_gf2(matrix):
    n = 64
    aug = [row[:] + [1 if i == j else 0 for j in range(n)] for i, row in enumerate(matrix)]

    for col in range(n):
        pivot = None
        for row in range(col, n):
            if aug[row][col]:
                pivot = row
                break
        if pivot is None:
            raise ValueError('matrix is singular over GF(2)')

        if pivot != col:
            aug[col], aug[pivot] = aug[pivot], aug[col]

        for row in range(n):
            if row != col and aug[row][col]:
                for j in range(2 * n):
                    aug[row][j] ^= aug[col][j]

    return [row[n:] for row in aug]


def decrypt_pair(d0, d1, mask1, mask2):
    matrix = build_key_matrix(mask1, mask2)
    inv = invert_matrix_gf2(matrix)
    cipher_bits = [(d0 >> i) & 1 for i in range(32)] + [(d1 >> i) & 1 for i in range(32)]

    plain = 0
    for i in range(64):
        bit = 0
        for j in range(64):
            bit ^= inv[i][j] & cipher_bits[j]
        plain |= (bit & 1) << i

    return plain & 0xFFFFFFFF, (plain >> 32) & 0xFFFFFFFF


def parity64(x):
    return x.bit_count() & 1


def encrypt_pair(d0, d1, mask1, mask2):
    data = ((d1 & 0xFFFFFFFF) << 32) | (d0 & 0xFFFFFFFF)
    v0 = 0
    v1 = 0
    for i in range(32):
        key1 = ((mask2[i] & 0xFFFFFFFF) << 32) | (mask1[i] & 0xFFFFFFFF)
        key2 = ((mask2[i + 32] & 0xFFFFFFFF) << 32) | (mask1[i + 32] & 0xFFFFFFFF)
        v0 = parity64(data & key1) ^ ((v0 << 1) & 0xFFFFFFFF)
        v1 = parity64(data & key2) ^ ((v1 << 1) & 0xFFFFFFFF)
    return v0 & 0xFFFFFFFF, v1 & 0xFFFFFFFF


def main():
    pe = pefile.PE(str(EXE_PATH))
    A1 = read_dwords(pe, 0x41C2C0)
    A2 = read_dwords(pe, 0x41C3C0)
    B1 = read_dwords(pe, 0x41C4C0)
    B2 = read_dwords(pe, 0x41C5C0)

    h0, h1, h2 = TARGET

    mid, z = decrypt_pair(h1, h2, B1, B2)
    x, y = decrypt_pair(h0, mid, A1, A2)

    print('Name   : KCTF')
    print('Serial : %08X %08X %08X' % (x, y, z))

    stage1 = encrypt_pair(x, y, A1, A2)
    stage2 = encrypt_pair(stage1[1], z, B1, B2)

    print('Stage1 : %08X %08X' % stage1)
    print('Stage2 : %08X %08X' % stage2)
    print('Expect : %08X %08X %08X' % TARGET)
    print('Check  :', stage1[0] == h0 and stage2[0] == h1 and stage2[1] == h2)


if __name__ == '__main__':
    main()
