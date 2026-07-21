#!/usr/bin/env python3
"""一键更新看板 - 改完 CSV 后运行此脚本，云端网页自动更新

用法（在 Jupyter 单元格里）：
    !python3 一键更新.py

或在终端里：
    python3 一键更新.py
"""
import base64, json, os, shutil, subprocess, sys, urllib.request, urllib.parse, urllib.error

# ============ 配置 ============
OWNER = 'suxx-1234'
REPO = 'sucai-dashboard'
BRANCH = 'main'
BASE = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(BASE, '.github_token')

# ============ 读取 Token ============
if not os.path.exists(TOKEN_FILE):
    print(f'❌ 找不到 token 文件：{TOKEN_FILE}')
    print('   请创建 .github_token 文件，写入你的 GitHub Personal Access Token')
    sys.exit(1)
with open(TOKEN_FILE) as f:
    TOKEN = f.read().strip()

# ============ 第1步：从 CSV 生成新 HTML ============
print('=' * 50)
print('第1步：从 CSV 生成新 HTML')
print('=' * 50)
subprocess.check_call([sys.executable, os.path.join(BASE, 'build_html.py')])

# 复制为 index.html（GitHub Pages 需要）
shutil.copy(
    os.path.join(BASE, '素材维度分析看板.html'),
    os.path.join(BASE, 'index.html')
)
print('已生成 index.html')

# ============ 第2步：上传到 GitHub ============
print()
print('=' * 50)
print('第2步：上传到 GitHub')
print('=' * 50)

def upload_file(repo_path, local_path):
    """上传单个文件到 GitHub（已存在则更新）"""
    with open(local_path, 'rb') as f:
        content = base64.b64encode(f.read()).decode('utf-8')
    encoded = urllib.parse.quote(repo_path)
    url = f'https://api.github.com/repos/{OWNER}/{REPO}/contents/{encoded}'

    # 先查当前文件的 SHA（更新已存在文件需要）
    sha = None
    try:
        req = urllib.request.Request(
            f'{url}?ref={BRANCH}',
            headers={'Authorization': f'token {TOKEN}', 'Accept': 'application/vnd.github+json'}
        )
        resp = urllib.request.urlopen(req)
        sha = json.loads(resp.read()).get('sha')
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise

    # 上传
    payload = {
        'message': f'周更 {repo_path}',
        'content': content,
        'branch': BRANCH,
    }
    if sha:
        payload['sha'] = sha
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=data, method='PUT',
        headers={'Authorization': f'token {TOKEN}', 'Content-Type': 'application/json',
                 'Accept': 'application/vnd.github+json'}
    )
    resp = urllib.request.urlopen(req)
    status = resp.status
    print(f'  ✓ {repo_path} (HTTP {status})')

# 上传 index.html（网页内容）
upload_file('index.html', os.path.join(BASE, 'index.html'))

# 上传 CSV（数据源备份，可选）
upload_file('素材维度分析_完整大表.csv', os.path.join(BASE, '素材维度分析_完整大表.csv'))

# ============ 完成 ============
print()
print('=' * 50)
print('✅ 完成！')
print('=' * 50)
print(f'分享链接（不变）：')
print(f'  https://{OWNER}.github.io/{REPO}/')
print()
print('云端会在 1-2 分钟后自动更新（GitHub Pages 部署需要时间）')
print('刷新浏览器即可看到新数据（Cmd+R 或 Ctrl+R）')
