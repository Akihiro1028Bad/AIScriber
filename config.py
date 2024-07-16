# config.py

import os
from flask import Flask
from anthropic import Anthropic
from dotenv import load_dotenv
from flaskext.markdown import Markdown

# .envファイルの内容を読み込む
load_dotenv()

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

def create_app(config_class=Config):
    """
    Flaskアプリケーションを作成し、設定を行う関数
    
    Args:
        config_class: 設定クラス（デフォルトはConfig）
    
    Returns:
        Flask: 設定済みのFlaskアプリケーションインスタンス
    """
    app = Flask(__name__)
    
    # 設定の適用
    app.config.from_object(config_class)
    
    # Markdownの設定
    Markdown(app)
    
    # Anthropic APIクライアントの初期化
    app.anthropic = Anthropic(api_key=app.config['ANTHROPIC_API_KEY'])
    
    # アップロードフォルダの作成
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    return app