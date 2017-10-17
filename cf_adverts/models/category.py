from django.db import models
from model_utils.models import TimeStampedModel

__all__ = [
    'Category'
]


class Category(TimeStampedModel):
    name = models.CharField("название", max_length=512, default='')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "категория"
        verbose_name_plural = "категория"
