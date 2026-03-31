# legal-doc-compare

适用于 [Claude Code](https://claude.ai/code) 的 PE/VC 法律文件跨轮次对比分析 skill，面向非诉律师和法务人员。

## 功能简介

- **自动制备对比版**：仅提供前后两版clean文本即可，自动生成 diff 标注版
- **修订登记**：区分实质修订、新投资人新增享有原股东权利（但股东权利机制不变）、wording调整，强制前置登记防止遗漏
- **融资数据测算**：从 SHA 附表 / captable 自动提取客户具体股比，确保相关数据核对无误
- **法律分析**：结合谈判立场（强势 / 中立 / 弱势）以及客户身份，对每处实质修订出具风险等级与谈判建议
- **矛盾条款核查**：跨文件比对，识别 SPA、SHA、章程、决议等文件间的条款冲突
- **总结输出**：固定章节结构，以 .docx 格式交付，含修订登记表附录

## 文件结构

```
legal-doc-compare/
├── commands/
│   └── doc-compare.md          # skill 主文件（放入 ~/.claude/commands/）
├── templates/
│   └── doc-compare-summary.md  # 简式总结输出模板（放入 ~/.claude/templates/）
└── scripts/
    └── verify-doc-compare.py   # 报告完整性验证脚本（放入 ~/.claude/scripts/）
```

## 安装方法                                                                                           
                                                            
前提：已安装 [Claude Code](https://claude.ai/code)
                                                                                                        
将三个文件复制到对应的 Claude Code 配置目录：

```bash
cp commands/doc-compare.md ~/.claude/commands/
cp templates/doc-compare-summary.md ~/.claude/templates/
cp scripts/verify-doc-compare.py ~/.claude/scripts/
```

## 配置 Playbook（可选）

本 skill 在法律分析环节支持与使用者自备的 PE/VC 谈判 Playbook 进行比对。如需启用：

1. 准备一份 Playbook 文件（Markdown 格式），记录你在各类条款（反稀释、优先清算、回购权等）上的标准立场与红线
2. 将文件放置在 `~/.claude/` 目录下
3. 在 `doc-compare.md` 第 4.3 节中更新引用路径

若未配置 Playbook，skill 仍可正常运行，Playbook 比对环节将跳过。

## 使用方式

在 Claude Code 中触发以下任意关键词即可自动调用：

> "对比"、"比较"、"前后轮"、"修订了哪些"、"有什么变化"、"审阅（含多版本文件）"

或直接执行：

```
/doc-compare
```

## 支持的输入格式

- 已有对比版（含 `[INS]` / `[DEL]` 标注的 .docx）
- 前后两版净文本（PDF、DOCX、TXT 均可），skill 自动制备 diff 版

## 验证脚本

`verify-doc-compare.py` 用于核查报告完整性，支持双向核查：

```bash
python3 ~/.claude/scripts/verify-doc-compare.py \
  --report <报告.md> \
  --docs <对比版文件夹路径>
```

- **正向核查**：对比文件有修订 → 报告中是否覆盖
- **反向核查**：报告中分析的条款 → 对比文件是否有修订支撑

依赖：`lxml`（`pip install lxml`）

## 适用场景

- PE/VC 投资：SPA、SHA、股东协议、公司章程跨轮次对比
- 投后管理：修订版文件与原版比对
- 重组 / 上市前整改：全套文件修订总结

## License

Apache-2.0
