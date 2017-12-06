from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from model_utils import Choices
from model_utils.models import TimeStampedModel

__all__ = [
    'Event'
]


class Event(TimeStampedModel):
    """
    Events for project.
    Would be used to display time-line on project page.
    """

    TYPE_CHOICES = Choices(
        ('CUSTOM', _('custom event')),
        ('PROJECT_CREATED', _('advert created')),
        ('PROJECT_EDITED', _('advert changed')),
        ('USER_JOINED', _('user joined')),
        ('PERCENT_CHANGED', _('percent changed')),
        ('PROJECT_DONE', _('advert done')),
        ('PAYMENT_RECEIVED', _('payment received')),
        ('RESOURCE_RECEIVED', _('resource received'))
    )

    advert = models.ForeignKey(
        'cf_adverts.advert',
        verbose_name=_('advert'),
        related_name='events'
    )

    base_type = models.CharField(verbose_name=_('base type'), max_length=64,
                                 choices=TYPE_CHOICES)
    percent = models.IntegerField(verbose_name=_('percent'))
    description = models.TextField(verbose_name=_('description'), default='',
                                   blank=True)

    def get_event_time(self):
        return timezone.localtime(self.created)

    def __str__(self):
        return self.description

    class Meta:
        ordering = ['-created']
        verbose_name = _('advert event')
        verbose_name_plural = _('advert events')
