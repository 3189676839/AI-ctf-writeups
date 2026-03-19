# CORE CrackMe v2.0

## 状态

**已解出**

## 结果

- 用户名：`KCTF`
- 正确注册码：`A86CA89F 77F81C3C FD2620F0`

## 目录导航

- `writeup.md`：完整中文 writeup
- `exp/solve.py`：逆矩阵求解脚本
- `attachments/CORE_CRACKME3.zip`：题目原始附件

## 核心思路

```text
name -> reverse(name)*3 + name
-> 魔改 hash(sub_401500)
-> 两层 GF(2) 线性变换(sub_401AD0)
-> 逆矩阵解出 3 段 32 位十六进制注册码
```
