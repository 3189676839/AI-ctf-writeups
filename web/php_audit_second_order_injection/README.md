# PHP 代码审计 / 二次注入

## 状态

**已解出**

## 结果

- flag：`flag{99f447a5-78e3-4751-8335-fe4eb64cb636}`

## 目录导航

- `writeup.md`：中文 writeup
- `exp/README.md`：exp 说明
- `attachments/README.md`：附件说明

## 利用链摘要

```text
rename.php 二次注入 -> 修改数据库中的 extension 置空
-> 上传真实 jpg 木马 -> 再次重命名为 .php
-> getshell -> 读取 /flag_emmmmmmmmm
```
