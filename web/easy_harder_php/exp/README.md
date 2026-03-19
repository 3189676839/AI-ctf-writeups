# exp 说明

这道题的完整 exp 已经写入 `../writeup.md` 的“完整 exp”章节中。

当前没有再单独拆出独立脚本文件，原因是：

- 利用过程中包含了同 session 验证码求解
- PHP 5.5 + soap 兼容对象生成
- 管理员会话劫持
- 文件名爆破与 LFI 包含

如果后续需要，我可以再把 `writeup.md` 中的完整 exp 单独提取为 `exp.py`。
