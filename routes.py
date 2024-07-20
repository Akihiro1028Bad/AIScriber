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
    # Limiterの設定
    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=["1500 per day", "15 per minute"]
    )

    @app.before_request
    def before_request():
        """リクエスト前に実行される関数"""
        # セッションIDが無い場合は新規作成
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())

    @app.route('/', methods=['GET', 'POST'])
    @limiter.limit("1500 per day")
    def upload_file():
        """
        ファイルのアップロードと処理を行うメインのルート関数
        
        Returns:
            str: レンダリングされたHTMLテンプレート（GETリクエスト時）
            または
            json: 処理結果のJSON（POSTリクエスト時）
        """
        global usage_count
        if request.method == 'POST':
            file = request.files.get('file')
            
            # セッション固有のアップロードディレクトリを作成
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], session['session_id'])
            os.makedirs(upload_dir, exist_ok=True)
            
            transcription, minutes_html, error = process_upload(
                file, 
                upload_dir, 
                current_app.config['ALLOWED_EXTENSIONS'], 
                socketio
            )
            
            if error:
                return render_template('index.html', message=error, transcription="", minutes="")
            
            # 利用回数をインクリメント
            usage_count += 1
            
            return json.dumps({
                'transcription': transcription, 
                'minutes_html': minutes_html
            }), 200, {'ContentType':'application/json'}
        
        return render_template('index.html', transcription="", minutes="")

    @app.route('/regenerate_minutes', methods=['POST'])
    @limiter.limit("1500 per day")
    def regenerate_minutes():
        """
        議事録を再生成するルート関数
        
        Returns:
            json: 再生成された議事録のHTML
            または
            json: エラーメッセージ
        """
        global usage_count
        data = request.json
        transcription = data.get('transcription', '')
        
        if not transcription:
            return jsonify({'error': '文字起こしテキストが提供されていません'}), 400

        try:
            # 議事録の生成 (Gemini, OpenAI, Claude の順に試行)
            for generate_func, api_name in [
                (gemini_generate_minutes, "Gemini API"), 
                (openai_generate_minutes, "ChatGPT API"), 
                (generate_minutes, "Claude API")
            ]:
                socketio.emit('status_update', {'status': f'{api_name} を使用して議事録を生成中...'})
                minutes = generate_func(transcription)
                if minutes and minutes != "議事録の生成中にエラーが発生しました。":
                    # 議事録生成成功
                    socketio.emit('api_used', {'api_name': api_name}) # 使用したAPI名を送信
                    break
            else:
                # 全てのツールで失敗
                raise Exception("全ての議事録生成ツールでエラーが発生しました。")
            
            # セッションに議事録を保存
            session['minutes'] = minutes
            
            # Markdownを HTML に変換
            minutes_html = render_template_string("{{ minutes|markdown }}", minutes=minutes)
            
            # 利用回数をインクリメント
            usage_count += 1
            
            return jsonify({'minutes_html': minutes_html}), 200
        except Exception as e:
            print(f"議事録の再生成中にエラーが発生しました: {str(e)}")
            return jsonify({'error': '議事録の再生成中にエラーが発生しました'}), 500

    @app.route('/download/<file_type>')
    def download_file(file_type):
        """
        議事録をダウンロードするルート関数

        Args:
            file_type (str): ダウンロードするファイルのタイプ ('text' または 'markdown')

        Returns:
            flask.send_file: ダウンロード可能なファイルオブジェクト
            または
            tuple: エラーメッセージとHTTPステータスコード
        """
        minutes = session.get('minutes', '')
        if not minutes:
            return "議事録が見つかりません", 404

        # ファイルの準備
        file_info = prepare_download_file(minutes, file_type)
        if file_info is None:
            return "無効なファイルタイプです", 400

        filename, content, mimetype = file_info
        return create_download_file(filename, content, mimetype)

    @app.route('/api/usage-status')
    def get_usage_status():
        """
        現在の利用状況を返すAPI関数

        Returns:
            json: 現在の利用回数と制限状態
        """
        global usage_count, last_reset
        
        # 日付が変わっていたらリセット
        today = datetime.datetime.now().date()
        if today > last_reset:
            usage_count = 0
            last_reset = today
        
        return jsonify({
            'usedToday': usage_count,
            'isLimited': usage_count >= 1500
        })

    @socketio.on('connect')
    def handle_connect():
        """クライアント接続時のハンドラ関数"""
        print('Client connected')

    @app.teardown_appcontext
    def cleanup_session_files(error):
        """
        セッション終了時に一時ファイルとディレクトリを削除する関数
        """
        session_id = g.get('session_id')
        if session_id:
            session_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], session_id)
            if os.path.exists(session_dir):
                for file in os.listdir(session_dir):
                    os.remove(os.path.join(session_dir, file))
                os.rmdir(session_dir)

    @socketio.on('disconnect')
    def handle_disconnect():
        """クライアント切断時のハンドラ関数"""
        print('Client disconnected')
        cleanup_session_files(None)