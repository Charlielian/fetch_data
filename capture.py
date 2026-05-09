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

    def __init__(self):
        self.requests = []
        self._lock = threading.Lock()
        self._running = False
        self._last_count = 0  # 上次读取时的数量，用于检测新增

    def start(self):
        self._running = True
        self._last_count = 0  # 重置计数器

    def stop(self):
        self._running = False

    def add_request(self, req_data):
        """添加新请求到列表"""
        if not self._running:
            return
        with self._lock:
            self.requests.append(req_data)

    def update_request(self, req_data):
        """更新已有请求（根据 _id 匹配）"""
        with self._lock:
            for i, r in enumerate(self.requests):
                if r.get("_id") == req_data.get("_id"):
                    self.requests[i] = req_data
                    break

    def get_requests(self):
        with self._lock:
            return list(self.requests)

    def get_new_requests(self):
        """获取自上次调用以来的新增请求"""
        with self._lock:
            new_items = self.requests[self._last_count:]
            self._last_count = len(self.requests)
            return list(new_items)

    def clear(self):
        with self._lock:
            self.requests.clear()
            self._last_count = 0  # 重置计数器

    def export_json(self, filepath):
        with self._lock:
            data = json.dumps(self.requests, ensure_ascii=False, indent=2)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(data)

    def export_har(self, filepath):
        """导出为 HAR (HTTP Archive) 格式，可用 Chrome DevTools 直接打开"""
        with self._lock:
            requests = list(self.requests)

        entries = []
        for req in requests:
            # 解析时间戳
            started = req.get("timestamp", "00:00:00.000")
            try:
                h, m, s_ms = started.split(":")
                s, ms = s_ms.split(".")
                started_ms = (int(h) * 3600 + int(m) * 60 + int(s)) * 1000 + int(ms)
            except Exception:
                started_ms = 0

            # 请求头
            req_headers = []
            for k, v in req.get("request_headers", {}).items():
                req_headers.append({"name": k, "value": v})

            # 响应头
            resp_headers = []
            for k, v in req.get("response_headers", {}).items():
                resp_headers.append({"name": k, "value": v})

            # 响应体
            resp_body = req.get("response_body", "")
            resp_size = req.get("response_size") or (len(resp_body.encode("utf-8")) if resp_body else 0)

            # 请求体
            req_body = req.get("request_body", "")
            req_post_data = None
            if req_body:
                req_post_data = {"mimeType": "application/x-www-form-urlencoded", "text": req_body}

            # content-type
            content_type = ""
            for h in resp_headers:
                if h["name"].lower() == "content-type":
                    content_type = h["value"]
                    break

            entry = {
                "startedDateTime": datetime.now().isoformat(timespec="milliseconds"),
                "time": 0,
                "request": {
                    "method": req.get("method", "GET"),
                    "url": req.get("url", ""),
                    "httpVersion": "HTTP/1.1",
                    "headers": req_headers,
                    "queryString": [],
                    "cookies": [],
                    "headersSize": -1,
                    "bodySize": len(req_body.encode("utf-8")) if req_body else 0,
                },
                "response": {
                    "status": req.get("status_code") or 0,
                    "statusText": "",
                    "httpVersion": "HTTP/1.1",
                    "headers": resp_headers,
                    "cookies": [],
                    "content": {
                        "size": resp_size,
                        "mimeType": content_type,
                        "text": resp_body if resp_body else None,
                    },
                    "redirectURL": "",
                    "headersSize": -1,
                    "bodySize": resp_size,
                },
                "cache": {},
                "timings": {
                    "send": 0,
                    "wait": 0,
                    "receive": 0,
                },
            }

            if req_post_data:
                entry["request"]["postData"] = req_post_data

            entries.append(entry)

        har_data = {
            "log": {
                "version": "1.2",
                "creator": {"name": "PlaywrightCapture", "version": "1.0.0"},
                "entries": entries,
            }
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(har_data, f, ensure_ascii=False, indent=2)

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
