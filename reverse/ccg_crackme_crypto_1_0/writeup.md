# CCG CrackMe crypto 1.0 writeup

## 题目信息
- 题目：`CCG CrackMe crypto 1.0`
- 方向：`Reverse`
- 类型：Win32 GUI / C + API / Crypto CrackMe
- 目标：对用户名 `KCTF` 计算出正确序列号，使程序弹框显示注册成功

## 最终结果
- 用户名：`KCTF`
- 正确序列号：`0uUNukUQCw81NjE2ODk3MjA5ODYxMDgxODA1`

---

## 1. 入口与主事件回调

入口点 `WinMain`：

```c
int __stdcall WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nShowCmd)
{
    dword_4171EC = (int)hInstance;
    dword_413118(hInstance, 101, 0, sub_401230, 101);
    return 0;
}
```

这是一个标准的对话框程序，核心回调在 `sub_401230`。

在消息 `273`（按钮点击）分支里，程序读取两个输入框：

- `1008`：Name
- `1007`：Serial

然后调用：

```c
sub_401610(&unk_417180, &unk_417100)
```

因此真正的校验函数就是：

```text
sub_401610(name, serial)
```

---

## 2. Serial 首先会被 Base64 解码

`sub_401020` 具备非常明显的 Base64 解码特征：

- 输入长度必须是 4 的倍数
- 每 4 个字符解出 3 个字节
- 结尾处理 `=` / `==`

因此：

```text
用户输入的 Serial 不是原始数据，而是一个 Base64 字符串
```

在 `sub_401610` 中：

```c
v4 = sub_401020(a2, v3, v2);
if ( v4 < 8u )
    fail;
```

说明 Base64 解码后长度必须至少为 8。

接着程序继续检查：

```c
v5 = 8;
if ( v4 > 8u ) {
    do {
        v6 = v3[v5];
        if ( v6 < 48 || v6 > 57 )
            fail;
    } while ( ++v5 < v4 );
}
```

也就是说，解码后的结构必须满足：

```text
decoded_serial = [前 8 字节二进制] + [十进制数字串]
```

最终用户输入格式为：

```text
Serial = Base64(prefix8 || decimal_digits)
```

---

## 3. Name 会先走 MD5

程序对 Name 的处理流程：

```c
sub_408310(v10);
v7 = strlen(name);
sub_408340(v10, name, v7);
sub_4085F0(v10);
```

其中：

- `sub_408340` 是标准 `MD5Update`
- `sub_4088A0` 是标准 `MD5Transform`
- 因此整个链就是 `MD5(name)`

对用户名 `KCTF`：

```text
MD5(KCTF) = 7a1ab1c6a2999f9797f5abd5b49fd9a0
```

拆成两部分：

- 前 8 字节：`7a1ab1c6a2999f97`
- 后 8 字节：`97f5abd5b49fd9a0`

---

## 4. 前 8 字节校验：RC4

程序里有两段非常明显的 RC4：

- `sub_408FF0`：RC4 KSA
- `sub_4090F0`：RC4 PRGA

密钥由：

```c
qmemcpy(v13, ")G\a", 3);
v13[3] = -123;
v13[4] = -121;
qmemcpy(v14, "3%D", sizeof(v14));
```

拼起来可得 8 字节 key：

```text
29 47 07 85 87 33 25 44
```

即：

```python
key = bytes.fromhex('2947078587332544')
```

程序执行：

```c
sub_408FF0(v13, 8, v15);
sub_4090F0(v3, 8, v15);
if ( memcmp(v11, v3, 8u) )
    fail;
```

也就是：

```text
对 decoded_serial 的前 8 字节做 RC4 变换后，结果必须等于 MD5(name) 的前 8 字节
```

因此要构造合法的 `prefix8`，只需要对 MD5 前 8 字节做同一 RC4 流的逆过程。由于 RC4 是异或流密码，加密/解密是同一个过程，所以：

```text
prefix8 = RC4(key, MD5(name)[:8])
```

对 `KCTF` 计算得到：

```text
prefix8 = d2 e5 0d ba 45 10 0b 0f
```

---

## 5. 数字后缀校验：RSA / 大整数模幂

程序后半段：

```c
sub_4071D0(v3 + 8, (int)&v16);      // 十进制字符串 -> 大整数
sub_4071D0(a65537, (int)&v17);      // e = 65537
sub_406ED0(aB80a90bf53c6c9, (int)&v18); // 十六进制字符串 -> n
sub_405E40(v16, v17, v18, &v19);    // v19 = v16^e mod n
sub_4014F0(v12, 8, v20);            // MD5 后 8 字节 -> hex string
sub_406ED0(v20, (int)v21);          // hex string -> bigint
if ( sub_402290(v21[0], v19) )
    fail;
else
    success;
```

这就是标准的：

```text
suffix^e mod n == c
```

其中：

- `e = 65537`
- `c = int(MD5(name)[8:16].hex(), 16)`

符号名 `aB80a90bf53c6c9` 被截断，但按程序语义和独立枚举可恢复出完整模数：

```text
n = 0xB80A90BF53C6C979
```

并且可分解为：

```text
n = 3533507051 * 3753090347
```

因此：

```text
phi(n) = (p-1)(q-1)
d = e^{-1} mod phi(n)
suffix = c^d mod n
```

对 `KCTF`：

```text
c = 0x97f5abd5b49fd9a0
suffix = 5616897209861081805
```

---

## 6. 最终拼装 Serial

现在已经得到：

```text
prefix8 = d2e50dba45100b0f
suffix  = 5616897209861081805
```

拼接原始 serial 数据：

```text
raw = prefix8 || b"5616897209861081805"
```

再进行 Base64 编码：

```text
Serial = Base64(raw)
```

最终得到：

```text
0uUNukUQCw81NjE2ODk3MjA5ODYxMDgxODA1
```

---

## 7. 最终答案

```text
Name   : KCTF
Serial : 0uUNukUQCw81NjE2ODk3MjA5ODYxMDgxODA1
```

---

## 8. 纯 Python 求解脚本

见同目录：

```text
exp/solve.py
```

脚本会：

1. 计算 `MD5(name)`
2. 用固定 RC4 key 计算前缀 8 字节
3. 计算 RSA 数字后缀
4. Base64 编码输出最终序列号

---

## 9. 核心思路总结

这题不是“爆破序列号”，而是标准的**组合型算法校验**：

```text
MD5(name)
-> 前 8 字节走 RC4
-> 后 8 字节走 RSA 逆运算
-> 拼接后再 Base64
```

所以本题最关键的识别点是：

- `sub_401020` 的 Base64 特征
- `sub_408340/sub_4088A0` 的 MD5 特征
- `sub_408FF0/sub_4090F0` 的 RC4 特征
- `sub_4071D0/sub_406ED0/sub_405E40` 的大整数 / RSA 特征
