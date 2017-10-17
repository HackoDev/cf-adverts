from django.db import models
from django.utils import timezone
from model_utils import Choices
from model_utils.models import TimeStampedModel

__all__ = [
    'Event'
]


class Event(TimeStampedModel):
    """
    События проекта.
    Будет использоваться для отображения временой шкалы и событий на ней 
    по конкретному проекту.
    """

    TYPE_CHOICES = Choices(
        ('CUSTOM', "Ручное создание"),
        ('PROJECT_CREATED', "Проект создан"),
        ('PROJECT_EDITED', "Проект отредактирован"),
        ('USER_JOINED', "Новый участник"),
        ('PERCENT_CHANGED', "Достижение процентов цели"),
        ('PROJECT_DONE', "Проект завершен"),
        ('PAYMENT_RECEIVED', "Принят платеж"),
        ('RESOURCE_RECEIVED', "Принят материал/ресурс")
    )

    advert = models.ForeignKey(
        'cf_adverts.advert',
        verbose_name="объявление",
        related_name='events'
    )

    base_type = models.CharField("тип события", max_length=64,
                                 choices=TYPE_CHOICES)
    percent = models.IntegerField("процент сборов")
    description = models.TextField("описание", default='', blank=True)

    def get_event_time(self):
        return timezone.localtime(self.created)

    def __str__(self):
        return self.description

    class Meta:
        ordering = ['-created']
        verbose_name = "событие объявления"
        verbose_name_plural = "события объявлений"
