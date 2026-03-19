# PHP 代码审计 / 二次注入 writeup

## 题目状态

已解出。

## 最终结果

- flag 路径：`/flag_emmmmmmmmm`
- flag：`flag{99f447a5-78e3-4751-8335-fe4eb64cb636}`

## 已确认的关键点

- `rename.php` 存在二次注入。
- `upload.php` 上传类型限制为：`gif / jpg / png / zip / txt`。
- 通过源码确认：`rename.php` 会把数据库中的 `filename` 再次拼回 SQL，导致二次注入触发。

## 利用思路

```text
先通过 rename 逻辑触发二次注入
-> 把数据库中的 extension 置空
-> 上传真实 jpg 木马
-> 再次重命名为 .php
-> getshell
-> 读取 /flag_emmmmmmmmm
```

## 说明

当前仓库里还没有找到这道题当时留下的原始 exp 或题目附件，因此本题先保留基于已确认解题记录整理的 writeup。
