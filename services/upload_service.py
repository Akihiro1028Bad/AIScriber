import os
import uuid
from werkzeug.utils import secure_filename
from flask import session, render_template_string
from services.transcription_service import transcribe_audio
from services.minutes_service import generate_minutes
from services.openai_miniutes_service import openai_generate_minutes
from services.gemni_miniutes_service import gemini_generate_minutes
import logging

logger = logging.getLogger(__name__)

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
        # ユニークなファイル名を生成
        unique_filename = str(uuid.uuid4()) + '_' + secure_filename(file.filename)
        filepath = os.path.join(upload_folder, unique_filename)
        file.save(filepath)

        socketio.emit('status_update', {'status': '音声認識を開始します...'})
        
        def progress_callback(progress):
            socketio.emit('transcription_progress', {'progress': progress})
        
        transcription = transcribe_audio(filepath, progress_callback)

        # 議事録の生成 (Gemini, OpenAI, Claude の順に試行)
        minutes = None
        for generate_func, api_name in [
            (gemini_generate_minutes, "Gemini API"), 
            (openai_generate_minutes, "ChatGPT API"), 
            (generate_minutes, "Claude API")
        ]:
            socketio.emit('status_update', {'status': f'{api_name} を使用して議事録を生成中...'})
            minutes = generate_func(transcription)
            if minutes and minutes != "議事録の生成中にエラーが発生しました。":
                socketio.emit('api_used', {'api_name': api_name})
                break
        
        if not minutes:
            raise Exception("全ての議事録生成ツールでエラーが発生しました。")

        # メモリを節約するため、大きな変数を早めに解放
        del transcription

        # セッションに議事録を保存
        session['minutes'] = minutes
        minutes_html = render_template_string("{{ minutes|markdown }}", minutes=minutes)

        # 一時ファイルの削除
        os.remove(filepath)

        socketio.emit('status_update', {'status': '処理が完了しました'})
        return None, minutes_html, None

    except Exception as e:
        logger.error(f"ファイル処理中にエラーが発生しました: {str(e)}", exc_info=True)
        return None, None, f"ファイル処理中にエラーが発生しました: {str(e)}"

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