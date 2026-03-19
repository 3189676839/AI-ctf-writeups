# CORE CrackMe v2.0 writeup

## 题目信息
- 题目：`CORE CrackMe v2.0`
- 方向：`Reverse`
- 类型：Win32 GUI / CrackMe
- 目标：求固定用户名 `KCTF` 的正确注册码

## 最终结果
- 用户名：`KCTF`
- 正确注册码：`A86CA89F 77F81C3C FD2620F0`

---

## 1. 样本基础信息

收到的原始附件：

```text
CORE_CRACKME3_1773928614319.zip
SHA256 = 1988945355545edc744f81fd6de33d724619b5806de76ef1080b95534c35d0a6
```

压缩包内只有一个文件：

```text
CRACKME3.EXE
size = 62511
```

初始侦察结果：

```text
PE32 / Windows x86 GUI / UPX packed
```

本机 `upx -d` 直接失败：

```text
CantUnpackException: this program is packed with an obsolete version and cannot be unpacked
```

因此后续改用 `unipacker` 模拟执行并导出解压后的 PE，得到：

```text
/tmp/core_unipacker_out/unpacked_CRACKME3.EXE
SHA256 = afac912df6c04b28ae73094ef7f5942dfd5d940ab8afc8b7aefa35b4ac0e57a5
```

真实 OEP 为：

```text
0x4047CB
```

---

## 2. 关键字符串与成功分支定位

解压后能直接看到关键字符串：

```text
Registered
... Man, you're good enough to join CORE! ...
... Better luck next time ...
... Hmmm, you don't even pass the first threshold ...
%lx%lx%lx
```

从这些字符串反查引用后，可以定位到核心校验函数 `0x4020A0` 一带。它的尾部逻辑大致是：

1. 构造待校验字符串
2. 调 `sub_401500` 计算自定义摘要
3. 用 `sscanf(serial, "%lx%lx%lx", &x, &y, &z)` 解析用户输入的三个 32 位数
4. 调两次 `sub_401AD0`
5. 与摘要结果的前三个 `_DWORD` 比较
6. 全部相等则弹出 `Welcome / Registered`

也就是说，最终注册码输入格式已经确定为：

```text
8位十六进制 + 空白 + 8位十六进制 + 空白 + 8位十六进制
```

---

## 3. 用户名参与摘要前的处理

函数 `0x408D70` 不是加密，而是**原地反转字符串**。

因此：

```text
KCTF -> FTCK
```

在核心函数里，真实拼接顺序不是：

```text
KCTFFTCK
```

而是：

```text
FTCKFTCKFTCKKCTF
```

也就是：

- 反转后的用户名 `FTCK` 拼接 3 次
- 最后再拼接原始用户名 `KCTF`

最终参与摘要的字符串为：

```text
FTCKFTCKFTCKKCTF
```

---

## 4. `sub_401500`：看起来像 MD5，但其实是魔改 hash

一开始很容易被这几个初始化常量误导：

```c
0x67452301
0xEFCDAB89
0x98BADCFE
0x10325476
```

因为这四个值和 MD5 的初始状态完全一致。

但是继续看轮函数就会发现：

- 轮常量表不是标准 MD5 的 `T[i]`
- 消息字选择顺序也被改过
- 不能直接拿标准 `hashlib.md5()` 去复现结果

这题的 `sub_401500` 本质上是一个**以 MD5 为外形模板、但内部常量和轮次都被替换过的自定义 hash**。

已知在用户名 `KCTF` 下，程序内部实际得到的目标 hash（前 16 字节）为：

```text
0D15B8BA2C8F30576BD8A9AEC0C6DBFA
```

程序只用它的前三个 `_DWORD` 参与后续比较：

```text
0xBAB8150D
0x57308F2C
0xAEA9D86B
```

---

## 5. `sub_401AD0`：64x64 GF(2) 线性变换

`sub_401AD0` 结构如下：

```c
v13 = *a3 & *v10;
v11 = popcount(*a2 & *a1);
v6  = (popcount(v13) ^ v11) & 1 ^ (2 * v6);
```

其中：

- `sub_401AB0` 就是 `popcount`
- 最终只取奇偶性 `& 1`
- 所以每一轮输出的本质是：

```text
parity((data0 & mask1[i])) XOR parity((data1 & mask2[i]))
```

把 `data[0]`、`data[1]` 视为一个 64 位向量，
把 `maskKey1[i]`、`maskKey2[i]` 视为一个 64 位掩码，
那么这整个函数就是一个 **GF(2) 上的线性变换**。

关键点在于：

- 构造矩阵时，行顺序要按程序实际逻辑**倒序取**
- 第一组输出对应 `31-i`
- 第二组输出对应 `63-i`

正确矩阵构造方式如下：

```python
def build_key_matrix(mask1, mask2):
    M = [[0] * 64 for _ in range(64)]
    for i in range(32):
        key1 = ((mask2[31 - i] & 0xffffffff) << 32) | (mask1[31 - i] & 0xffffffff)
        key2 = ((mask2[63 - i] & 0xffffffff) << 32) | (mask1[63 - i] & 0xffffffff)
        for j in range(64):
            M[i][j] = (key1 >> j) & 1
            M[i + 32][j] = (key2 >> j) & 1
    return M
```

然后对这个 64x64 矩阵做 GF(2) 高斯消元求逆，就能把输出反解回输入。

---

## 6. 正确解法：先逆第二层，再逆第一层

程序校验顺序是：

```text
(x, y, z)
-> sub_401AD0((x, y), A1, A2)      得到 (h0, t)
-> sub_401AD0((t, z), B1, B2)      得到 (h1, h2)
```

而目标摘要的前三个 `_DWORD` 已知：

```text
h0 = 0xBAB8150D
h1 = 0x57308F2C
h2 = 0xAEA9D86B
```

所以逆向求解步骤应当是：

1. 先解第二层：
   ```text
   (t, z) <- inverse_B(h1, h2)
   ```
2. 再解第一层：
   ```text
   (x, y) <- inverse_A(h0, t)
   ```

本地复算得到：

```text
x = 0xA86CA89F
y = 0x77F81C3C
z = 0xFD2620F0
```

也就是最终注册码：

```text
A86CA89F 77F81C3C FD2620F0
```

---

## 7. 闭环验证

将上面的结果重新正向送回程序逻辑：

### 第一层
```text
sub_401AD0((0xA86CA89F, 0x77F81C3C), A1, A2)
= (0xBAB8150D, 0xA9DCA7E9)
```

### 第二层
```text
sub_401AD0((0xA9DCA7E9, 0xFD2620F0), B1, B2)
= (0x57308F2C, 0xAEA9D86B)
```

与目标完全对齐：

```text
0xBAB8150D
0x57308F2C
0xAEA9D86B
```

因此这组 serial 是闭环成立的。

---

## 8. 最终答案

```text
Name   : KCTF
Serial : A86CA89F 77F81C3C FD2620F0
```

---

## 9. 错误方向 vs 正确方向

这题中途我自己走错了几次，后面都已纠正，单独列出来：

### 错误方向 1：把 `sub_401500` 当成标准 MD5
**错误原因：**
看到初始化常量是 `67452301 / EFCDAB89 / 98BADCFE / 10325476`，直觉把它当成标准 MD5。

**为什么错：**
继续比对轮常量和消息字调度后，发现它只是“外形像 MD5”，内部是魔改的自定义 hash。

**正确方向：**
不能直接拿 `hashlib.md5()` 替代，必须以题目中的目标 hash / 轮函数实现为准。

---

### 错误方向 2：把参与摘要的输入串拼接顺序看反
**错误猜测：**
先后试过：

```text
KCTFFTCK
KCTFFTCKFTCKFTCK
```

**为什么错：**
核心逻辑实际是：

```text
reverse(name) * 3 + name
```

**正确方向：**
对 `KCTF` 应拼出：

```text
FTCKFTCKFTCKKCTF
```

---

### 错误方向 3：`sub_401AD0` 的矩阵行顺序没倒过来
**错误原因：**
前期虽然看出了这是 GF(2) 线性变换，但按自然顺序构矩阵，导致逆出来的 serial 一直不对。

**为什么错：**
程序实际取表时，行顺序对应：

```text
31-i
63-i
```

不是顺序正着读。

**正确方向：**
构矩阵时必须倒序取 key 行，才能得到和程序一致的逆变换。

---

### 错误方向 4：一度把公开 WP 当成“直接答案来源”
**错误原因：**
在自己静态还原已经比较深但还差最后一层时，主人发来了公开 WP 链接。若直接照搬最终 serial，会让本地分析链条断掉。

**正确处理：**
后续只把公开 WP 当作**差异定位器**：

- 用它确认自己错在“输入串顺序”和“矩阵倒序”这两个点
- 然后回到本地样本，把矩阵、逆变换、最终 serial 全部重新复算并闭环验证

因此本文最终结果不是“只抄答案”，而是：

```text
公开 WP 用于纠偏
+ 本地静态与脚本复算完成最终闭环
```

---

## 10. solve.py 说明

见同目录：

```text
exp/solve.py
```

脚本会：

1. 从解压样本中读取四组 mask 表
2. 用 GF(2) 高斯消元求逆矩阵
3. 以程序实际目标值 `BAB8150D / 57308F2C / AEA9D86B` 为输入
4. 逆出 `KCTF` 对应的最终注册码
5. 再正向加密一次，验证结果确实能回到目标值
