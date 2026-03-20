# rechall

## 状态

**已解出**

## 结果

- 最终 flag：`flag{e7f8f02a-90a38781-054d1c1b-0ddf83d6}`
- 对应 4 个十进制输入：
  - `3891851306`
  - `2426636161`
  - `88939547`
  - `232752086`

## 目录导航

- `writeup.md`：完整中文 writeup
- `exp/solve.py`：本地复现求解脚本
- `attachments/rechall.zip`：题目原始附件

## 核心思路

```text
read 4 unsigned ints
-> checker1/checker2/checker3/checker4
-> sprintf("flag{%08x-%08x-%08x-%08x}")
-> MD5
-> compare with embedded 16-byte target
```
