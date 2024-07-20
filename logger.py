import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(name, log_file, level=logging.INFO):
    """ロガーをセットアップする関数"""
    formatter = logging.Formatter('%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] - %(message)s')
    
    # ログファイルのディレクトリを作成
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    handler = RotatingFileHandler(log_file, maxBytes=10000000, backupCount=5)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    # コンソールにも出力
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

# アプリケーション全体で使用するロガーを作成
app_logger = setup_logger('app_logger', 'logs/app.log')