#!/bin/bash
# legal-doc-compare 一键安装脚本（适用于 Claude Code CLI 用户）

set -e

COMMANDS_DIR="$HOME/.claude/commands"
TEMPLATES_DIR="$HOME/.claude/templates"
SCRIPTS_DIR="$HOME/.claude/scripts"

echo "正在安装 legal-doc-compare skill..."

# 创建目录（如不存在）
mkdir -p "$COMMANDS_DIR" "$TEMPLATES_DIR" "$SCRIPTS_DIR"

# 检查源文件是否存在
MISSING=0
[ ! -f "commands/doc-compare.md" ] && echo "缺少文件：commands/doc-compare.md" && MISSING=1
[ ! -f "templates/doc-compare-summary.md" ] && echo "缺少文件：templates/doc-compare-summary.md" && MISSING=1
[ ! -f "scripts/verify-doc-compare.py" ] && echo "缺少文件：scripts/verify-doc-compare.py" && MISSING=1

if [ "$MISSING" -eq 1 ]; then
  echo ""
  echo "请确保在 legal-doc-compare 仓库根目录下运行此脚本。"
  exit 1
fi

# 复制文件
cp commands/doc-compare.md "$COMMANDS_DIR/"
cp templates/doc-compare-summary.md "$TEMPLATES_DIR/"
cp scripts/verify-doc-compare.py "$SCRIPTS_DIR/"

echo ""
echo "安装完成！"
echo ""
echo "在 Claude Code 中输入 /doc-compare 或说"对比两个版本"即可使用。"
echo ""
echo "（可选）如需启用 Playbook 比对，请将 Playbook.md 放置到 ~/.claude/ 目录下。"
