from collections import deque


def sar32(x, n):
    x &= 0xffffffff
    if x & 0x80000000:
        x -= 0x100000000
    return (x >> n) & 0xffffffff


def seed_from_name(name: bytes) -> int:
    ebx = 0x13572468
    for ch in name:
        eax = (ebx + ch) & 0xffffffff
        eax = (eax * 0x03721273 + 0x24681357) & 0xffffffff
        ebx = ((eax << 25) & 0xffffffff) | sar32(eax, 7)
    return ebx & 0xffffffff


def init_state(seed: int):
    bits = [0] * 10
    for i in range(1, 9):
        bits[i] = (seed >> i) & 1
    bits[9] = 1
    state = 0
    for i in range(1, 10):
        state |= (bits[i] << (i - 1))
    return state


def apply(state: int, r: int):
    bits = [0] * 10
    for i in range(1, 10):
        bits[i] = (state >> (i - 1)) & 1

    if r == 1:
        bits[1] ^= 1
    else:
        if bits[r - 1] != 1:
            return None
        for i in range(1, r - 1):
            if bits[i] != 1:
                return None
        bits[r] ^= 1

    new_state = 0
    for i in range(1, 10):
        new_state |= (bits[i] << (i - 1))
    return new_state


def bfs(start: int, goal: int = 0x1ff):
    q = deque([start])
    prev = {start: (None, None)}
    while q:
        s = q.popleft()
        if s == goal:
            path = []
            while prev[s][0] is not None:
                old, digit = prev[s]
                path.append(digit)
                s = old
            return path[::-1]
        for r in range(1, 10):
            ns = apply(s, r)
            if ns is None or ns in prev:
                continue
            prev[ns] = (s, r)
            q.append(ns)
    return None


def gen_serial(name: str) -> str:
    name_b = name.encode()
    seed = seed_from_name(name_b)
    start = init_state(seed)
    path = bfs(start)
    if path is None:
        raise ValueError('no solution')
    out = []
    for i, r in enumerate(path):
        rem = ((seed >> (i % 31)) & 0xffffffff) % 10
        digit = (r - rem) % 10
        out.append(str(digit))
    return ''.join(out)


def check(name: str, serial: str) -> bool:
    seed = seed_from_name(name.encode())
    state = init_state(seed)
    if not serial or any(c < '0' or c > '9' for c in serial):
        return False
    for i, ch in enumerate(serial):
        rem = ((seed >> (i % 31)) & 0xffffffff) % 10
        r = (rem + ord(ch) - 0x30) % 10
        ns = apply(state, r)
        if ns is None:
            return False
        state = ns
    return state == 0x1ff


if __name__ == '__main__':
    name = 'KCTF'
    serial = gen_serial(name)
    print('Name   :', name)
    print('Serial :', serial)
    print('Check  :', check(name, serial))
