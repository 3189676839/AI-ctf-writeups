# CrackMe看雪.金山2007 writeup

## 题目信息
- 题目：`CrackMe看雪.金山2007`
- 方向：`Reverse`
- 类型：Win32 GUI / 极小型注册程序
- 目标：求用户名 `KCTF` 对应的正确序列号

## 最终结果
- 用户名：`KCTF`
- 正确序列号：`38193105`

---

## 1. 程序结构

程序体积非常小，只有一个对话框入口。

入口：

```asm
0x400522: push 0
0x400524: call GetModuleHandleA
0x40052c: push 0x400437
0x400533: push 0x65
0x400536: call DialogBoxParamA
```

因此：

- 对话框资源 ID：`101`
- 主回调函数：`0x400437`

导入表也非常简单：

- `GetModuleHandleA`
- `DialogBoxParamA`
- `GetDlgItemTextA`
- `MessageBoxA`
- `EndDialog`

这说明题目没有复杂外部依赖，核心逻辑都在 `.text` 中。

---

## 2. 主事件逻辑

`0x400437` 是标准的对话框消息处理函数。

关键分支在：

```asm
cmp [ebp+0xc], 0x111   ; WM_COMMAND
```

当按钮 ID 为 `0x3E8/0x3E9` 一类控件时，会读取两个输入框：

```asm
GetDlgItemTextA(hDlg, 0x3E9, name_buf, 0x10)
GetDlgItemTextA(hDlg, 0x3EA, serial_buf, 0x1000)
```

随后调用真正的校验函数：

```asm
call 0x4002cc
```

所以真正需要分析的目标函数是：

```text
0x4002cc
```

---

## 3. `0x4002cc` 的总体思路

这个函数不是传统“直接比较 serial”的逻辑，而是：

1. 先把用户名压成一个 32 位种子 `seed`
2. 再把 `seed` 的若干二进制位拆到一个状态数组里
3. 遍历用户输入的 serial 数字串
4. 每一位数字都会驱动一次状态转移
5. 最后要求所有关键状态位都变成 1

也就是说，这题本质上是一个 **digit-driven state machine**。

---

## 4. Name -> seed

在 `0x4004da ~ 0x4004fb` 之间，程序对用户名逐字节更新一个 32 位值：

```asm
movsx eax, byte ptr [name + i]
add eax, ebx
imul eax, eax, 0x03721273
add eax, 0x24681357
mov esi, eax
shl esi, 0x19
sar eax, 0x7
or esi, eax
mov ebx, esi
```

等价的高层逻辑：

```python
def update(ebx, ch):
    eax = (ebx + ch) & 0xffffffff
    eax = (eax * 0x03721273 + 0x24681357) & 0xffffffff
    ebx = ((eax << 25) & 0xffffffff) | ((eax >> 7) & 0xffffffff)
    return ebx
```

对 `KCTF` 逐字节运算后可得：

```text
seed = 0xfffec610
```

---

## 5. 初始化状态数组

程序接着把 `seed` 的部分 bit 抽出来，写入局部数组：

```asm
for edi in 1..8:
    bit[edi] = (seed >> edi) & 1
```

并且还有一个额外状态位初始为 0。

因此初始 9 位状态为：

```text
[0, 0, 0, 1, 0, 0, 0, 0, 0]
```

其中第 4 位一开始就是 1。

---

## 6. Serial 每一位如何驱动状态转移

程序遍历输入 serial 的每个字符，要求必须是数字：

```asm
cmp al, 0x30
jl fail
cmp al, 0x39
jg fail
```

然后计算当前位置 `i` 对应的一个值：

```asm
edx = i % 31
rem = (seed >> edx) % 10
r = (rem + digit) % 10
```

更准确地说，程序取：

```text
r = (((seed >> (i % 31)) % 10) + digit_i) % 10
```

接着：

### 情况 1：`r == 1`
```asm
xor byte ptr [bit1], 1
```

即切换第 1 位。

### 情况 2：`r > 1`
程序要求：

- `bit[r-1] == 1`
- 并且 `bit[1..r-2]` 也都已经是 1

只有满足前置条件，才能：

```asm
xor byte ptr [bit[r]], 1
```

也就是说，状态位只能“从前往后”依次点亮。

---

## 7. 成功条件

遍历完所有 serial 数字后，程序检查 1~9 位是否全为 1：

```asm
for i in 1..9:
    if bit[i] == 0:
        fail
```

因此目标就变成：

```text
找一串数字，使状态从 [0,0,0,1,0,0,0,0,0] 变成 [1,1,1,1,1,1,1,1,1]
```

---

## 8. 建模求解

把状态位压成位掩码后，这就是一个非常小的 BFS 搜索问题。

对 `KCTF` 的初始状态，最短可行的目标转移序列为：

```text
r = [1, 2, 3, 5, 6, 7, 8, 9]
```

而输入 digit 与 `r` 的关系是：

```text
digit_i = (r_i - ((seed >> (i % 31)) % 10)) mod 10
```

逐位反推可得：

```text
38193105
```

---

## 9. 最终答案

```text
Name   : KCTF
Serial : 38193105
```

---

## 10. 复现脚本

见同目录：

```text
exp/solve.py
```

脚本会：

1. 从用户名计算 `seed`
2. 初始化状态
3. 用 BFS 搜索最短可行转移路径
4. 反推得到最终 serial

---

## 11. 总结

这题的难点不在壳，而在于把短小汇编识别成：

```text
Name -> 32 位种子
Seed -> 初始 bit 状态
Serial 每位数字 -> 一次状态转移
最终将 9 个状态位全部点亮
```

它不是传统的哈希比对题，而是一个很典型的**状态机构造题**。
