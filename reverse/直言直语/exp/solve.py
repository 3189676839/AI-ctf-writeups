#!/usr/bin/env python3

# 直言直语 solve record
# core logic recovered from sub_402600 / sub_402AF0 / sub_402CA0 / sub_402E80

ARR = bytes([
    0x5B, 0xD6, 0xD0, 0x26, 0xC8, 0xDD, 0x19, 0x7E,
    0x6E, 0x3E, 0xCB, 0x16, 0x91, 0x7D, 0xFF, 0xAF,
    0xDD, 0x76, 0x64, 0xB0, 0xF7, 0xE5, 0x89, 0x57,
    0x82, 0x9F, 0x0C, 0x00, 0x9E, 0xD0, 0x45, 0xFA,
])
KEY = b'qwertyuiop'


def rc4_init(key: bytes):
    s = list(range(256))
    j = 0
    for i in range(256):
        j = (j + s[i] + key[i % len(key)]) % 256
        s[i], s[j] = s[j], s[i]
    return s


def rc4_crypt(s, data: bytearray):
    i = 0
    j = 0
    for idx in range(len(data)):
        i = (i + 1) % 256
        j = (j + s[i]) % 256
        s[i], s[j] = s[j], s[i]
        data[idx] ^= s[(s[i] + s[j]) % 256]
    return bytes(data)


def solve():
    # arr is the post-RC4 comparison array used by sub_402600
    # decrypt to recover the string after sub_402AF0 preprocessing
    processed = rc4_crypt(rc4_init(KEY), bytearray(ARR))
    # sub_402AF0 reverses the 32-byte content inside flag{...}
    inner = processed[::-1].decode()
    final_flag = f'flag{{{inner}}}'
    return processed.decode(), inner, final_flag


def main():
    processed, inner, final_flag = solve()
    print('[+] rc4 key      =', KEY.decode())
    print('[+] processed    =', processed)
    print('[+] input inner  =', inner)
    print('[+] final flag   =', final_flag)


if __name__ == '__main__':
    main()
