from django.db import models
from django.utils.translation import ugettext_lazy as _
from model_utils.models import TimeStampedModel

__all__ = [
    'Category'
]


class Category(TimeStampedModel):
    name = models.CharField(verbose_name=_('title'), max_length=512, default='')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')
