# routes.py

import json
from flask import render_template, request, jsonify, session, render_template_string
from services.minutes_service import generate_minutes
from services.file_service import prepare_download_file, create_download_file
from services.upload_service import process_upload

def register_routes(app, socketio):
    """
    アプリケーションにルートを登録する関数

    Args:
        app: Flaskアプリケーションインスタンス
        socketio: Flask-SocketIOインスタンス
    """

    @app.route('/', methods=['GET', 'POST'])
    def upload_file():
        """
        ファイルのアップロードと処理を行うメインのルート関数
        
        Returns:
            str: レンダリングされたHTMLテンプレート（GETリクエスト時）
            または
            json: 処理結果のJSON（POSTリクエスト時）
        """
        if request.method == 'POST':
            file = request.files.get('file')
            transcription, minutes_html, error = process_upload(
                file, 
                app.config['UPLOAD_FOLDER'], 
                app.config['ALLOWED_EXTENSIONS'], 
                socketio
            )
            
            if error:
                return render_template('index.html', message=error, transcription="", minutes="")
            
            return json.dumps({
                'transcription': transcription, 
                'minutes_html': minutes_html
            }), 200, {'ContentType':'application/json'}
        
        return render_template('index.html', transcription="", minutes="")

    @app.route('/regenerate_minutes', methods=['POST'])
    def regenerate_minutes():
        """
        議事録を再生成するルート関数
        
        Returns:
            json: 再生成された議事録のHTML
            または
            json: エラーメッセージ
        """
        data = request.json
        transcription = data.get('transcription', '')
        
        if not transcription:
            return jsonify({'error': '文字起こしテキストが提供されていません'}), 400

        try:
            # 議事録の再生成
            minutes = generate_minutes(transcription)
            
            # Markdownを HTML に変換
            minutes_html = render_template_string("{{ minutes|markdown }}", minutes=minutes)
            
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

    @socketio.on('connect')
    def handle_connect():
        """クライアント接続時のハンドラ関数"""
        print('Client connected')