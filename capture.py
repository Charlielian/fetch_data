# -*- coding: utf-8 -*-
"""
Playwright 网络抓包工具 - 主程序
功能：启动浏览器，捕获所有网络请求，支持 GUI 界面查看和 JSON 导出
"""

import sys
import os
import json
import threading
import time
from datetime import datetime
from pathlib import Path

# 确保资源路径正确（打包后兼容）
def resource_path(relative_path):
    """获取资源文件的绝对路径（兼容 PyInstaller 打包）"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


class RequestCapture:
    """网络请求捕获器"""

    def __init__(self, on_request_callback=None):
        self.requests = []
        self._lock = threading.Lock()
        self._callback = on_request_callback
        self._running = False

    def start(self):
        self._running = True

    def stop(self):
        self._running = False

    def add_request(self, req_data):
        if not self._running:
            return
        with self._lock:
            self.requests.append(req_data)
        if self._callback:
            self._callback(req_data)

    def get_requests(self):
        with self._lock:
            return list(self.requests)

    def clear(self):
        with self._lock:
            self.requests.clear()

    def export_json(self, filepath):
        with self._lock:
            data = json.dumps(self.requests, ensure_ascii=False, indent=2)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(data)

    def get_filtered_requests(self, keyword=None, method=None, status_code=None):
        """根据条件过滤请求"""
        results = self.get_requests()
        if keyword:
            keyword = keyword.lower()
            results = [r for r in results if keyword in r.get("url", "").lower()]
        if method:
            method = method.upper()
            results = [r for r in results if r.get("method", "").upper() == method]
        if status_code:
            try:
                code = int(status_code)
                results = [r for r in results if r.get("status_code") == code]
            except ValueError:
                pass
        return results
