# services/audio_service.py

import os
import subprocess
import ffmpeg
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
        # ffmpeg-pythonを使用してファイルを変換
        stream = ffmpeg.input(input_file)
        stream = ffmpeg.output(stream, output_file, acodec='pcm_s16le', ac=2, ar='44100')
        ffmpeg.run(stream, overwrite_output=True)
        
        app_logger.info(f"Audio file converted successfully: {output_file}")
    except ffmpeg.Error as e:
        app_logger.error(f"Error converting audio file: {str(e)}", exc_info=True)
        raise
    
    return output_file

def split_audio(audio_file, output_dir, segment_length=60):
    """
    音声ファイルを指定された長さ（秒）のセグメントに分割する関数
    
    Args:
        audio_file (str): 分割する音声ファイルのパス
        output_dir (str): 出力ディレクトリのパス
        segment_length (int): 分割するセグメントの長さ（秒）
    
    Returns:
        list: 分割されたセグメントファイルのパスのリスト
    """
    app_logger.info(f"Splitting audio file: {audio_file}")
    segments = []
    
    try:
        # ffprobeを使用して音声ファイルの長さを取得
        probe = ffmpeg.probe(audio_file)
        duration = float(probe['streams'][0]['duration'])
        
        # セグメントに分割
        for i in range(0, int(duration), segment_length):
            segment_file = os.path.join(output_dir, f"segment_{i // segment_length}.wav")
            stream = ffmpeg.input(audio_file, ss=i, t=segment_length)
            stream = ffmpeg.output(stream, segment_file, acodec='pcm_s16le', ac=2, ar='44100')
            ffmpeg.run(stream, overwrite_output=True, quiet=True)
            segments.append(segment_file)
            app_logger.debug(f"Created segment: {segment_file}")
        
        app_logger.info(f"Audio file split into {len(segments)} segments")
    except ffmpeg.Error as e:
        app_logger.error(f"Error splitting audio file: {str(e)}", exc_info=True)
        raise
    
    return segments