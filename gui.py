# -*- coding: utf-8 -*-
"""
Playwright 网络抓包工具 - GUI 界面
使用 tkinter 构建，提供实时请求监控、过滤、查看和导出功能
"""

import sys
import os
import json
import logging
import time
import threading
import webbrowser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from datetime import datetime
from capture import RequestCapture, resource_path

# 配置日志 - 输出到文件和控制台
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, f"capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)
logger.info(f"日志文件: {LOG_FILE}")


class CaptureGUI:
    """抓包工具 GUI 主界面"""

    # 颜色主题
    COLORS = {
        "bg": "#1e1e2e",
        "fg": "#cdd6f4",
        "accent": "#89b4fa",
        "success": "#a6e3a1",
        "warning": "#f9e2af",
        "error": "#f38ba8",
        "info": "#89dceb",
        "header_bg": "#313244",
        "row_alt": "#181825",
        "row_normal": "#1e1e2e",
        "button_bg": "#45475a",
        "button_fg": "#cdd6f4",
        "entry_bg": "#313244",
        "entry_fg": "#cdd6f4",
        "select_bg": "#585b70",
    }

    METHOD_COLORS = {
        "GET": "#a6e3a1",
        "POST": "#89b4fa",
        "PUT": "#f9e2af",
        "DELETE": "#f38ba8",
        "PATCH": "#cba6f7",
        "HEAD": "#94e2d5",
        "OPTIONS": "#fab387",
    }

    def __init__(self):
        self.capture = RequestCapture()
        self.browser_thread = None
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.is_running = False
        self.request_count = 0
        self._poll_job = None  # 定时轮询任务 ID

        self.root = tk.Tk()
        self.root.title("🔍 Playwright 网络抓包工具")
        self.root.geometry("1200x750")
        self.root.minsize(900, 550)
        self.root.configure(bg=self.COLORS["bg"])
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # 设置 DPI 感知（Windows）
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

        self._build_styles()
        self._build_toolbar()
        self._build_filter_bar()
        self._build_request_table()
        self._build_detail_panel()
        self._build_status_bar()

    def _build_styles(self):
        """配置 ttk 样式"""
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Treeview",
                        background=self.COLORS["bg"],
                        foreground=self.COLORS["fg"],
                        fieldbackground=self.COLORS["bg"],
                        borderwidth=0,
                        rowheight=26,
                        font=("Consolas", 10))
        style.configure("Treeview.Heading",
                        background=self.COLORS["header_bg"],
                        foreground=self.COLORS["fg"],
                        borderwidth=0,
                        font=("Microsoft YaHei UI", 10, "bold"))
        style.map("Treeview",
                  background=[("selected", self.COLORS["select_bg"])],
                  foreground=[("selected", "#ffffff")])
        style.map("Treeview.Heading",
                  background=[("active", self.COLORS["select_bg"])])

        style.configure("TButton",
                        background=self.COLORS["button_bg"],
                        foreground=self.COLORS["button_fg"],
                        borderwidth=0,
                        font=("Microsoft YaHei UI", 10),
                        padding=(12, 6))
        style.map("TButton",
                  background=[("active", self.COLORS["select_bg"])])

        style.configure("TEntry",
                        fieldbackground=self.COLORS["entry_bg"],
                        foreground=self.COLORS["entry_fg"],
                        borderwidth=0)
        style.map("TEntry",
                  fieldbackground=[("focus", self.COLORS["select_bg"])])

        style.configure("TCombobox",
                        fieldbackground=self.COLORS["entry_bg"],
                        foreground=self.COLORS["entry_fg"],
                        borderwidth=0)
        style.map("TCombobox",
                  fieldbackground=[("readonly", self.COLORS["entry_bg"])])

        style.configure("TLabel",
                        background=self.COLORS["bg"],
                        foreground=self.COLORS["fg"],
                        font=("Microsoft YaHei UI", 10))

        style.configure("Status.TLabel",
                        background=self.COLORS["header_bg"],
                        foreground=self.COLORS["fg"],
                        font=("Consolas", 9))

        style.configure("Toolbar.TFrame", background=self.COLORS["header_bg"])
        style.configure("Main.TFrame", background=self.COLORS["bg"])
        style.configure("Filter.TFrame", background=self.COLORS["header_bg"])
        style.configure("Detail.TFrame", background=self.COLORS["bg"])
        style.configure("Status.TFrame", background=self.COLORS["header_bg"])

        style.configure("Green.TButton",
                        background="#40a02b",
                        foreground="#ffffff",
                        font=("Microsoft YaHei UI", 10, "bold"),
                        padding=(16, 6))
        style.map("Green.TButton",
                  background=[("active", "#50b03b")])

        style.configure("Red.TButton",
                        background="#d20f39",
                        foreground="#ffffff",
                        font=("Microsoft YaHei UI", 10, "bold"),
                        padding=(16, 6))
        style.map("Red.TButton",
                  background=[("active", "#e22f59")])

    def _build_toolbar(self):
        """构建工具栏"""
        toolbar = ttk.Frame(self.root, style="Toolbar.TFrame", padding=(10, 8))
        toolbar.pack(fill=tk.X)

        # 标题
        title_label = tk.Label(toolbar, text="🔍 Playwright 抓包工具",
                               bg=self.COLORS["header_bg"],
                               fg=self.COLORS["accent"],
                               font=("Microsoft YaHei UI", 14, "bold"))
        title_label.pack(side=tk.LEFT, padx=(0, 20))

        # 启动按钮
        self.start_btn = ttk.Button(toolbar, text="▶ 启动浏览器",
                                    style="Green.TButton",
                                    command=self._start_browser)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 5))

        # 停止按钮
        self.stop_btn = ttk.Button(toolbar, text="⏹ 停止抓包",
                                   style="Red.TButton",
                                   command=self._stop_browser,
                                   state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 5))

        # 清空按钮
        ttk.Button(toolbar, text="🗑 清空",
                   command=self._clear_requests).pack(side=tk.LEFT, padx=(0, 5))

        # 导出按钮
        ttk.Button(toolbar, text="💾 导出 JSON",
                   command=self._export_json).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="📄 导出 HAR",
                   command=self._export_har).pack(side=tk.LEFT, padx=(0, 5))

        # URL 输入框
        url_frame = ttk.Frame(toolbar, style="Toolbar.TFrame")
        url_frame.pack(side=tk.RIGHT)

        tk.Label(url_frame, text="URL:",
                 bg=self.COLORS["header_bg"],
                 fg=self.COLORS["fg"],
                 font=("Microsoft YaHei UI", 10)).pack(side=tk.LEFT, padx=(0, 5))

        self.url_entry = ttk.Entry(url_frame, width=45)
        self.url_entry.insert(0, "https://www.baidu.com")
        self.url_entry.pack(side=tk.LEFT, padx=(0, 5))

    def _build_filter_bar(self):
        """构建过滤栏"""
        filter_bar = ttk.Frame(self.root, style="Filter.TFrame", padding=(10, 6))
        filter_bar.pack(fill=tk.X)

        tk.Label(filter_bar, text="🔍 过滤:",
                 bg=self.COLORS["header_bg"],
                 fg=self.COLORS["fg"],
                 font=("Microsoft YaHei UI", 10)).pack(side=tk.LEFT, padx=(0, 5))

        self.filter_entry = ttk.Entry(filter_bar, width=40)
        self.filter_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.filter_entry.bind("<Return>", lambda e: self._apply_filter())
        self.filter_entry.bind("<KeyRelease>", lambda e: self._apply_filter())

        tk.Label(filter_bar, text="方法:",
                 bg=self.COLORS["header_bg"],
                 fg=self.COLORS["fg"],
                 font=("Microsoft YaHei UI", 10)).pack(side=tk.LEFT, padx=(0, 5))

        self.method_var = tk.StringVar(value="ALL")
        method_combo = ttk.Combobox(filter_bar, textvariable=self.method_var,
                                    values=["ALL", "GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
                                    width=8, state="readonly")
        method_combo.pack(side=tk.LEFT, padx=(0, 10))
        method_combo.bind("<<ComboboxSelected>>", lambda e: self._apply_filter())

        tk.Label(filter_bar, text="状态码:",
                 bg=self.COLORS["header_bg"],
                 fg=self.COLORS["fg"],
                 font=("Microsoft YaHei UI", 10)).pack(side=tk.LEFT, padx=(0, 5))

        self.status_entry = ttk.Entry(filter_bar, width=6)
        self.status_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.status_entry.bind("<KeyRelease>", lambda e: self._apply_filter())

        # 请求计数
        self.count_label = tk.Label(filter_bar, text="共 0 条请求",
                                    bg=self.COLORS["header_bg"],
                                    fg=self.COLORS["accent"],
                                    font=("Microsoft YaHei UI", 10, "bold"))
        self.count_label.pack(side=tk.RIGHT)

    def _build_request_table(self):
        """构建请求列表表格"""
        table_frame = ttk.Frame(self.root, style="Main.TFrame")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(5, 0))

        columns = ("index", "method", "status", "url", "type", "size", "time")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings",
                                 selectmode="browse")

        self.tree.heading("index", text="#")
        self.tree.heading("method", text="方法")
        self.tree.heading("status", text="状态")
        self.tree.heading("url", text="URL")
        self.tree.heading("type", text="类型")
        self.tree.heading("size", text="大小")
        self.tree.heading("time", text="时间")

        self.tree.column("index", width=50, minwidth=40, anchor=tk.CENTER)
        self.tree.column("method", width=70, minwidth=60, anchor=tk.CENTER)
        self.tree.column("status", width=60, minwidth=50, anchor=tk.CENTER)
        self.tree.column("url", width=500, minwidth=200)
        self.tree.column("type", width=100, minwidth=80)
        self.tree.column("size", width=80, minwidth=60, anchor=tk.E)
        self.tree.column("time", width=160, minwidth=120)

        # 滚动条
        scrollbar_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # 绑定选择事件
        self.tree.bind("<<TreeviewSelect>>", self._on_select_request)
        self.tree.bind("<Double-1>", self._on_double_click)

    def _build_detail_panel(self):
        """构建详情面板"""
        detail_frame = ttk.Frame(self.root, style="Detail.TFrame")
        detail_frame.pack(fill=tk.BOTH, padx=5, pady=5)

        # 标签页
        self.notebook = ttk.Notebook(detail_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # 通用信息标签页
        self.general_text = scrolledtext.ScrolledText(
            self.notebook, wrap=tk.WORD,
            bg=self.COLORS["bg"], fg=self.COLORS["fg"],
            insertbackground=self.COLORS["fg"],
            font=("Consolas", 10),
            state=tk.DISABLED, height=8
        )
        self.notebook.add(self.general_text, text="📋 通用信息")

        # 请求头标签页
        self.req_headers_text = scrolledtext.ScrolledText(
            self.notebook, wrap=tk.WORD,
            bg=self.COLORS["bg"], fg=self.COLORS["fg"],
            insertbackground=self.COLORS["fg"],
            font=("Consolas", 10),
            state=tk.DISABLED, height=8
        )
        self.notebook.add(self.req_headers_text, text="📤 请求头")

        # 响应头标签页
        self.resp_headers_text = scrolledtext.ScrolledText(
            self.notebook, wrap=tk.WORD,
            bg=self.COLORS["bg"], fg=self.COLORS["fg"],
            insertbackground=self.COLORS["fg"],
            font=("Consolas", 10),
            state=tk.DISABLED, height=8
        )
        self.notebook.add(self.resp_headers_text, text="📥 响应头")

        # 响应体标签页
        self.resp_body_text = scrolledtext.ScrolledText(
            self.notebook, wrap=tk.WORD,
            bg=self.COLORS["bg"], fg=self.COLORS["fg"],
            insertbackground=self.COLORS["fg"],
            font=("Consolas", 10),
            state=tk.DISABLED, height=8
        )
        self.notebook.add(self.resp_body_text, text="📄 响应体")

        # 请求体标签页
        self.req_body_text = scrolledtext.ScrolledText(
            self.notebook, wrap=tk.WORD,
            bg=self.COLORS["bg"], fg=self.COLORS["fg"],
            insertbackground=self.COLORS["fg"],
            font=("Consolas", 10),
            state=tk.DISABLED, height=8
        )
        self.notebook.add(self.req_body_text, text="📤 请求体")

    def _build_status_bar(self):
        """构建状态栏"""
        status_bar = ttk.Frame(self.root, style="Status.TFrame", padding=(10, 4))
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_label = tk.Label(status_bar, text="就绪 - 请点击「启动浏览器」开始抓包",
                                     bg=self.COLORS["header_bg"],
                                     fg=self.COLORS["fg"],
                                     font=("Microsoft YaHei UI", 9),
                                     anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _set_text(self, widget, content):
        """安全地设置文本控件内容"""
        widget.configure(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, content)
        widget.configure(state=tk.DISABLED)

    def _format_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes is None:
            return "-"
        try:
            size = int(size_bytes)
            if size < 1024:
                return f"{size} B"
            elif size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"
            else:
                return f"{size / (1024 * 1024):.1f} MB"
        except (ValueError, TypeError):
            return str(size_bytes)

    def _get_status_color(self, status_code):
        """根据状态码返回颜色"""
        if status_code is None:
            return self.COLORS["fg"]
        code = int(status_code)
        if 200 <= code < 300:
            return self.COLORS["success"]
        elif 300 <= code < 400:
            return self.COLORS["info"]
        elif 400 <= code < 500:
            return self.COLORS["warning"]
        else:
            return self.COLORS["error"]

    def _start_polling(self):
        """启动定时轮询，每 200ms 从 capture 中读取新增请求并更新表格"""
        if self._poll_job is not None:
            return
        self._poll()

    def _poll(self):
        """轮询一次：读取新增请求，更新表格"""
        new_requests = self.capture.get_new_requests()
        if new_requests:
            for req in new_requests:
                self.request_count += 1
                self._insert_request_row(req, self.request_count)
            self.count_label.configure(text=f"共 {self.request_count} 条请求")

        if self.is_running:
            self._poll_job = self.root.after(200, self._poll)

    def _stop_polling(self):
        """停止定时轮询"""
        if self._poll_job is not None:
            self.root.after_cancel(self._poll_job)
            self._poll_job = None
        # 最后再拉一次，确保不遗漏
        new_requests = self.capture.get_new_requests()
        if new_requests:
            for req in new_requests:
                self.request_count += 1
                self._insert_request_row(req, self.request_count)
            self.count_label.configure(text=f"共 {self.request_count} 条请求")

    def _insert_request_row(self, req, index):
        """插入一行请求到表格"""
        method = req.get("method", "-")
        status = req.get("status_code", "-")
        url = req.get("url", "-")
        resource_type = req.get("resource_type", "-")
        size = self._format_size(req.get("response_size"))
        timestamp = req.get("timestamp", "-")

        # 截断过长的 URL
        display_url = url if len(url) <= 120 else url[:117] + "..."

        item_id = self.tree.insert("", tk.END, values=(
            index, method, status, display_url, resource_type, size, timestamp
        ))

        # 设置方法列颜色标签
        method_color = self.METHOD_COLORS.get(method.upper(), self.COLORS["fg"])
        self.tree.tag_configure(f"method_{method}_{index}", foreground=method_color)
        self.tree.item(item_id, tags=(f"method_{method}_{index}",))

    def _apply_filter(self):
        """应用过滤条件"""
        keyword = self.filter_entry.get().strip()
        method = self.method_var.get()
        status = self.status_entry.get().strip()

        if method == "ALL":
            method = None
        if not status:
            status = None

        # 清空表格
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 获取过滤后的请求
        filtered = self.capture.get_filtered_requests(keyword, method, status)

        for i, req in enumerate(filtered):
            self._insert_request_row(req, i + 1)

        self.count_label.configure(text=f"显示 {len(filtered)} / {self.request_count} 条请求")

    def _on_select_request(self, event):
        """选择请求时显示详情"""
        selection = self.tree.selection()
        if not selection:
            return

        item = selection[0]
        values = self.tree.item(item, "values")
        index = int(values[0]) - 1

        requests = self.capture.get_filtered_requests(
            self.filter_entry.get().strip() or None,
            self.method_var.get() if self.method_var.get() != "ALL" else None,
            self.status_entry.get().strip() or None
        )

        if index < len(requests):
            self._show_request_detail(requests[index])

    def _show_request_detail(self, req):
        """显示请求详情"""
        # 通用信息
        general_info = (
            f"{'=' * 60}\n"
            f"  请求 URL:  {req.get('url', '-')}\n"
            f"  请求方法:  {req.get('method', '-')}\n"
            f"  状态码:    {req.get('status_code', '-')}\n"
            f"  资源类型:  {req.get('resource_type', '-')}\n"
            f"  响应大小:  {self._format_size(req.get('response_size'))}\n"
            f"  请求时间:  {req.get('timestamp', '-')}\n"
            f"{'=' * 60}"
        )
        self._set_text(self.general_text, general_info)

        # 请求头
        req_headers = req.get("request_headers", {})
        if req_headers:
            headers_str = "\n".join(f"  {k}: {v}" for k, v in req_headers.items())
            self._set_text(self.req_headers_text, f"请求头:\n{headers_str}")
        else:
            self._set_text(self.req_headers_text, "（无请求头数据）")

        # 响应头
        resp_headers = req.get("response_headers", {})
        if resp_headers:
            headers_str = "\n".join(f"  {k}: {v}" for k, v in resp_headers.items())
            self._set_text(self.resp_headers_text, f"响应头:\n{headers_str}")
        else:
            self._set_text(self.resp_headers_text, "（无响应头数据）")

        # 响应体
        resp_body = req.get("response_body", "")
        if resp_body:
            # 尝试格式化 JSON
            try:
                parsed = json.loads(resp_body)
                body_str = json.dumps(parsed, ensure_ascii=False, indent=2)
            except (json.JSONDecodeError, TypeError):
                body_str = str(resp_body)
            # 限制显示长度
            if len(body_str) > 50000:
                body_str = body_str[:50000] + "\n\n... (内容过长，已截断，请导出 JSON 查看完整内容)"
            self._set_text(self.resp_body_text, body_str)
        else:
            self._set_text(self.resp_body_text, "（无响应体数据）")

        # 请求体
        req_body = req.get("request_body", "")
        if req_body:
            try:
                parsed = json.loads(req_body)
                body_str = json.dumps(parsed, ensure_ascii=False, indent=2)
            except (json.JSONDecodeError, TypeError):
                body_str = str(req_body)
            if len(body_str) > 50000:
                body_str = body_str[:50000] + "\n\n... (内容过长，已截断)"
            self._set_text(self.req_body_text, body_str)
        else:
            self._set_text(self.req_body_text, "（无请求体数据）")

    def _on_double_click(self, event):
        """双击请求时在浏览器中打开 URL"""
        selection = self.tree.selection()
        if not selection:
            return
        item = selection[0]
        values = self.tree.item(item, "values")
        url = values[3]
        webbrowser.open(url)

    def _start_browser(self):
        """启动浏览器并开始抓包"""
        if self.is_running:
            return

        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("提示", "请输入要打开的 URL")
            return

        if not url.startswith(("http://", "https://")):
            url = "https://" + url
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, url)

        self.is_running = True
        self.capture.start()
        self.start_btn.configure(state=tk.DISABLED)
        self.stop_btn.configure(state=tk.NORMAL)
        self.status_label.configure(text="正在启动浏览器...")

        # 启动定时轮询
        self._start_polling()

        self.browser_thread = threading.Thread(target=self._run_browser, args=(url,), daemon=True)
        self.browser_thread.start()

    def _run_browser(self, url):
        """在独立线程中运行浏览器"""
        logger.info(f"=== 浏览器线程启动 === url={url}")
        try:
            from playwright.sync_api import sync_playwright
            logger.info("Playwright 导入成功")

            self.playwright = sync_playwright().start()
            logger.info("sync_playwright().start() 成功")

            # 启动 Chromium 浏览器（有头模式）
            logger.info("正在启动 Chromium...")
            self.browser = self.playwright.chromium.launch(
                headless=False,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                ]
            )
            logger.info(f"Chromium 启动成功, connected={self.browser.is_connected()}")

            # 创建上下文
            self.context = self.browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            logger.info("浏览器上下文创建成功")

            # 创建页面
            self.page = self.context.new_page()
            logger.info("页面创建成功")

            # 注册网络请求监听
            self.page.on("request", self._on_request)
            self.page.on("response", self._on_response)
            logger.info("网络请求监听已注册")

            self.root.after(0, lambda: self.status_label.configure(
                text=f"浏览器已启动 - 正在抓包中... | URL: {url}"))

            # 导航到目标 URL
            logger.info(f"正在导航到: {url}")
            self.page.goto(url, wait_until="domcontentloaded")
            logger.info(f"页面加载完成: {url}")

            # 保持浏览器打开，直到用户点击停止或手动关闭浏览器窗口
            logger.info("进入保持循环, 等待用户操作...")
            try:
                loop_count = 0
                while self.is_running:
                    # 检查浏览器是否被用户手动关闭
                    connected = self.browser.is_connected()
                    if not connected:
                        logger.warning(f"浏览器连接已断开 (loop #{loop_count})")
                        break
                    if loop_count % 20 == 0:
                        logger.debug(f"保持循环中... (loop #{loop_count}, connected={connected})")
                    loop_count += 1
                    time.sleep(0.5)
                logger.info(f"保持循环退出, loop_count={loop_count}, is_running={self.is_running}")
            except Exception as e:
                logger.error(f"保持循环异常: {e}", exc_info=True)

        except ImportError:
            logger.error("Playwright 库未安装")
            self.root.after(0, lambda: self._show_error(
                "缺少 Playwright 库！\n\n请运行以下命令安装：\n"
                "pip install playwright\n"
                "playwright install chromium"
            ))
        except Exception as e:
            logger.error(f"浏览器启动失败: {e}", exc_info=True)
            self.root.after(0, lambda: self._show_error(f"启动浏览器失败：\n{str(e)}"))
        finally:
            logger.info("=== 浏览器线程结束, 开始清理 ===")
            try:
                if self.playwright:
                    self.playwright.stop()
                    logger.info("playwright.stop() 完成")
            except Exception as e:
                logger.error(f"playwright.stop() 异常: {e}", exc_info=True)
            self._cleanup_browser()
            logger.info("清理完成")

    def _on_request(self, request):
        """处理请求事件"""
        try:
            req_headers = {}
            try:
                headers = request.headers
                if headers:
                    req_headers = dict(headers)
            except Exception as e:
                logger.debug(f"获取请求头失败: {e}")

            req_body = ""
            try:
                post_data = request.post_data
                if post_data:
                    req_body = post_data
            except Exception as e:
                logger.debug(f"获取请求体失败: {e}")

            # 使用自增序号作为唯一 ID，避免 URL+method 重复导致覆盖
            if not hasattr(self, '_req_counter'):
                self._req_counter = 0
            self._req_counter += 1

            req_data = {
                "_id": self._req_counter,
                "url": request.url,
                "method": request.method,
                "resource_type": request.resource_type,
                "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
                "request_headers": req_headers,
                "request_body": req_body,
                "status_code": None,
                "response_headers": {},
                "response_body": "",
                "response_size": None,
            }

            # 用唯一 ID 存储到 pending，等响应到达时补充
            if not hasattr(self, '_pending_requests'):
                self._pending_requests = {}
            self._pending_requests[id(request)] = req_data

            # 直接添加到捕获列表
            self.capture.add_request(req_data)

        except Exception as e:
            logger.error(f"_on_request 异常: {e}", exc_info=True)

    def _on_response(self, response):
        """处理响应事件 - 更新已有请求的响应信息"""
        try:
            # 通过 request 对象的 id 查找对应的 pending 记录
            req_data = None
            if hasattr(self, '_pending_requests'):
                # 遍历找到匹配的请求（url + method + 时间戳匹配）
                for key, pending in list(self._pending_requests.items()):
                    if (pending.get("url") == response.url and
                            pending.get("method") == response.request.method and
                            pending.get("status_code") is None):
                        req_data = pending
                        self._pending_requests.pop(key, None)
                        break

            if req_data is None:
                # 没有对应的请求记录，创建一个新的
                if not hasattr(self, '_req_counter'):
                    self._req_counter = 0
                self._req_counter += 1
                req_data = {
                    "_id": self._req_counter,
                    "url": response.url,
                    "method": response.request.method,
                    "resource_type": "",
                    "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
                    "request_headers": {},
                    "request_body": "",
                    "status_code": None,
                    "response_headers": {},
                    "response_body": "",
                    "response_size": None,
                }
                self.capture.add_request(req_data)

            # 更新响应信息
            req_data["status_code"] = response.status

            # 获取响应头
            try:
                resp_headers = dict(response.headers)
                req_data["response_headers"] = resp_headers
            except Exception as e:
                logger.debug(f"获取响应头失败: {e}")

            # 获取响应体
            try:
                content_type = ""
                try:
                    content_type = response.headers.get("content-type", "")
                except Exception:
                    pass

                # 只捕获文本类内容，避免二进制文件
                if any(t in content_type.lower() for t in [
                    "json", "text", "html", "xml", "javascript", "css",
                    "form", "urlencoded", "plain"
                ]):
                    body = response.text()
                    if body:
                        req_data["response_body"] = body
                        req_data["response_size"] = len(body.encode("utf-8"))
            except Exception as e:
                logger.debug(f"获取响应体失败 [{response.url}]: {e}")

            # 通知 GUI 刷新该行
            self.capture.update_request(req_data)

        except Exception as e:
            logger.error(f"_on_response 异常: {e}", exc_info=True)

    def _stop_browser(self):
        """停止浏览器"""
        logger.info("用户点击停止抓包")
        self.is_running = False
        self.capture.stop()
        self._stop_polling()
        self.status_label.configure(text="正在停止浏览器...")
        self.stop_btn.configure(state=tk.DISABLED)

        if self.browser_thread and self.browser_thread.is_alive():
            # 等待线程结束
            self.browser_thread.join(timeout=5)

        self._cleanup_browser()
        self.start_btn.configure(state=tk.NORMAL)
        self.status_label.configure(text=f"抓包已停止 - 共捕获 {self.request_count} 条请求")

    def _cleanup_browser(self):
        """清理浏览器资源"""
        try:
            if self.page and not self.page.is_closed():
                self.page.close()
        except Exception:
            pass
        try:
            if self.context:
                self.context.close()
        except Exception:
            pass
        try:
            if self.browser and self.browser.is_connected():
                self.browser.close()
        except Exception:
            pass
        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None

    def _clear_requests(self):
        """清空请求列表"""
        self.capture.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.request_count = 0
        self.count_label.configure(text="共 0 条请求")
        self._set_text(self.general_text, "")
        self._set_text(self.req_headers_text, "")
        self._set_text(self.resp_headers_text, "")
        self._set_text(self.resp_body_text, "")
        self._set_text(self.req_body_text, "")
        self.status_label.configure(text="已清空所有请求")

    def _export_json(self):
        """导出请求为 JSON 文件"""
        requests = self.capture.get_requests()
        if not requests:
            messagebox.showinfo("提示", "没有可导出的请求数据")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"capture_{timestamp}.json"

        filepath = filedialog.asksaveasfilename(
            title="导出 JSON 文件",
            defaultextension=".json",
            initialfile=default_name,
            filetypes=[("JSON 文件", "*.json"), ("所有文件", "*.*")]
        )

        if filepath:
            try:
                self.capture.export_json(filepath)
                messagebox.showinfo("导出成功", f"已导出 {len(requests)} 条请求到：\n{filepath}")
                self.status_label.configure(text=f"已导出到: {filepath}")
            except Exception as e:
                messagebox.showerror("导出失败", f"导出失败：\n{str(e)}")

    def _export_har(self):
        """导出请求为 HAR 文件（可用 Chrome DevTools 打开）"""
        requests = self.capture.get_requests()
        if not requests:
            messagebox.showinfo("提示", "没有可导出的请求数据")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"capture_{timestamp}.har"

        filepath = filedialog.asksaveasfilename(
            title="导出 HAR 文件",
            defaultextension=".har",
            initialfile=default_name,
            filetypes=[("HAR 文件", "*.har"), ("所有文件", "*.*")]
        )

        if filepath:
            try:
                self.capture.export_har(filepath)
                messagebox.showinfo(
                    "导出成功",
                    f"已导出 {len(requests)} 条请求到：\n{filepath}\n\n"
                    f"提示：可以在 Chrome DevTools → Network 面板中\n"
                    f"直接拖入 .har 文件查看完整请求记录"
                )
                self.status_label.configure(text=f"已导出 HAR 到: {filepath}")
            except Exception as e:
                messagebox.showerror("导出失败", f"导出失败：\n{str(e)}")

    def _show_error(self, message):
        """显示错误信息"""
        self.is_running = False
        self.start_btn.configure(state=tk.NORMAL)
        self.stop_btn.configure(state=tk.DISABLED)
        self.status_label.configure(text="错误")
        messagebox.showerror("错误", message)

    def _on_close(self):
        """关闭窗口"""
        logger.info("用户关闭窗口")
        self.is_running = False
        self.capture.stop()
        self._stop_polling()
        self._cleanup_browser()
        self.root.destroy()

    def run(self):
        """运行 GUI"""
        self.root.mainloop()


if __name__ == "__main__":
    app = CaptureGUI()
    app.run()
