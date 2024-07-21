# app.py
from gevent import monkey
monkey.patch_all()

import os
import psutil
from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from config import Config
from routes import register_routes
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from logger import app_logger

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    app_logger.debug(f"ANTHROPIC_API_KEY set: {'ANTHROPIC_API_KEY' in os.environ}")
    app_logger.debug(f"GOOGLE_API_KEY set: {'GOOGLE_API_KEY' in os.environ}")
    app_logger.debug(f"OPENAI_API_KEY set: {'OPENAI_API_KEY' in os.environ}")
    
    upload_dir = app.config['UPLOAD_FOLDER']
    if os.access(upload_dir, os.W_OK):
        app_logger.debug(f"Upload directory is writable: {upload_dir}")
    else:
        app_logger.error(f"Upload directory is not writable: {upload_dir}")
    
    # Limiterの設定 (インメモリストレージを使用)
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://"
    )
    
    # Socket.IOの初期化
    socketio = SocketIO(app)
    
    # ルートの登録
    register_routes(app, socketio)
    
    # メモリ使用量チェック
    def check_memory_usage():
        memory_percent = psutil.virtual_memory().percent
        if memory_percent > 90:  # メモリ使用率が90%を超えた場合
            app_logger.warning(f"High memory usage: {memory_percent}%")
            raise Exception("サーバーのメモリ使用率が高すぎます。後でもう一度お試しください。")

    @app.before_request
    def before_request():
        check_memory_usage()

    # グローバルなエラーハンドラー
    @app.errorhandler(Exception)
    def handle_exception(e):
        app_logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
        return jsonify(error=str(e)), 500

    # Socket.IOイベントハンドラ
    @socketio.on('connect')
    def handle_connect():
        app_logger.info("Client connected")

    @socketio.on('disconnect')
    def handle_disconnect():
        app_logger.info("Client disconnected")

    return app, socketio

app, socketio = create_app()

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app_logger.info(f"Starting server on port {port}")
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    server = pywsgi.WSGIServer(('0.0.0.0', port), app, handler_class=WebSocketHandler)
    try:
        server.serve_forever()
    except Exception as e:
        app_logger.error(f"Server error: {str(e)}", exc_info=True)