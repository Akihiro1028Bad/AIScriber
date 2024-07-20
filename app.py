# app.py
import os
from flask_socketio import SocketIO
from config import create_app
from routes import register_routes

# アプリケーションの作成
app = create_app()

# Socket.IOの初期化
socketio = SocketIO(app)

# ルートの登録
register_routes(app, socketio)

if __name__ == '__main__':
    # アプリケーションの実行
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)