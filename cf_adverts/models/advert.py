import logging

from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db.models.signals import post_save
from django.utils import timezone
from django.db import models, transaction
from model_utils.models import TimeStampedModel
from easy_thumbnails.fields import ThumbnailerImageField

from cf_core import managers as core_managers

from cf_adverts import utils
from .. import managers
from cf_core.models import BaseModerateModel
from ..signals import project_created, project_edited, project_status_changed

logger = logging.getLogger(__name__)

__all__ = [
    'PublishedAdvert',
    'BannedAdvert',
    'DraftAdvert',
    'NewAdvert',
    'Advert',

    'AdvertEstimate',

    'get_now_date'
]


def get_now_date():
    return timezone.now().date()


class Advert(BaseModerateModel, TimeStampedModel):
    AUDIT_APPROVED_CHOICES = core_managers.MODERATE_STATUS_CHOICES

    title = models.CharField("название", max_length=2048, default='')

    location = models.ForeignKey(
        'cf_core.Location',
        verbose_name="район",
        related_name='projects',
        default=None,
        null=True
    )

    category = models.ForeignKey(
        'cf_adverts.Category',
        verbose_name="категория",
        related_name='projects',
        on_delete=models.PROTECT
    )

    logo = ThumbnailerImageField("большой блок", default=None, null=True)
    small_logo = ThumbnailerImageField("маленький блок")
    video = models.URLField(verbose_name="ссылка на youtube video",
                            default='', blank=True)

    short_description = models.TextField("короткое описание", default='')

    description = models.TextField("подробное описание", default='')

    status = models.ForeignKey('cf_core.Status', verbose_name="статус")

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="инициатор",
        related_name='owned_projects'
    )

    origin = models.OneToOneField(
        'self',
        verbose_name="оригинал",
        related_name='draft',
        editable=False,
        default=None,
        null=True
    )

    ended_at = models.DateField("завершение проекта", null=True, blank=True)
    total_amount = models.BigIntegerField("общая сумма для сборов", default=0,
                                          help_text="Цель")
    collected_amount = models.BigIntegerField("собранные средства", default=0)

    articles_of_association = models.FileField(
        verbose_name="устав",
        default='',
        blank=True
    )

    articles_of_association_approved = models.NullBooleanField(
        verbose_name="устав подтвержден",
        default=False
    )

    extract_from_egrul = models.FileField(verbose_name="Выписка из ЮГРЮЛ",
                                          default='', blank=True)
    extract_from_egrul_approved = models.NullBooleanField(
        verbose_name="выписка из ЮГРЮЛ подтверждена",
        default=False
    )

    general_meeting_decision = models.FileField(
        verbose_name="решение общего собрания об утверждении проекта",
        default='',
        blank=True
    )

    general_meeting_decision_approved = models.NullBooleanField(
        verbose_name="файл решения общего собрания подтвержден",
        default=False
    )

    auditor = models.ForeignKey(
        'cf_users.User',
        verbose_name="аудитор",
        related_name='project_audits',
        null=True,
        blank=True
    )

    auditor_notes = models.TextField(
        verbose_name="заметка аудитора",
        max_length=1024,
        default='',
        blank=True
    )

    auditor_approved = models.NullBooleanField(
        verbose_name="подтвержден аудитором",
        default=None,
        choices=AUDIT_APPROVED_CHOICES
    )

    objects = managers.ProjectManager()

    # files = GenericRelation('storage.File')

    def __str__(self):
        return self.title

    def __init__(self, *args, **kwargs):
        super(Advert, self).__init__(*args, **kwargs)
        self.old_status = getattr(self, 'status', None)
        self.old_ended_at = getattr(self, 'ended_at', None)

    def process_moderate(self, moderation_note, commit=True, with_check=True):
        if with_check:
            draft = DraftAdvert.objects.filter(pk=self.pk).last()
            new_project = NewAdvert.objects.filter(pk=self.pk).last()
            banned_project = NewAdvert.objects.filter(pk=self.pk).last()

            if draft:
                draft.process_moderate(moderation_note, commit=commit,
                                       with_check=False)
            elif new_project:
                new_project.process_moderate(moderation_note, commit=commit,
                                             with_check=False)
            elif banned_project:
                banned_project.process_moderate(moderation_note, commit=commit,
                                                with_check=False)
            else:
                super(Advert, self).process_moderate(moderation_note,
                                                     commit=commit)
        else:
            super(Advert, self).process_moderate(moderation_note,
                                                 commit=commit)

    def perms(self, user):
        return {
            'can_manage_content': self.can_manage_roles(user),
            'can_manage_roles': self.can_manage_content(user)
        }

    def get_expired_at(self):
        days = 0
        if self.ended_at:
            days = (self.ended_at - timezone.now().date()).days
        return days

    @property
    def is_draft(self):
        return self.origin is not None

    @classmethod
    def autocomplete_search_fields(cls):
        return 'title',

    def get_collected_percent(self):
        if self.collected_amount:
            return int(
                self.collected_amount * 100.0 / float(self.total_amount))
        return 0

    def has_draft(self):
        return Advert.objects.filter(origin_id=self.id).exists()

    def get_draft(self):
        try:
            return self.draft
        except Advert.DoesNotExist:
            pass

    @transaction.atomic
    def get_or_create_draft(self):
        # assert self.is_available, _("Project must be moderated")

        draft = self.get_draft()

        if draft:
            return draft

        draft = DraftAdvert(
            origin_id=self.id,
            status=self.status
        )

        for field in self._meta.fields:
            if field.name not in DraftAdvert.exclude_fields:
                if isinstance(field, models.ForeignObject):
                    field_name = '{field_name}_id'.format(
                        field_name=field.name)
                    setattr(draft, field_name, getattr(self, field_name))
                else:
                    setattr(draft, field.name, getattr(self, field.name))
        draft.save()

        for estimate in self.estimates.all():
            draft.estimates.create(
                title=estimate.title,
                amount=estimate.amount,
            )
        return draft

    @transaction.atomic
    def apply_draft_to_origin(self):

        original = self.origin
        logger.info("Draft project #{pk} start applying...".format(
            pk=self.pk,
        ))
        for field in self._meta.fields:
            if field.name not in DraftAdvert.exclude_fields:
                if isinstance(field, models.ForeignObject):
                    field_name = '{field_name}_id'.format(
                        field_name=field.name)
                    setattr(original, field_name, getattr(self, field_name))
                else:
                    setattr(original, field.name, getattr(self, field.name))

        logger.info("Draft project #{pk} successfully applied...".format(
            pk=self.pk,
        ))
        original.save()

        original.estimates.all().delete()
        self.estimates.update(advert_id=original.id)
        original.send_edit_signal(instance=original)
        return original

    def get_base_permissions(self, user):
        # TODO: вынесено в отдельное приложение ролей
        return self.roles.filter(
            is_active=True,
            user_id=user.id,
            base_type=self.roles.model.TYPE_CHOICES.STAFF,
            is_available=BaseModerateModel.MODERATE_STATUS_CHOICES.ALLOWED
        )

    @staticmethod
    def has_staff_permissions(user):
        return user.is_staff or user.is_superuser

    def can_manage_roles(self, user):
        if self.has_staff_permissions(user) or self.owner_id == user.id:
            return True
        permissions = self.get_base_permissions(user)
        return permissions.filter(can_manage_roles=True).exists()

    def can_manage_content(self, user):
        if self.has_staff_permissions(user):
            return True
        permissions = self.get_base_permissions(user)
        return permissions.filter(can_manage_content=True).exists()

    def get_active_roles(self):
        # TODO: вынесено в отдельное приложение ролей
        return self.get_roles().filter(
            is_available=BaseModerateModel.MODERATE_STATUS_CHOICES.ALLOWED,
            is_active=True
        )

    def get_collected_amount(self):
        return utils.format_number(self.collected_amount)

    def get_total_amount(self):
        return utils.format_number(self.total_amount)

    def get_active_roles_counter(self):
        return self.get_active_roles().count() + 1

    def roles_dict(self):
        # TODO: вынесено в отдельное приложение ролей
        roles = self.get_active_roles()
        result_dict = {
            'staffs': []
        }
        for role in roles:
            role_key = '%ss' % role.base_type.lower()
            result_dict.setdefault(role_key, [])
            result_dict.get(role_key).append(role)
        result_dict.get('staffs').append({
            'user': self.owner
        })
        return result_dict

    @staticmethod
    def send_create_signal(**kwargs):
        if kwargs['created']:
            project_created.send(sender=kwargs['instance'])

    @staticmethod
    def send_status_change_signal(**kwargs):
        if not kwargs['created'] and kwargs['instance'].old_status != \
                kwargs['instance'].status:
            project_status_changed.send(sender=kwargs['instance'],
                                        old_status=kwargs[
                                            'instance'].old_status,
                                        new_status=kwargs['instance'].status)
        kwargs['instance']._status = kwargs['instance'].status

    @staticmethod
    def send_edit_signal(**kwargs):
        project_edited.send(sender=kwargs['instance'])

    def save(self, *args, **kwargs):
        origin = Advert.objects.filter(id=self.id).last()
        if origin and self.is_available and not origin.is_available and \
                not self.ended_at:
            self.ended_at = timezone.now() + timezone.timedelta(days=60)
        super(Advert, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "объявление"
        verbose_name_plural = "объявления"


class AdvertEstimate(TimeStampedModel):
    advert = models.ForeignKey('Advert', verbose_name="проект",
                               related_name='estimates')
    title = models.CharField("работа/материал", max_length=512)
    amount = models.IntegerField("сумма в рубля")

    class Meta:
        verbose_name = "смета проекта"
        verbose_name_plural = "сметы проектов"


class PublishedAdvert(Advert):
    """
    Используется в качестве опубликованного проекта.
    """

    objects = managers.PublishedAdvertManager()

    class Meta:
        proxy = True
        verbose_name = "объявление"
        verbose_name_plural = "объявления"


class NewAdvert(Advert):
    """
    Используется в качестве нового объявления.
    """

    objects = managers.WaitAdvertManager()

    class Meta:
        proxy = True
        verbose_name = "новое объявление"
        verbose_name_plural = "новые объявления"


class BannedAdvert(Advert):
    """
    Используется в качестве заблокированного объявления.
    """

    objects = managers.BannedProjectManager()

    class Meta:
        proxy = True
        verbose_name = "заблокированное объявление"
        verbose_name_plural = "заблокированное объявление"


class DraftAdvert(Advert):
    """
    Используется в качестве черновика.
    """

    exclude_fields = [
        'origin',
        'id',
        'status',
        'is_available',
        'approved_at',
        'approved_by',
        'created',
        'modified'
    ]

    objects = managers.DraftProjectManager()

    def process_moderate(self, moderation_note, commit=True, with_check=True):
        super(DraftAdvert, self).process_moderate(
            moderation_note,
            commit=False,
            with_check=with_check
        )
        from cf_adverts.tasks import process_apply_draft_project

        if self.is_available:
            # self.status = config.draft_apply_status

            self.process_status = self.MODERATE_PROCESS_TYPES.APPLY
            moderation_note.instance = self.origin
            moderation_note.save()
            process_apply_draft_project.apply_async(
                args=[self.id],
                countdown=15
            )
        self.save()

    class Meta:
        proxy = True
        verbose_name = "черновик объявления"
        verbose_name_plural = "черновики объявлений"


post_save.connect(Advert.send_create_signal, sender=Advert)
post_save.connect(PublishedAdvert.send_status_change_signal,
                  sender=PublishedAdvert)
post_save.connect(Advert.send_status_change_signal, sender=Advert)
post_save.connect(BannedAdvert.send_status_change_signal, sender=BannedAdvert)
post_save.connect(DraftAdvert.send_status_change_signal, sender=DraftAdvert)
