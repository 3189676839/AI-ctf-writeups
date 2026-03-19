# PHP 代码审计 / 二次注入

## 状态

**已解出**

## 题目概况

- 类型：Web
- 关键考点：二次注入、文件上传、后缀控制、重命名逻辑利用
- flag：`flag{99f447a5-78e3-4751-8335-fe4eb64cb636}`

## 已确认的关键信息

- 目标站点中：`rename.php` 存在二次注入。
- `upload.php` 上传类型限制为：`gif / jpg / png / zip / txt`。
- 通过源码确认：`rename.php` 会把数据库中的 `filename` 再次拼回 SQL，导致二次注入触发。
- 后续利用链为：

```text
先通过 rename 逻辑触发二次注入
-> 把数据库中的 extension 置空
-> 上传真实 jpg 木马
-> 再次重命名为 .php
-> getshell
-> 读取 /flag_emmmmmmmmm
```

## 结果

- flag 路径：`/flag_emmmmmmmmm`
- flag：`flag{99f447a5-78e3-4751-8335-fe4eb64cb636}`

## 说明

当前仓库里还没有找到这道题当时留下的原始 exp 或附件，因此先保留已确认的中文解题摘要。后续如果补到当时的脚本或附件，再继续追加。
