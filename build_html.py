#!/usr/bin/env python3
"""构建素材维度数据分析网页 - 单文件 HTML

可移植用法：
  1. 把本脚本和「素材维度分析_完整大表.csv」放在同一个文件夹
  2. 运行 python3 build_html.py
  3. 同目录下生成「素材维度分析看板.html」

也可以用命令行参数指定 CSV 路径和输出路径：
  python3 build_html.py --csv /path/to/素材维度分析_完整大表.csv --out /path/to/看板.html
"""
import csv, json, os, sys, argparse

# 脚本所在目录，作为默认工作目录（不再硬编码本机路径）
BASE = os.path.dirname(os.path.abspath(__file__))

# 维度列与指标列定义（与「素材维度分析_完整大表.csv」列顺序一致）
DIMS = ['主体', '内容', '类型', '痛点', '打点', '打点分桶', '呈现方式',
        '演员', '编导', '后期', '投放剪辑', '制作月份', '是否投放双开头']
METRICS = ['消耗', '转化数', '录入数', 't0加微数', '当月录入当月邀约数',
           '当月录入当月初诊数', '当月录入当月首付费数', '当月录入当月付费金额',
           'T0加微率', '当月当期邀约率', '当月当期到诊率', '当月当期付费总金额',
           '当月当期客单价', '当月当期ROI']
# 需要按字符串保留、不能被 Excel/JSON 当数字处理的列
STR_COLS = {'素材ID', '制作月份'}


def to_num(val):
    """把 CSV 字符串转成数字；空串/无法解析则返回空串（保持与原 data.json 一致）"""
    if val is None or val == '':
        return ''
    try:
        f = float(val)
        if f.is_integer():
            return int(f)
        return f
    except (ValueError, TypeError):
        return val


def load_data(csv_path):
    """直接从「素材维度分析_完整大表.csv」构建看板所需的 JSON 数据结构"""
    with open(csv_path, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        records = []
        dim_options = {d: [] for d in DIMS}
        seen = {d: set() for d in DIMS}
        for row in reader:
            rec = {}
            for k, v in row.items():
                k = (k or '').strip()
                if k in STR_COLS:
                    rec[k] = (v or '').strip()
                elif k in METRICS:
                    rec[k] = to_num((v or '').strip())
                else:
                    rec[k] = (v or '').strip()
            records.append(rec)
            for d in DIMS:
                v = rec.get(d, '')
                if v != '' and v not in seen[d]:
                    seen[d].add(v)
                    dim_options[d].append(v)
        # 与历史 data.json 保持一致：各维度候选值按字符串升序排序
        for d in DIMS:
            dim_options[d] = sorted(dim_options[d])
        return {
            'records': records,
            'dims': DIMS,
            'metrics': METRICS,
            'dim_options': dim_options,
        }


def main():
    parser = argparse.ArgumentParser(description='构建素材维度数据分析网页')
    parser.add_argument('--csv', default=os.path.join(BASE, '素材维度分析_完整大表.csv'),
                        help='源 CSV 路径（默认与脚本同目录）')
    parser.add_argument('--out', default=os.path.join(BASE, '素材维度分析看板.html'),
                        help='输出 HTML 路径（默认与脚本同目录）')
    args = parser.parse_args()

    csv_path = os.path.abspath(args.csv)
    out_path = os.path.abspath(args.out)

    if not os.path.exists(csv_path):
        # 兜底：同目录没有 CSV 时，尝试用旧的 data.json
        data_json = os.path.join(BASE, 'data.json')
        if os.path.exists(data_json):
            with open(data_json, 'r', encoding='utf-8') as f:
                DATA = json.load(f)
            print(f'⚠️ 未找到 CSV：{csv_path}，已回退使用旧 data.json')
        else:
            print(f'❌ 找不到源数据：{csv_path}')
            print('   请把「素材维度分析_完整大表.csv」与本脚本放在同一目录，或用 --csv 指定路径。')
            sys.exit(1)
    else:
        DATA = load_data(csv_path)
        print(f'已读取源数据：{csv_path}（{len(DATA["records"])} 条素材）')

    global DATA_JSON
    DATA_JSON = json.dumps(DATA, ensure_ascii=False)
    build(out_path)


def build(out_path):
    # 真正写入 HTML 的部分放在 build() 里，DATA_JSON 已由 main() 准备好
    html = HTML_TEMPLATE.replace('__DATA__', DATA_JSON)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'OK: {out_path} ({len(html)} chars)')


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>素材维度数据分析</title>
<script src="https://unpkg.com/vue@3/dist/vue.global.prod.js"></script>
<style>
:root{
  --primary:#2563eb; --primary-dark:#1d4ed8; --primary-light:#eff6ff;
  --bg:#f8fafc; --card:#ffffff; --border:#e2e8f0; --border-light:#f1f5f9;
  --text:#1e293b; --text-sub:#64748b; --text-light:#94a3b8;
  --thead:#f8fafc; --hover:#f1f5f9;
  --red:#dc2626; --green:#16a34a; --amber:#d97706;
  --shadow:0 1px 3px rgba(0,0,0,.04), 0 1px 2px rgba(0,0,0,.06);
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;font-size:14px;line-height:1.5}
button{font-family:inherit;cursor:pointer;border:none;background:none}
input,select{font-family:inherit;font-size:14px}

/* Header */
.header{background:linear-gradient(135deg,#1e3a8a 0%,#2563eb 100%);color:#fff;padding:18px 28px;box-shadow:0 2px 8px rgba(0,0,0,.1)}
.header h1{font-size:20px;font-weight:600;display:flex;align-items:center;gap:10px}
.header .sub{opacity:.85;font-size:13px;margin-top:4px}
.header .stats{display:flex;gap:24px;margin-top:12px;font-size:12px}
.header .stats span b{font-size:16px;font-weight:600;margin-right:4px}

/* Tabs */
.tabs{background:var(--card);border-bottom:1px solid var(--border);padding:0 28px;display:flex;gap:4px}
.tab{padding:14px 20px;font-size:14px;color:var(--text-sub);border-bottom:2px solid transparent;transition:all .2s;font-weight:500}
.tab:hover{color:var(--primary)}
.tab.active{color:var(--primary);border-bottom-color:var(--primary);background:linear-gradient(180deg,transparent 0%,var(--primary-light) 100%)}

/* Layout */
.container{display:flex;gap:20px;padding:20px 28px;align-items:flex-start}
.sidebar{width:280px;background:var(--card);border-radius:10px;box-shadow:var(--shadow);padding:18px;position:sticky;top:20px;max-height:calc(100vh - 40px);overflow-y:auto;flex-shrink:0}
.main{flex:1;min-width:0}

/* Sidebar sections */
.sb-section{margin-bottom:18px;padding-bottom:18px;border-bottom:1px solid var(--border-light)}
.sb-section:last-child{border-bottom:none;margin-bottom:0;padding-bottom:0}
.sb-title{font-size:13px;font-weight:600;color:var(--text);margin-bottom:10px;display:flex;align-items:center;justify-content:space-between}
.sb-title .badge{font-size:11px;background:var(--primary-light);color:var(--primary);padding:2px 8px;border-radius:10px;font-weight:500}

/* Chips */
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{display:inline-flex;align-items:center;gap:4px;padding:5px 11px;border:1px solid var(--border);border-radius:16px;background:#fff;font-size:12px;color:var(--text-sub);transition:all .15s;user-select:none}
.chip:hover{border-color:var(--primary);color:var(--primary)}
.chip.active{background:var(--primary);border-color:var(--primary);color:#fff}
.chip .x{opacity:.6;margin-left:2px}

/* Radio group */
.radio-group{display:flex;flex-direction:column;gap:6px}
.radio-row{display:flex;align-items:center;gap:8px;padding:6px 10px;border-radius:6px;cursor:pointer;font-size:13px;color:var(--text-sub)}
.radio-row:hover{background:var(--hover)}
.radio-row.active{background:var(--primary-light);color:var(--primary);font-weight:500}
.radio-row input{accent-color:var(--primary)}

/* Search */
.search{width:100%;padding:8px 12px;border:1px solid var(--border);border-radius:6px;font-size:13px;outline:none;transition:border .2s}
.search:focus{border-color:var(--primary);box-shadow:0 0 0 3px rgba(37,99,235,.1)}

/* Multi-select dropdown */
.ms-wrap{position:relative;margin-bottom:10px}
.ms-label{font-size:12px;color:var(--text-sub);margin-bottom:4px;font-weight:500}
.ms-trigger{display:flex;align-items:center;justify-content:space-between;padding:6px 10px;border:1px solid var(--border);border-radius:6px;background:#fff;font-size:12px;cursor:pointer;min-height:32px}
.ms-trigger:hover{border-color:var(--primary)}
.ms-trigger .placeholder{color:var(--text-light)}
.ms-trigger .count{background:var(--primary);color:#fff;border-radius:10px;padding:1px 7px;font-size:11px;margin-left:6px}
.ms-trigger .arrow{color:var(--text-light);transition:transform .2s}
.ms-wrap.open .ms-trigger .arrow{transform:rotate(180deg)}
.ms-panel{position:fixed;background:#fff;border:1px solid var(--border);border-radius:8px;box-shadow:0 8px 24px rgba(0,0,0,.12);z-index:1000;max-height:280px;overflow-y:auto;padding:6px}
.ms-search{width:100%;padding:6px 10px;border:1px solid var(--border);border-radius:4px;font-size:12px;margin-bottom:6px;outline:none}
.ms-search:focus{border-color:var(--primary)}
.ms-item{display:flex;align-items:center;gap:8px;padding:6px 8px;border-radius:4px;cursor:pointer;font-size:12px;color:var(--text);transition:background .1s;user-select:none}
.ms-item:hover{background:var(--hover)}
.ms-item input{accent-color:var(--primary)}
.ms-actions{display:flex;justify-content:space-between;padding:4px 8px;font-size:11px;color:var(--primary);border-top:1px solid var(--border-light);margin-top:4px}
.ms-actions button{padding:4px 6px;border-radius:4px}
.ms-actions button:hover{background:var(--primary-light)}

/* Card */
.card{background:var(--card);border-radius:10px;box-shadow:var(--shadow);overflow:hidden;margin-bottom:16px}
.card-header{padding:14px 18px;border-bottom:1px solid var(--border-light);display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px}
.card-header h3{font-size:15px;font-weight:600}
.card-header .desc{font-size:12px;color:var(--text-sub);margin-top:2px}
.card-tools{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.card-body{padding:0}

/* Buttons */
.btn{padding:7px 14px;border-radius:6px;font-size:13px;font-weight:500;transition:all .15s;display:inline-flex;align-items:center;gap:6px;border:1px solid var(--border);background:#fff;color:var(--text)}
.btn:hover{border-color:var(--primary);color:var(--primary)}
.btn-primary{background:var(--primary);color:#fff;border-color:var(--primary)}
.btn-primary:hover{background:var(--primary-dark);color:#fff}
.btn-sm{padding:5px 10px;font-size:12px}

/* Table */
.tbl-wrap{overflow-x:auto;max-height:calc(100vh - 320px);overflow-y:auto}
table{width:100%;border-collapse:collapse;font-size:13px}
thead{position:sticky;top:0;background:var(--thead);z-index:10}
thead th{padding:10px 12px;text-align:left;font-weight:600;color:var(--text-sub);border-bottom:2px solid var(--border);white-space:nowrap;font-size:12px;text-transform:uppercase;letter-spacing:.03em;user-select:none}
thead th.sortable{cursor:pointer}
thead th.sortable:hover{color:var(--primary)}
thead th .sort-icon{margin-left:4px;opacity:.5;font-size:10px}
thead th.sorted .sort-icon{opacity:1;color:var(--primary)}
tbody td{padding:9px 12px;border-bottom:1px solid var(--border-light);white-space:nowrap}
tbody tr:hover{background:var(--hover)}
tbody tr:last-child td{border-bottom:none}
.num{text-align:right;font-variant-numeric:tabular-nums;font-family:"SF Mono",Menlo,Consolas,monospace;font-size:12.5px}
.dim-cell{color:var(--text);font-weight:500}
.empty-row{text-align:center;padding:40px;color:var(--text-light)}
.material-name{max-width:280px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;display:inline-block;vertical-align:middle}

/* ROI cell coloring (Chinese convention: red=up, green=down) */
.roi-up{color:var(--red);font-weight:600}
.roi-down{color:var(--green);font-weight:600}
.roi-flat{color:var(--text-sub)}

/* Pagination */
.pagination{display:flex;align-items:center;gap:8px;padding:12px 18px;border-top:1px solid var(--border-light);font-size:13px;color:var(--text-sub);flex-wrap:wrap;justify-content:space-between}
.pagination .info{font-size:12px}
.pagination .controls{display:flex;align-items:center;gap:4px}
.pagination button{padding:5px 10px;border:1px solid var(--border);border-radius:4px;background:#fff;color:var(--text);font-size:12px}
.pagination button:hover:not(:disabled){border-color:var(--primary);color:var(--primary)}
.pagination button:disabled{opacity:.4;cursor:not-allowed}
.pagination button.active{background:var(--primary);color:#fff;border-color:var(--primary)}
.pagination select{padding:4px 8px;border:1px solid var(--border);border-radius:4px;font-size:12px;background:#fff}

/* Summary stats bar */
.summary-bar{display:flex;gap:0;background:var(--card);border-radius:10px;box-shadow:var(--shadow);overflow:hidden;margin-bottom:16px}
.summary-item{flex:1;padding:14px 18px;border-right:1px solid var(--border-light)}
.summary-item:last-child{border-right:none}
.summary-item .label{font-size:11px;color:var(--text-sub);text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px}
.summary-item .value{font-size:18px;font-weight:600;font-variant-numeric:tabular-nums}
.summary-item .value.red{color:var(--red)}
.summary-item .value.green{color:var(--green)}

/* Empty state */
.empty-state{text-align:center;padding:60px 20px;color:var(--text-light)}
.empty-state .icon{font-size:36px;margin-bottom:8px;opacity:.4}
.empty-state .text{font-size:13px}

/* Scrollbar */
::-webkit-scrollbar{width:8px;height:8px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:#cbd5e1;border-radius:4px}
::-webkit-scrollbar-thumb:hover{background:#94a3b8}

/* Responsive */
@media (max-width: 1024px){
  .container{flex-direction:column}
  .sidebar{width:100%;position:static;max-height:none}
}
</style>
</head>
<body>
<div id="app">
  <!-- Header -->
  <div class="header">
    <h1>📊 素材维度数据分析</h1>
    <div class="sub">基于「素材维度分析_完整大表」365 条素材数据 · 13 个维度 · 14 项指标</div>
    <div class="stats">
      <span><b>{{ formatNum(totalConsumption) }}</b>总消耗</span>
      <span><b>{{ formatNum(totalConversion) }}</b>总转化数</span>
      <span><b>{{ formatNum(totalPayAmount) }}</b>当月付费金额</span>
      <span><b>{{ totalROI.toFixed(2) }}</b>整体ROI</span>
    </div>
  </div>

  <!-- Tabs -->
  <div class="tabs">
    <button class="tab" :class="{active:tab==='agg'}" @click="tab='agg'">① 多维度聚合分析</button>
    <button class="tab" :class="{active:tab==='detail'}" @click="tab='detail'">② 素材明细筛选</button>
    <button class="tab" :class="{active:tab==='dist'}" @click="tab='dist'">③ 维度分布统计</button>
  </div>

  <!-- ============ Module 1: 多维度聚合 ============ -->
  <div class="container" v-show="tab==='agg'">
    <div class="sidebar">
      <!-- 维度选择 -->
      <div class="sb-section">
        <div class="sb-title">分组维度 <span class="badge">{{ aggDims.length }} 已选</span></div>
        <div class="chips">
          <button v-for="d in dims" :key="d" class="chip" :class="{active:aggDims.includes(d)}" @click="toggleAggDim(d)">{{ d }}</button>
        </div>
        <div style="margin-top:8px;font-size:11px;color:var(--text-light)">点击选择一个或多个维度作为分组依据</div>
      </div>

      <!-- 指标选择 -->
      <div class="sb-section">
        <div class="sb-title">聚合指标 <span class="badge">{{ aggMetrics.length }} 已选</span></div>
        <div class="chips">
          <button v-for="m in metrics" :key="m" class="chip" :class="{active:aggMetrics.includes(m)}" @click="toggleAggMetric(m)">{{ m }}</button>
        </div>
      </div>

      <!-- 聚合方式 -->
      <div class="sb-section">
        <div class="sb-title">聚合方式</div>
        <div class="radio-group">
          <label class="radio-row" :class="{active:aggFunc==='sum'}"><input type="radio" v-model="aggFunc" value="sum"> 总和（求和）</label>
          <label class="radio-row" :class="{active:aggFunc==='mean'}"><input type="radio" v-model="aggFunc" value="mean"> 平均值</label>
          <label class="radio-row" :class="{active:aggFunc==='count'}"><input type="radio" v-model="aggFunc" value="count"> 计数（素材数）</label>
          <label class="radio-row" :class="{active:aggFunc==='weighted'}"><input type="radio" v-model="aggFunc" value="weighted"> 加权计算（率指标）</label>
        </div>
        <div style="margin-top:6px;font-size:11px;color:var(--text-light)">"加权"针对率类指标按分子/分母汇总，数值指标仍求和</div>
      </div>

      <!-- 操作 -->
      <div class="sb-section">
        <button class="btn btn-primary" style="width:100%" @click="exportAggCSV">⬇ 下载聚合结果 CSV</button>
        <button class="btn" style="width:100%;margin-top:8px" @click="resetAgg">↺ 重置选择</button>
      </div>
    </div>

    <div class="main">
      <!-- 顶部统计 -->
      <div class="summary-bar">
        <div class="summary-item"><div class="label">分组数</div><div class="value">{{ aggRows.length }}</div></div>
        <div class="summary-item"><div class="label">覆盖素材</div><div class="value">{{ formatNum(aggCoverCount) }}</div></div>
        <div class="summary-item"><div class="label">消耗合计</div><div class="value">¥{{ formatNum(aggConsumption) }}</div></div>
        <div class="summary-item"><div class="label">付费金额合计</div><div class="value">¥{{ formatNum(aggPayAmount) }}</div></div>
        <div class="summary-item"><div class="label">综合ROI</div><div class="value" :class="aggROI>=1?'red':'green'">{{ aggROI.toFixed(2) }}</div></div>
      </div>

      <!-- 聚合表格 -->
      <div class="card">
        <div class="card-header">
          <div>
            <h3>多维度聚合结果</h3>
            <div class="desc">按 <b>{{ aggDims.length ? aggDims.join(' / ') : '请选择维度' }}</b> 分组，{{ aggFuncText }}</div>
          </div>
          <div class="card-tools">
            <input class="search" style="width:200px" placeholder="搜索分组值..." v-model="aggSearch">
          </div>
        </div>
        <div class="card-body">
          <div class="tbl-wrap">
            <table v-if="aggRows.length">
              <thead>
                <tr>
                  <th v-for="d in aggDims" :key="'h-'+d" class="sortable" :class="{sorted:aggSortKey===d}" @click="aggSort(d)">{{ d }} <span class="sort-icon">{{ aggSortIcon(d) }}</span></th>
                  <th class="num">素材数</th>
                  <th v-for="m in aggMetrics" :key="'h-'+m" class="sortable num" :class="{sorted:aggSortKey===m}" @click="aggSort(m)">{{ m }} <span class="sort-icon">{{ aggSortIcon(m) }}</span></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, idx) in aggRowsPaged" :key="idx">
                  <td v-for="d in aggDims" :key="d" class="dim-cell">{{ row[d] || '(空)' }}</td>
                  <td class="num">{{ row.__count }}</td>
                  <td v-for="m in aggMetrics" :key="m" class="num" :class="metricClass(m, row[m])">{{ formatMetric(m, row[m]) }}</td>
                </tr>
              </tbody>
              <tfoot v-if="aggRows.length > 1">
                <tr style="background:var(--thead);font-weight:600">
                  <td :colspan="aggDims.length">合计（{{ aggRows.length }} 组）</td>
                  <td class="num">{{ aggTotalRow.__count }}</td>
                  <td v-for="m in aggMetrics" :key="m" class="num" :class="metricClass(m, aggTotalRow[m])">{{ formatMetric(m, aggTotalRow[m]) }}</td>
                </tr>
              </tfoot>
            </table>
            <div v-else class="empty-state">
              <div class="icon">🗂️</div>
              <div class="text" v-if="!aggDims.length">请选择至少一个分组维度</div>
              <div class="text" v-else>无匹配数据</div>
            </div>
          </div>
          <div class="pagination" v-if="aggRows.length">
            <div class="info">共 {{ aggRowsFiltered.length }} 组 · 第 {{ aggPage }} / {{ aggTotalPages }} 页</div>
            <div class="controls">
              <button @click="aggPage=1" :disabled="aggPage===1">«</button>
              <button @click="aggPage--" :disabled="aggPage===1">‹</button>
              <span style="padding:0 8px">{{ aggPage }} / {{ aggTotalPages }}</span>
              <button @click="aggPage++" :disabled="aggPage===aggTotalPages">›</button>
              <button @click="aggPage=aggTotalPages" :disabled="aggPage===aggTotalPages">»</button>
              <select v-model.number="aggPageSize">
                <option :value="20">20/页</option>
                <option :value="50">50/页</option>
                <option :value="100">100/页</option>
                <option :value="9999">全部</option>
              </select>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- ============ Module 2: 素材明细筛选 ============ -->
  <div class="container" v-show="tab==='detail'">
    <div class="sidebar">
      <!-- 关键词搜索 -->
      <div class="sb-section">
        <div class="sb-title">关键词搜索</div>
        <input class="search" placeholder="素材名称 / 素材ID..." v-model="keyword">
      </div>

      <!-- 维度筛选 -->
      <div class="sb-section">
        <div class="sb-title">维度筛选 <span class="badge">{{ activeDimFilters }} 项</span></div>
        <div v-for="d in dims" :key="d" class="ms-wrap" :class="{open: openDropdown===d}">
          <div class="ms-label">{{ d }}</div>
          <div class="ms-trigger" @click.stop="toggleDropdown(d, $event)">
            <span v-if="!filters[d].length" class="placeholder">全部</span>
            <span v-else>
              {{ filters[d].slice(0,2).join(', ') }}<span v-if="filters[d].length>2">...</span>
              <span class="count">{{ filters[d].length }}</span>
            </span>
            <span class="arrow">▾</span>
          </div>
          <div class="ms-panel" v-show="openDropdown===d" :style="panelStyle()">
            <input class="ms-search" placeholder="搜索..." v-model="dimSearch[d]" @click.stop>
            <label class="ms-item" v-for="v in filteredDimOptions(d)" :key="v">
              <input type="checkbox" :value="v" v-model="filters[d]">
              <span>{{ v }}</span>
            </label>
            <div class="ms-actions">
              <button @click.stop="filters[d]=[]">清空</button>
              <button @click.stop="filters[d]=dimOptions[d].slice()">全选</button>
            </div>
          </div>
        </div>
      </div>

      <!-- 操作 -->
      <div class="sb-section">
        <button class="btn btn-primary" style="width:100%" @click="exportDetailCSV">⬇ 下载筛选结果 CSV</button>
        <button class="btn" style="width:100%;margin-top:8px" @click="resetFilters">↺ 重置筛选</button>
      </div>
    </div>

    <div class="main">
      <!-- 顶部统计 -->
      <div class="summary-bar">
        <div class="summary-item"><div class="label">筛选结果</div><div class="value">{{ filteredRecords.length }} 条</div></div>
        <div class="summary-item"><div class="label">消耗合计</div><div class="value">¥{{ formatNum(detailConsumption) }}</div></div>
        <div class="summary-item"><div class="label">转化数合计</div><div class="value">{{ formatNum(detailConversion) }}</div></div>
        <div class="summary-item"><div class="label">付费金额合计</div><div class="value">¥{{ formatNum(detailPayAmount) }}</div></div>
        <div class="summary-item"><div class="label">综合ROI</div><div class="value" :class="detailROI>=1?'red':'green'">{{ detailROI.toFixed(2) }}</div></div>
      </div>

      <div class="card">
        <div class="card-header">
          <div>
            <h3>素材明细</h3>
            <div class="desc">点击表头排序 · {{ filteredRecords.length }} / {{ records.length }} 条素材</div>
          </div>
          <div class="card-tools">
            <select v-model="detailColumnSet" style="padding:6px 10px;border:1px solid var(--border);border-radius:6px;font-size:12px">
              <option value="all">显示全部列</option>
              <option value="key">仅核心列</option>
              <option value="dim">仅维度列</option>
              <option value="metric">仅指标列</option>
            </select>
          </div>
        </div>
        <div class="card-body">
          <div class="tbl-wrap">
            <table v-if="filteredRecords.length">
              <thead>
                <tr>
                  <th style="width:50px" class="num">#</th>
                  <th v-for="c in detailColumns" :key="c" class="sortable" :class="{sorted:detailSortKey===c, num:isMetric(c)}" @click="detailSort(c)">{{ c }} <span class="sort-icon">{{ detailSortIcon(c) }}</span></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(r, idx) in detailPaged" :key="r['素材ID']">
                  <td class="num">{{ (detailPage-1)*detailPageSize + idx + 1 }}</td>
                  <td v-for="c in detailColumns" :key="c" :class="{num:isMetric(c), 'dim-cell':!isMetric(c)}">
                    <span v-if="c==='素材名称'" class="material-name" :title="r[c]">{{ r[c] }}</span>
                    <span v-else :class="metricClass(c, r[c])">{{ formatMetric(c, r[c]) }}</span>
                  </td>
                </tr>
              </tbody>
            </table>
            <div v-else class="empty-state">
              <div class="icon">🔍</div>
              <div class="text">没有匹配的素材，请调整筛选条件</div>
            </div>
          </div>
          <div class="pagination" v-if="filteredRecords.length">
            <div class="info">共 {{ filteredRecords.length }} 条 · 第 {{ detailPage }} / {{ detailTotalPages }} 页</div>
            <div class="controls">
              <button @click="detailPage=1" :disabled="detailPage===1">«</button>
              <button @click="detailPage--" :disabled="detailPage===1">‹</button>
              <span style="padding:0 8px">{{ detailPage }} / {{ detailTotalPages }}</span>
              <button @click="detailPage++" :disabled="detailPage===detailTotalPages">›</button>
              <button @click="detailPage=detailTotalPages" :disabled="detailPage===detailTotalPages">»</button>
              <select v-model.number="detailPageSize">
                <option :value="20">20/页</option>
                <option :value="50">50/页</option>
                <option :value="100">100/页</option>
              </select>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- ============ Module 3: 维度分布统计 ============ -->
  <div class="container" v-show="tab==='dist'">
    <div class="sidebar">
      <!-- 统计维度选择 -->
      <div class="sb-section">
        <div class="sb-title">统计维度 <span class="badge">{{ distDims.length }} 已选</span></div>
        <div class="chips">
          <button v-for="d in dims" :key="d" class="chip" :class="{active:distDims.includes(d)}" @click="toggleDistDim(d)">{{ d }}</button>
        </div>
        <div style="margin-top:8px;font-size:11px;color:var(--text-light)">每个选中维度输出一张分布表</div>
      </div>

      <!-- 额外统计指标 -->
      <div class="sb-section">
        <div class="sb-title">附加指标 <span class="badge">{{ distMetrics.length }} 已选</span></div>
        <div class="chips">
          <button v-for="m in metrics" :key="m" class="chip" :class="{active:distMetrics.includes(m)}" @click="toggleDistMetric(m)">{{ m }}</button>
        </div>
        <div style="margin-top:8px;font-size:11px;color:var(--text-light)">素材数+占比为固定列，可附加其他指标汇总</div>
      </div>

      <!-- 排序方式 -->
      <div class="sb-section">
        <div class="sb-title">排序方式</div>
        <div class="radio-group">
          <label class="radio-row" :class="{active:distSort==='count_desc'}"><input type="radio" v-model="distSort" value="count_desc"> 素材数降序（默认）</label>
          <label class="radio-row" :class="{active:distSort==='count_asc'}"><input type="radio" v-model="distSort" value="count_asc"> 素材数升序</label>
          <label class="radio-row" :class="{active:distSort==='cost_desc'}"><input type="radio" v-model="distSort" value="cost_desc"> 按消耗降序排序</label>
          <label class="radio-row" :class="{active:distSort==='value_asc'}"><input type="radio" v-model="distSort" value="value_asc"> 按维度值排序</label>
        </div>
      </div>

      <!-- 显示选项 -->
      <div class="sb-section">
        <div class="sb-title">显示选项</div>
        <div class="radio-group">
          <label class="radio-row"><input type="checkbox" v-model="distShowBar"> 显示占比条形图</label>
          <label class="radio-row"><input type="checkbox" v-model="distShowEmpty"> 包含空值项</label>
        </div>
      </div>

      <!-- 操作 -->
      <div class="sb-section">
        <button class="btn btn-primary" style="width:100%" @click="exportDistCSV">⬇ 下载全部分布 CSV</button>
        <button class="btn" style="width:100%;margin-top:8px" @click="resetDist">↺ 重置选择</button>
      </div>
    </div>

    <div class="main">
      <!-- 顶部统计 -->
      <div class="summary-bar">
        <div class="summary-item"><div class="label">统计维度数</div><div class="value">{{ distDims.length }}</div></div>
        <div class="summary-item"><div class="label">总素材数</div><div class="value">{{ records.length }}</div></div>
        <div class="summary-item"><div class="label">总维度值数</div><div class="value">{{ distTotalValues }}</div></div>
        <div class="summary-item"><div class="label">平均每维值数</div><div class="value">{{ distAvgValues }}</div></div>
        <div class="summary-item"><div class="label">最高频值</div><div class="value" style="font-size:13px">{{ distTopValue }}</div></div>
      </div>

      <!-- 各维度分布卡片 -->
      <div v-for="d in distDims" :key="'dist-'+d" class="card">
        <div class="card-header">
          <div>
            <h3>{{ d }} 分布</h3>
            <div class="desc">{{ getDistData(d).length }} 个值 · 共 {{ records.length }} 条素材</div>
          </div>
          <div class="card-tools">
            <button class="btn btn-sm" @click="exportSingleDistCSV(d)">⬇ 导出此表</button>
          </div>
        </div>
        <div class="card-body">
          <div class="tbl-wrap" style="max-height:none">
            <table>
              <thead>
                <tr>
                  <th>{{ d }}</th>
                  <th class="num">素材数</th>
                  <th class="num">占比</th>
                  <th class="num" style="min-width:180px">分布可视化</th>
                  <th v-for="mc in expandDistMetricColumns(d)" :key="mc.key" class="num">{{ mc.label }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, idx) in getDistData(d)" :key="idx">
                  <td class="dim-cell">{{ row.value || '(空)' }}</td>
                  <td class="num"><b>{{ row.count }}</b></td>
                  <td class="num">{{ (row.percent * 100).toFixed(1) }}%</td>
                  <td class="num">
                    <div v-if="distShowBar" style="display:flex;align-items:center;gap:6px">
                      <div style="flex:1;height:18px;background:var(--border-light);border-radius:3px;overflow:hidden;min-width:100px">
                        <div :style="`width:${(row.percent*100).toFixed(1)}%;height:100%;background:linear-gradient(90deg,#3b82f6,#2563eb);border-radius:3px`"></div>
                      </div>
                      <span style="font-size:11px;color:var(--text-sub);min-width:36px">{{ (row.percent*100).toFixed(1) }}%</span>
                    </div>
                    <span v-else style="font-size:11px;color:var(--text-light)">—</span>
                  </td>
                  <td v-for="mc in expandDistMetricColumns(d)" :key="mc.key" class="num" :class="mc.type==='metric'?metricClass(mc.baseKey||mc.key, row[mc.key]):''">
                    <template v-if="mc.type==='metric'">
                      {{ formatMetric(mc.baseKey||mc.key, row[mc.key]) }}
                    </template>
                    <template v-else-if="distShowBar">
                      <div style="display:flex;align-items:center;gap:6px">
                        <div style="flex:1;height:18px;background:var(--border-light);border-radius:3px;overflow:hidden;min-width:100px">
                          <div :style="`width:${(row[mc.key]*100).toFixed(1)}%;height:100%;background:linear-gradient(90deg,#3b82f6,#2563eb);border-radius:3px`"></div>
                        </div>
                        <span style="font-size:11px;color:var(--text-sub);min-width:36px">{{ (row[mc.key]*100).toFixed(1) }}%</span>
                      </div>
                    </template>
                    <template v-else>
                      {{ (row[mc.key]*100).toFixed(1) }}%
                    </template>
                  </td>
                </tr>
              </tbody>
              <tfoot>
                <tr style="background:var(--thead);font-weight:600">
                  <td>合计</td>
                  <td class="num">{{ records.length }}</td>
                  <td class="num">100.0%</td>
                  <td class="num"></td>
                  <td v-for="mc in expandDistMetricColumns(d)" :key="mc.key" class="num" :class="mc.type==='metric'?metricClass(mc.baseKey||mc.key, getDistTotal(d, mc.baseKey||mc.key)):''">
                    <template v-if="mc.type==='metric'">
                      {{ formatMetric(mc.baseKey||mc.key, getDistTotal(d, mc.baseKey||mc.key)) }}
                    </template>
                    <template v-else-if="distShowBar">
                      <div style="display:flex;align-items:center;gap:6px">
                        <div style="flex:1;height:18px;background:var(--border-light);border-radius:3px;overflow:hidden;min-width:100px">
                          <div style="width:100%;height:100%;background:linear-gradient(90deg,#3b82f6,#2563eb);border-radius:3px"></div>
                        </div>
                        <span style="font-size:11px;color:var(--text-sub);min-width:36px">100.0%</span>
                      </div>
                    </template>
                    <template v-else>
                      100.0%
                    </template>
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      </div>

      <div v-if="!distDims.length" class="card">
        <div class="empty-state">
          <div class="icon">📊</div>
          <div class="text">请选择至少一个统计维度</div>
        </div>
      </div>
    </div>
  </div>
</div>

<script>
const DATA = __DATA__;
const { createApp, ref, computed, reactive, watch, onMounted, nextTick } = Vue;

createApp({
  setup() {
    const records = DATA.records;
    const dims = DATA.dims;
    const metrics = DATA.metrics;
    const dimOptions = DATA.dim_options;

    // 率类指标（按加权方式计算）
    const ratioMetrics = ['T0加微率','当月当期邀约率','当月当期到诊率','当月当期ROI','当月当期客单价'];
    // 率指标的分子分母定义
    const ratioDefs = {
      'T0加微率': { num: 't0加微数', den: '录入数' },
      '当月当期邀约率': { num: '当月录入当月邀约数', den: '录入数' },
      '当月当期到诊率': { num: '当月录入当月初诊数', den: '当月录入当月邀约数' },
      '当月当期ROI': { num: '当月录入当月付费金额', den: '消耗' },
      '当月当期客单价': { num: '当月录入当月付费金额', den: '当月录入当月首付费数' }
    };
    const isRatio = m => ratioMetrics.includes(m);
    const isMetric = c => metrics.includes(c);

    // ===== 全局汇总 =====
    const toNum = v => (v===''||v==null||isNaN(v))?0:Number(v);
    const totalConsumption = records.reduce((s,r)=>s+toNum(r['消耗']),0);
    const totalConversion = records.reduce((s,r)=>s+toNum(r['转化数']),0);
    const totalPayAmount = records.reduce((s,r)=>s+toNum(r['当月录入当月付费金额']),0);
    const totalROI = totalPayAmount / totalConsumption;

    const formatNum = n => {
      if (!isFinite(n)) return '0';
      if (Math.abs(n) >= 100000000) return (n/100000000).toFixed(2) + '亿';
      if (Math.abs(n) >= 10000) return (n/10000).toFixed(2) + '万';
      return Math.round(n).toLocaleString();
    };
    const formatMetric = (m, v) => {
      if (v===''||v==null) return '-';
      if (m === '素材ID') return String(v);
      if (isMetric(m)) {
        const n = Number(v);
        if (!isFinite(n)) return '-';
        if (isRatio(m)) return n.toFixed(2) + (m==='当月当期ROI'?'':'%');
        if (m.includes('金额') || m.includes('消耗') || m.includes('客单价') || m.includes('总金额')) return '¥' + n.toLocaleString(undefined,{maximumFractionDigits:2});
        return n.toLocaleString();
      }
      return String(v);
    };
    const metricClass = (m, v) => {
      if (m === '当月当期ROI') {
        const n = Number(v);
        if (!isFinite(n)) return '';
        if (n >= 1) return 'roi-up';
        if (n < 1) return 'roi-down';
      }
      return '';
    };

    // ===== Tab =====
    const tab = ref('agg');

    // ===== Module 1: 多维度聚合 =====
    const aggDims = ref(['主体','类型']);
    const aggMetrics = ref(['消耗','当月录入当月付费金额','当月当期ROI']);
    const aggFunc = ref('sum');
    const aggSearch = ref('');
    const aggSortKey = ref('');
    const aggSortDir = ref('desc');
    const aggPage = ref(1);
    const aggPageSize = ref(20);

    const toggleAggDim = d => {
      const i = aggDims.value.indexOf(d);
      if (i >= 0) aggDims.value.splice(i, 1);
      else aggDims.value.push(d);
      aggPage.value = 1;
    };
    const toggleAggMetric = m => {
      const i = aggMetrics.value.indexOf(m);
      if (i >= 0) aggMetrics.value.splice(i, 1);
      else aggMetrics.value.push(m);
    };
    const resetAgg = () => {
      aggDims.value = ['主体','类型'];
      aggMetrics.value = ['消耗','当月录入当月付费金额','当月当期ROI'];
      aggFunc.value = 'sum';
      aggSearch.value = '';
      aggSortKey.value = '';
      aggPage.value = 1;
    };
    const aggFuncText = computed(() => ({
      sum: '数值求和；率指标自动按加权（Σ分子÷Σ分母）',
      mean: '全部算术平均',
      count: '返回该组的素材数',
      weighted: '数值求和；率指标按加权（Σ分子÷Σ分母）'
    }[aggFunc.value]));

    // 计算聚合结果
    const aggRows = computed(() => {
      if (!aggDims.value.length) return [];
      const groups = {};
      for (const r of records) {
        const key = aggDims.value.map(d => r[d] || '').join('|||');
        if (!groups[key]) {
          const g = { __records: [] };
          aggDims.value.forEach(d => g[d] = r[d] || '');
          groups[key] = g;
        }
        groups[key].__records.push(r);
      }
      const rows = Object.values(groups);
      for (const g of rows) {
        g.__count = g.__records.length;
        for (const m of aggMetrics.value) {
          if (aggFunc.value === 'count') {
            g[m] = g.__count;
          } else if (aggFunc.value === 'mean') {
            // 平均：算术平均
            const vals = g.__records.map(r => toNum(r[m]));
            g[m] = vals.length ? vals.reduce((a,b)=>a+b,0)/vals.length : 0;
          } else {
            // sum / weighted：数值列求和，率指标按加权（Σ分子÷Σ分母）
            if (isRatio(m)) {
              const { num, den } = ratioDefs[m];
              const sN = g.__records.reduce((s,r)=>s+toNum(r[num]),0);
              const sD = g.__records.reduce((s,r)=>s+toNum(r[den]),0);
              g[m] = sD === 0 ? 0 : sN / sD;
            } else {
              g[m] = g.__records.reduce((s,r)=>s+toNum(r[m]),0);
            }
          }
        }
        // 保留 __records 供合计行加权使用
      }
      return rows;
    });

    const aggRowsFiltered = computed(() => {
      if (!aggSearch.value.trim()) return aggRows.value;
      const kw = aggSearch.value.trim().toLowerCase();
      return aggRows.value.filter(r => aggDims.value.some(d => String(r[d]).toLowerCase().includes(kw)));
    });

    const aggTotalRow = computed(() => {
      if (!aggRowsFiltered.value.length) return { __count: 0 };
      const total = { __count: 0 };
      total.__count = aggRowsFiltered.value.reduce((s,r)=>s+r.__count,0);
      // 用筛选后的所有 records 重新加权计算合计（与各组加权口径一致）
      const filteredRecs = aggRowsFiltered.value.flatMap(r => r.__records || []);
      for (const m of aggMetrics.value) {
        if (aggFunc.value === 'count') {
          total[m] = total.__count;
        } else if (isRatio(m)) {
          const { num, den } = ratioDefs[m];
          const sN = filteredRecs.reduce((s,r)=>s+toNum(r[num]),0);
          const sD = filteredRecs.reduce((s,r)=>s+toNum(r[den]),0);
          total[m] = sD === 0 ? 0 : sN / sD;
        } else {
          total[m] = aggRowsFiltered.value.reduce((s,r)=>s+Number(r[m]||0),0);
        }
      }
      return total;
    });

    const aggRowsSorted = computed(() => {
      if (!aggSortKey.value) return aggRowsFiltered.value;
      const k = aggSortKey.value;
      const dir = aggSortDir.value === 'asc' ? 1 : -1;
      return [...aggRowsFiltered.value].sort((a, b) => {
        const av = a[k], bv = b[k];
        if (typeof av === 'number' && typeof bv === 'number') return (av - bv) * dir;
        return String(av).localeCompare(String(bv)) * dir;
      });
    });

    const aggTotalPages = computed(() => Math.max(1, Math.ceil(aggRowsSorted.value.length / aggPageSize.value)));
    const aggRowsPaged = computed(() => {
      const start = (aggPage.value - 1) * aggPageSize.value;
      return aggRowsSorted.value.slice(start, start + aggPageSize.value);
    });

    const aggSort = k => {
      if (aggSortKey.value === k) {
        aggSortDir.value = aggSortDir.value === 'asc' ? 'desc' : 'asc';
      } else {
        aggSortKey.value = k;
        aggSortDir.value = 'desc';
      }
    };
    const aggSortIcon = k => {
      if (aggSortKey.value !== k) return '↕';
      return aggSortDir.value === 'asc' ? '↑' : '↓';
    };

    // 聚合模块统计
    const aggCoverCount = computed(() => aggRows.value.reduce((s,r)=>s+r.__count,0));
    const aggConsumption = computed(() => {
      if (aggFunc.value === 'weighted' || aggFunc.value === 'mean') {
        return records.reduce((s,r)=>s+toNum(r['消耗']),0);
      }
      return aggRows.value.reduce((s,r)=>s+toNum(r['消耗']),0);
    });
    const aggPayAmount = computed(() => {
      if (aggMetrics.value.includes('当月录入当月付费金额')) {
        // 用total row
        return Number(aggTotalRow.value['当月录入当月付费金额'] || 0);
      }
      return records.reduce((s,r)=>s+toNum(r['当月录入当月付费金额']),0);
    });
    const aggROI = computed(() => {
      const sP = records.reduce((s,r)=>s+toNum(r['当月录入当月付费金额']),0);
      const sC = records.reduce((s,r)=>s+toNum(r['消耗']),0);
      return sC === 0 ? 0 : sP / sC;
    });

    const exportAggCSV = () => {
      if (!aggRowsSorted.value.length) { alert('暂无数据可导出'); return; }
      const headers = [...aggDims.value, '素材数', ...aggMetrics.value];
      const lines = [headers.join(',')];
      for (const r of aggRowsSorted.value) {
        const row = [...aggDims.value.map(d => r[d] || ''), r.__count, ...aggMetrics.value.map(m => r[m])];
        lines.push(row.map(v => {
          const s = String(v);
          return s.includes(',') || s.includes('"') ? '"' + s.replace(/"/g,'""') + '"' : s;
        }).join(','));
      }
      downloadCSV(lines.join('\n'), '素材维度聚合结果.csv');
    };

    watch([aggDims, aggMetrics, aggFunc], () => { aggPage.value = 1; aggSortKey.value=''; });

    // ===== Module 2: 素材明细筛选 =====
    const keyword = ref('');
    const filters = reactive({});
    dims.forEach(d => filters[d] = []);
    const openDropdown = ref('');
    const dimSearch = reactive({});
    dims.forEach(d => dimSearch[d] = '');
    const detailSortKey = ref('消耗');
    const detailSortDir = ref('desc');
    const detailPage = ref(1);
    const detailPageSize = ref(20);
    const detailColumnSet = ref('key');

    const toggleDropdown = (d, evt) => {
      if (openDropdown.value === d) {
        openDropdown.value = '';
        return;
      }
      openDropdown.value = d;
      dimSearch[d] = '';
      // 计算 panel 显示位置（fixed 定位，避免被 sidebar 裁剪）
      if (evt && evt.currentTarget) {
        const rect = evt.currentTarget.getBoundingClientRect();
        panelPos.value = { top: rect.bottom + 4, left: rect.left, width: rect.width };
      }
    };
    const panelPos = ref({ top: 0, left: 0, width: 0 });
    const panelStyle = () => `top:${panelPos.value.top}px;left:${panelPos.value.left}px;width:${panelPos.value.width}px`;
    const filteredDimOptions = d => {
      const kw = (dimSearch[d] || '').toLowerCase();
      return dimOptions[d].filter(v => String(v).toLowerCase().includes(kw));
    };
    const activeDimFilters = computed(() => dims.filter(d => filters[d].length).length);

    const filteredRecords = computed(() => {
      const kw = keyword.value.trim().toLowerCase();
      return records.filter(r => {
        if (kw) {
          const matched = String(r['素材名称']).toLowerCase().includes(kw) || String(r['素材ID']).includes(kw);
          if (!matched) return false;
        }
        for (const d of dims) {
          if (filters[d].length && !filters[d].includes(String(r[d]))) return false;
        }
        return true;
      });
    });

    const detailColumns = computed(() => {
      if (detailColumnSet.value === 'all') return ['素材ID','素材名称',...dims,...metrics];
      if (detailColumnSet.value === 'dim') return ['素材ID','素材名称',...dims];
      if (detailColumnSet.value === 'metric') return ['素材ID','素材名称',...metrics];
      // key
      return ['素材ID','素材名称','主体','类型','痛点','呈现方式','演员','编导','后期','制作月份','消耗','转化数','当月录入当月付费金额','当月当期ROI'];
    });

    const detailSorted = computed(() => {
      if (!detailSortKey.value) return filteredRecords.value;
      const k = detailSortKey.value;
      const dir = detailSortDir.value === 'asc' ? 1 : -1;
      return [...filteredRecords.value].sort((a, b) => {
        const av = a[k], bv = b[k];
        if (typeof av === 'number' && typeof bv === 'number') return (av - bv) * dir;
        const an = Number(av), bn = Number(bv);
        if (!isNaN(an) && !isNaN(bn)) return (an - bn) * dir;
        return String(av).localeCompare(String(bv)) * dir;
      });
    });

    const detailTotalPages = computed(() => Math.max(1, Math.ceil(detailSorted.value.length / detailPageSize.value)));
    const detailPaged = computed(() => {
      const start = (detailPage.value - 1) * detailPageSize.value;
      return detailSorted.value.slice(start, start + detailPageSize.value);
    });

    const detailSort = c => {
      if (detailSortKey.value === c) {
        detailSortDir.value = detailSortDir.value === 'asc' ? 'desc' : 'asc';
      } else {
        detailSortKey.value = c;
        detailSortDir.value = isMetric(c) ? 'desc' : 'asc';
      }
    };
    const detailSortIcon = c => {
      if (detailSortKey.value !== c) return '↕';
      return detailSortDir.value === 'asc' ? '↑' : '↓';
    };

    // 明细模块统计
    const detailConsumption = computed(() => filteredRecords.value.reduce((s,r)=>s+toNum(r['消耗']),0));
    const detailConversion = computed(() => filteredRecords.value.reduce((s,r)=>s+toNum(r['转化数']),0));
    const detailPayAmount = computed(() => filteredRecords.value.reduce((s,r)=>s+toNum(r['当月录入当月付费金额']),0));
    const detailROI = computed(() => {
      const sC = detailConsumption.value;
      return sC === 0 ? 0 : detailPayAmount.value / sC;
    });

    const resetFilters = () => {
      keyword.value = '';
      dims.forEach(d => filters[d] = []);
      detailPage.value = 1;
    };

    const exportDetailCSV = () => {
      if (!filteredRecords.value.length) { alert('暂无数据可导出'); return; }
      const cols = detailColumns.value;
      const lines = [cols.join(',')];
      for (const r of filteredRecords.value) {
        const row = cols.map(c => r[c]);
        lines.push(row.map(v => {
          const s = String(v ?? '');
          return s.includes(',') || s.includes('"') ? '"' + s.replace(/"/g,'""') + '"' : s;
        }).join(','));
      }
      downloadCSV(lines.join('\n'), '素材明细筛选结果.csv');
    };

    watch(filteredRecords, () => { detailPage.value = 1; });
    watch(detailPageSize, () => { detailPage.value = 1; });
    watch(detailColumnSet, () => { detailPage.value = 1; });

    // 关闭下拉（点 panel 内部不关）
    document.addEventListener('click', e => {
      if (e.target.closest('.ms-wrap') || e.target.closest('.ms-panel')) return;
      openDropdown.value = '';
    });
    // 滚动 / 窗口尺寸变化时关闭下拉，避免 fixed 定位错位
    const closeOnScroll = () => { openDropdown.value = ''; };
    onMounted(() => {
      document.querySelectorAll('.sidebar').forEach(el => {
        el.addEventListener('scroll', closeOnScroll);
      });
      window.addEventListener('resize', closeOnScroll);
    });

    function downloadCSV(content, filename) {
      const BOM = '\uFEFF';
      const blob = new Blob([BOM + content], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }

    // ===== Module 3: 维度分布统计 =====
    const distDims = ref(['主体','类型','痛点','呈现方式','编导']);
    const distMetrics = ref(['消耗','当月录入当月付费金额','当月当期ROI']);
    const shareMetrics = ['消耗','当月录入当月付费金额'];

    const expandDistMetricColumns = () => {
      const cols = [];
      for (const m of distMetrics.value) {
        cols.push({ key: m, label: m, type: 'metric' });
        if (shareMetrics.includes(m)) {
          cols.push({ key: m + 'Share', label: m + '占比', type: 'share', baseKey: m });
        }
      }
      return cols;
    };
    const distSort = ref('count_desc');
    const distShowBar = ref(true);
    const distShowEmpty = ref(false);

    const toggleDistDim = d => {
      const i = distDims.value.indexOf(d);
      if (i >= 0) distDims.value.splice(i, 1);
      else distDims.value.push(d);
    };
    const toggleDistMetric = m => {
      const i = distMetrics.value.indexOf(m);
      if (i >= 0) distMetrics.value.splice(i, 1);
      else distMetrics.value.push(m);
    };
    const resetDist = () => {
      distDims.value = ['主体','类型','痛点','呈现方式','编导'];
      distMetrics.value = ['消耗','当月录入当月付费金额','当月当期ROI'];
      distSort.value = 'count_desc';
      distShowBar.value = true;
      distShowEmpty.value = false;
    };

    const getDistData = (d) => {
      const counts = {};
      for (const r of records) {
        const v = r[d] || '';
        if (!v && !distShowEmpty.value) continue;
        if (!counts[v]) counts[v] = { value: v, count: 0, __records: [] };
        counts[v].count++;
        counts[v].__records.push(r);
      }
      const arr = Object.values(counts);
      for (const item of arr) {
        for (const m of distMetrics.value) {
          if (isRatio(m)) {
            const { num, den } = ratioDefs[m];
            const sN = item.__records.reduce((s,r)=>s+toNum(r[num]),0);
            const sD = item.__records.reduce((s,r)=>s+toNum(r[den]),0);
            item[m] = sD === 0 ? 0 : sN / sD;
          } else {
            item[m] = item.__records.reduce((s,r)=>s+toNum(r[m]),0);
          }
        }
        // 排序可能用到消耗，确保始终存在
        if (!distMetrics.value.includes('消耗')) {
          item['消耗'] = item.__records.reduce((s,r)=>s+toNum(r['消耗']),0);
        }
        delete item.__records;
      }
      // 计算需要展示占比的指标的份额
      const metricTotals = {};
      for (const m of distMetrics.value) {
        if (shareMetrics.includes(m)) {
          metricTotals[m] = arr.reduce((s,x)=>s+Number(x[m]||0),0);
        }
      }
      arr.forEach(x => {
        x.percent = arr.reduce((s,i)=>s+i.count,0) === 0 ? 0 : x.count / arr.reduce((s,i)=>s+i.count,0);
        for (const m of distMetrics.value) {
          if (shareMetrics.includes(m)) {
            x[m+'Share'] = metricTotals[m] === 0 ? 0 : x[m] / metricTotals[m];
          }
        }
      });
      if (distSort.value === 'count_desc') arr.sort((a,b)=>b.count-a.count);
      else if (distSort.value === 'count_asc') arr.sort((a,b)=>a.count-b.count);
      else if (distSort.value === 'cost_desc') arr.sort((a,b)=>Number(b['消耗']||0)-Number(a['消耗']||0));
      else if (distSort.value === 'value_asc') arr.sort((a,b)=>String(a.value).localeCompare(String(b.value)));
      return arr;
    };

    const getDistTotal = (d, m) => {
      if (isRatio(m)) {
        const { num, den } = ratioDefs[m];
        const sN = records.reduce((s,r)=>s+toNum(r[num]),0);
        const sD = records.reduce((s,r)=>s+toNum(r[den]),0);
        return sD === 0 ? 0 : sN / sD;
      }
      return getDistData(d).reduce((s,x)=>s+Number(x[m]||0),0);
    };

    const distTotalValues = computed(() => distDims.value.reduce((s,d)=>s+getDistData(d).length,0));
    const distAvgValues = computed(() => distDims.value.length ? Math.round(distTotalValues.value / distDims.value.length) : 0);
    const distTopValue = computed(() => {
      let top = null;
      for (const d of distDims.value) {
        const data = getDistData(d);
        if (!data.length) continue;
        const max = data.reduce((a,b)=>a.count>=b.count?a:b, data[0]);
        if (!top || max.count > top.count) {
          top = { dim: d, value: max.value, count: max.count };
        }
      }
      return top ? `${top.dim}: ${top.value || '(空)'} (${top.count})` : '—';
    });

    const exportDistCSV = () => {
      if (!distDims.value.length) { alert('请选择至少一个统计维度'); return; }
      const lines = [];
      const cols = expandDistMetricColumns();
      for (const d of distDims.value) {
        lines.push(`# 维度: ${d}`);
        const headers = [d, '素材数', '占比', ...cols.map(c => c.label)];
        lines.push(headers.join(','));
        for (const row of getDistData(d)) {
          const vals = [row.value || '', row.count, (row.percent*100).toFixed(1)+'%', ...cols.map(c => {
            if (c.type === 'share') return (row[c.key]*100).toFixed(1)+'%';
            return row[c.key];
          })];
          lines.push(vals.map(v => {
            const s = String(v);
            return s.includes(',') || s.includes('"') ? '"'+s.replace(/"/g,'""')+'"' : s;
          }).join(','));
        }
        lines.push('');
      }
      downloadCSV(lines.join('\n'), '维度分布统计.csv');
    };

    const exportSingleDistCSV = (d) => {
      const cols = expandDistMetricColumns();
      const headers = [d, '素材数', '占比', ...cols.map(c => c.label)];
      const lines = [headers.join(',')];
      for (const row of getDistData(d)) {
        const vals = [row.value || '', row.count, (row.percent*100).toFixed(1)+'%', ...cols.map(c => {
          if (c.type === 'share') return (row[c.key]*100).toFixed(1)+'%';
          return row[c.key];
        })];
        lines.push(vals.map(v => {
          const s = String(v);
          return s.includes(',') || s.includes('"') ? '"'+s.replace(/"/g,'""')+'"' : s;
        }).join(','));
      }
      downloadCSV(lines.join('\n'), `${d}分布统计.csv`);
    };

    return {
      records, dims, metrics, dimOptions,
      // global
      totalConsumption, totalConversion, totalPayAmount, totalROI,
      formatNum, formatMetric, metricClass,
      // tab
      tab,
      // module 1
      aggDims, aggMetrics, aggFunc, aggSearch, aggFuncText,
      toggleAggDim, toggleAggMetric, resetAgg,
      aggRows, aggRowsFiltered, aggRowsPaged, aggTotalRow,
      aggSortKey, aggSortDir, aggSort, aggSortIcon,
      aggPage, aggPageSize, aggTotalPages,
      aggCoverCount, aggConsumption, aggPayAmount, aggROI,
      exportAggCSV,
      // module 2
      keyword, filters, openDropdown, dimSearch,
      toggleDropdown, filteredDimOptions, activeDimFilters, panelStyle,
      filteredRecords, detailColumns, detailColumnSet,
      detailSortKey, detailSortDir, detailSort, detailSortIcon,
      detailPage, detailPageSize, detailTotalPages, detailPaged,
      detailConsumption, detailConversion, detailPayAmount, detailROI,
      resetFilters, exportDetailCSV,
      // module 3
      distDims, distMetrics, distSort, distShowBar, distShowEmpty, shareMetrics,
      toggleDistDim, toggleDistMetric, resetDist,
      expandDistMetricColumns, getDistData, getDistTotal, distTotalValues, distAvgValues, distTopValue,
      exportDistCSV, exportSingleDistCSV,
      isMetric
    };
  }
}).mount('#app');
</script>
</body>
</html>
"""

if __name__ == '__main__':
    main()
