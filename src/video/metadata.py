import os
import math
import string
import random
import tempfile
import librosa
import subprocess as sp
from moviepy.video.io.VideoFileClip import VideoFileClip

from core.settings import EXIF_PATH


def create_temp_file(suffix='audio.ogg'):
    """Create a random temp audio filepath for extracted video audio."""
    random_string = ''.join(random.choices(string.ascii_uppercase + string.digits, k=20))
    return os.path.join(tempfile.gettempdir(), f'{random_string}-{suffix}')


def _parse_exif_output(exif_stdout):
    exifdata = {}
    for line in exif_stdout.splitlines():
        key, _, value = line.partition(':')
        if key:
            exifdata[key.strip()] = value.strip()
    return exifdata


def _safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _extract_max_audio_decibel(tmp_file):
    try:
        y, _ = librosa.load(tmp_file)
        rms = librosa.feature.rms(y=y)
        max_rms = max(rms[0])
        return f"{round(20 * math.log10(max_rms), 2)} db"
    except Exception:
        return '--'


def _format_duration(total_seconds):
    total_seconds = int(total_seconds or 0)
    hours, remainder = divmod(total_seconds, 3600)
    mins, seconds = divmod(remainder, 60)
    return f'{hours}:{mins:02d}:{seconds:02d}'


def get_video_metadata(file, file_size=0, temp_audio_file='audio.ogg'):
    """Extract normalized metadata for a video file."""
    del file_size

    tmp_file = create_temp_file(temp_audio_file)

    video = VideoFileClip(file)
    try:
        if video.audio:
            video.audio.write_audiofile(tmp_file, verbose=False, logger=None)

        process = sp.run(
            [EXIF_PATH, file],
            capture_output=True,
            text=True,
            check=False,
        )
        exifdata = _parse_exif_output(process.stdout)

        file_name = exifdata.get('File Name', '--')
        file_type_extn = exifdata.get('File Type Extension', '--')
        audio_type_extn = exifdata.get('Audio Format', '--').split(' ')[0]
        video_codec = exifdata.get('Compressor Name', '--').split(' ')[0]
        video_bit_rate = round(_safe_int(exifdata.get('Average Bitrate', '0')) / 1024, 1)
        file_size = exifdata.get('File Size', '--')

        max_audio_decibel = _extract_max_audio_decibel(tmp_file)

        width = int(video.w)
        height = int(video.h)
        video_fps = round(video.fps, 2)

        audio_channel = _safe_int(exifdata.get('Audio Channels', '0'))
        audio_bit_per_sample = _safe_int(exifdata.get('Audio Bits Per Sample', '0'))
        audio_sample_rate = _safe_int(exifdata.get('Audio Sample Rate', '0'))
        audio_bit_rate = (audio_channel * audio_bit_per_sample * audio_sample_rate) / 1024

        gcd = math.gcd(width, height) if width and height else 1
        aspect_ratio = f'{int(width / gcd)}x{int(height / gcd)}'

        return {
            'file_name': file_name,
            'file_size': file_size,
            'duration': _format_duration(video.duration),
            'format': file_type_extn,
            'resolution': f'{width}x{height}',
            'video_width': width,
            'video_height': height,
            'aspect_ratio': aspect_ratio,
            'frame_rate': f'{video_fps} fps',
            'video_bit_rate': f'{video_bit_rate} kbps',
            'audio_bit_rate': f'{audio_bit_rate} kbps',
            'audio_sample_rate': f'{audio_sample_rate / 1000} kHz',
            'max_audio_decibel': f'{max_audio_decibel}',
            'video_codec': video_codec.lower(),
            'audio_codec': audio_type_extn.lower(),
        }
    finally:
        video.close()
        if os.path.exists(tmp_file):
            os.remove(tmp_file)
