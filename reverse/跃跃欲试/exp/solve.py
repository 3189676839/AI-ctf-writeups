#!/usr/bin/env python3

# yyys solve record
# Recovered from the unpacked dialog callback constraints.


def solve():
    s = ['?'] * 16

    # direct constraints / arithmetic relations recovered from asm
    s[0] = 'B'
    s[15] = chr(0x9B - 0x42)   # serial[15] + 0x42 == 0x9b

    s[1] = chr(0x57 + 3)       # serial[1] - 3 == 0x57
    s[14] = chr(0x9B - ord(s[1]))

    s[2] = chr(0x3A - 1)       # serial[2] + 1 == 0x3a
    s[13] = chr(0x9B - ord(s[2]))

    s[3] = 'd'
    s[12] = chr(0x9B - 0x64)   # serial[12] + 0x64 == 0x9b

    s[4] = 'm'
    s[11] = chr(0xC8 - 0x81)   # serial[11] + 0x81 == 0xc8

    s[5] = chr(0x44 + 0x2D)    # serial[5] - 0x2d == 0x44
    s[10] = chr(0xAA - ord(s[5]))

    s[6] = '4'
    s[9] = chr(0x9B - 0x34)    # serial[9] + 0x34 == 0x9b

    s[7] = 'c'
    s[8] = chr(0x9B - 0x63)    # serial[8] + 0x63 == 0x9b

    serial = ''.join(s)
    return serial


def main():
    serial = solve()
    print('[+] recovered serial:', serial)
    print('[+] length =', len(serial))
    print('[+] example email = a@b.c')


if __name__ == '__main__':
    main()
