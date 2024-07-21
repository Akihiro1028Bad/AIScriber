# services/audio_service.py

import os
import subprocess
from pydub import AudioSegment
from logger import app_logger

def convert_to_wav(input_file, output_dir):
    app_logger.info(f"Converting audio file to WAV: {input_file}")
    name, ext = os.path.splitext(os.path.basename(input_file))
    output_file = os.path.join(output_dir, f"{name}.wav")
    
    try:
        # ファイルの存在確認
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found: {input_file}")

        # ffmpegコマンドの構築
        command = [
            'ffmpeg',
            '-i', input_file,
            '-acodec', 'pcm_s16le',
            '-ac', '2',
            '-ar', '44100',
            '-y',
            output_file
        ]
        
        # ffmpegの実行
        app_logger.debug(f"Executing ffmpeg command: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode != 0:
            app_logger.error(f"ffmpeg error: {result.stderr}")
            raise Exception(f"ffmpeg command failed: {result.stderr}")
        
        # 出力ファイルの存在確認
        if not os.path.exists(output_file):
            raise FileNotFoundError(f"Output file was not created: {output_file}")

        # 出力ファイルのサイズ確認
        file_size = os.path.getsize(output_file)
        app_logger.info(f"Converted file size: {file_size} bytes")
        if file_size == 0:
            raise Exception("Converted file is empty")

        # 変換されたファイルの検証
        try:
            audio = AudioSegment.from_wav(output_file)
            app_logger.info(f"Successfully loaded converted file. Duration: {len(audio) / 1000} seconds")
        except Exception as e:
            app_logger.error(f"Failed to validate converted WAV file: {str(e)}")
            raise Exception(f"WAV file validation failed: {str(e)}")
        
        app_logger.info(f"Audio file converted and validated successfully: {output_file}")
        return output_file
    
    except Exception as e:
        app_logger.error(f"Error converting audio file: {str(e)}", exc_info=True)
        raise

def split_audio(audio_file, output_dir, segment_length=60):
    app_logger.info(f"Splitting audio file: {audio_file}")
    segments = []
    try:
        # ファイルの存在確認
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"Audio file not found: {audio_file}")

        audio = AudioSegment.from_wav(audio_file)
        duration = len(audio)
        app_logger.info(f"Total audio duration: {duration / 1000} seconds")

        for i in range(0, duration, segment_length * 1000):
            segment = audio[i:i + segment_length * 1000]
            segment_file = os.path.join(output_dir, f"segment_{i // (segment_length * 1000)}.wav")
            segment.export(segment_file, format="wav")
            
            # セグメントファイルの検証
            if not os.path.exists(segment_file):
                raise FileNotFoundError(f"Segment file was not created: {segment_file}")
            
            file_size = os.path.getsize(segment_file)
            if file_size == 0:
                raise Exception(f"Segment file is empty: {segment_file}")

            segments.append(segment_file)
            app_logger.debug(f"Created segment: {segment_file}, size: {file_size} bytes")
        
        app_logger.info(f"Audio file split into {len(segments)} segments")
    except Exception as e:
        app_logger.error(f"Error splitting audio file: {str(e)}", exc_info=True)
        raise
    
    return segments

# テスト用のコード
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