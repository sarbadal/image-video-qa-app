import json
import re
from django.shortcuts import get_object_or_404, render
from django.db.models import Max, Q
from users.models import UserPreferences, Profile
from video.models import (
    VideoTable,
    VideoTableMetaData,
    VideoAspectRatio,
    VideoDurations,
    VideoFormats,
    AudioDecibel
)
from video.metadata import get_video_metadata


DIM_PATTERN = re.compile(r'[_-]?\d+x\d+[_]?')


def _get_latest_upload_instance(user):
    return VideoTable.objects.filter(user=user).aggregate(Max('upload_instance')).get('upload_instance__max')


def _get_next_upload_instance(user):
    latest_instance = _get_latest_upload_instance(user)
    if latest_instance is None:
        return 0
    return int(latest_instance) + 1


def _extract_name_dimensions(filename):
    match = DIM_PATTERN.search(filename.replace(' ', ''))
    if not match:
        return '0', '0'

    cleaned = match.group(0).replace('-', '').replace('_', '')
    width, height = cleaned.split('x', maxsplit=1)
    return width, height


def _seconds_to_hms(seconds):
    total_seconds = int(seconds or 0)
    hours, remainder = divmod(total_seconds, 3600)
    mins, secs = divmod(remainder, 60)
    return f'{hours}:{mins:02d}:{secs:02d}'


def _parse_decibel(decibel_value):
    try:
        cleaned = decibel_value.replace('db', '').replace('-inf', '').replace('--', '').replace(' ', '')
        return float(cleaned)
    except (AttributeError, TypeError, ValueError):
        return 0.0


def _get_decibel_bounds(user):
    decibel_qry = AudioDecibel.objects.filter(user=user).first()
    if not decibel_qry:
        return 0.0, 0.0
    return float(decibel_qry.min_decibel), float(decibel_qry.max_decibel)


def _get_video_rules(user):
    aspect_ratios = {
        f'{item.width}x{item.height}'.lower()
        for item in VideoAspectRatio.objects.filter(user=user)
    }
    durations = {
        _seconds_to_hms(item.durations)
        for item in VideoDurations.objects.filter(user=user)
    }
    formats = {
        item.formats.lower()
        for item in VideoFormats.objects.filter(user=user)
    }
    min_decibel, max_decibel = _get_decibel_bounds(user)
    return aspect_ratios, durations, formats, min_decibel, max_decibel


def _build_video_payload(video_name, metadata, name_width, name_height, upload_instance, serial_no):
    return {
        'name': video_name,
        'size': metadata.get('file_size'),
        'video_type': metadata.get('format'),
        'video_width': metadata.get('video_width'),
        'video_height': metadata.get('video_height'),
        'resolution': metadata.get('resolution'),
        'aspect_ratio': metadata.get('aspect_ratio'),
        'video_fps': metadata.get('frame_rate'),
        'video_bit_rate': metadata.get('video_bit_rate'),
        'audio_bit_rate': metadata.get('audio_bit_rate'),
        'audio_sample_rate': metadata.get('audio_sample_rate'),
        'max_audio_decibel': metadata.get('max_audio_decibel'),
        'video_codec': metadata.get('video_codec'),
        'audio_codec': metadata.get('audio_codec'),
        'duration': metadata.get('duration'),
        'name_width': name_width,
        'name_height': name_height,
        'upload_instance': upload_instance,
        'sl_no': serial_no,
    }


def _video_content_type(video_type):
    normalized_type = (video_type or '').lower()
    if normalized_type in ['quicktime', 'apple']:
        return 'video/mp4'
    return f'video/{video_type}'


def process_video(request):
    """process video files"""
    data = []
    video_type = []

    if request.method == "POST":
        videos = request.FILES.getlist('videos')
        video_instance_max = _get_next_upload_instance(request.user)

        if video_instance_max > 0 and len(videos) > 0:
            VideoTable.objects.filter(
                Q(user=request.user) & Q(upload_instance__lt=video_instance_max)
            ).delete()

        for index, video_file in enumerate(videos, start=1):
            if 'video' not in (video_file.content_type or ''):
                continue

            video_metadata = get_video_metadata(video_file.temporary_file_path())
            name_width, name_height = _extract_name_dimensions(video_file.name)
            payload = _build_video_payload(
                video_name=video_file.name,
                metadata=video_metadata,
                name_width=name_width,
                name_height=name_height,
                upload_instance=video_instance_max,
                serial_no=index,
            )

            VideoTable.objects.create(user=request.user, video_src=video_file, **payload)
            VideoTableMetaData.objects.create(user=request.user, **payload)

    video_instance_last = _get_latest_upload_instance(request.user)
    videos = None
    if video_instance_last is not None:
        videos = VideoTable.objects.filter(
            Q(upload_instance=video_instance_last) & Q(user=request.user)
        )

    aspect_ratios, durations, formats, min_decibel, max_decibel = _get_video_rules(request.user)

    if videos:
        for vdo in videos:
            r_obj = []

            r_obj.append(vdo.video_src.url)
            r_obj.append(vdo.name)
            r_obj.append(vdo.duration)
            r_obj.append(vdo.video_fps)
            r_obj.append(vdo.video_type)
            r_obj.append(vdo.size)
            r_obj.append(vdo.resolution)
            r_obj.append(vdo.aspect_ratio)
            r_obj.append(vdo.video_bit_rate)
            r_obj.append(vdo.audio_bit_rate)
            r_obj.append(vdo.max_audio_decibel)
            r_obj.append(vdo.video_codec)
            r_obj.append(vdo.audio_codec)

            r_obj.append('TRUE' if (vdo.aspect_ratio or '').lower() in aspect_ratios else 'FALSE')
            r_obj.append('TRUE' if vdo.duration in durations else 'FALSE')
            r_obj.append('TRUE' if (vdo.video_codec or '').lower() in formats else 'FALSE')

            file_decibel = _parse_decibel(vdo.max_audio_decibel)

            if min_decibel <= file_decibel <= max_decibel and file_decibel != 0:
                r_obj.append('TRUE')
            else:
                r_obj.append('FALSE')

            data.append(r_obj)

            video_type.append(_video_content_type(vdo.video_type))

    user_pref = get_object_or_404(UserPreferences, user=request.user)
    zoom_index = user_pref.default_video_zoom
    threshold_index = user_pref.default_video_threshold
    r_index = user_pref.default_tbl_color_r
    g_index = user_pref.default_tbl_color_g
    b_index = user_pref.default_tbl_color_b

    context = {
        'data': json.dumps(data),
        'user_pref': {
            'zoom': zoom_index, 'threshold': threshold_index,
            'r': r_index, 'g': g_index, 'b': b_index
        },
        'avatar': get_object_or_404(Profile, user=request.user).profile_image,
        'video_type': video_type
    }

    return render(request, 'video/videoHome.html', context)
