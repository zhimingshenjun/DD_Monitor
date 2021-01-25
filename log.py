# -*- coding: utf-8 -*-
"""全局日志
Note: 仅在入口文件中导入一次
"""
import os
import datetime
import logging


log_path = os.path.join('.', r'logs/log-%s.txt' % datetime.datetime.today().strftime('%Y-%m-%d'))
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
    handlers=[
        logging.FileHandler(log_path),
        logging.StreamHandler()
    ]
)
