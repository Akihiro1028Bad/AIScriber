# services/transcription_service.py

import os
import speech_recognition as sr
import concurrent.futures
from functools import partial
from services.audio_service import split_audio

def transcribe_segment(segment, recognizer, progress_callback, total_segments, processed_segments):
    """
    単一の音声セグメントを文字起こしする関数

    Args:
        segment (str): 音声セグメントファイルのパス
        recognizer (speech_recognition.Recognizer): 音声認識器のインスタンス
        progress_callback (function): 進捗状況を更新するためのコールバック関数
        total_segments (int): 全セグメント数
        processed_segments (list): 処理済みセグメントを追跡するリスト

    Returns:
        str: 文字起こしされたテキスト
    """
    with sr.AudioFile(segment) as source:
        audio_data = recognizer.record(source)
    try:
        # Google Speech RecognitionのAPIを使用して文字起こしを行う
        text = recognizer.recognize_google(audio_data, language="ja-JP")
        return text
    except sr.UnknownValueError:
        return "音声を認識できませんでした "
    except sr.RequestError as e:
        return f"音声認識サービスでエラーが発生しました: {str(e)} "
    finally:
        # 進捗状況の更新
        processed_segments.append(1)
        progress = (len(processed_segments) / total_segments) * 100
        progress_callback(progress)
        # 一時ファイルの削除
        os.remove(segment)

def transcribe_audio(audio_file, progress_callback):
    """
    音声ファイルをテキストに変換する関数（並行処理版）

    Args:
        audio_file (str): 変換する音声ファイルのパス
        progress_callback (function): 進捗状況を更新するためのコールバック関数

    Returns:
        str: 文字起こしされたテキスト全体
    """
    # 音声ファイルをセグメントに分割
    segments = split_audio(audio_file)
    total_segments = len(segments)
    transcription = ""
    processed_segments = []
    
    recognizer = sr.Recognizer()
    
    # 部分関数を作成して、progress_callback、total_segments、processed_segmentsを固定
    transcribe_func = partial(transcribe_segment, recognizer=recognizer, 
                              progress_callback=progress_callback, 
                              total_segments=total_segments,
                              processed_segments=processed_segments)
    
    # 並行処理を使用して各セグメントを文字起こし
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        future_to_segment = {executor.submit(transcribe_func, segment): segment for segment in segments}
        for future in concurrent.futures.as_completed(future_to_segment):
            segment = future_to_segment[future]
            try:
                text = future.result()
                transcription += text + " "
            except Exception as exc:
                print(f'{segment} generated an exception: {exc}')
    
    return transcription