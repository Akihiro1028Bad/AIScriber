# routes.py

import json
import uuid
import os
import datetime
from flask import render_template, request, jsonify, session, render_template_string, current_app, g
from services.minutes_service import generate_minutes
from services.gemni_miniutes_service import gemini_generate_minutes
from services.openai_miniutes_service import openai_generate_minutes
from services.file_service import prepare_download_file, create_download_file
from services.upload_service import process_upload
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from logger import app_logger

# グローバル変数で利用回数を追跡
usage_count = 0
last_reset = datetime.datetime.now().date()

def register_routes(app, socketio):
    """
    アプリケーションにルートを登録する関数

    Args:
        app: Flaskアプリケーションインスタンス
        socketio: Flask-SocketIOインスタンス
    """
    app_logger.info("Registering routes")

    # Limiterの設定
    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=["1500 per day", "15 per minute"]
    )
    app_logger.info("Limiter configured")

    @app.before_request
    def before_request():
        """リクエスト前に実行される関数"""
        # セッションIDが無い場合は新規作成
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
            app_logger.info(f"New session created: {session['session_id']}")

    @app.route('/', methods=['GET', 'POST'])
    @limiter.limit("1500 per day")
    def upload_file():
        global usage_count
        app_logger.info(f"Request to upload_file. Method: {request.method}")
        if request.method == 'POST':
            app_logger.info("Processing POST request for file upload")
            file = request.files.get('file')
            
            # セッション固有のアップロードディレクトリを作成
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], session['session_id'])
            os.makedirs(upload_dir, exist_ok=True)
            app_logger.info(f"Upload directory created: {upload_dir}")
            
            transcription, minutes_html, error = process_upload(
                file, 
                upload_dir, 
                current_app.config['ALLOWED_EXTENSIONS'], 
                socketio
            )
            
            if error:
                app_logger.error(f"Error in file processing: {error}")
                return render_template('index.html', message=error, transcription="", minutes="")
            
            # 利用回数をインクリメント
            usage_count += 1
            app_logger.info(f"Usage count incremented. Current count: {usage_count}")
            
            return json.dumps({
                'transcription': transcription, 
                'minutes_html': minutes_html
            }), 200, {'ContentType':'application/json'}
        
        app_logger.info("Rendering index.html for GET request")
        return render_template('index.html', transcription="", minutes="")

    @app.route('/regenerate_minutes', methods=['POST'])
    @limiter.limit("1500 per day")
    def regenerate_minutes():
        global usage_count
        app_logger.info("Request to regenerate minutes")
        data = request.json
        transcription = data.get('transcription', '')
        
        if not transcription:
            app_logger.warning("No transcription provided for regenerating minutes")
            return jsonify({'error': '文字起こしテキストが提供されていません'}), 400

        try:
            # 議事録の生成 (Gemini, OpenAI, Claude の順に試行)
            for generate_func, api_name in [
                (gemini_generate_minutes, "Gemini API"), 
                (openai_generate_minutes, "ChatGPT API"), 
                (generate_minutes, "Claude API")
            ]:
                app_logger.info(f"Attempting to generate minutes using {api_name}")
                socketio.emit('status_update', {'status': f'{api_name} を使用して議事録を生成中...'})
                minutes = generate_func(transcription)
                if minutes and minutes != "議事録の生成中にエラーが発生しました。":
                    # 議事録生成成功
                    app_logger.info(f"Minutes successfully generated using {api_name}")
                    socketio.emit('api_used', {'api_name': api_name}) # 使用したAPI名を送信
                    break
            else:
                # 全てのツールで失敗
                raise Exception("全ての議事録生成ツールでエラーが発生しました。")
            
            # セッションに議事録を保存
            session['minutes'] = minutes
            app_logger.info("Minutes saved to session")
            
            # Markdownを HTML に変換
            minutes_html = render_template_string("{{ minutes|markdown }}", minutes=minutes)
            
            # 利用回数をインクリメント
            usage_count += 1
            app_logger.info(f"Usage count incremented. Current count: {usage_count}")
            
            return jsonify({'minutes_html': minutes_html}), 200
        except Exception as e:
            app_logger.error(f"Error in regenerating minutes: {str(e)}", exc_info=True)
            return jsonify({'error': '議事録の再生成中にエラーが発生しました'}), 500

    @app.route('/download/<file_type>')
    def download_file(file_type):
        app_logger.info(f"Request to download file. Type: {file_type}")
        minutes = session.get('minutes', '')
        if not minutes:
            app_logger.warning("No minutes found in session for download")
            return "議事録が見つかりません", 404

        # ファイルの準備
        file_info = prepare_download_file(minutes, file_type)
        if file_info is None:
            app_logger.warning(f"Invalid file type for download: {file_type}")
            return "無効なファイルタイプです", 400

        filename, content, mimetype = file_info
        app_logger.info(f"File prepared for download: {filename}")
        return create_download_file(filename, content, mimetype)

    @app.route('/api/usage-status')
    def get_usage_status():
        global usage_count, last_reset
        app_logger.info("Request for usage status")
        
        # 日付が変わっていたらリセット
        today = datetime.datetime.now().date()
        if today > last_reset:
            usage_count = 0
            last_reset = today
            app_logger.info("Usage count reset due to new day")
        
        return jsonify({
            'usedToday': usage_count,
            'isLimited': usage_count >= 1500
        })

    @socketio.on('connect')
    def handle_connect():
        app_logger.info("Client connected")

    @app.teardown_appcontext
    def cleanup_session_files(error):
        session_id = g.get('session_id')
        if session_id:
            session_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], session_id)
            if os.path.exists(session_dir):
                for file in os.listdir(session_dir):
                    os.remove(os.path.join(session_dir, file))
                os.rmdir(session_dir)
                app_logger.info(f"Cleaned up session directory: {session_dir}")

    @socketio.on('disconnect')
    def handle_disconnect():
        app_logger.info("Client disconnected")
        cleanup_session_files(None)

    app_logger.info("All routes registered successfully")