# ListScanner 图表导出方案

## 方案一：Mermaid CLI 批量导出

### 安装
```bash
npm install -g @mermaid-js/mermaid-cli
```

### 使用
```powershell
# 导出 SVG + PNG（默认）
.\export-diagrams.ps1

# 只导出 SVG
.\export-diagrams.ps1 -Format svg

# 只导出 PNG，自定义分辨率
.\export-diagrams.ps1 -Format png -Width 2400 -Height 1400

# 手动导出单个
mmdc -i diagrams_mmd\architecture.mmd -o architecture.svg -t neutral -b white -c diagrams_mmd\mermaid-config.json
```

### 输出
- SVG 矢量图 → 直接插入 Word（推荐，无损缩放）
- PNG 位图 → 截图用途

---

## 方案五：Draw.io 手动优化

### 使用
1. 打开 https://app.diagrams.net
2. 菜单 → 文件 → 打开 → 选择 `diagrams_drawio/*.xml`
3. 手动调整布局、样式、颜色
4. 导出为 SVG / PNG / PDF

### 已提供的模板
- `architecture_drawio.xml` — 系统整体架构图
- `functional_drawio.xml` — 功能结构图
- `deployment_drawio.xml` — 系统部署架构图

---

## 推荐流程

1. 先用 Mermaid CLI 批量导出所有 11 个图表的 SVG
2. 挑选 2-3 个关键图表（架构图、功能结构图、部署图）用 Draw.io 精调
3. 最终统一导出为 SVG 插入论文

## 文件结构
```
BYSJ/
├── diagrams_mmd/           # Mermaid 源文件 (11个 .mmd)
│   ├── architecture.mmd
│   ├── functional.mmd
│   ├── class.mmd
│   ├── dataflow.mmd
│   ├── er.mmd
│   ├── check_path.mmd
│   ├── risk_decision.mmd
│   ├── requests_flow.mmd
│   ├── deployment.mmd
│   ├── module_dep.mmd
│   ├── scan_workflow.mmd
│   ├── mermaid-config.json
│   └── README.md
├── diagrams_drawio/        # Draw.io 模板 (3个关键图表)
│   ├── architecture_drawio.xml
│   ├── functional_drawio.xml
│   └── deployment_drawio.xml
├── diagrams_output/        # 导出输出目录
├── export-diagrams.ps1     # Mermaid CLI 批量导出脚本
└── screenshot-diagrams.js  # Puppeteer 截图备用方案
```
