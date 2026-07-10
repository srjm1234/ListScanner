"""生成本地测试靶场的「模拟暴露敏感文件」。

说明
----
仓库中大部分模拟敏感文件（.env、.htaccess、backup.sql、config.php.bak 等）
都是普通文件名，可直接纳入 Git 版本控制。

但 `.git` / `.svn` / `.hg` 这类**版本控制目录**会与 Git 自身冲突，
既无法被正常提交，也会让 Git 误判为嵌套仓库。因此在启动靶场前，
由本脚本自动在 testsite/ 下生成这些文件，用于演示扫描器对「源码泄露」的识别。
"""

from pathlib import Path


def prepare_testsite(site_dir):
    """在 site_dir 下生成模拟暴露的版本控制目录，返回生成的文件列表。"""
    site_dir = Path(site_dir)
    site_dir.mkdir(parents=True, exist_ok=True)
    created = []

    # 模拟暴露的 .git 目录
    git_dir = site_dir / ".git"
    git_dir.mkdir(exist_ok=True)
    git_config = git_dir / "config"
    git_config.write_text(
        "[core]\n"
        "\trepositoryformatversion = 0\n"
        "\tfilemode = false\n"
        "\tbare = false\n"
        "\tlogallrefupdates = true\n",
        encoding="utf-8",
    )
    created.append(str(git_config))

    # 模拟暴露的 .svn 目录
    svn_dir = site_dir / ".svn"
    svn_dir.mkdir(exist_ok=True)
    svn_entries = svn_dir / "entries"
    svn_entries.write_text("12\n\n\n\n", encoding="utf-8")
    created.append(str(svn_entries))

    # 模拟暴露的 .hg 目录
    hg_dir = site_dir / ".hg"
    hg_dir.mkdir(exist_ok=True)
    (hg_dir / "store").mkdir(exist_ok=True)
    hg_requires = hg_dir / "requires"
    hg_requires.write_text("revlogv1\nstore\n", encoding="utf-8")
    created.append(str(hg_requires))

    return created


if __name__ == "__main__":
    import sys

    target = sys.argv[1] if len(sys.argv) > 1 else "."
    files = prepare_testsite(target)
    print("已生成模拟敏感文件：")
    for f in files:
        print("  -", f)
