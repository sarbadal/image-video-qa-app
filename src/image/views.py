import json
import re
from PIL import Image
from io import BytesIO
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.db.models import Max, Q
from users.models import UserPreferences, Profile
from image.models import ImageTable, ImageTableMetaData


DIM_PATTERN = re.compile(r'[_-]?\d+x\d+[_]?')


def _get_latest_upload_instance(user):
    return ImageTable.objects.filter(user=user).aggregate(Max('upload_instance')).get('upload_instance__max')


def _get_next_upload_instance(user):
    latest_instance = _get_latest_upload_instance(user)
    if latest_instance is None:
        return 0
    return int(latest_instance) + 1


def _extract_name_dimensions(filename):
    match = DIM_PATTERN.search(filename.replace(' ', ''))
    if not match:
        return '0', '0'

    raw_dim = match.group(0).replace('-', '').replace('_', '')
    return tuple(raw_dim.split('x', maxsplit=1))


def _build_data_row(image):
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


@login_required
def process_files(request):
    """doc string"""

    data = []

    if request.method == "POST":
        files = request.FILES.getlist('files')
        img_instance_max = _get_next_upload_instance(request.user)

        if img_instance_max > 0 and len(files) > 0:
            ImageTable.objects.filter(
                Q(user=request.user) & Q(upload_instance__lt=img_instance_max)
            ).delete()

        for index, uploaded_file in enumerate(files, start=1):

            if 'image' in uploaded_file.content_type:
                img = Image.open(uploaded_file)
                buffered = BytesIO()
                f_type = uploaded_file.content_type.split('/')[-1]
                img.save(buffered, format=f_type)
                width, height = img.size

                name_width, name_height = _extract_name_dimensions(uploaded_file.name)

                payload = {
                    'name': uploaded_file.name,
                    'size_kb': uploaded_file.size,
                    'img_type': f_type,
                    'img_width': width,
                    'img_height': height,
                    'name_width': name_width,
                    'name_height': name_height,
                    'upload_instance': img_instance_max,
                    'sl_no': index,
                }

                ImageTable.objects.create(user=request.user, img_src=uploaded_file, **payload)
                ImageTableMetaData.objects.create(user=request.user, **payload)

    img_instance_last = _get_latest_upload_instance(request.user)
    images = None
    if img_instance_last is not None:
        images = ImageTable.objects.filter(
            Q(upload_instance=img_instance_last) & Q(user=request.user)
        )

    if images:
        data = [_build_data_row(img) for img in images]

    user_pref = get_object_or_404(UserPreferences, user=request.user)
    zoom_index = user_pref.default_img_zoom
    threshold_index = user_pref.default_img_threshold
    r_index = user_pref.default_tbl_color_r
    g_index = user_pref.default_tbl_color_g
    b_index = user_pref.default_tbl_color_b

    context = {
        'data': json.dumps(data),
        'user_pref': {
            'zoom': zoom_index, 'threshold': threshold_index,
            'r': r_index, 'g': g_index, 'b': b_index
        },
        'avatar': get_object_or_404(Profile, user=request.user).profile_image
    }

    return render(request, 'image/imageHome.html', context)


@login_required
def display_img(request, id):
    """doc string"""
    if request.method == 'GET':
        img_instance_last = _get_latest_upload_instance(request.user)
        image = get_object_or_404(
            ImageTable,
            user=request.user,
            upload_instance=img_instance_last,
            sl_no=id
        )
        img_src = image.img_src.url

        return render(request, 'displayImg/singleImage.html', {'src': img_src})

    return render(request, 'displayImg/singleImage.html', {'src': None})
