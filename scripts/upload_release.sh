#!/usr/bin/env bash
#
# 发布 ListScanner v1.0.0 到 GitHub Releases（将 ListScanner.exe 作为附件）
#
# 前置条件：
#   1. 已执行 git push（远程仓库已存在）
#   2. 已登录 GitHub CLI：  gh auth login
#
# 用法：
#   bash scripts/upload_release.sh
#
set -euo pipefail

VERSION="v1.0.0"
EXE="exe/ListScanner.exe"
NOTES="RELEASE-v1.0.0.md"

if [ ! -f "$EXE" ]; then
  echo "错误：未找到 $EXE，请先确认文件存在。" >&2
  exit 1
fi

if [ ! -f "$NOTES" ]; then
  echo "错误：未找到 $NOTES 发布说明文件。" >&2
  exit 1
fi

# 确保 gh 已登录
if ! gh auth status >/dev/null 2>&1; then
  echo "未登录 GitHub CLI，正在引导登录..."
  gh auth login
fi

echo "正在创建 Release $VERSION 并上传 $EXE ..."
gh release create "$VERSION" \
  --title "ListScanner $VERSION" \
  --notes-file "$NOTES" \
  "$EXE"

echo "完成！Release 地址："
gh release view "$VERSION" --web 2>/dev/null || true
