# babyfirst / babyfirst-revenge / babyfirst-revenge-v2

## 状态

**阶段性分析记录，当前未统一形成最终通关 writeup**

## 1. babyfirst

已确认源码关键点：

```php
exec("/bin/orange " . implode(" ", $args));
```

参数过滤：

```php
preg_match('/^\w+$/', $args[$i])
```

### 已确认突破

- `^\w+$` 可被**末尾换行**绕过。
- 例如 `x\n` 能通过校验，从而把命令拆成多行，形成盲命令执行。
- 已验证 payload：

```text
?args[]=x%0A&args[]=touch&args[]=aaa
```

会成功创建 Web 可访问文件 `/aaa`，说明 blind RCE 成立。

### 当前结论

- `exec()` 不回显 stdout，后续利用必须围绕“写文件 / 拉二阶段 / 间接回显”展开。
- 已确认可用原语：`cp`、`install`、`tar cf`、`sed w目标 源文件`。
- 外带方面，`wget / ftpget / tftp` 是否可稳定使用，曾经没有完全确认；HTTP 外带也一度未打通。

## 2. babyfirst-revenge / revenge-v2

后续对同系列题做过变种区分，总结为：

- 当限制更像 `strlen(cmd) <= 5` 时，优先考虑原版：

```text
ls -t>g
```

文件名构造链。

- 当限制更像 `strlen(cmd) <= 4` 时，更接近：

```text
dir + * + rev
```

这条更严格的路线。

## 3. 经验总结

- 先辨别题目属于哪个长度限制变种。
- 先做最小 canary，例如 `STARTOK`、`START6`。
- 再判断问题出在：
  - payload 本身
  - VPS 二阶段脚本
  - 还是端口出网/网络环境

## 说明

当前工作区里没有找到能明确对应这组题目的最终可用 exp 文件，因此这里只保留已确认的中文分析记录，避免把无关脚本误传进仓库。
