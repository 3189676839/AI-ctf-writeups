# babytrick

## 状态

**已解出**

## 结果

- flag：`flag{ba5193ad-9cf2-4fc5-a922-9d7a0da4f567}`

## 目录导航

- `writeup.md`：完整中文 writeup
- `exp/exp.py`：最终命中 exp
- `exp/README.md`：exp 说明
- `attachments/README.md`：附件说明

## 老链与新链区别

### 老链（公开 WP 常见）

```text
CVE-2016-7124 -> 跳过 __wakeup -> show() SQLi -> 读 orange 密码 -> login() -> flag
```

### 新链（当前实例实际命中）

```text
当前 PHP 5.6.40 已修复 7124
-> 直接构造 login() 反序列化 payload
-> ORÄNGE 绕过 orange 过滤
-> 使用已知密码 babytrick1234
-> 直接返回 flag
```
