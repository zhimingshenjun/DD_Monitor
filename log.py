# -*- coding: utf-8 -*-
"""全局日志
Note: 仅在入口文件中导入一次
"""
import os
import datetime
import logging
import sys


def get_submod_log(submod_name):
    return logging.getLogger('Main' + '.' + submod_name)


class LoggerStream(object):
    """假 stream，将 stdout/stderr 流重定向到日志，避免win上无头模式运行时报错。
    ref: https://docs.python.org/3/library/sys.html#sys.__stdout__
    """
    def __init__(self, name, level, fileno):
        """
        :param logger: 日志实例
        :param level: 日志等级
        """
        self.logger = get_submod_log(name)
        self.level = level
        self.fileno = fileno

    def fileno(self):
        return self.fileno

    def write(self, lines):
        for line in lines.splitlines():
            self.logger.log(self.level, line)

    def flush(self):
        for handler in self.logger.handlers:
            handler.flush()


log_path = os.path.join('.', r'logs/log-%s.txt' % datetime.datetime.today().strftime('%Y-%m-%d'))
if sys.stderr:
    get_submod_log('log').addHandler(logging.StreamHandler())
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler()
        ]
    )
else:
    logging.basicConfig(
       level=logging.INFO,
       format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
       filename=log_path,
       filemode='a'
    )


sys.stdout = LoggerStream('STDOUT', logging.INFO, 1)
sys.stderr = LoggerStream('STDERR', logging.ERROR, 2)
