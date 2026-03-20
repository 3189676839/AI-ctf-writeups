# 跃跃欲试 writeup

## 题目信息
- 题目：`跃跃欲试`
- 方向：`Reverse`
- 类型：Win32 GUI / CrackMe / ASPack
- 目标：恢复正确注册码（题目中可视作 flag）

## 最终结果
- 正确注册码 / 序列号：`BZ9dmq4c8g9G7bAY`
- 邮箱框只需填写任意合法格式值，例如：`a@b.c`

---

## 1. 附件与样本基础信息

收到原始附件：

```text
/root/.openclaw/qqbot/downloads/yyys_1773969403495.zip
```

解压后仅有一个文件：

```text
yyys.exe
```

基础侦察结果：

```text
PE32 executable for MS Windows 5.01 (GUI), Intel i386, 7 sections
```

节区中有非常明显的壳特征：

```text
.text
.rdata
.data
.rsrc
.reloc
.aspack
.adata
```

而且程序入口点直接落在 `.aspack`：

```text
AddressOfEntryPoint = 0x17001
VA = 0x417001
```

导入表也极少，只剩下：

```text
GetProcAddress
GetModuleHandleA
LoadLibraryA
DialogBoxParamW
```

这说明当前看到的是典型的 **ASPack 壳入口**，真正逻辑还没展开。

---

## 2. 第一步：确认是 ASPack 壳，不要误把壳代码当业务逻辑

最开始直接看入口反汇编，会看到大量：

- `pushad / popad`
- 内存展开
- 重定位修复
- 导入表修复
- 跳回真实 OEP

这类代码的目标不是校验序列号，而是：

```text
把原程序解压、修复 IAT、修复重定位，再转交给真实入口
```

因此这里不能急着在壳层字符串里找注册码，要先把壳拆掉。

---

## 3. 脱壳：使用 unipacker 成功导出真实程序

本地直接尝试 `upx -d` 无效，因为它不是 UPX：

```text
NotPackedException: not packed by UPX
```

随后改用 `unipacker` 对 ASPack 壳做模拟执行脱壳，成功导出：

```text
/tmp/yyys_unpack/unpacked_yyys.exe
```

日志中能看到：

```text
Fixing sections
Fixing SizeOfImage
Fixing Memory Protection of Sections
Dumping state to /tmp/yyys_unpack/unpacked_yyys.exe
```

这一步完成后，真实 OEP 变为：

```text
AddressOfEntryPoint = 0x16bb
VA = 0x4016bb
```

并且导入表被恢复，出现了完整 GUI 相关 API：

```text
DialogBoxParamW
GetDlgItemTextA
GetDlgItem
MessageBoxA
EndDialog
SetClassLongA
LoadIconW
LoadCursorW
```

到这里才算真正进入题目逻辑分析阶段。

---

## 4. 定位主入口：这是一个对话框程序

脱壳后 `main` 很短，核心就一件事：

```c
DialogBoxParamW(hInstance, 101, 0, 0x401020, 0);
```

说明：

- 对话框资源 ID = `101`
- 对话框回调函数 = `0x401020`

也就是说，**真正的序列号校验函数就在这个回调里**。

---

## 5. 对话框回调：读取两个输入框

在 `0x401020` 这段逻辑里，很快就能看到对 `GetDlgItemTextA` 的调用：

```text
GetDlgItemTextA(hDlg, 1001, email_buf, 0x100)
GetDlgItemTextA(hDlg, 1002, serial_buf, 0x100)
```

因此可以确定这两个输入框分别是：

- `1001`：邮箱
- `1002`：序列号

同时还可看到消息分发：

- `WM_INITDIALOG = 0x110`
- `WM_COMMAND = 0x111`
- `wParam low word == 1`，说明这是点击某个按钮后进入校验逻辑

---

## 6. 邮箱校验：先判断格式合法性

回调里先对邮箱字符串做检查，若失败会跳到错误提示：

```text
Your E-mail address in not valid.
```

从汇编行为可以看出，它至少检查了：

1. 邮箱中存在 `@`
2. `@` 后面还有内容
3. 后续还要出现 `.`
4. 各段不能是空串

也就是说，这一关并不要求特定邮箱内容，只要求**格式像正常邮箱**。

因此运行时填任意简单合法值即可，例如：

```text
a@b.c
```

这一点很关键：

```text
邮箱不是 flag 的一部分
它只是前置格式门槛
```

---

## 7. 序列号长度：必须是 16 字符

邮箱通过后，程序开始检查序列号：

```asm
sub ecx, edx
cmp ecx, 0x10
jne fail
```

也就是：

```text
strlen(serial) == 16
```

因此序列号长度被严格卡死为 **16**。

---

## 8. 序列号恢复：逐字符约束直接可解

最关键的部分在 `0x4011a4 ~ 0x40129f` 一段。

这里不是哈希，也不是复杂加密，而是直接对 16 个字符逐位做约束。汇编形态包括：

- 直接比较某个位置等于某字符
- 两个位置相加等于某常量
- 某个位置加上固定偏移等于某常量
- 某个位置减固定偏移后等于某字符

我把对应约束还原如下：

### 第 0 位
```text
serial[0] == 'B'
```
因为：
```text
cmp byte ptr [...], 0x42
```

### 第 15 位
```text
serial[15] + 0x42 == 0x9b
=> serial[15] == 0x59 == 'Y'
```

### 第 1 位
```text
serial[1] - 3 == 0x57
=> serial[1] == 0x5a == 'Z'
```

### 第 14 位
```text
serial[14] + serial[1] == 0x9b
=> serial[14] = 0x9b - 0x5a = 0x41 = 'A'
```

### 第 2 位
```text
serial[2] + 1 == 0x3a
=> serial[2] == 0x39 == '9'
```

### 第 13 位
```text
serial[13] + serial[2] == 0x9b
=> serial[13] = 0x9b - 0x39 = 0x62 = 'b'
```

### 第 3 位
```text
serial[3] == 'd'
```

### 第 12 位
```text
serial[12] + 0x64 == 0x9b
=> serial[12] == 0x37 == '7'
```

### 第 4 位
```text
serial[4] == 'm'
```

### 第 11 位
```text
serial[11] + 0x81 == 0xc8
=> serial[11] == 0x47 == 'G'
```

### 第 5 位
```text
serial[5] - 0x2d == 0x44
=> serial[5] == 0x71 == 'q'
```

### 第 10 位
```text
serial[10] + serial[5] == 0xaa
=> serial[10] = 0xaa - 0x71 = 0x39 == '9'
```

### 第 6 位
```text
serial[6] == '4'
```

### 第 9 位
```text
serial[9] + 0x34 == 0x9b
=> serial[9] == 0x67 == 'g'
```

### 第 7 位
```text
serial[7] == 'c'
```

### 第 8 位
```text
serial[8] + 0x63 == 0x9b
=> serial[8] == 0x38 == '8'
```

将 0~15 位串起来：

```text
B Z 9 d m q 4 c 8 g 9 G 7 b A Y
```

最终得到：

```text
BZ9dmq4c8g9G7bAY
```

---

## 9. 成功/失败分支

回调后面有两种消息文本：

```text
Registeration
Your E-mail address in not valid.
Registration fai...
...Your flag...
```

成功分支会把恢复出的序列号带入拼好的提示文本，失败分支则弹错误消息框。

虽然样本字符串在 `.rdata` 中有拼接/重叠现象，导致肉眼看上去有些混乱，但从控制流可以确认：

- 邮箱不合法 -> 弹邮箱格式错误
- 序列号不对 -> 弹注册失败
- 全部通过 -> 进入成功提示

而在静态还原中，16 字符序列号已经闭环恢复完成。

---

## 10. 错误方向 vs 正确方向

### 错误方向 1：在 ASPack 壳层直接找注册码
**错误原因：**
样本初始导入表非常少，入口落在 `.aspack`，如果这时直接在入口附近硬逆，看到的大多是壳的解压/IAT 修复代码。

**为什么错：**
这些代码不属于业务逻辑，只是壳的自举流程。

**正确方向：**
先脱壳，恢复真实 OEP 与真实导入表，再看对话框回调和业务逻辑。

---

### 错误方向 2：把邮箱当成参与注册码计算的核心输入
**错误原因：**
程序同时读取邮箱和序列号，容易直觉认为注册码可能和邮箱绑定。

**为什么错：**
当前样本中邮箱只用于**格式合法性检查**，并没有参与后续 16 位序列号的字符约束生成。

**正确方向：**
邮箱只要满足合法格式即可；真正的答案是固定 16 位 serial。

---

### 错误方向 3：把成功字符串中的 “Your flag” 当成需要额外解密的内容
**错误原因：**
`.rdata` 中成功/失败字符串有重叠、拼接痕迹，视觉上会让人误以为还藏了第二层 flag。

**为什么错：**
当前主校验逻辑已经直接恢复出唯一 16 位注册码，题面所说的序列号本身就是最终答案。

**正确方向：**
把题目按 CrackMe/序列号题处理，输出恢复出的正确 serial 即可。

---

## 11. solve 记录

本题不需要复杂爆破。solve 过程本质是：

1. 脱 ASPack 壳
2. 定位 `DialogBoxParamW` 回调
3. 确认 `GetDlgItemTextA` 读取邮箱与 serial
4. 先识别邮箱格式检查
5. 从回调汇编中逐项恢复 16 个字符约束
6. 组合得到最终注册码

同目录 `exp/solve.py` 里给出的是一个**求解记录脚本**：

- 直接把从汇编恢复出的约束写成 Python
- 最后输出序列号 `BZ9dmq4c8g9G7bAY`

它的作用是**记录恢复过程和结果**，而不是动态攻击程序。

---

## 12. 最终答案

```text
Serial: BZ9dmq4c8g9G7bAY
```

运行示例：

```text
E-mail : a@b.c
Serial : BZ9dmq4c8g9G7bAY
```
