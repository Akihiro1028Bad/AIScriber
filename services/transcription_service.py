import os
import speech_recognition as sr
from pydub import AudioSegment
import concurrent.futures
from functools import partial
import logging
import psutil
import time

# ロガーの設定
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# ファイルハンドラ
file_handler = logging.FileHandler('transcription_service.log')
file_handler.setLevel(logging.DEBUG)

# コンソールハンドラ
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# フォーマッタ
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# ハンドラをロガーに追加
logger.addHandler(file_handler)
logger.addHandler(console_handler)

def get_memory_usage():
    """現在のメモリ使用量を取得"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024  # MB単位

def transcribe_segment(segment_info, recognizer, progress_callback, total_segments, processed_segments, audio_file):
    """
    単一の音声セグメントを文字起こしする関数

    Args:
        segment_info (tuple): (インデックス, 開始時間, 継続時間)のタプル
        recognizer (speech_recognition.Recognizer): 音声認識器のインスタンス
        progress_callback (function): 進捗状況を更新するためのコールバック関数
        total_segments (int): 全セグメント数
        processed_segments (list): 処理済みセグメントを追跡するリスト
        audio_file (str): 音声ファイルのパス

    Returns:
        tuple: (インデックス, 文字起こしされたテキスト)
    """
    index, start_time, duration = segment_info
    logger.debug(f"開始: セグメント {index} の処理")
    start_process_time = time.time()
    start_memory = get_memory_usage()

    try:
        # AudioSegmentを使用してメモリ上で直接セグメントを処理
        audio = AudioSegment.from_wav(audio_file)[start_time:start_time+duration]
        audio_data = audio.raw_data
        sample_rate = audio.frame_rate
        
        logger.debug(f"Google Speech Recognitionを使用した文字起こし: セグメント {index}")
        text = recognizer.recognize_google(audio_data, sample_rate=sample_rate, language="ja-JP")
        logger.info(f"セグメント {index} の文字起こしが成功しました")
        return index, text
    except sr.UnknownValueError:
        logger.warning(f"セグメント {index} の文字起こしに失敗しました: 音声を認識できませんでした")
        return index, ""
    except sr.RequestError as e:
        logger.error(f"セグメント {index} の文字起こし中にエラーが発生しました: {str(e)}")
        return index, f"音声認識サービスでエラーが発生しました: {str(e)}"
    finally:
        processed_segments.append(1)
        progress = (len(processed_segments) / total_segments) * 100
        progress_callback(progress)
        end_process_time = time.time()
        end_memory = get_memory_usage()
        logger.debug(f"終了: セグメント {index} の処理. 処理時間: {end_process_time - start_process_time:.2f}秒, "
                     f"メモリ使用量変化: {end_memory - start_memory:.2f}MB")

def transcribe_audio(audio_file, progress_callback):
    """
    音声ファイルをテキストに変換する関数（並行処理版）

    Args:
        audio_file (str): 変換する音声ファイルのパス
        progress_callback (function): 進捗状況を更新するためのコールバック関数

    Returns:
        str: 文字起こしされたテキスト全体（正しい順序で結合）
    """
    logger.info(f"音声ファイル {audio_file} の文字起こしを開始します")
    start_time = time.time()
    start_memory = get_memory_usage()

    try:
        audio = AudioSegment.from_wav(audio_file)
        total_duration = len(audio)
        segment_duration = 60000  # 60秒
        total_segments = (total_duration + segment_duration - 1) // segment_duration

        processed_segments = []
        recognizer = sr.Recognizer()

        transcribe_func = partial(transcribe_segment, recognizer=recognizer, 
                                  progress_callback=progress_callback, 
                                  total_segments=total_segments,
                                  processed_segments=processed_segments,
                                  audio_file=audio_file)

        segment_infos = [(i, i*segment_duration, min(segment_duration, total_duration-i*segment_duration)) 
                         for i in range(total_segments)]

        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(os.cpu_count(), total_segments)) as executor:
            future_to_segment = {executor.submit(transcribe_func, segment_info): segment_info for segment_info in segment_infos}
            for future in concurrent.futures.as_completed(future_to_segment):
                segment_info = future_to_segment[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as exc:
                    logger.error(f'セグメント {segment_info} の処理中に例外が発生しました: {exc}', exc_info=True)

        logger.debug("文字起こし結果をソートして結合中")
        sorted_results = sorted(results, key=lambda x: x[0])
        transcription = " ".join(text for _, text in sorted_results)

        end_time = time.time()
        end_memory = get_memory_usage()
        logger.info(f"文字起こしが完了しました. 処理時間: {end_time - start_time:.2f}秒, "
                    f"合計メモリ使用量変化: {end_memory - start_memory:.2f}MB")

        return transcription

    except Exception as e:
        logger.error(f"文字起こし処理中に予期せぬエラーが発生しました: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    # テスト用のコード
    def dummy_progress_callback(progress):
        print(f"進捗: {progress:.2f}%")

    test_audio_file = "path/to/test/audio/file.wav"

    try:
        result = transcribe_audio(test_audio_file, dummy_progress_callback)
        print("文字起こし結果:", result[:500] + "..." if len(result) > 500 else result)
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")