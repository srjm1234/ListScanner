# ListScanner v1.0.0

> 轻量级 Web 路径扫描与敏感文件检测工具 · 首个正式发布

ListScanner 是一款面向**授权安全测试与教学实验**的轻量级 Web 扫描工具，自动化探测目标站点中常见的后台目录、接口入口与敏感文件，并按风险等级（高 / 中 / 低）进行分类。提供 **WebUI（Flask）** 与 **命令行（CLI）** 两种使用方式，并内置开箱即用的本地授权测试靶场。

## 📦 本版本包含

| 资源 | 说明 |
|------|------|
| `ListScanner.exe` | Windows 桌面 / 便携版可执行文件（无需安装 Python 环境） |
| 仓库源码 | 完整扫描引擎、WebUI、CLI、字典、靶场与文档 |

## 💾 下载与运行（Windows）

1. 在下方 **Assets** 中下载 `ListScanner.exe`
2. 双击运行，浏览器会自动打开 `http://127.0.0.1:5000`
3. 命令行参数：
   ```
   ListScanner.exe                      # 启动扫描器（默认端口 5000）
   ListScanner.exe --port 8888          # 指定端口
   ListScanner.exe --no-browser         # 不自动打开浏览器
   ListScanner.exe --testsite           # 启动内置测试靶场（端口 8080）
   ```

## 🔐 文件校验

下载后建议校验完整性（SHA256）：

```
183f22524868620cf57675dd06640c0c042e94b6c3612867375c7642cd997527  ListScanner.exe
```

PowerShell 校验命令：

```powershell
 certutil -hashfile ListScanner.exe SHA256
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

*本发布内容作者信息已做匿名化处理。*
