# CCG CrackMe crypto 1.0

## 状态

**已解出**

## 结果

- 用户名：`KCTF`
- 正确序列号：`0uUNukUQCw81NjE2ODk3MjA5ODYxMDgxODA1`

## 目录导航

- `writeup.md`：完整中文 writeup
- `exp/solve.py`：纯 Python 求解脚本
- `attachments/ccg_crackme_crypto.zip`：题目原始附件

## 核心思路

```text
MD5(name)
-> 前 8 字节走 RC4
-> 后 8 字节走 RSA 逆运算
-> 拼接后再 Base64
```
