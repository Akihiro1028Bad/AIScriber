# Procfile
web: ./install_ffmpeg.sh && gunicorn --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker -w 1 app:app
