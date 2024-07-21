# upload_service.py

import os
import uuid
from werkzeug.utils import secure_filename
from flask import session, render_template_string
from services.audio_service import convert_to_wav
from services.transcription_service import transcribe_audio
from services.minutes_service import generate_minutes
from services.openai_miniutes_service import openai_generate_minutes
from services.gemni_miniutes_service import gemini_generate_minutes
from logger import app_logger

def process_upload(file, upload_folder, allowed_extensions, socketio):
    app_logger.debug(f"Received file: {file.filename}, Size: {file.content_length} bytes, Content-Type: {file.content_type}")
    if not file or file.filename == '':
        return None, None, 'ファイルが選択されていません'

    if not allowed_file(file.filename, allowed_extensions):
        return None, None, '許可されていないファイル形式です'

    try:
        unique_filename = str(uuid.uuid4()) + '_' + secure_filename(file.filename)
        filepath = os.path.join(upload_folder, unique_filename)
        file.save(filepath)
        app_logger.info(f"File saved: {filepath}")

        socketio.emit('status_update', {'status': 'ファイルを変換中...'})
        try:
            wav_file = convert_to_wav(filepath, upload_folder)
            app_logger.info(f"File converted to WAV: {wav_file}")
        except Exception as e:
            app_logger.error(f"Error converting file to WAV: {str(e)}", exc_info=True)
            return None, None, f"音声ファイルの変換中にエラーが発生しました: {str(e)}"

        socketio.emit('status_update', {'status': '音声認識を開始します...'})
        def progress_callback(progress):
            socketio.emit('transcription_progress', {'progress': progress})
        
        try:
            transcription = transcribe_audio(wav_file, progress_callback)
            app_logger.info("Transcription completed")
        except Exception as e:
            app_logger.error(f"Error during transcription: {str(e)}", exc_info=True)
            return None, None, f"音声認識中にエラーが発生しました: {str(e)}"

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
        else:
            raise Exception("全ての議事録生成ツールでエラーが発生しました。")

        session['minutes'] = minutes
        minutes_html = render_template_string("{{ minutes|markdown }}", minutes=minutes)

        # os.remove(filepath)
        # os.remove(wav_file)

        socketio.emit('status_update', {'status': '処理が完了しました'})
        return transcription, minutes_html, None

    except Exception as e:
        error_message = f"ファイル処理中に予期せぬエラーが発生しました: {str(e)}"
        app_logger.error(error_message, exc_info=True)
        return None, None, error_message

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions