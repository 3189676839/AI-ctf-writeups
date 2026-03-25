# KCTF2022 春第十题 陷入轮回

## 状态

**已解出**

## 结果

- flag：`flag{83aa2416-88d9-4f66-99f8-83ed48c2c3a2}`

## 目录导航

- `writeup.md`：完整中文 writeup（含你的 WP 整理 + 我的复盘 + 新解法）
- `exp/alt_solve.py`：我自己的两阶段自动化利用脚本
- `attachments/The_Mystery_of_Marie_Roget.rar`：题目原始附件
- `attachments/reference_wp.md`：你发来的参考 WP

## 核心思路

```text
先 Reverse 出输入如何组织成 vec<vec<string>> 与 VM 指令体系
-> 识别 Rust 手写容器 StackVec 的 push 边界检查错误
-> 前一个栈 off-by-one 覆盖后一个栈 length
-> 先 OOB 泄漏 __libc_start_main_ret
-> 再动态计算 one_gadget 并覆盖返回地址
-> getshell 后 cat /flag
```

## 关键反思

```text
这题表面是 Pwn，实质是 Reverse-first Pwn。
真正高效的切入方式不是一开始死磕 payload，而是先把入口层 / block 层 / 指令层分清，再用 Rust/unsafe 视角去找手写容器边界错误。
```
