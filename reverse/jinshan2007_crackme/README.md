# CrackMe看雪.金山2007

## 状态

**已解出**

## 结果

- 用户名：`KCTF`
- 正确序列号：`38193105`

## 目录导航

- `writeup.md`：完整中文 writeup
- `exp/solve.py`：纯 Python 求解脚本
- `attachments/CrackMe.zip`：题目原始附件

## 核心思路

```text
Name -> 32位种子
Seed -> 初始 bit 状态
Serial 每位数字 -> 一次状态转移
最终将 9 个状态位全部点亮
```
