# one-line-php-challenge

## 状态

**未在当前实例打通**

## 已确认结论

- 题目源码核心为：

```php
($_=@$_GET['orange']) && @substr(file($_)[0],0,6) === '@<?php' ? include($_) : highlight_file(__FILE__);
```

- 已确认官方主链是：

```text
PHP_SESSION_UPLOAD_PROGRESS + session 文件 + triple base64-decode + race
```

- 但在当前实战实例中，多轮验证都没有稳定命中，倾向于说明：
  - 当前题机环境和公开 writeup 默认环境存在差异
  - 不能机械照搬官方 exp

## 当前目录

- `exp_one_line_php_py3.py`：历史实验脚本，保留作复现参考

## 说明

这题目前保留的是**分析记录**和**历史 exp**，不是最终通关 writeup。
如果后续用户提供新的可用实例，可以在此目录继续补充完整解法。
