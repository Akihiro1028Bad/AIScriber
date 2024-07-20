# app.py
from gevent import monkey
monkey.patch_all()

import os
from flask_socketio import SocketIO
from config import create_app
from routes import register_routes
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# アプリケーションの作成
app = create_app()

# Redis URLの設定
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')

# Flask-Limiterの設定
limiter = Limiter(
    get_remote_address,
    app=app,
    storage_uri=redis_url
)

# Socket.IOの初期化
socketio = SocketIO(app)

# ルートの登録
register_routes(app, socketio)

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    server = pywsgi.WSGIServer(('0.0.0.0', port), app, handler_class=WebSocketHandler)
    server.serve_forever()