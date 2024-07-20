# services/audio_service.py

from pydub import AudioSegment
import os

def convert_to_wav(input_file, output_dir):
    """
    入力されたオーディオファイルをWAV形式に変換する関数
    
    Args:
        input_file (str): 入力ファイルのパス
        output_dir (str): 出力ディレクトリのパス
    
    Returns:
        str: 変換後のWAVファイルのパス
    """
    name, ext = os.path.splitext(os.path.basename(input_file))
    output_file = os.path.join(output_dir, f"{name}.wav")
    
    # MP4ファイルの場合は特別な処理が必要
    if ext.lower() == '.mp4':
        audio = AudioSegment.from_file(input_file, format="mp4")
    else:
        # その他の形式の場合は自動で形式を判断
        audio = AudioSegment.from_file(input_file)
    
    # WAV形式でエクスポート
    audio.export(output_file, format="wav")
    
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
    audio = AudioSegment.from_wav(audio_file)
    segments = []
    
    # 音声ファイルを指定された長さで分割
    for i in range(0, len(audio), segment_length):
        segment = audio[i:i+segment_length]
        segment_file = os.path.join(output_dir, f"segment_{i//segment_length}.wav")
        segment.export(segment_file, format="wav")
        segments.append(segment_file)
    
    return segments