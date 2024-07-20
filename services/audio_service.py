# services/audio_service.py

from pydub import AudioSegment
import os
from logger import app_logger

def convert_to_wav(input_file, output_dir):
    """
    入力されたオーディオファイルをWAV形式に変換する関数
    
    Args:
        input_file (str): 入力ファイルのパス
        output_dir (str): 出力ディレクトリのパス
    
    Returns:
        str: 変換後のWAVファイルのパス
    """
    app_logger.info(f"Converting audio file to WAV: {input_file}")
    name, ext = os.path.splitext(os.path.basename(input_file))
    output_file = os.path.join(output_dir, f"{name}.wav")
    
    try:
        # MP4ファイルの場合は特別な処理が必要
        if ext.lower() == '.mp4':
            app_logger.debug("Processing MP4 file")
            audio = AudioSegment.from_file(input_file, format="mp4")
        else:
            # その他の形式の場合は自動で形式を判断
            app_logger.debug(f"Processing audio file with extension: {ext}")
            audio = AudioSegment.from_file(input_file)
        
        # WAV形式でエクスポート
        audio.export(output_file, format="wav")
        app_logger.info(f"Audio file converted successfully: {output_file}")
    except Exception as e:
        app_logger.error(f"Error converting audio file: {str(e)}", exc_info=True)
        raise
    
    return output_file

def split_audio(audio_file, output_dir, segment_length=60000):
    """
    音声ファイルを指定された長さ（ミリ秒）のセグメントに分割する関数
    
    Args:
        audio_file (str): 分割する音声ファイルのパス
        output_dir (str): 出力ディレクトリのパス
        segment_length (int): 分割するセグメントの長さ（ミリ秒）
    
    Returns:
        list: 分割されたセグメントファイルのパスのリスト
    """
    app_logger.info(f"Splitting audio file: {audio_file}")
    try:
        audio = AudioSegment.from_wav(audio_file)
        segments = []
        
        # 音声ファイルを指定された長さで分割
        for i in range(0, len(audio), segment_length):
            segment = audio[i:i+segment_length]
            segment_file = os.path.join(output_dir, f"segment_{i//segment_length}.wav")
            segment.export(segment_file, format="wav")
            segments.append(segment_file)
            app_logger.debug(f"Created segment: {segment_file}")
        
        app_logger.info(f"Audio file split into {len(segments)} segments")
    except Exception as e:
        app_logger.error(f"Error splitting audio file: {str(e)}", exc_info=True)
        raise
    
    return segments