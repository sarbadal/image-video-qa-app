import re
from django.db import models
from accounts.models import CustomUser


def image_file_path(instance, filename):
    filename = filename.replace(' ', '').strip()
    filename = re.sub(r'(?u)[^-\w. ]', '', filename)
    return 'image/user_{0}/{1}'.format(instance.user.id, filename)


class ImageRecordBase(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=500)
    size_kb = models.IntegerField(default=0)
    img_type = models.CharField(max_length=25)
    img_width = models.IntegerField(default=0)
    img_height = models.IntegerField(default=0)
    name_width = models.IntegerField(default=0)
    name_height = models.IntegerField(default=0)
    upload_instance = models.IntegerField(default=0)
    sl_no = models.IntegerField(default=0)
    date_added = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class ImageTable(ImageRecordBase):
    img_src = models.FileField(upload_to=image_file_path, blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Image Table'

    def delete(self, *args, **kwargs):
        if self.img_src:
            self.img_src.delete(save=False)
        super().delete(*args, **kwargs)


class ImageTableMetaData(ImageRecordBase):
    class Meta:
        verbose_name_plural = 'Image Table Meta Data'
