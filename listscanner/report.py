from collections import Counter
from datetime import datetime
from html import escape
from pathlib import Path


def save_html_report(results, output_file, target_url, stats):
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    risk_counter = Counter(item.risk_level for item in results)
    type_counter = Counter(item.risk_type for item in results)
    rows_html = build_rows(results)
    type_html = build_type_list(type_counter)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>Web路径扫描报告</title>
  <style>
    body {{
      font-family: Arial, "Microsoft YaHei", sans-serif;
      margin: 24px;
      color: #222;
    }}
    h1, h2 {{
      margin-bottom: 10px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
    }}
    th, td {{
      border: 1px solid #ccc;
      padding: 8px;
      text-align: left;
    }}
    th {{
      background: #eee;
    }}
    a {{
      word-break: break-all;
    }}
    .high {{
      color: #c00;
    }}
    .middle {{
      color: #d97706;
    }}
    .low {{
      color: #15803d;
    }}
  </style>
</head>
<body>
  <h1>Web路径扫描报告</h1>
  <p>目标地址：{escape(target_url)}</p>
  <p>生成时间：{escape(now)}</p>

  <h2>扫描统计</h2>
  <table>
    <tr>
      <th>测试路径</th>
      <th>发现结果</th>
      <th>高风险</th>
      <th>中风险</th>
      <th>请求失败</th>
    </tr>
    <tr>
      <td>{stats.total}</td>
      <td>{len(results)}</td>
      <td>{risk_counter.get("高风险", 0)}</td>
      <td>{risk_counter.get("中风险", 0)}</td>
      <td>{stats.errors}</td>
    </tr>
  </table>

  <h2>分类统计</h2>
  <ul>
    {type_html}
  </ul>

  <h2>扫描结果</h2>
  <table>
    <thead>
      <tr>
        <th>状态码</th>
        <th>风险</th>
        <th>类型</th>
        <th>URL</th>
        <th>大小</th>
        <th>Content-Type</th>
      </tr>
    </thead>
    <tbody>
      {rows_html}
    </tbody>
  </table>
</body>
</html>
"""
    output_path.write_text(html, encoding="utf-8")


def build_rows(results):
    if not results:
        return '<tr><td colspan="6">没有发现有效路径</td></tr>'

    rows = []
    for item in results:
        risk_class = get_risk_class(item.risk_level)
        rows.append(
            "<tr>"
            f"<td>{item.status_code}</td>"
            f'<td class="{risk_class}">{escape(item.risk_level)}</td>'
            f"<td>{escape(item.risk_type)}</td>"
            f'<td><a href="{escape(item.url)}" target="_blank" rel="noreferrer">{escape(item.url)}</a></td>'
            f"<td>{item.size} B</td>"
            f"<td>{escape(item.content_type or '-')}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def build_type_list(type_counter):
    if not type_counter:
        return "<li>暂无分类结果</li>"

    return "\n".join(
        f"<li>{escape(name)}：{count} 条</li>"
        for name, count in type_counter.items()
    )


def get_risk_class(risk_level):
    if risk_level == "高风险":
        return "high"
    if risk_level == "中风险":
        return "middle"
    return "low"
