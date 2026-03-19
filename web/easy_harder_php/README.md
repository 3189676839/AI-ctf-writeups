# easy_harder_php

## 状态

**已解出**

## 结果

- flag：`flag{15c294ce-500c-44bc-95f0-72c94a08c9dc}`

## 目录导航

- `writeup.md`：完整中文 writeup
- `exp/README.md`：exp 说明
- `attachments/README.md`：附件说明

## 利用链摘要

```text
备份源码泄露 -> signature SQLi -> 盲注确认 admin 密码 nu1ladmin
-> showmess() 反序列化 -> PHP 5.5 兼容 SoapClient 对象
-> SSRF/CRLF 本地登录 admin -> 管理员上传 -shell.php
-> 绕过 rm *.jpg 清理 -> 爆破真实文件名 -> LFI 包含执行 -> 读 flag
```
