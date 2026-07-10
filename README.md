# ListScanner — 基于 Python 的 Web 路径暴力破解与敏感文件扫描工具

> 轻量级 Web 路径扫描与敏感文件检测工具
>
> ![Python](https://img.shields.io/badge/python-3.13-blue)
> ![License](https://img.shields.io/badge/License-MIT-yellow.svg)
> ![Flask](https://img.shields.io/badge/Flask-3.x-black)

## 项目简介

ListScanner 是一款面向教学实验和授权测试场景的轻量级 Web 安全扫描工具，能够自动化探测目标站点中常见的后台目录、接口入口和敏感文件。系统以 Python 为主要开发语言，提供 **WebUI（Flask）** 和 **CTK 桌面应用（CustomTkinter）** 两种交互方式，共享同一套核心扫描引擎。

## 核心功能

- 路径字典枚举与扩展名自动补全
- 多线程并发 HTTP 请求（`ThreadPoolExecutor`）
- HTTP 状态码判定与结果过滤
- 基于关键词的风险分类（高 / 中 / 低三级）
- 结构化 HTML 扫描报告生成
- WebUI 支持异步扫描与多格式报告导出（HTML / CSV / JSON）
- 内置本地授权测试靶场，开箱即用

## 系统架构

```
表示层:  WebUI (Flask B/S)  |  CTK 桌面应用 (C/S)
控制层:  扫描器 (WebScanner) | 风险分类器 (check_risk) | 字典处理器 (read_wordlist)
数据层:  数据模型 (ScanResult/ScanStats) | 配置管理 | 报告生成器
外部层:  字典文件 (dictionary/) | 目标网站 (HTTP Server)
```

## 项目结构

```
ListScanner/
├── ListScanner.py            # CLI 入口
├── main.py                   # EXE 打包入口（WebUI + 靶场服务）
├── webapp.py                 # Flask WebUI 后端
├── build.py                  # PyInstaller 打包脚本
├── requirements.txt          # Python 依赖
├── Dockerfile                # Docker 构建文件
├── docker-compose.yml        # Docker Compose 编排
├── .gitignore / .gitattributes / LICENSE
│
├── listscanner/              # 核心扫描引擎包
│   ├── __init__.py           # 版本信息 (v2.0)
│   ├── models.py             # 数据模型 (ScanResult, ScanStats)
│   ├── config.py             # 默认配置管理
│   ├── wordlist.py           # 字典加载与候选路径生成
│   ├── classifier.py         # 风险分类 (check_risk)
│   ├── scanner.py            # 扫描核心 (WebScanner)
│   ├── report.py             # HTML 报告生成
│   └── cli.py                # 命令行参数解析
│
├── templates/                # Flask 模板
│   ├── index.html            # WebUI 主界面
│   └── diagrams/             # 论文配图（HTML/SVG）
│
├── exe/                      # CTK 桌面应用源码与图标
│   ├── gui_ctk.py            # CustomTkinter GUI 源码
│   └── app.ico               # 应用图标
│   （注：打包后的 ListScanner.exe 通过 GitHub Releases 发布，不纳入仓库）
│
├── dictionary/               # 扫描字典
│   └── wordlist.txt          # 默认预设字典
│
├── testsite/                 # 本地授权测试靶场
│   ├── prepare_testsite.py   # 启动靶场时自动生成模拟暴露的 .git/.svn/.hg
│   ├── index.html / admin/ / login/ / api/ ...
│   ├── .env / .htaccess / backup.sql / config.php.bak / db.sql ...
│   └── ...                   # 其他测试资源
│
├── diagrams_mmd/             # Mermaid 源文件（论文配图，11 张）
└── diagrams_drawio/          # Draw.io 源文件（论文配图，11 张）
```

## 环境要求

- Python 3.8+
- Windows 系统（CTK 桌面应用需要，WebUI/CLI 跨平台）
- Docker（可选，用于容器化部署）

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动 WebUI

```bash
python webapp.py
```

浏览器访问 `http://localhost:5000` 即可使用。

### 3. CLI 命令行模式

```bash
python ListScanner.py -u http://target-site:8080
```

常用参数：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-u` | 目标 URL | （必填） |
| `-w` | 字典文件路径 | dictionary/wordlist.txt |
| `-e` | 扩展名列表 | php,html,bak,txt |
| `-t` | 线程数 | 10 |
| `--timeout` | 请求超时(秒) | 5 |
| `-o` | 报告输出路径 | report.html |

### 4. CTK 桌面应用

```bash
# 源码运行
python exe/gui_ctk.py
```

> 预打包的 `ListScanner.exe` 体积较大（约 20MB），通过 **GitHub Releases** 发布，不纳入 Git 仓库。需要可执行文件时请前往 Releases 下载，或自行用 `build.py` 打包。

### 5. Docker 部署

```bash
docker-compose up -d
```

访问 `http://localhost:5000`。

### 6. 启动本地测试靶场

```bash
# 方式 A：通过 WebUI 的「靶场」按钮启动（自动在 testsite/ 下生成模拟敏感文件）
# 方式 B：命令行
python main.py --testsite
# 方式 C：直接用 Python 静态服务器
cd testsite
python -m http.server 8080
```

靶场包含常见敏感文件与目录（`.env`、`.htaccess`、`backup.sql`、`config.php.bak`、后台目录 `admin/`、登录入口 `login.php` 等），用于验证扫描器的检测能力。

> **关于 `.git` / `.svn` / `.hg` 模拟文件**：这些版本控制目录会与 Git 自身冲突、无法纳入仓库，因此在启动靶场时会由 `testsite/prepare_testsite.py` 自动生成。若手工启动 `python -m http.server`，可先执行 `python testsite/prepare_testsite.py` 生成它们，以便演示「源码泄露」类风险的识别。

## 风险分类规则

| 优先级 | 匹配关键词 | 资源类型 | 风险等级 |
|--------|-----------|----------|----------|
| 1 | .git / .svn / .hg | 源码泄露 | 高 |
| 2 | backup / bak / old | 备份文件 | 高 |
| 3 | .env / .htaccess / web.config / config | 配置文件 | 高 |
| 4 | .zip / .rar / .tar / .gz | 压缩文件 | 高 |
| 5 | .sql / db. | 数据库文件 | 高 |
| 6 | admin | 后台入口 | 高 |
| 7 | manage | 管理目录 | 高 |
| 8 | login | 登录入口 | 中 |
| 9 | phpinfo | 环境信息 | 中 |
| 10 | log | 日志文件 | 中 |
| 11 | test | 测试文件 | 中 |
| 12 | 以 / 结尾 | 普通目录 | 低 |
| 13 | 其余 | 普通文件 | 低 |

## 测试数据

在本地授权测试环境中，系统从 32 条候选路径中成功识别 28 条有效结果：

- 高风险：11 条（.env、.git/config、.htaccess、backup.sql 等）
- 中风险：5 条（login.php、log.txt、admin/ 等）
- 低风险：12 条（普通目录与文件）
- 未发现：4 条
- 请求失败：0 条

## 技术栈

| 技术 | 用途 |
|------|------|
| Python 3.x | 主开发语言 |
| Requests | HTTP 请求 |
| Flask | WebUI 后端服务 |
| CustomTkinter | 桌面 GUI |
| ThreadPoolExecutor | 多线程并发 |
| PyInstaller | EXE 打包 |
| Docker / Gunicorn | 容器化部署 |

## 合规声明

本工具仅用于授权环境下的安全测试与教学实验，不包含密码爆破、漏洞利用、认证绕过或批量攻击等功能。使用者须确保已获得目标系统的明确授权。因滥用本工具造成的一切后果由使用者自行承担。

## 许可证

本项目基于 [MIT License](./LICENSE) 开源。
