#!/bin/bash
# ============================================================
# 一键更新脚本 - 改完 CSV 后运行此脚本，云端网页自动更新
#
# 用法（在 Jupyter 单元格里）：
#   !bash 一键更新.sh
#
# 或在终端里：
#   bash 一键更新.sh
# ============================================================

set -e  # 出错即停

echo "========== 第1步：从 CSV 生成新 HTML =========="
python3 build_html.py

echo ""
echo "========== 第2步：复制为 index.html（GitHub Pages 需要）=========="
cp "素材维度分析看板.html" "index.html"
echo "已生成 index.html"

echo ""
echo "========== 第3步：提交到 GitHub =========="
git add -A
git commit -m "周更 $(date '+%Y-%m-%d %H:%M')"
git push

echo ""
echo "========== 完成！ =========="
echo "云端链接会在 1-2 分钟后自动更新（GitHub Pages 部署需要一点时间）"
echo "你的固定分享链接不变，刷新浏览器即可看到新数据"
