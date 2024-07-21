import os
import subprocess
from pydub import AudioSegment
from logger import app_logger

def convert_to_wav(input_file, output_dir):
    app_logger.info(f"Converting audio file to WAV: {input_file}")
    name, ext = os.path.splitext(os.path.basename(input_file))
    output_file = os.path.join(output_dir, f"{name}.wav")
    
    try:
        # ffmpegを使用してファイルを変換
        command = [
            'ffmpeg',
            '-i', input_file,
            '-acodec', 'pcm_s16le',
            '-ac', '2',
            '-ar', '44100',
            '-y',
            output_file
        ]
        
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode != 0:
            app_logger.error(f"ffmpeg error: {result.stderr}")
            raise Exception(f"ffmpeg command failed: {result.stderr}")
        
        # 変換されたファイルの検証
        try:
            AudioSegment.from_wav(output_file)
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
        audio = AudioSegment.from_wav(audio_file)
        duration = len(audio)
        for i in range(0, duration, segment_length * 1000):
            segment = audio[i:i + segment_length * 1000]
            segment_file = os.path.join(output_dir, f"segment_{i // (segment_length * 1000)}.wav")
            segment.export(segment_file, format="wav")
            segments.append(segment_file)
            app_logger.debug(f"Created segment: {segment_file}")
        
        app_logger.info(f"Audio file split into {len(segments)} segments")
    except Exception as e:
        app_logger.error(f"Error splitting audio file: {str(e)}", exc_info=True)
        raise
    
    return segments