# ベースイメージの指定
FROM python:3.10

# 作業ディレクトリの設定
WORKDIR /app

# 必要なパッケージのインストール
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Pythonの依存関係をインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションのソースコードをコピー
COPY . .

# アップロードディレクトリの作成と権限設定
RUN mkdir -p /app/uploads && chmod 777 /app/uploads

# 環境変数の設定
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# ポートの公開
EXPOSE 8080

# アプリケーションの実行
CMD ["gunicorn", "--worker-class", "geventwebsocket.gunicorn.workers.GeventWebSocketWorker", "--bind", "0.0.0.0:8080", "app:app"]