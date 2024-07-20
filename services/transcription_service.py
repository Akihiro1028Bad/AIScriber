# services/transcription_service.py

import os
import speech_recognition as sr
import concurrent.futures
from functools import partial
from services.audio_service import split_audio

def transcribe_segment(segment_info, recognizer, progress_callback, total_segments, processed_segments):
    """
    単一の音声セグメントを文字起こしする関数

    Args:
        segment_info (tuple): (インデックス, セグメントファイルパス)のタプル
        recognizer (speech_recognition.Recognizer): 音声認識器のインスタンス
        progress_callback (function): 進捗状況を更新するためのコールバック関数
        total_segments (int): 全セグメント数
        processed_segments (list): 処理済みセグメントを追跡するリスト

    Returns:
        tuple: (インデックス, 文字起こしされたテキスト)
    """
    index, segment = segment_info
    with sr.AudioFile(segment) as source:
        audio_data = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio_data, language="ja-JP")
        return index, text
    except sr.UnknownValueError:
        return index, ""
    except sr.RequestError as e:
        return index, f"音声認識サービスでエラーが発生しました: {str(e)} "
    finally:
        processed_segments.append(1)
        progress = (len(processed_segments) / total_segments) * 100
        progress_callback(progress)
        os.remove(segment)

def transcribe_audio(audio_file, output_dir, progress_callback):
    """
    音声ファイルをテキストに変換する関数（並行処理版）

    Args:
        audio_file (str): 変換する音声ファイルのパス
        output_dir (str): セグメントファイルを保存するディレクトリのパス
        progress_callback (function): 進捗状況を更新するためのコールバック関数

    Returns:
        str: 文字起こしされたテキスト全体（正しい順序で結合）
    """
    segments = split_audio(audio_file, output_dir)
    total_segments = len(segments)
    processed_segments = []
    
    recognizer = sr.Recognizer()
    
    transcribe_func = partial(transcribe_segment, recognizer=recognizer, 
                              progress_callback=progress_callback, 
                              total_segments=total_segments,
                              processed_segments=processed_segments)
    
    # セグメントにインデックスを付与
    indexed_segments = list(enumerate(segments))
    
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=200) as executor:
        future_to_segment = {executor.submit(transcribe_func, segment_info): segment_info for segment_info in indexed_segments}
        for future in concurrent.futures.as_completed(future_to_segment):
            segment_info = future_to_segment[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as exc:
                print(f'{segment_info} generated an exception: {exc}')
    
    # 結果を正しい順序でソートして結合
    sorted_results = sorted(results, key=lambda x: x[0])
    transcription = " ".join(text for _, text in sorted_results)
    
    return transcription