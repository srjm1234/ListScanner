def check_risk(path):
    lower_path = path.lower()
    file_name = lower_path.rstrip("/").split("/")[-1]

    if ".git" in lower_path or ".svn" in lower_path:
        return "源码泄露", "高风险"

    if "backup" in lower_path or "bak" in lower_path or "old" in lower_path:
        return "备份文件", "高风险"

    if file_name in {".env", ".htaccess", "web.config"} or "config" in lower_path:
        return "配置文件", "高风险"

    if file_name.endswith((".zip", ".rar", ".tar", ".gz")):
        return "压缩文件", "高风险"

    if file_name.endswith(".sql") or file_name.startswith("db."):
        return "数据库文件", "高风险"

    if "admin" in lower_path:
        return "后台入口", "高风险"

    if "manage" in lower_path:
        return "管理目录", "高风险"

    if "login" in lower_path:
        return "登录入口", "中风险"

    if "phpinfo" in lower_path:
        return "环境信息", "中风险"

    if file_name == "log.txt" or file_name.startswith("log.") or file_name.endswith(".log"):
        return "日志文件", "中风险"

    if "test" in lower_path:
        return "测试文件", "中风险"

    if lower_path.endswith("/"):
        return "普通目录", "低风险"

    return "普通文件", "低风险"
