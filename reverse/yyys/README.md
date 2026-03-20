# yyys

## 状态

**已解出**

## 结果

- 最终注册码 / 序列号：`BZ9dmq4c8g9G7bAY`
- 运行时邮箱填写任意**合法格式**值即可，例如：`a@b.c`

## 目录导航

- `writeup.md`：完整中文 writeup
- `exp/solve.py`：求解记录脚本（直接输出恢复出的序列号）
- `attachments/yyys.zip`：题目原始附件

## 核心思路

```text
ASPack 壳 -> 脱壳
-> 定位 DialogBoxParamW 对话框回调
-> GetDlgItemTextA 读取邮箱与序列号
-> 先校验邮箱格式
-> 再在回调里逐字符恢复 16 字节 serial
```
