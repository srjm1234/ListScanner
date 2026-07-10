"""
ListScanner - Web路径与敏感文件扫描工具
EXE打包入口文件
"""

import os
import sys
import threading
import webbrowser
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path


def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


def get_bundle_dir():
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent


BASE_DIR = get_base_dir()
BUNDLE_DIR = get_bundle_dir()

os.chdir(BASE_DIR)
sys.path.insert(0, str(BUNDLE_DIR))


def run_scanner(port=5000, open_browser=True):
    """启动扫描器WebUI"""
    from webapp import app

    app.template_folder = str(BUNDLE_DIR / "templates")
    app.static_folder = str(BUNDLE_DIR / "static")

    dict_dir = BASE_DIR / "dictionary"
    if not dict_dir.exists():
        src_dict = BUNDLE_DIR / "dictionary"
        if src_dict.exists():
            import shutil
            shutil.copytree(str(src_dict), str(dict_dir))

    if open_browser:
        threading.Timer(1.5, lambda: webbrowser.open(f"http://127.0.0.1:{port}")).start()

    print(f"ListScanner WebUI 已启动: http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


def run_testsite(port=8080, open_browser=True):
    """启动简易靶场 (静态文件服务)"""
    # 优先使用EXE旁边的testsite目录, 否则用打包内的
    site_dir = BASE_DIR / "testsite"
    if not site_dir.exists():
        site_dir = BUNDLE_DIR / "testsite"
    if not site_dir.exists():
        print("错误: 未找到testsite目录")
        return

    handler = partial(SimpleHTTPRequestHandler, directory=str(site_dir))

    # 自动生成模拟暴露的 .git/.svn/.hg 等版本控制目录（这些文件无法纳入 Git 仓库）
    try:
        from testsite.prepare_testsite import prepare_testsite
        prepare_testsite(site_dir)
    except Exception as e:
        print(f"[靶场] 生成模拟敏感文件失败（可忽略）: {e}")

    # 抑制日志输出
    import logging
    log = logging.getLogger("http.server")
    log.setLevel(logging.WARNING)

    server = HTTPServer(("0.0.0.0", port), handler)

    if open_browser:
        threading.Timer(1.0, lambda: webbrowser.open(f"http://127.0.0.1:{port}")).start()

    print(f"简易Web靶场已启动: http://127.0.0.1:{port}")
    print(f"服务目录: {site_dir}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


def main():
    import argparse
    parser = argparse.ArgumentParser(description="ListScanner - Web路径扫描工具")
    parser.add_argument("--testsite", action="store_true", help="启动简易靶场模式")
    parser.add_argument("--port", type=int, default=None, help="指定端口")
    parser.add_argument("--no-browser", action="store_true", help="不自动打开浏览器")
    args = parser.parse_args()

    open_browser = not args.no_browser

    if args.testsite:
        port = args.port or 8080
        run_testsite(port=port, open_browser=open_browser)
    else:
        port = args.port or 5000
        run_scanner(port=port, open_browser=open_browser)


if __name__ == "__main__":
    main()
