# services/audio_service.py

import os
import subprocess
import psutil
from logger import app_logger

def get_memory_usage():
    """現在のプロセスのメモリ使用量をMB単位で取得する"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def convert_to_wav(input_file, output_dir, chunk_size=1024*1024):  # デフォルトチャンクサイズを1MBに設定
    """
    入力されたオーディオファイルをWAV形式に変換する関数
    
    Args:
        input_file (str): 入力ファイルのパス
        output_dir (str): 出力ディレクトリのパス
        chunk_size (int): 一度に処理するチャンクのサイズ（バイト）
    
    Returns:
        str: 変換後のWAVファイルのパス
    """
    app_logger.info(f"Converting audio file to WAV: {input_file}")
    start_memory = get_memory_usage()
    
    name, ext = os.path.splitext(os.path.basename(input_file))
    output_file = os.path.join(output_dir, f"{name}.wav")
    
    try:
        # ffmpegコマンドを構築
        command = [
            'ffmpeg',
            '-i', 'pipe:0',  # 入力をパイプから読み取る
            '-acodec', 'pcm_s16le',  # 16ビットPCMにエンコード
            '-ac', '2',  # ステレオ
            '-ar', '44100',  # サンプリングレート44.1kHz
            '-f', 'wav',  # WAV形式で出力
            'pipe:1'  # 出力をパイプに書き込む
        ]
        
        with open(input_file, 'rb') as infile, open(output_file, 'wb') as outfile:
            # subprocessを使用してffmpegを実行
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # 入力ファイルをチャンクで読み込み、ffmpegに送信
            while True:
                chunk = infile.read(chunk_size)
                if not chunk:
                    break
                process.stdin.write(chunk)
            process.stdin.close()
            
            # ffmpegからの出力を読み取り、出力ファイルに書き込む
            for chunk in iter(lambda: process.stdout.read(chunk_size), b''):
                outfile.write(chunk)
            
            # エラー出力を確認
            stderr = process.stderr.read()
            if stderr:
                app_logger.warning(f"ffmpeg警告/エラー: {stderr.decode()}")
        
        end_memory = get_memory_usage()
        app_logger.info(f"Audio file converted successfully: {output_file}")
        app_logger.info(f"Memory usage: Before: {start_memory:.2f}MB, After: {end_memory:.2f}MB, Difference: {end_memory - start_memory:.2f}MB")
    
    except Exception as e:
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
    start_memory = get_memory_usage()
    
    segments = []
    try:
        # ffprobeを使用して音声ファイルの長さを取得
        probe_command = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', audio_file]
        duration = float(subprocess.check_output(probe_command).decode().strip())
        
        # セグメントに分割
        for i in range(0, int(duration), segment_length):
            segment_file = os.path.join(output_dir, f"segment_{i // segment_length}.wav")
            command = [
                'ffmpeg',
                '-i', audio_file,
                '-ss', str(i),
                '-t', str(segment_length),
                '-acodec', 'pcm_s16le',
                '-ac', '2',
                '-ar', '44100',
                segment_file
            ]
            subprocess.run(command, check=True, capture_output=True)
            segments.append(segment_file)
            app_logger.debug(f"Created segment: {segment_file}")
        
        end_memory = get_memory_usage()
        app_logger.info(f"Audio file split into {len(segments)} segments")
        app_logger.info(f"Memory usage: Before: {start_memory:.2f}MB, After: {end_memory:.2f}MB, Difference: {end_memory - start_memory:.2f}MB")
    
    except subprocess.CalledProcessError as e:
        app_logger.error(f"Error splitting audio file: {e.stderr.decode()}", exc_info=True)
        raise
    except Exception as e:
        app_logger.error(f"Unexpected error splitting audio file: {str(e)}", exc_info=True)
        raise
    
    return segments

# テスト用のコード（必要に応じてコメントアウトまたは削除）
if __name__ == "__main__":
    test_audio_file = "path/to/test/audio/file.mp3"
    test_output_dir = "path/to/test/output/directory"
    
    try:
        wav_file = convert_to_wav(test_audio_file, test_output_dir)
        print(f"Converted file: {wav_file}")
        
        segments = split_audio(wav_file, test_output_dir)
        print(f"Created segments: {segments}")
    except Exception as e:
        print(f"Error during test: {str(e)}")