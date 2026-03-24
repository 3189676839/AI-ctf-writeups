# KCTF2022 春第六题 BROP

## 状态

**已解出**

## 结果

- flag：`flag{1654821f-980b-42ac-a638-32b33d94029a}`

## 目录导航

- `writeup.md`：完整中文 writeup
- `exp/exp.py`：最终命中 exp

## 核心思路

```text
边界测试确认 15/16 字节分界
-> 结合题目 WP 校正程序模型
-> 确认基址 0x400000、readRet=0x4000EE、sysCall=0x400100
-> 先用 SROP 泄露 ELF 头验证同源性
-> 两段式 SROP：read(0, .bss, 0x400) -> execve('/bin/sh', 0, 0)
-> cat /flag
```

## 关键反思

```text
这题虽然题面写 BROP，但真正高效路径不是长期盲扫 gadget，
而是尽快切到“极小 ELF + syscall + SROP”模型。
```
