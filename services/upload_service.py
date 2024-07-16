# services/upload_service.py

import os
from werkzeug.utils import secure_filename
from flask import session, render_template_string
from services.audio_service import convert_to_wav
from services.transcription_service import transcribe_audio
from services.minutes_service import generate_minutes

def process_upload(file, upload_folder, allowed_extensions, socketio):
    """
    アップロードされたファイルを処理し、文字起こしと議事録を生成する関数

    Args:
        file: アップロードされたファイルオブジェクト
        upload_folder (str): アップロードされたファイルを保存するフォルダのパス
        allowed_extensions (set): 許可されるファイル拡張子のセット
        socketio: Socket.IOオブジェクト（進捗状況の更新に使用）

    Returns:
        tuple: (transcription, minutes_html, error_message)
            transcription (str): 文字起こしされたテキスト
            minutes_html (str): 生成された議事録のHTML形式
            error_message (str): エラーが発生した場合のメッセージ、なければNone
    """
    if not file or file.filename == '':
        return None, None, 'ファイルが選択されていません'

    if not allowed_file(file.filename, allowed_extensions):
        return None, None, '許可されていないファイル形式です'

    try:
        # ファイルの保存
        filename = secure_filename(file.filename)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)

        # 音声ファイルの変換
        socketio.emit('status_update', {'status': 'ファイルを変換中...'})
        wav_file = convert_to_wav(filepath)

        # 音声認識
        socketio.emit('status_update', {'status': '音声認識を開始します...'})
        def progress_callback(progress):
            socketio.emit('transcription_progress', {'progress': progress})
        transcription = transcribe_audio(wav_file, progress_callback)

        # 議事録の生成
        socketio.emit('status_update', {'status': '議事録を生成中...'})
        minutes = generate_minutes(transcription)

        # セッションに議事録を保存
        session['minutes'] = minutes
        minutes_html = render_template_string("{{ minutes|markdown }}", minutes=minutes)

        # 一時ファイルの削除
        os.remove(filepath)
        os.remove(wav_file)

        socketio.emit('status_update', {'status': '処理が完了しました'})
        return transcription, minutes_html, None

    except Exception as e:
        error_message = f"ファイル処理中にエラーが発生しました: {str(e)}"
        print(error_message)
        return None, None, error_message

def allowed_file(filename, allowed_extensions):
    """
    アップロードされたファイルが許可された拡張子かどうかをチェックする関数

    Args:
        filename (str): チェックするファイル名
        allowed_extensions (set): 許可されるファイル拡張子のセット

    Returns:
        bool: ファイルが許可された拡張子を持っている場合はTrue、そうでない場合はFalse
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions