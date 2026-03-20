# 直言直语

## 状态

**已解出**

## 结果

- 最终 flag：`flag{973387a11fa3f724d74802857d3e052f}`

## 目录导航

- `writeup.md`：完整中文 writeup
- `exp/solve.py`：本地还原输入与校验流程的 solve 记录脚本
- `attachments/zyzy.zip`：题目原始附件

## 核心思路

```text
Win32 GUI / MFC 程序
-> 主校验函数 sub_402600
-> 花指令清理
-> sub_402AF0 先校验长度并提取 flag{} 内部 32 字节后倒序
-> sub_402CA0 / sub_402E80 为 RC4
-> key = qwertyuiop
-> 与内置 32 字节常量比较
-> 逆向恢复最终输入
```
