# rechall writeup

## 题目信息
- 题目：`rechall`
- 方向：`Reverse`
- 类型：Linux ELF / 输入校验
- 目标：从附件中恢复最终 flag

## 最终结果
- 最终 flag：`flag{e7f8f02a-90a38781-054d1c1b-0ddf83d6}`
- 程序对应输入：
  - `3891851306`
  - `2426636161`
  - `88939547`
  - `232752086`

---

## 1. 附件与样本基础信息

收到原始附件：

```text
/root/.openclaw/qqbot/downloads/rechall_1773968610348.zip
```

解压后只有一个文件：

```text
rechall
```

基础侦察结果：

```text
ELF 64-bit LSB pie executable, x86-64
动态链接
not stripped
```

`checksec` 结果：

```text
Full RELRO
Canary found
NX enabled
PIE enabled
```

这说明它不是靠漏洞利用，而是典型的逆向逻辑恢复题；同时因为 **未 strip**，函数名会直接暴露主逻辑结构。

---

## 2. 第一轮侦察：字符串直接暴露关键格式

直接跑 `strings` 就能看到最关键的几项：

```text
flag{%08x-%08x-%08x-%08x}
Right!
Your flag is: %s
Wrong!
checker1
checker2
checker3
checker4
md5_init
md5_update
md5_final
```

这个信息量已经非常大：

1. 程序最终会构造一个 `flag{...}` 格式的字符串
2. flag 内部是 **4 段 8 位十六进制**
3. 程序里有四个显式 checker
4. 后面还会做 MD5 校验

到这里就可以先做出高置信判断：

```text
输入 4 个数
-> 分别过 checker1~checker4
-> 拼成 flag 字符串
-> 做 MD5
-> 与内置常量比较
```

---

## 3. main 函数还原

反汇编 `main` 后，逻辑非常直接：

1. 连续四次 `scanf("%u", &x)`，读取 4 个无符号十进制整数
2. 分别调用：
   - `checker1(x1, 0x5294b771)`
   - `checker2(x2)`
   - `checker3(x3)`
   - `checker4(x4)`
3. 四关都通过后执行：

```c
sprintf(buf, "flag{%08x-%08x-%08x-%08x}", x1, x2, x3, x4);
```

4. 然后对这个字符串做标准 MD5
5. 最后把 MD5 结果和程序内置常量比较：

```text
f2 d5 f9 78 de 74 c1 ce 7a 9f f5 34 61 ca 3f d2
```

如果相等则输出：

```text
Right!
Your flag is: <flag>
```

否则输出：

```text
Wrong!
```

因此题目已经被完全拆成两个层次：

### 第一层
先把 4 个整数逆出来，使 `checker1~4` 全部通过。

### 第二层
如果某个 checker 存在多解，再用最终 MD5 常量判唯一正确解。

---

## 4. checker1：线性方程直接出解

`checker1` 伪代码：

```c
int checker1(unsigned int a, unsigned int b) {
    return (a - b == 0x956438b9) ? 0 : -1;
}
```

而主函数传入的第二个参数固定为：

```text
0x5294b771
```

所以：

```text
x1 - 0x5294b771 = 0x956438b9
x1 = 0x956438b9 + 0x5294b771 mod 2^32
x1 = 0xe7f8f02a
```

转成十进制：

```text
x1 = 3891851306
```

---

## 5. checker2：位运算表达式，唯一解

`checker2` 是一串 32 位位运算和加减法混合，最终要求：

```text
expr(x2) == 0xc2407eea
```

这类表达式手推当然可以，但没有必要。题目本身就是确定性的 32 位算术约束，最稳的方式是直接用 SMT 求解。

本地用 `z3` 建模后得到唯一解：

```text
x2 = 0x90a38781
```

十进制：

```text
x2 = 2426636161
```

---

## 6. checker3：带上界条件的 32 位约束

`checker3` 开头先卡了一个范围：

```c
if (x3 > 0x10000000) return -1;
```

然后又是一大串位运算，最后要求：

```text
expr(x3) == 0x251bc4bd
```

同样用 `z3` 建模，带上上界约束一起求解，得到唯一解：

```text
x3 = 0x054d1c1b
```

十进制：

```text
x3 = 88939547
```

这里的一个关键细节是：

```text
flag 格式使用的是 %08x
```

因此虽然 `0x054d1c1b` 的高位有前导 `0`，最终 flag 中这一段必须保留为 8 位：

```text
054d1c1b
```

---

## 7. checker4：存在两个候选，需要靠 MD5 判别

`checker4` 也有同样的上界：

```c
if (x4 > 0x10000000) return -1;
```

继续对它建模后，会发现它**不是唯一解**，而是有两个候选：

```text
0x0ddf83d6
0x0e5f83d6
```

即十进制：

```text
232752086
241140694
```

这一步非常关键：

- 如果只看到 `checker4` 通过，就贸然宣布答案，会出错
- 必须结合主函数最后的 MD5 比较做闭环验证

---

## 8. 最终 MD5 校验：筛掉假解

程序固定使用：

```c
sprintf(flag_buf, "flag{%08x-%08x-%08x-%08x}", x1, x2, x3, x4);
md5(flag_buf) == embedded_digest
```

其中内置 MD5 digest 为：

```text
f2d5f978de74c1ce7a9ff53461ca3fd2
```

把两个候选分别代入：

### 候选 1
```text
flag{e7f8f02a-90a38781-054d1c1b-0ddf83d6}
MD5 = f2d5f978de74c1ce7a9ff53461ca3fd2
```

### 候选 2
```text
flag{e7f8f02a-90a38781-054d1c1b-0e5f83d6}
MD5 = 0d77210702fe152373394498903d1191
```

只有 **候选 1** 命中程序内置 MD5，因此唯一正确结果为：

```text
flag{e7f8f02a-90a38781-054d1c1b-0ddf83d6}
```

---

## 9. 本地运行验证

将四个十进制输入喂给程序：

```text
3891851306
2426636161
88939547
232752086
```

程序输出：

```text
Right!
Your flag is: flag{e7f8f02a-90a38781-054d1c1b-0ddf83d6}
```

说明已经完整闭环。

---

## 10. 错误方向 vs 正确方向

### 错误方向 1：以为四个 checker 都会只有唯一解
**错误原因：**
前三个值求得很顺，容易自然假设第四个也唯一。

**为什么错：**
`checker4` 实际上存在两个满足局部约束的输入。

**正确方向：**
不能只停在“通过 checker4”，必须继续走到主函数最后一层 MD5 比较，做全链路验证。

---

### 错误方向 2：把 MD5 当成需要逆的主逻辑
**错误原因：**
看到 `md5_init / update / final`，容易第一反应想从 MD5 目标逆 flag。

**为什么错：**
这题并不是直接做 MD5 preimage，而是先通过 4 个 checker 把搜索空间压缩到极小，最后 MD5 只是**判真伪的最后一层筛子**。

**正确方向：**
优先逆前面的输入约束，再拿 MD5 做唯一性确认，难度会大幅下降。

---

## 11. solve.py 说明

见同目录：

```text
exp/solve.py
```

脚本做的事：

1. 直接按程序逻辑写出 `checker1~4` 的约束
2. 用 `z3` 求出 `x2/x3/x4`
3. 枚举 `x4` 的全部候选
4. 把所有候选拼成 `flag{%08x-%08x-%08x-%08x}`
5. 用内置 MD5 常量筛出唯一正确 flag

这样可以完整复现本题求解过程。

---

## 12. 最终答案

```text
flag{e7f8f02a-90a38781-054d1c1b-0ddf83d6}
```
