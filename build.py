"""
PyInstaller打包脚本
用法: python build.py
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
DIST_DIR = PROJECT_DIR / "dist"
BUILD_DIR = PROJECT_DIR / "build"


def clean():
    for d in [DIST_DIR, BUILD_DIR]:
        if d.exists():
            shutil.rmtree(str(d))
    for f in PROJECT_DIR.glob("*.spec"):
        f.unlink()


def build():
    sep = ";" if os.name == "nt" else ":"

    data_args = []
    data_args.append(f"--add-data=templates{sep}templates")
    data_args.append(f"--add-data=dictionary{sep}dictionary")
    data_args.append(f"--add-data=listscanner{sep}listscanner")

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name=ListScanner",
        "--console",
        "--clean",
        *data_args,
        "--hidden-import=flask",
        "--hidden-import=requests",
        "--hidden-import=listscanner",
        "--hidden-import=listscanner.classifier",
        "--hidden-import=listscanner.config",
        "--hidden-import=listscanner.models",
        "--hidden-import=listscanner.report",
        "--hidden-import=listscanner.scanner",
        "--hidden-import=listscanner.wordlist",
        "--exclude-module=numpy",
        "--exclude-module=matplotlib",
        "--exclude-module=PIL",
        "--exclude-module=pandas",
        "--exclude-module=scipy",
        "--exclude-module=PyQt5",
        "--exclude-module=tkinter",
        "--exclude-module=IPython",
        "--exclude-module=jupyter",
        "--exclude-module=nbformat",
        "--exclude-module=sphinx",
        "--exclude-module=black",
        "--exclude-module=yapf",
        "--exclude-module=pytest",
        "--exclude-module=zmq",
        "--exclude-module=nacl",
        "main.py",
    ]

    print("开始打包...")
    result = subprocess.run(cmd, cwd=str(PROJECT_DIR))

    if result.returncode == 0:
        print(f"\n打包成功! EXE文件位于: {DIST_DIR / 'ListScanner.exe'}")

        # 复制字典文件
        dist_dict = DIST_DIR / "dictionary"
        if not dist_dict.exists():
            src_dict = PROJECT_DIR / "dictionary"
            if src_dict.exists():
                shutil.copytree(str(src_dict), str(dist_dict))
                print(f"已复制字典文件到: {dist_dict}")

        # 复制testsite靶场目录
        dist_testsite = DIST_DIR / "testsite"
        src_testsite = PROJECT_DIR / "testsite"
        if src_testsite.exists() and not dist_testsite.exists():
            shutil.copytree(str(src_testsite), str(dist_testsite))
            print(f"已复制靶场目录到: {dist_testsite}")

        # 创建使用说明
        readme = DIST_DIR / "使用说明.txt"
        readme.write_text("""ListScanner - Web路径扫描工具

使用方法:
  1. 双击 ListScanner.exe 启动扫描器 (默认端口5000)
  2. 浏览器会自动打开 http://127.0.0.1:5000

命令行参数:
  ListScanner.exe                    启动扫描器 (端口5000)
  ListScanner.exe --port 8888        指定端口
  ListScanner.exe --no-browser       不自动打开浏览器
  ListScanner.exe --testsite         启动简易靶场 (端口8080)
  ListScanner.exe --testsite --port 9090  靶场指定端口

简易靶场:
  包含常见敏感文件和目录的测试环境
  用于验证扫描器的检测能力

目录结构:
  ListScanner.exe    主程序
  dictionary/        扫描字典
  testsite/          简易靶场
""", encoding="utf-8")
        print(f"已创建使用说明: {readme}")
    else:
        print("\n打包失败!")
        sys.exit(1)


if __name__ == "__main__":
    clean()
    build()
