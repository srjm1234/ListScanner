# ListScanner

> 轻量级 Web 路径扫描与敏感文件检测工具

ListScanner 是一款面向**授权安全测试与教学实验**的轻量级 Web 扫描工具，能够自动化探测目标站点中常见的后台目录、接口入口与敏感文件，并按风险等级（高 / 中 / 低）进行分类。工具以 Python 开发，提供 **WebUI（Flask）** 与 **命令行（CLI）** 两种使用方式，共享同一套核心扫描引擎，并内置一个开箱即用的本地授权测试靶场。

## ✨ 功能特性

- **字典枚举**：路径字典 + 扩展名自动补全，支持自定义字典与在线编辑
- **并发扫描**：基于 `ThreadPoolExecutor` 的多线程 HTTP 请求
- **风险分类**：依据关键词将结果划分为高 / 中 / 低三级（源码泄露、备份文件、配置文件、数据库文件、后台入口、登录入口等）
- **多格式报告**：HTML 报告自动生成，并支持导出 CSV / JSON
- **内置靶场**：一键启动本地测试站点，含常见敏感文件与目录用于演示检测能力
- **容器化**：提供 Dockerfile 与 docker-compose，便于部署
- **双形态**：WebUI 适合交互式使用，CLI 适合自动化与批量集成

## 🚀 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动 WebUI（浏览器访问 http://localhost:5000）
python webapp.py

# 3. 或使用命令行
python ListScanner.py -u http://target-site:8080
```

### Docker 部署

```bash
docker-compose up -d
# 访问 http://localhost:5000
```

### 本地测试靶场

```bash
python main.py --testsite          # 靶场运行于 http://localhost:8080
# 通过 WebUI 的「靶场」按钮启动会自动生成模拟暴露的敏感文件
```

## 🧭 风险分类示例

| 风险等级 | 典型命中 |
|----------|----------|
| 高 | `.git` / `.svn` 源码泄露、`.env` / `backup.sql` 配置与数据库文件、后台目录 `admin/` |
| 中 | `login.php` 登录入口、`phpinfo.php` 环境信息、`log.txt` 日志文件 |
| 低 | 普通目录与普通文件 |

## ⚖️ 合规声明

本工具**仅用于授权环境下的安全测试与教学实验**，不包含密码爆破、漏洞利用、认证绕过或批量攻击等功能。使用者须确保已获得目标系统的明确授权；因滥用本工具造成的一切后果由使用者自行承担。

## 📄 许可证

基于 [MIT License](./LICENSE) 开源。

---

*本仓库作者信息已做匿名化处理。*
