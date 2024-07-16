# services/audio_service.py

from pydub import AudioSegment
import os  # osモジュールをインポート

def convert_to_wav(input_file):
    """
    入力されたオーディオファイルをWAV形式に変換する関数
    
    Args:
        input_file (str): 入力ファイルのパス
    
    Returns:
        str: 変換後のWAVファイルのパス
    """
    name, ext = os.path.splitext(input_file)
    output_file = f"{name}.wav"
    
    # MP4ファイルの場合は特別な処理が必要
    if ext.lower() == '.mp4':
        audio = AudioSegment.from_file(input_file, format="mp4")
    else:
        # その他の形式の場合は自動で形式を判断
        audio = AudioSegment.from_file(input_file)
    
    # WAV形式でエクスポート
    audio.export(output_file, format="wav")
    
    return output_file

def split_audio(audio_file, segment_length=60000):
    """
    音声ファイルを指定された長さ（ミリ秒）のセグメントに分割する関数
    
    Args:
        audio_file (str): 分割する音声ファイルのパス
        segment_length (int): 分割するセグメントの長さ（ミリ秒）
    
    Returns:
        list: 分割されたセグメントファイルのパスのリスト
    """
    audio = AudioSegment.from_wav(audio_file)
    segments = []
    
    # 音声ファイルを指定された長さで分割
    for i in range(0, len(audio), segment_length):
        segment = audio[i:i+segment_length]
        segment_file = f"segment_{i//segment_length}.wav"
        segment.export(segment_file, format="wav")
        segments.append(segment_file)
    
    return segments