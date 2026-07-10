"""
ListScanner 桌面版 (CustomTkinter) — 现代化 UI
"""

import os
import sys
import shutil
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
    BUNDLE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).parent.parent
    BUNDLE_DIR = BASE_DIR

sys.path.insert(0, str(BUNDLE_DIR))
os.chdir(BASE_DIR)

from listscanner.report import save_html_report
from listscanner.scanner import WebScanner
from listscanner.wordlist import read_wordlist
from listscanner.models import ScanStats

# ==================== 主题 ====================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

C_BG = "#0f172a"
C_CARD = "#1e293b"
C_INPUT = "#0f172a"
C_PRIMARY = "#0ea5e9"
C_GREEN = "#22c55e"
C_RED = "#ef4444"
C_AMBER = "#f59e0b"
C_TEXT = "#f1f5f9"
C_DIM = "#94a3b8"
C_MUTED = "#475569"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ListScanner v2.0")
        self.geometry("1150x720")
        self.minsize(950, 600)

        # 设置图标
        if getattr(sys, "frozen", False):
            icon_path = Path(sys.executable).parent / "app.ico"
        else:
            icon_path = Path(__file__).parent / "app.ico"
        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except:
                pass

        self.scanning = False
        self.results = []
        self.wl_files = []   # 实际文件路径列表
        self.wl_display = [] # 显示名称列表

        self._build_ui()
        self._load_wordlists()

    # ==================== UI ====================
    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ===== 左侧面板 =====
        left = ctk.CTkFrame(self, width=340, corner_radius=0, fg_color=C_CARD)
        left.grid(row=0, column=0, sticky="nsew")
        left.grid_propagate(False)

        # 标题
        header = ctk.CTkFrame(left, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(16, 8))
        ctk.CTkLabel(header, text="ListScanner", font=ctk.CTkFont(size=20, weight="bold"),
                      text_color=C_PRIMARY).pack(side="left")
        ctk.CTkLabel(header, text="v2.0", font=ctk.CTkFont(family="Consolas", size=11),
                      text_color=C_MUTED).pack(side="left", padx=(6, 0))

        # 滚动区域
        scroll = ctk.CTkScrollableFrame(left, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=4)

        # 目标地址
        self._label(scroll, "目标地址")
        self.url_var = ctk.StringVar(value="http://127.0.0.1")
        ctk.CTkEntry(scroll, textvariable=self.url_var,
                      font=ctk.CTkFont(family="Consolas", size=13),
                      placeholder_text="http://target.com").pack(fill="x", padx=12, pady=(0, 10))

        # 字典文件
        self._label(scroll, "字典文件")
        wl_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        wl_frame.pack(fill="x", padx=12, pady=(0, 4))
        self.wl_combo = ctk.CTkComboBox(wl_frame, values=["加载中..."], width=220,
                                         font=ctk.CTkFont(family="Consolas", size=12),
                                         command=self._on_wordlist_change)
        self.wl_combo.pack(side="left", fill="x", expand=True)

        btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_frame.pack(fill="x", padx=12, pady=(0, 4))
        ctk.CTkButton(btn_frame, text="导入字典", height=30, width=80,
                       font=ctk.CTkFont(size=12),
                       fg_color="#334155", hover_color="#475569",
                       command=self._import_wordlist).pack(side="left")
        ctk.CTkButton(btn_frame, text="浏览", height=30, width=60,
                       font=ctk.CTkFont(size=12),
                       fg_color="#334155", hover_color="#475569",
                       command=self._browse_wordlist).pack(side="left", padx=(6, 0))

        # 字典预览
        self.wl_preview = ctk.CTkLabel(scroll, text="", font=ctk.CTkFont(size=11),
                                         text_color=C_MUTED, anchor="w", wraplength=280)
        self.wl_preview.pack(fill="x", padx=12, pady=(0, 10))

        # 扩展名
        self._label(scroll, "文件扩展名")
        self.ext_var = ctk.StringVar(value="php,html,bak,zip,asp,aspx,jsp,txt,old,sql")
        ctk.CTkEntry(scroll, textvariable=self.ext_var,
                      font=ctk.CTkFont(family="Consolas", size=13)).pack(fill="x", padx=12, pady=(0, 10))

        # 线程数
        self._label(scroll, "线程数")
        self.threads_var = ctk.IntVar(value=10)
        t_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        t_frame.pack(fill="x", padx=12, pady=(0, 10))
        self.threads_slider = ctk.CTkSlider(t_frame, from_=1, to=50, variable=self.threads_var,
                                              width=220, command=self._update_threads_label)
        self.threads_slider.pack(side="left")
        self.threads_label = ctk.CTkLabel(t_frame, text="10", width=40,
                                            font=ctk.CTkFont(family="Consolas", size=14, weight="bold"),
                                            text_color=C_PRIMARY)
        self.threads_label.pack(side="left", padx=(10, 0))

        # 超时
        self._label(scroll, "超时 (秒)")
        self.timeout_var = ctk.IntVar(value=5)
        to_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        to_frame.pack(fill="x", padx=12, pady=(0, 10))
        self.timeout_slider = ctk.CTkSlider(to_frame, from_=1, to=30, variable=self.timeout_var,
                                              width=220, command=self._update_timeout_label)
        self.timeout_slider.pack(side="left")
        self.timeout_label = ctk.CTkLabel(to_frame, text="5", width=40,
                                            font=ctk.CTkFont(family="Consolas", size=14, weight="bold"),
                                            text_color=C_PRIMARY)
        self.timeout_label.pack(side="left", padx=(10, 0))

        # 报告输出
        self._label(scroll, "报告输出")
        self.output_var = ctk.StringVar(value="report.html")
        ctk.CTkEntry(scroll, textvariable=self.output_var,
                      font=ctk.CTkFont(family="Consolas", size=13)).pack(fill="x", padx=12, pady=(0, 10))

        # 分隔线
        ctk.CTkFrame(left, height=1, fg_color=C_MUTED).pack(fill="x", padx=16, pady=12)

        # 按钮
        self.scan_btn = ctk.CTkButton(left, text="▶  开始扫描", height=44,
                                        font=ctk.CTkFont(size=15, weight="bold"),
                                        fg_color=C_PRIMARY, hover_color="#0284c7",
                                        command=self._start_scan)
        self.scan_btn.pack(fill="x", padx=16, pady=(0, 8))

        self.stop_btn = ctk.CTkButton(left, text="■  停止扫描", height=36,
                                       font=ctk.CTkFont(size=13),
                                       fg_color="#334155", hover_color="#475569",
                                       state="disabled", command=self._stop_scan)
        self.stop_btn.pack(fill="x", padx=16, pady=(0, 16))

        # 统计卡片
        stats_frame = ctk.CTkFrame(left, fg_color="transparent")
        stats_frame.pack(fill="x", padx=12, pady=(0, 12))
        stats_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.stat_labels = {}
        for i, (key, label, color) in enumerate([
            ("total", "测试路径", C_PRIMARY),
            ("found", "发现结果", C_GREEN),
            ("high", "高风险", C_RED),
            ("errors", "请求失败", C_AMBER),
        ]):
            card = ctk.CTkFrame(stats_frame, fg_color=C_INPUT, corner_radius=8)
            card.grid(row=0, column=i, padx=3, sticky="nsew")
            lbl = ctk.CTkLabel(card, text="0", font=ctk.CTkFont(family="Consolas", size=20, weight="bold"),
                                text_color=color)
            lbl.pack(pady=(8, 0))
            ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=10),
                          text_color=C_MUTED).pack(pady=(0, 6))
            self.stat_labels[key] = lbl

        # 进度条
        self.progress = ctk.CTkProgressBar(left, height=8, corner_radius=4)
        self.progress.pack(fill="x", padx=16, pady=(0, 6))
        self.progress.set(0)

        self.status_label = ctk.CTkLabel(left, text="就绪", font=ctk.CTkFont(size=11),
                                           text_color=C_MUTED, anchor="w")
        self.status_label.pack(fill="x", padx=16, pady=(0, 16))

        # ===== 右侧面板 =====
        right = ctk.CTkFrame(self, fg_color=C_BG, corner_radius=0)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        # 工具栏
        toolbar = ctk.CTkFrame(right, fg_color="transparent")
        toolbar.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 6))

        ctk.CTkLabel(toolbar, text="扫描结果", font=ctk.CTkFont(size=15, weight="bold"),
                      text_color=C_TEXT).pack(side="left")

        self.filter_var = ctk.StringVar(value="all")
        filter_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        filter_frame.pack(side="left", padx=(20, 0))
        for val, label in [("all", "全部"), ("高风险", "高风险"), ("中风险", "中风险"), ("低风险", "低风险")]:
            ctk.CTkRadioButton(filter_frame, text=label, variable=self.filter_var, value=val,
                                font=ctk.CTkFont(size=12), command=self._apply_filter,
                                fg_color=C_PRIMARY, border_color=C_MUTED,
                                hover_color=C_PRIMARY).pack(side="left", padx=6)

        ctk.CTkButton(toolbar, text="导出报告", width=90, height=30,
                       font=ctk.CTkFont(size=12),
                       fg_color="#334155", hover_color="#475569",
                       command=self._export_report).pack(side="right")

        # 结果区域
        result_frame = ctk.CTkFrame(right, fg_color=C_CARD, corner_radius=8)
        result_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(4, 8))
        result_frame.grid_rowconfigure(0, weight=1)
        result_frame.grid_columnconfigure(0, weight=1)

        # 结果文本框（高性能滚动）
        self.result_text = ctk.CTkTextbox(result_frame, fg_color=C_INPUT, text_color=C_TEXT,
                                            font=ctk.CTkFont(family="Consolas", size=12),
                                            corner_radius=6, state="disabled",
                                            scrollbar_button_color="#1e293b",
                                            scrollbar_button_hover_color="#334155")
        self.result_text.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)

        # 配置颜色标签
        self.result_text.tag_config("header", foreground=C_DIM)
        self.result_text.tag_config("high", foreground="#fca5a5")
        self.result_text.tag_config("med", foreground="#fcd34d")
        self.result_text.tag_config("low", foreground="#86efac")
        self.result_text.tag_config("sep", foreground="#334155")

        right.grid_rowconfigure(1, weight=1)

        self._reset_results()

    def _label(self, parent, text):
        ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(size=12, weight="bold"),
                      text_color=C_DIM, anchor="w").pack(fill="x", padx=12, pady=(8, 2))

    def _update_threads_label(self, val):
        self.threads_label.configure(text=str(int(val)))

    def _update_timeout_label(self, val):
        self.timeout_label.configure(text=str(int(val)))

    # ==================== 字典管理 ====================
    def _load_wordlists(self):
        """扫描 dictionary/ 目录，加载所有 .txt 字典"""
        self.wl_files = []
        self.wl_display = []
        dict_dir = BASE_DIR / "dictionary"

        if dict_dir.is_dir():
            for f in sorted(dict_dir.glob("*.txt")):
                self.wl_files.append(str(f))
                count = self._count_wordlist(f)
                self.wl_display.append(f"{f.name}  ({count} 条)")

        if self.wl_display:
            self.wl_combo.configure(values=self.wl_display)
            self.wl_combo.set(self.wl_display[0])
            self._on_wordlist_change(self.wl_display[0])
        else:
            self.wl_combo.configure(values=["无字典文件"])
            self.wl_combo.set("无字典文件")
            self.wl_preview.configure(text="请导入或创建字典文件")

    def _count_wordlist(self, path):
        """统计字典有效条目数"""
        try:
            lines = Path(path).read_text(encoding="utf-8").splitlines()
            return sum(1 for l in lines if l.strip() and not l.strip().startswith("#"))
        except:
            return 0

    def _on_wordlist_change(self, selection=None):
        """切换字典时更新预览"""
        path = self._get_selected_path()
        if path:
            count = self._count_wordlist(path)
            self.wl_preview.configure(text=f"已选择: {Path(path).name}  |  {count} 条路径")
        else:
            self.wl_preview.configure(text="")

    def _get_selected_path(self):
        """从下拉框选中项获取实际文件路径"""
        sel = self.wl_combo.get()
        if not sel or sel == "无字典文件":
            return None
        name = sel.split("  (")[0].strip()
        for f in self.wl_files:
            if Path(f).name == name:
                return f
        if Path(sel).exists():
            return sel
        return None

    def _import_wordlist(self):
        """导入外部字典文件到 dictionary/ 目录"""
        path = filedialog.askopenfilename(
            title="选择要导入的字典文件",
            filetypes=[("文本文件", "*.txt"), ("字典文件", "*.dic *.lst"), ("所有文件", "*.*")],
        )
        if not path:
            return

        src = Path(path)
        dict_dir = BASE_DIR / "dictionary"
        dict_dir.mkdir(exist_ok=True)
        dst = dict_dir / src.name

        # 检查是否已存在
        if dst.exists():
            overwrite = messagebox.askyesno("文件已存在",
                                             f"dictionary/{src.name} 已存在，是否覆盖？")
            if not overwrite:
                return

        try:
            shutil.copy2(str(src), str(dst))
            count = self._count_wordlist(dst)
            messagebox.showinfo("导入成功",
                                 f"已导入: {src.name}\n"
                                 f"条目数: {count}\n"
                                 f"位置: {dst}")
            self._load_wordlists()
            # 选中新导入的
            display = f"{src.name}  ({count} 条)"
            if display in self.wl_display:
                self.wl_combo.set(display)
                self._on_wordlist_change(display)
        except Exception as e:
            messagebox.showerror("导入失败", str(e))

    def _browse_wordlist(self):
        """浏览选择任意位置的字典文件（不复制，直接引用）"""
        path = filedialog.askopenfilename(
            title="选择字典文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
            initialdir=str(BASE_DIR / "dictionary"),
        )
        if not path:
            return

        p = Path(path)
        count = self._count_wordlist(p)
        display = f"{p.name}  ({count} 条)"

        # 添加到列表（如果还没有）
        if path not in self.wl_files:
            self.wl_files.append(path)
            self.wl_display.append(display)
            self.wl_combo.configure(values=self.wl_display)

        self.wl_combo.set(display)
        self._on_wordlist_change(display)

    # ==================== 筛选 ====================
    def _reset_results(self):
        """重置结果区域"""
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("end", "\n\n\n  扫描结果将在此处显示\n\n  配置左侧参数后点击「开始扫描」\n", "header")
        self.result_text.configure(state="disabled")

    def _apply_filter(self):
        """根据筛选条件重新渲染结果"""
        f = self.filter_var.get()
        filtered = [r for r in self.results if f == "all" or r.risk_level == f]

        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")

        # 表头
        hdr = f"{'状态码':<8}{'风险':<10}{'类型':<14}{'大小':>8}  {'Content-Type'}\n"
        self.result_text.insert("end", hdr, "header")
        self.result_text.insert("end", "─" * 80 + "\n", "sep")

        if not filtered:
            msg = "  暂无匹配结果\n" if f != "all" else ""
            self.result_text.insert("end", msg, "header")
        else:
            for r in filtered:
                self._write_result(r)

        self.result_text.configure(state="disabled")

    def _write_result(self, r):
        """写入一条结果到文本框"""
        tag = "high" if r.risk_level == "高风险" else "med" if r.risk_level == "中风险" else "low"
        rc = {"high": "🔴", "med": "🟡", "low": "🟢"}[tag]
        line = f"{r.status_code:<8}{rc} {r.risk_level:<8}{r.risk_type:<14}{r.size:>6}B  {r.content_type or '-'}\n"
        url_line = f"         {r.url}\n"
        self.result_text.configure(state="normal")
        self.result_text.insert("end", line, tag)
        self.result_text.insert("end", url_line, "header")
        self.result_text.configure(state="disabled")

    # ==================== 扫描 ====================
    def _start_scan(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("提示", "请输入目标地址")
            return
        wl = self._get_selected_path()
        if not wl:
            messagebox.showwarning("提示", "请选择字典文件")
            return

        exts = [e.strip() for e in self.ext_var.get().split(",") if e.strip()]
        try:
            words = read_wordlist(wl, exts)
        except Exception as e:
            messagebox.showerror("错误", f"读取字典失败: {e}")
            return
        if not words:
            messagebox.showwarning("提示", "字典为空")
            return

        self.results = []
        self._reset_results()
        for key in self.stat_labels:
            self.stat_labels[key].configure(text="0")
        self.progress.set(0)
        self.scanning = True
        self.scan_btn.configure(state="disabled", text="扫描中...", fg_color="#334155")
        self.stop_btn.configure(state="normal")
        self.status_label.configure(text=f"扫描中... 共 {len(words)} 条路径", text_color=C_PRIMARY)

        scanner = WebScanner(url, words, self.threads_var.get(), self.timeout_var.get())
        threading.Thread(target=self._run_scan, args=(scanner,), daemon=True).start()

    def _run_scan(self, scanner):
        from concurrent.futures import ThreadPoolExecutor, as_completed

        total = len(scanner.wordlist)
        completed = found = high = errors = 0

        with ThreadPoolExecutor(max_workers=scanner.threads) as pool:
            futures = [pool.submit(scanner.check_path, path) for path in scanner.wordlist]
            for future in as_completed(futures):
                if not self.scanning:
                    pool.shutdown(wait=False, cancel_futures=True)
                    break
                result, state = future.result()
                completed += 1
                if state == "found":
                    found += 1
                    if result.risk_level == "高风险":
                        high += 1
                    self.results.append(result)
                    self.after(0, self._add_row, result)

                elif state == "error":
                    errors += 1
                pct = round(completed / total * 100)
                self.after(0, self._update_progress, pct, total, found, high, errors)

        self.scanning = False
        self.after(0, self._scan_done)

    def _add_row(self, r):
        """实时添加一条结果"""
        if len(self.results) == 1:
            self.result_text.configure(state="normal")
            self.result_text.delete("1.0", "end")
            hdr = f"{'状态码':<8}{'风险':<10}{'类型':<14}{'大小':>8}  {'Content-Type'}\n"
            self.result_text.insert("end", hdr, "header")
            self.result_text.insert("end", "─" * 80 + "\n", "sep")
            self.result_text.configure(state="disabled")
        self._write_result(r)
        self.result_text.see("end")

    def _update_progress(self, pct, total, found, high, errors):
        self.progress.set(pct / 100)
        self.stat_labels["total"].configure(text=str(total))
        self.stat_labels["found"].configure(text=str(found))
        self.stat_labels["high"].configure(text=str(high))
        self.stat_labels["errors"].configure(text=str(errors))
        self.status_label.configure(text=f"扫描中... {pct}%  |  发现 {found} 条  |  高风险 {high} 条")

    def _scan_done(self):
        self.scan_btn.configure(state="normal", text="▶  开始扫描", fg_color=C_PRIMARY)
        self.stop_btn.configure(state="disabled")
        self.results.sort(key=lambda r: ({"高风险": 0, "中风险": 1, "低风险": 2}.get(r.risk_level, 9),
                                         r.status_code, r.path))
        self._apply_filter()
        total = int(self.stat_labels["total"].cget("text"))
        found = int(self.stat_labels["found"].cget("text"))
        high = int(self.stat_labels["high"].cget("text"))
        self.status_label.configure(text=f"扫描完成  |  共 {total} 条  |  发现 {found} 条  |  高风险 {high} 条",
                                     text_color=C_GREEN)
        messagebox.showinfo("扫描完成", f"发现 {found} 条结果，其中高风险 {high} 条")

    def _stop_scan(self):
        self.scanning = False
        self.status_label.configure(text="已停止", text_color=C_AMBER)

    # ==================== 导出 ====================
    def _export_report(self):
        if not self.results:
            messagebox.showwarning("提示", "没有可导出的结果")
            return
        path = filedialog.asksaveasfilename(
            title="保存报告", defaultextension=".html",
            filetypes=[("HTML文件", "*.html")], initialfile=self.output_var.get())
        if not path:
            return
        stats = ScanStats(total=int(self.stat_labels["total"].cget("text")))
        stats.found = len(self.results)
        stats.errors = int(self.stat_labels["errors"].cget("text"))
        try:
            save_html_report(self.results, path, self.url_var.get(), stats)
            messagebox.showinfo("导出成功", f"报告已保存到:\n{path}")
        except Exception as e:
            messagebox.showerror("导出失败", str(e))


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
