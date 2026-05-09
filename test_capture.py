# -*- coding: utf-8 -*-
"""
无 GUI 抓包脚本 - 打开浏览器，用户操作后抓取所有请求
"""
import time
from datetime import datetime
from capture import RequestCapture

def interactive_capture():
    capture = RequestCapture()
    capture.start()

    from playwright.sync_api import sync_playwright

    pw = sync_playwright().start()
    browser = pw.chromium.launch(
        headless=False,  # 显示浏览器窗口
        args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
    )
    context = browser.new_context(
        viewport={"width": 1280, "height": 800},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
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

    # 关键：监听 context 级别，捕获所有页面的请求
    context.on("request", on_request)
    context.on("response", on_response)

    print("=" * 60)
    print("  浏览器已启动，您可以自由操作网页")
    print("  关闭浏览器窗口或按 Ctrl+C 结束抓包")
    print("=" * 60)

    # 打开初始页面
    page.goto("https://www.baidu.com", wait_until="domcontentloaded")

    # 保持运行，直到用户关闭浏览器
    try:
        while browser.is_connected():
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n用户中断")

    browser.close()
    pw.stop()
    capture.stop()

    requests = capture.get_requests()
    print(f"\n{'='*60}")
    print(f"  总共捕获: {len(requests)} 条请求")
    print(f"{'='*60}")

    # 导出为 JSON
    import json
    output_file = f"capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(requests, f, ensure_ascii=False, indent=2)
    print(f"\n  已导出到: {output_file}")

    # 统计
    methods = {}
    for r in requests:
        m = r.get("method", "?")
        methods[m] = methods.get(m, 0) + 1

    print(f"\n  按方法统计:")
    for k, v in sorted(methods.items()):
        print(f"    {k}: {v}")

    return len(requests)

if __name__ == "__main__":
    interactive_capture()
