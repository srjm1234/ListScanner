import csv
import io
import json
import os
import subprocess
import sys
import threading
import uuid
from pathlib import Path

from flask import Flask, Response, jsonify, render_template, request, send_file

from listscanner.classifier import check_risk
from listscanner.config import load_settings
from listscanner.models import ScanResult, ScanStats
from listscanner.report import save_html_report
from listscanner.scanner import WebScanner, fix_url
from listscanner.wordlist import read_wordlist

app = Flask(__name__)

# 靶场进程管理
testsite_process = None
testsite_port = 8080

# 活跃的扫描任务 {task_id: task_info}
tasks = {}
lock = threading.Lock()


@app.route("/")
def index():
    settings = load_settings()
    return render_template("index.html", settings=settings)


@app.route("/api/wordlists")
def api_wordlists():
    dict_dir = Path("dictionary")
    files = []
    if dict_dir.is_dir():
        for f in sorted(dict_dir.glob("*.txt")):
            files.append(str(f))
    return jsonify(files)


@app.route("/api/wordlist/content", methods=["POST"])
def api_wordlist_content():
    """读取字典文件原始内容"""
    data = request.json
    file_path = data.get("wordlist", "dictionary/wordlist.txt")
    try:
        content = Path(file_path).read_text(encoding="utf-8")
        return jsonify({"success": True, "content": content})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/wordlist/save", methods=["POST"])
def api_wordlist_save():
    """保存字典文件内容"""
    data = request.json
    file_path = data.get("wordlist", "")
    content = data.get("content", "")
    if not file_path:
        return jsonify({"success": False, "error": "未指定文件"}), 400
    try:
        p = Path(file_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/wordlist/create", methods=["POST"])
def api_wordlist_create():
    """创建新字典文件（支持导入内容）"""
    data = request.json
    name = data.get("name", "").strip()
    content = data.get("content", "")
    if not name:
        return jsonify({"success": False, "error": "请输入字典名称"}), 400
    if not name.endswith(".txt"):
        name += ".txt"
    file_path = Path("dictionary") / name
    if file_path.exists():
        return jsonify({"success": False, "error": "文件已存在"}), 400
    try:
        if content:
            file_path.write_text(content, encoding="utf-8")
        else:
            file_path.write_text("# 新字典文件\n# 每行一个路径\n", encoding="utf-8")
        return jsonify({"success": True, "path": str(file_path)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/wordlist/preview", methods=["POST"])
def api_wordlist_preview():
    data = request.json
    file_path = data.get("wordlist", "dictionary/wordlist.txt")
    extensions = data.get("extensions", "php,html,bak,zip").split(",")
    extensions = [e.strip().lstrip(".") for e in extensions if e.strip()]

    # 支持从直接内容预览
    content = data.get("content")
    if content is not None:
        try:
            tmp = Path("_tmp_preview.txt")
            tmp.write_text(content, encoding="utf-8")
            words = read_wordlist(str(tmp), extensions)
            tmp.unlink(missing_ok=True)
            return jsonify({"success": True, "count": len(words), "preview": words[:30]})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)})

    try:
        words = read_wordlist(file_path, extensions)
        return jsonify({"success": True, "count": len(words), "preview": words[:30]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/scan", methods=["POST"])
def api_scan():
    data = request.json
    target_url = data.get("url", "").strip()
    if not target_url:
        return jsonify({"success": False, "error": "请输入目标地址"}), 400

    wordlist = data.get("wordlist", "dictionary/wordlist.txt")
    extensions = data.get("extensions", "php,html,bak,zip")
    threads = int(data.get("threads", 10))
    timeout = float(data.get("timeout", 5))


    wordlist_content = data.get("wordlist_content")
    ext_list = [e.strip().lstrip(".") for e in extensions.split(",") if e.strip()]

    if wordlist_content:
        try:
            tmp = Path("_tmp_scan.txt")
            tmp.write_text(wordlist_content, encoding="utf-8")
            words = read_wordlist(str(tmp), ext_list)
            tmp.unlink(missing_ok=True)
        except Exception as e:
            return jsonify({"success": False, "error": f"读取字典失败: {e}"}), 400
    else:
        try:
            words = read_wordlist(wordlist, ext_list)
        except Exception as e:
            return jsonify({"success": False, "error": f"读取字典失败: {e}"}), 400

    if not words:
        return jsonify({"success": False, "error": "字典为空"}), 400

    task_id = str(uuid.uuid4())[:8]
    task = {
        "id": task_id,
        "status": "running",
        "target_url": fix_url(target_url),
        "total": len(words),
        "completed": 0,
        "found": 0,
        "not_found": 0,
        "errors": 0,
        "results": [],
        "output": data.get("output", "report.html"),
    }

    with lock:
        tasks[task_id] = task

    thread = threading.Thread(target=run_scan, args=(task_id, target_url, words, threads, timeout), daemon=True)
    thread.start()

    return jsonify({"success": True, "task_id": task_id})


def run_scan(task_id, target_url, wordlist, threads, timeout):
    task = tasks[task_id]
    scanner = WebScanner(target_url=target_url, wordlist=wordlist, threads=threads, timeout=timeout)

    from concurrent.futures import ThreadPoolExecutor, as_completed

    with ThreadPoolExecutor(max_workers=threads) as pool:
        futures = {pool.submit(scanner.check_path, path): path for path in wordlist}
        for future in as_completed(futures):
            result, state = future.result()
            with lock:
                task["completed"] += 1
                if state == "found":
                    task["found"] += 1
                    task["results"].append({
                        "path": result.path,
                        "url": result.url,
                        "status_code": result.status_code,
                        "size": result.size,
                        "content_type": result.content_type or "-",
                        "risk_type": result.risk_type,
                        "risk_level": result.risk_level,
                    })
                elif state == "not_found":
                    task["not_found"] += 1
                else:
                    task["errors"] += 1

    # 按风险排序
    risk_order = {"高风险": 0, "中风险": 1, "低风险": 2}
    task["results"].sort(key=lambda r: (risk_order.get(r["risk_level"], 9), r["status_code"], r["path"]))

    # 生成HTML报告
    scan_results = []
    for r in task["results"]:
        sr = ScanResult(
            path=r["path"], url=r["url"], status_code=r["status_code"],
            size=r["size"], content_type=r["content_type"],
            risk_type=r["risk_type"], risk_level=r["risk_level"],
        )
        scan_results.append(sr)

    stats = ScanStats(total=task["total"], found=task["found"], not_found=task["not_found"], errors=task["errors"])
    try:
        save_html_report(scan_results, task["output"], task["target_url"], stats)
    except Exception:
        pass

    task["status"] = "done"


@app.route("/api/scan/<task_id>")
def api_scan_status(task_id):
    with lock:
        task = tasks.get(task_id)
    if not task:
        return jsonify({"error": "任务不存在"}), 404
    return jsonify(task)


@app.route("/api/scan/<task_id>/report")
def api_scan_report(task_id):
    """下载扫描报告，支持 html/csv/json 格式"""
    with lock:
        task = tasks.get(task_id)
    if not task:
        return jsonify({"error": "任务不存在"}), 404
    if task["status"] != "done":
        return jsonify({"error": "扫描尚未完成"}), 400

    fmt = request.args.get("format", "html").lower()

    if fmt == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["状态码", "风险等级", "风险类型", "URL", "大小(B)", "Content-Type"])
        for r in task["results"]:
            writer.writerow([r["status_code"], r["risk_level"], r["risk_type"], r["url"], r["size"], r["content_type"]])
        buf.seek(0)
        return Response(
            "﻿" + buf.getvalue(),  # BOM for Excel 中文兼容
            mimetype="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename=scan_report_{task_id}.csv'},
        )

    if fmt == "json":
        report = {
            "target": task["target_url"],
            "stats": {
                "total": task["total"],
                "found": task["found"],
                "not_found": task["not_found"],
                "errors": task["errors"],
            },
            "results": task["results"],
        }
        return jsonify(report)

    # 默认 HTML
    output = Path(task["output"])
    if not output.exists():
        return jsonify({"error": "报告文件不存在"}), 404
    return send_file(output, as_attachment=True, download_name=f"scan_report_{task_id}.html")


@app.route("/diagrams/<name>")
def diagram_page(name):
    allowed = ["architecture", "functional", "class", "dataflow", "er", "check_path", "risk_decision", "requests_flow", "deployment", "scan_workflow", "module_dep"]
    if name not in allowed:
        return "Not Found", 404
    return render_template(f"diagrams/{name}.html")


@app.route("/api/risk-info")
def api_risk_info():
    return jsonify({
        "高风险": {
            "description": "可能导致敏感信息泄露或系统被入侵的安全隐患",
            "color": "red",
            "types": {
                "源码泄露": {"desc": ".git/.svn 等版本控制目录暴露，攻击者可获取完整源代码", "patterns": ".git, .svn, .hg"},
                "备份文件": {"desc": "backup/bak/old 等备份文件可能包含历史敏感数据", "patterns": "backup, bak, old, copy"},
                "配置文件": {"desc": ".env/.htaccess/web.config 等配置文件可能泄露数据库密码、API密钥等", "patterns": ".env, .htaccess, web.config, config"},
                "压缩文件": {"desc": ".zip/.rar/.tar.gz 等压缩包可能包含源码或敏感数据", "patterns": ".zip, .rar, .tar, .gz"},
                "数据库文件": {"desc": ".sql 等数据库备份文件可直接获取全部数据", "patterns": ".sql, db.*"},
                "后台入口": {"desc": "admin 路径可能是管理后台，存在暴力破解风险", "patterns": "admin"},
                "管理目录": {"desc": "manage 路径可能是管理功能入口", "patterns": "manage"},
            },
        },
        "中风险": {
            "description": "需要关注但不直接导致入侵的安全问题",
            "color": "amber",
            "types": {
                "登录入口": {"desc": "登录页面暴露，可能被用于暴力破解攻击", "patterns": "login"},
                "环境信息": {"desc": "phpinfo 等页面泄露服务器环境配置信息", "patterns": "phpinfo"},
                "日志文件": {"desc": "日志文件可能包含用户操作记录、错误信息等敏感数据", "patterns": "log, .log"},
                "测试文件": {"desc": "测试页面可能包含调试功能或测试数据", "patterns": "test"},
            },
        },
        "低风险": {
            "description": "一般性信息，通常不构成直接威胁",
            "color": "green",
            "types": {
                "普通目录": {"desc": "常规目录列表，可能泄露网站结构信息", "patterns": "/ 结尾的路径"},
                "普通文件": {"desc": "常规页面文件，一般不包含敏感信息", "patterns": "其他文件"},
            },
        },
    })


# ========== 靶场管理 ==========
def _start_testsite_subprocess(port):
    """启动靶场子进程 (本地模式)"""
    global testsite_process

    project_root = Path(__file__).parent
    site_dir = project_root / "testsite"
    print(f"[靶场] __file__={Path(__file__).resolve()}")
    print(f"[靶场] project_root={project_root.resolve()}")
    print(f"[靶场] site_dir={site_dir.resolve()}")
    print(f"[靶场] site_dir.exists()={site_dir.exists()}")
    if not site_dir.exists():
        return False, "testsite 目录不存在: " + str(site_dir)

    # 自动生成模拟暴露的 .git/.svn/.hg 等版本控制目录（这些文件无法纳入 Git 仓库）
    try:
        from testsite.prepare_testsite import prepare_testsite
        prepare_testsite(site_dir)
    except Exception as e:
        print(f"[靶场] 生成模拟敏感文件失败（可忽略）: {e}")

    try:
        import logging
        log = logging.getLogger("http.server")
        log.setLevel(logging.WARNING)

        from functools import partial
        from http.server import HTTPServer, SimpleHTTPRequestHandler

        handler = partial(SimpleHTTPRequestHandler, directory=str(site_dir))
        server = HTTPServer(("0.0.0.0", port), handler)

        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()

        # 等待服务器就绪
        import time, socket
        for _ in range(20):
            time.sleep(0.1)
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.5)
                s.connect(("127.0.0.1", port))
                s.close()
                break
            except:
                pass

        class _FakeProc:
            def __init__(self, srv):
                self._server = srv
            def poll(self):
                return None
            def terminate(self):
                try:
                    self._server.shutdown()
                except:
                    pass

        testsite_process = _FakeProc(server)
        print(f"[靶场] 启动成功，监听 0.0.0.0:{port}")
        return True, "靶场已启动"
    except Exception as e:
        import traceback
        print(f"[靶场] 启动失败: {e}")
        traceback.print_exc()
        return False, str(e)


@app.route("/api/testsite/start", methods=["POST"])
def api_testsite_start():
    data = request.json or {}
    port = data.get("port", testsite_port)

    # Docker模式: 靶场已在独立容器运行，固定使用 8080 端口
    if os.path.exists("/.dockerenv") or os.environ.get("DOCKER_CONTAINER"):
        return jsonify({"success": True, "message": "靶场已启动 (Docker容器)", "port": 8080, "docker": True})

    if testsite_process is not None and testsite_process.poll() is None:
        return jsonify({"success": True, "message": "靶场已在运行中", "port": port})

    ok, msg = _start_testsite_subprocess(port)
    if ok:
        return jsonify({"success": True, "message": msg, "port": port})
    else:
        return jsonify({"success": False, "error": msg})


@app.route("/api/testsite/stop", methods=["POST"])
def api_testsite_stop():
    global testsite_process
    # Docker模式: 靶场由 Docker Compose 管理，无法从应用内停止
    if os.path.exists("/.dockerenv") or os.environ.get("DOCKER_CONTAINER"):
        return jsonify({"success": True, "message": "Docker 靶场需通过 docker compose down 停止"})
    if testsite_process is not None and testsite_process.poll() is None:
        testsite_process.terminate()
        testsite_process = None
        return jsonify({"success": True, "message": "靶场已停止"})
    return jsonify({"success": True, "message": "靶场未在运行"})


@app.route("/api/testsite/status")
def api_testsite_status():
    # Docker模式: 靶场作为独立容器始终可用
    if os.path.exists("/.dockerenv") or os.environ.get("DOCKER_CONTAINER"):
        return jsonify({"running": True, "port": 8080, "docker": True})
    running = testsite_process is not None and testsite_process.poll() is None
    return jsonify({"running": running, "port": testsite_port})


if __name__ == "__main__":
    import os
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=5000, debug=debug)
