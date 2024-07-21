# logger.py

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

def setup_logger(name, log_file, level=logging.DEBUG):
    """ロガーをセットアップする関数"""
    formatter = logging.Formatter('%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] - %(message)s')
    
    # ログファイルのディレクトリを作成
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # ファイルハンドラの設定
    file_handler = RotatingFileHandler(log_file, maxBytes=10000000, backupCount=5)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    # コンソールハンドラの設定
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)

    # ロガーの作成と設定
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

# アプリケーション全体で使用するロガーを作成
app_logger = setup_logger('app_logger', 'logs/app.log', logging.DEBUG)