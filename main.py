# -*- coding: utf-8 -*-
"""
Playwright 网络抓包工具 - 入口文件
"""

import sys
import os

# 将当前目录加入路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui import CaptureGUI

if __name__ == "__main__":
    app = CaptureGUI()
    app.run()
