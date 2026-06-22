import json
import re
from io import BytesIO
from typing import Any

from PIL import Image
from PIL.ImageFile import ImageFile
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.db.models import Max
from django.http import HttpRequest, HttpResponse
from accounts.models import CustomUser
from users.models import Profile
from image.models import ImageTable, ImageTableMetaData


DIM_PATTERN = re.compile(r'[_-]?\d+x\d+[_]?')


def _get_slider_defaults() -> dict[str, int]:
    defaults = getattr(settings, 'IMAGE_TABLE_SLIDER_DEFAULTS', {})
    return {
        'zoom': int(defaults.get('zoom', 50)),
        'threshold': int(defaults.get('threshold', 150)),
        'r': int(defaults.get('r', 250)),
        'g': int(defaults.get('g', 250)),
        'b': int(defaults.get('b', 250)),
    }


def _get_latest_upload_instance(user: CustomUser) -> int | None:
    """Get the latest upload instance for a user."""
    return (
        ImageTable
            .objects
            .filter(user=user)
            .aggregate(Max('upload_instance'))
            .get('upload_instance__max')
    )


def _get_next_upload_instance(user: CustomUser) -> int:
    """Get the next upload instance for a user."""
    latest_instance = _get_latest_upload_instance(user)
    if latest_instance is None:
        return 0
    return int(latest_instance) + 1


def _extract_name_dimensions(filename: str) -> tuple[int, int]:
    """Extract dimensions from the filename."""
    match = DIM_PATTERN.search(filename.replace(' ', ''))
    if not match:
        return 0, 0

    raw_dim = match.group(0).replace('-', '').replace('_', '')
    width, height = raw_dim.split('x', maxsplit=1)
    return int(width), int(height)


def _build_data_row(image: ImageTable) -> list[str | int]:
    """Build a data row for the image table based on the image instance."""
    img_dim = f'{image.img_width}x{image.img_height}'
    name_dim = f'{image.name_width}x{image.name_height}'

    return [
        image.img_src.url,
        'TRUE',
        image.name,
        image.img_type,
        image.size_kb,
        image.size_kb,
        img_dim,
        name_dim,
        'TRUE' if img_dim == name_dim else 'FALSE',
    ]


def _is_image_file(uploaded_file: UploadedFile) -> bool:
    """Check if the uploaded file is an image based on its content type."""
    content_type = uploaded_file.content_type or ''
    return content_type.startswith('image/')


def _build_payload(uploaded_file: UploadedFile, index: int, upload_instance: int) -> dict[str, str | int]:
    """Build payload for image metadata."""
    buffered = BytesIO()
    img: ImageFile = Image.open(uploaded_file)
    f_type = (uploaded_file.content_type or '').split('/', maxsplit=1)[-1]
    img.save(buffered, format=f_type)
    width, height = img.size

    name_width, name_height = _extract_name_dimensions(uploaded_file.name)

    return {
        'name': uploaded_file.name,
        'size_kb': uploaded_file.size,
        'img_type': f_type,
        'img_width': width,
        'img_height': height,
        'name_width': name_width,
        'name_height': name_height,
        'upload_instance': upload_instance,
        'sl_no': index,
    }


@login_required
def process_files(request: HttpRequest) -> HttpResponse:
    """Process uploaded files and render the image home page."""
    if request.method == 'POST':
        files = request.FILES.getlist('files')
        image_files = [f for f in files if _is_image_file(f)]

        if image_files:
            upload_instance = _get_next_upload_instance(request.user)

            if upload_instance > 0:
                ImageTable.objects.filter(user=request.user, upload_instance__lt=upload_instance).delete()

            for index, uploaded_file in enumerate(image_files, start=1):
                payload = _build_payload(uploaded_file, index, upload_instance)
                ImageTable.objects.create(user=request.user, img_src=uploaded_file, **payload)
                ImageTableMetaData.objects.create(user=request.user, **payload)

    img_instance_last = _get_latest_upload_instance(request.user)
    images = ImageTable.objects.none()
    if img_instance_last is not None:
        images = ImageTable.objects.filter(upload_instance=img_instance_last, user=request.user)

    data = [_build_data_row(img) for img in images]
    user_pref = _get_slider_defaults()

    context: dict[str, Any] = {
        'data': json.dumps(data),
        'user_pref': user_pref,
        'avatar': get_object_or_404(Profile, user=request.user).profile_image,
    }

    return render(request, 'image/image_home.html', context)


@login_required
def display_img(request: HttpRequest, id: int) -> HttpResponse:
    """Display a single image based on the provided ID."""
    if request.method == 'GET':
        img_instance_last = _get_latest_upload_instance(request.user)
        image = get_object_or_404(
            ImageTable,
            user=request.user,
            upload_instance=img_instance_last,
            sl_no=id
        )
        img_src = image.img_src.url

        return render(request, 'display_img/single_image.html', {'src': img_src})

    return render(request, 'display_img/single_image.html', {'src': None})
