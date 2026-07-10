import argparse
import sys

from listscanner.config import load_settings
from listscanner.report import save_html_report
from listscanner.scanner import WebScanner, fix_url
from listscanner.wordlist import read_wordlist


def main():
    settings = load_settings()
    parser = build_parser(settings)

    if len(sys.argv) == 1:
        parser.print_help()
        return 0

    args = parser.parse_args()
    extensions = split_extensions(args.extensions)
    words = read_wordlist(args.wordlist, extensions)

    if not words:
        print("[错误] 字典为空，请检查字典文件。")
        return 1

    target_url = fix_url(args.url)
    print(f"[*] 目标地址：{target_url}")
    print(f"[*] 字典文件：{args.wordlist}")
    print(f"[*] 测试路径：{len(words)} 条")
    print(f"[*] 线程数量：{args.threads}")

    scanner = WebScanner(
        target_url=target_url,
        wordlist=words,
        threads=args.threads,
        timeout=args.timeout,
    )
    results = scanner.scan()

    save_html_report(results, args.output, target_url, scanner.stats)
    print("\n[*] 扫描完成")
    print(f"[*] 发现结果：{len(results)} 条")
    print(f"[*] 未发现：{scanner.stats.not_found} 条")
    print(f"[*] 请求失败：{scanner.stats.errors} 条")
    print(f"[*] HTML报告：{args.output}")
    return 0


def build_parser(settings):
    parser = argparse.ArgumentParser(
        prog="python ListScanner.py",
        description=" Web 路径与敏感文件扫描工具",
    )
    parser.add_argument("-u", "--url", required=True, help="目标站点地址，例如 http://127.0.0.1")
    parser.add_argument(
        "-w",
        "--wordlist",
        default=settings["wordlist"],
        help=f"字典文件，默认：{settings['wordlist']}",
    )
    parser.add_argument(
        "-e",
        "--extensions",
        default=settings["extensions"],
        help=f"扩展名，多个用逗号分隔，默认：{settings['extensions']}",
    )
    parser.add_argument(
        "-t",
        "--threads",
        type=int,
        default=settings["threads"],
        help=f"线程数量，默认：{settings['threads']}",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=settings["timeout"],
        help=f"请求超时时间，默认：{settings['timeout']} 秒",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=settings["output"],
        help=f"HTML报告文件，默认：{settings['output']}",
    )
    return parser


def split_extensions(value):
    extensions = []
    for item in value.split(","):
        item = item.strip().lstrip(".")
        if item:
            extensions.append(item)
    return extensions
