import logging

from django.conf import settings
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.db import models, transaction
from model_utils.models import TimeStampedModel
from easy_thumbnails.fields import ThumbnailerImageField

from cf_core import managers as core_managers
from cf_core.models import BaseModerateModel
from cf_core import utils
from cf_adverts import managers
from cf_adverts.signals import project_created, project_edited, project_status_changed

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

    title = models.CharField(verbose_name=_('title'), max_length=2048, default='')

    location = models.ForeignKey(
        'cf_core.Location',
        verbose_name=_('location'),
        related_name='projects',
        default=None,
        null=True
    )

    category = models.ForeignKey(
        'cf_adverts.Category',
        verbose_name=_('category'),
        related_name='projects',
        on_delete=models.PROTECT
    )

    logo = ThumbnailerImageField(verbose_name=_('logo'), default=None,
                                 null=True)
    small_logo = ThumbnailerImageField(verbose_name=_('small logo'))
    video = models.URLField(verbose_name=_('youtube video link'),
                            default='', blank=True)

    short_description = models.TextField(
        verbose_name=_('short description'),
        default=''
    )

    description = models.TextField(verbose_name=_('description'), default='')
    status = models.ForeignKey('cf_core.Status', verbose_name=_('status'))

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('owner'),
        related_name='owned_projects'
    )

    origin = models.OneToOneField(
        'self',
        verbose_name=_('original'),
        related_name='draft',
        editable=False,
        default=None,
        null=True
    )

    ended_at = models.DateField(
        verbose_name=_('ended at'),
        null=True,
        blank=True
    )
    total_amount = models.BigIntegerField(
        verbose_name=_('total amount'),
        default=0,
        help_text=_('goal')
    )
    collected_amount = models.BigIntegerField(
        verbose_name=_('collected amount'),
        default=0
    )

    articles_of_association = models.FileField(
        verbose_name=_('articles of association'),
        default='',
        blank=True
    )

    articles_of_association_approved = models.NullBooleanField(
        verbose_name=_('articles of association approved'),
        default=False
    )

    extract_from_egrul = models.FileField(verbose_name=_('extract from egrul'),
                                          default='', blank=True)
    extract_from_egrul_approved = models.NullBooleanField(
        verbose_name=_('extract from the Unified State Register of Legal Entities is confirmed'),
        default=False
    )

    general_meeting_decision = models.FileField(
        verbose_name=_('the decision of the general meeting on the approval of the project'),
        default='',
        blank=True
    )

    general_meeting_decision_approved = models.NullBooleanField(
        verbose_name=_('the file of the decision of the general meeting is confirmed'),
        default=False
    )

    auditor = models.ForeignKey(
        'cf_users.User',
        verbose_name=_('auditor'),
        related_name='project_audits',
        null=True,
        blank=True
    )

    auditor_notes = models.TextField(
        verbose_name=_('auditor notes'),
        max_length=1024,
        default='',
        blank=True
    )

    auditor_approved = models.NullBooleanField(
        verbose_name=_('approved by auditor'),
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
        """ autocomplete search fields for django-jet """
        return 'title',

    def get_collected_percent(self):
        if self.collected_amount:
            return int(
                self.collected_amount * 100.0 / float(self.total_amount)
            )
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
        """
        Apply draft instance to origin.

        :return:
        """

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
        # FIXME: moved to another app
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
        # FIXME: moved to another app
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
        # FIXME: moved to another app
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
        verbose_name = _('advert')
        verbose_name_plural = _('adverts')


class AdvertEstimate(TimeStampedModel):
    advert = models.ForeignKey('Advert', verbose_name=_('advert'),
                               related_name='estimates')
    title = models.CharField(_('title'), max_length=512)
    amount = models.IntegerField(verbose_name=_('amount'))

    class Meta:
        verbose_name = _('advert estimate')
        verbose_name_plural = _('advert estimates')


class PublishedAdvert(Advert):
    """
    Would be used as published advert.
    """

    objects = managers.PublishedAdvertManager()

    class Meta:
        proxy = True
        verbose_name = _('published advert')
        verbose_name_plural = _('published adverts')


class NewAdvert(Advert):
    """
    Would be used as new advert.
    """

    objects = managers.WaitAdvertManager()

    class Meta:
        proxy = True
        verbose_name = _('new advert')
        verbose_name_plural = _('new adverts')


class BannedAdvert(Advert):
    """
    Would be used as blocked advert
    """

    objects = managers.BannedProjectManager()

    class Meta:
        proxy = True
        verbose_name = _('blocked advert')
        verbose_name_plural = _('blocked adverts')


class DraftAdvert(Advert):
    """
    Would be used as draft advert.
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
        """
        Moderate instance.

        :param moderation_note: ModerationNote instance
        :param commit: bool
        :param with_check: bool
        :return:
        """

        super(DraftAdvert, self).process_moderate(
            moderation_note,
            commit=False,
            with_check=with_check
        )
        from cf_adverts.tasks import process_apply_draft_project

        if self.is_available:
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
        verbose_name = _('draft advert')
        verbose_name_plural = _('draft adverts')


post_save.connect(Advert.send_create_signal, sender=Advert)
post_save.connect(PublishedAdvert.send_status_change_signal,
                  sender=PublishedAdvert)
post_save.connect(Advert.send_status_change_signal, sender=Advert)
post_save.connect(BannedAdvert.send_status_change_signal, sender=BannedAdvert)
post_save.connect(DraftAdvert.send_status_change_signal, sender=DraftAdvert)
