# -*- coding: utf-8 -*-
"""
无 GUI 测试脚本 - 验证 Playwright 事件监听是否能正常捕获请求
"""
import time
from datetime import datetime
from capture import RequestCapture

def test_capture():
    capture = RequestCapture()
    capture.start()

    from playwright.sync_api import sync_playwright

    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=True, args=["--no-sandbox"])
    context = browser.new_context()
    page = context.new_page()

    def on_request(request):
        try:
            capture.add_request({
                "url": request.url,
                "method": request.method,
                "resource_type": request.resource_type,
                "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
                "request_headers": dict(request.headers) if request.headers else {},
                "request_body": request.post_data or "",
                "status_code": None,
                "response_headers": {},
                "response_body": "",
                "response_size": None,
            })
        except Exception as e:
            print(f"  [ERROR] on_request: {e}")

    def on_response(response):
        try:
            all_reqs = capture.get_requests()
            for i in range(len(all_reqs) - 1, -1, -1):
                r = all_reqs[i]
                if (r["url"] == response.url and
                        r["method"] == response.request.method and
                        r["status_code"] is None):
                    r["status_code"] = response.status
                    r["response_headers"] = dict(response.headers) if response.headers else {}
                    break
        except Exception as e:
            print(f"  [ERROR] on_response: {e}")

    page.on("request", on_request)
    page.on("response", on_response)

    print("正在访问 baidu.com ...")
    page.goto("https://www.baidu.com", wait_until="domcontentloaded")
    time.sleep(2)  # 等待所有请求完成

    browser.close()
    pw.stop()
    capture.stop()

    requests = capture.get_requests()
    print(f"\n{'='*60}")
    print(f"  总共捕获: {len(requests)} 条请求")
    print(f"{'='*60}")

    # 统计
    methods = {}
    types = {}
    status_ok = 0
    status_none = 0
    for r in requests:
        m = r.get("method", "?")
        methods[m] = methods.get(m, 0) + 1
        t = r.get("resource_type", "?")
        types[t] = types.get(t, 0) + 1
        if r.get("status_code"):
            status_ok += 1
        else:
            status_none += 1

    print(f"\n  按方法统计:")
    for k, v in sorted(methods.items()):
        print(f"    {k}: {v}")
    print(f"\n  按类型统计:")
    for k, v in sorted(types.items()):
        print(f"    {k}: {v}")
    print(f"\n  有状态码: {status_ok}")
    print(f"  无状态码: {status_none}")

    print(f"\n  前 10 条请求:")
    for i, r in enumerate(requests[:10]):
        s = str(r.get("status_code") or "...")
        print(f"    [{i+1}] {r['method']:6s} {s:>4s} {r['resource_type']:12s} {r['url'][:80]}")

    if len(requests) >= 5:
        print(f"\n  ✅ 测试通过！成功捕获 {len(requests)} 条请求")
    else:
        print(f"\n  ❌ 测试失败！仅捕获 {len(requests)} 条请求，预期至少 5 条")

    return len(requests)

if __name__ == "__main__":
    test_capture()
