# 看雪 2022 KCTF 春季赛 第十题《陷入轮回》复盘

## 题目定位
这题名义上是 Pwn，但本质更接近 **Reverse-first Pwn / VM Pwn**。

核心难点不在传统利用链，而在：
1. 还原合法输入格式
2. 理解 VM 指令语义
3. 找出 Rust 手写容器里的真实漏洞

---

## 一、官方/已有 WP 核心思路整理

### 1. 输入组织格式
程序会把输入组织成 `vec<vec<string>>`：
- 外层是若干 `block`
- 内层是每个 block 的若干 `line`

两个特殊控制行：
- `$`：结束当前块并开启下一块
- `#`：结束当前块并退出输入循环

这是整题最重要的入口层知识点。

### 2. 合法顶层指令
进入 `vmvec::start_vec` 后，按空格切分每行第一个单词，合法 opcode 包括：

- `//`
- `vec`
- `adj`
- `print`
- `cal`
- `cmd`
- `jmp`
- `je`
- `switch_stack`
- `halt`

说明这是一个自定义 VM。

### 3. VM 结构
题目维护：
- 两个 `StackVec` 栈（容量分别为 32 和 64）
- 一个整数数组 `vec<u64>`
- 一个字符串数组 `vec<string>`
- 多个名称到对象的 hashmap

部分指令作用：
- `vec int >>,0,1,2,...,`：向当前栈压数
- `vec xxx int >>,...`：创建命名整型数组
- `vec xxx str ...`：创建命名字符串数组
- `adj clear_stack ???`：清空当前栈
- `adj stack_move i`：移动当前栈元素
- `print`：打印栈顶
- `print xxx int/str`：打印命名数组
- `cal add/sub/mul/div ...`：做各种栈/寄存器间运算

### 4. 真正漏洞点
漏洞在 Rust 手写容器 `StackVec::push()`。

错误检查逻辑是：

```c
if (len > capacity) panic();
```

正确应该是：

```c
if (len >= capacity) panic();
```

因此当 `len == capacity` 时还能继续写，造成 **off-by-one 越界写**。

### 5. 利用原理
程序把两个 `StackVec` 相邻放在栈上，前一个栈溢出 1 个 `u64`，正好覆盖后一个栈的 `length`。

于是可以：
- 先污染第二个栈的长度
- 再借第二个栈实现更大范围 OOB 读写
- 最终泄漏 `__libc_start_main_ret`
- 覆盖返回地址到 one_gadget
- getshell 后读 `/flag`

### 6. 关键偏移
远端 libc 为 2.23：
- `__libc_start_main_ret` 偏移：`0x20840`
- one_gadget 偏移：`0xf1247`
- 差值：`0xf1247 - 0x20840 = 854535`

---

## 二、我自己的解题过程

### 1. 早期判断
我最初通过二进制符号和字符串看到了：
- `vmvec::main`
- `vmvec::start_vec`
- `vmvec::vec_comd::vec_ops`
- `vmvec::adjust_comd::adj_ops`
- `vmvec::print::print_op`
- `vmvec::stack_manage::*`
- `vmvec::jump::{jmp, je}`

以及一串 opcode：
- `vec`
- `adj`
- `print`
- `cal`
- `cmd`
- `jmp`
- `je`
- `switch_stack`
- `halt`

因此我很早就判断：

> 这不是传统裸栈溢出题，而是一个 Rust 自定义 VM / 解释器型 Pwn。

这个大方向是对的。

### 2. 我为什么会打偏
我没拿到已有 WP 之前，主要偏在两个地方：

#### （1）过早沉到指令层
我已经逆到很多 opcode，就开始不断猜：
- `halt`
- `vec/...`
- `cmd ...`
- `$#`
- `///`、`/`

但实际上我还没先搞清：

> 输入是怎么先被组织成 `vec<vec<string>>` 的。

所以研究了很多内层语法，但外层入口层还没过。

#### （2）误把 `$#` 当整体
我前期一度把 `$#` 视作一个整体分隔符，后来 WP 明确说明：
- `$` 是结束当前块并开启下一块
- `#` 是结束当前块并退出输入

这是我入口层理解错误的关键原因。

#### （3）对 Rust Pwn 的切入点不够“Rust化”
我虽然怀疑过：
- `StackVec`
- `switch_stack`
- `string_vec`

但前期更偏向研究 VM 逻辑漏洞和状态错乱。

而更高效的 Rust Pwn 审计思路应该是优先盯：
- `unsafe`
- `memcpy`
- 手写容器
- `len/capacity` 检查

### 3. 关键分界点
后面我逐渐意识到 `main.rs:101` 是绝对分界：
- 101 行前：输入组织 / block 构造阶段
- 101 行后：真正进入 VM 执行阶段

但这个意识来得稍晚，所以走了不少弯路。

---

## 三、拿到已有 WP 后，我自己补出来的新解法

我没有直接照抄“固定最终 payload 一把梭”的写法，而是做了一个 **两阶段自动化利用脚本**。

### 阶段 1：最小化 leak
先构造最小 OOB 读：

```text
vec int >>,0,1,2,3,...,63,646,
switch_stack
print
#
```

自动从远端读取 `__libc_start_main_ret`。

我实测从远端 `123.57.66.184:10014` 泄漏到：

```text
0x7f2cbb129840
```

### 阶段 2：动态计算 one_gadget
不直接“盲信”固定地址，而是程序里动态计算：

```python
one_gadget = leak - 0x20840 + 0xf1247
```

得到本次远端实例的目标地址：

```text
0x7f2cbb1fa247
```

### 阶段 3：第二次连接进行覆盖
第二次再发覆盖返回地址的 payload，最后：

```text
cat /flag*
```

成功获得：

```text
flag{83aa2416-88d9-4f66-99f8-83ed48c2c3a2}
```

### 这个新解法和已有 WP 的区别
相同点：
- 利用同一个主漏洞
- 最终仍然覆盖返回地址跳到 one_gadget

不同点：
- 我的写法更工程化
- 先 leak 再动态算目标地址
- 更适合复用成自动化 exploit 模板
- 对环境差异更稳

---

## 四、我还尝试过的“非主洞替代路线”

我在主洞打通后，还尝试寻找第二条路线，主要测试了：

### 1. `cmd`
结论：
- 至少需要两个栈元素
- 不是直接命令执行
- 不会简单回显系统命令结果

### 2. `print + hashmap`
结论：
- `print foo int` 和 `print foo str` 分开查不同映射
- 没有最简单的类型混淆

### 3. `vec str` / `print str`
这个点比较有意思：

```text
vec foo str >>,aa,bb,
print foo str
#
```

输出是：

```text
24929
25186
```

即：
- `aa` -> `0x6161` -> `24929`
- `bb` -> `0x6262` -> `25186`

说明 `print str` 不是正常字符串打印，而是把内容数值化后打印。这个行为异常，但我没有继续扩展成第二条稳定可利用路线。

### 结论
替代路线目前：
- 有研究价值
- 但未形成稳定 exploit 闭环
- 比起继续硬挖，主洞复盘更有收益

---

## 五、最终 flag

```text
flag{83aa2416-88d9-4f66-99f8-83ed48c2c3a2}
```

---

## 六、这题最值得记住的经验

### 1. 先确认入口层，再看指令层
对解释器 / VM 题，永远先分层：
- 入口层
- block 层
- 指令层

不能一上来就沉到 opcode。

### 2. Rust Pwn 优先找 unsafe / 手写容器 / memcpy
看到这些要优先审：
- `push`
- `insert`
- `pop`
- `truncate`
- `len/capacity`
- 指针复制 / `memcpy`

### 3. 主洞一旦闭环，替代路线要设止损
如果：
- 主洞已验证
- flag 已拿
- 替代路线只有“行为怪”没有“利用面”

就该收手，转入复盘。

---

## 七、一句话总结

这题不是“传统 Pwn 先找溢出再写 ROP”，而是：

> **先 Reverse 出 VM 的输入模型与指令语义，再从 Rust 手写容器中找到真正的边界检查错误，最后用工程化两阶段 leak+overwrite 拿 flag。**
