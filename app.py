# app.py
from gevent import monkey
monkey.patch_all()

import os
from flask_socketio import SocketIO
from config import create_app
from routes import register_routes
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from logger import app_logger

app_logger.info("Starting application")

# アプリケーションの作成
app = create_app()

# Redis URLの設定
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
app_logger.info(f"Redis URL: {redis_url}")

# Flask-Limiterの設定
limiter = Limiter(
    get_remote_address,
    app=app,
    storage_uri=redis_url
)
app_logger.info("Flask-Limiter configured")

# Socket.IOの初期化
socketio = SocketIO(app)
app_logger.info("SocketIO initialized")

# ルートの登録
register_routes(app, socketio)
app_logger.info("Routes registered")

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