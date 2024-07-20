# config.py

import os
from flask import Flask
from anthropic import Anthropic
from dotenv import load_dotenv
from flaskext.markdown import Markdown
from logger import app_logger

# .envファイルの内容を読み込む
load_dotenv()
app_logger.info(".env file loaded")

class Config:
    """アプリケーションの設定を管理するクラス"""
    
    # セッション用のシークレットキー
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your_secret_key')
    
    # アップロードされたファイルを保存するフォルダ
    UPLOAD_FOLDER = 'uploads'
    
    # アップロードを許可するファイルの拡張子
    ALLOWED_EXTENSIONS = {'mp4', 'wav', 'mp3'}
    
    # Anthropic APIキー
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
    
    # Google API Key
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

    app_logger.info("Config class initialized")

def create_app(config_class=Config):
    """
    Flaskアプリケーションを作成し、設定を行う関数
    
    Args:
        config_class: 設定クラス（デフォルトはConfig）
    
    Returns:
        Flask: 設定済みのFlaskアプリケーションインスタンス
    """
    app = Flask(__name__)
    app_logger.info("Flask app created")
    
    # 設定の適用
    app.config.from_object(config_class)
    app_logger.info("Config applied to app")
    
    # Markdownの設定
    Markdown(app)
    app_logger.info("Markdown configured")
    
    # Anthropic APIクライアントの初期化
    app.anthropic = Anthropic(api_key=app.config['ANTHROPIC_API_KEY'])
    app_logger.info("Anthropic API client initialized")
    
    # アップロードフォルダの作成
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app_logger.info(f"Upload folder created: {app.config['UPLOAD_FOLDER']}")
    
    return app