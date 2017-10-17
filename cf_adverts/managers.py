from django.db import models

from cf_core import managers
from cf_users.models import Profile


class ProjectQuerySet(managers.ModerateQuerySet):
    def waiting(self):
        return super(ProjectQuerySet, self).waiting().filter(origin=None)

    def allowed(self):
        return super(ProjectQuerySet, self).allowed().filter(origin=None)

    def banned(self):
        return super(ProjectQuerySet, self).banned().filter(origin=None)

    def drafts(self):
        return super(ProjectQuerySet, self).exclude(origin=None)


class ModerateManager(models.Manager):
    def get_queryset(self):
        return managers.ModerateQuerySet(self.model, using=self.db)

    def allowed(self):
        return self.get_queryset().allowed()

    def banned(self):
        return self.get_queryset().banned()

    def waiting(self):
        return self.get_queryset().waiting()


class ProjectManager(ModerateManager):
    def get_queryset(self):
        return ProjectQuerySet(self.model, using=self.db)


class PublishedAdvertManager(models.Manager):
    def get_queryset(self):
        return ProjectQuerySet(self.model, using=self.db).allowed().filter(
            owner__profile__base_type=Profile.TYPE_CHOICES.NCO)


class WaitAdvertManager(models.Manager):
    def get_queryset(self):
        return ProjectQuerySet(self.model, using=self.db).waiting().filter(
            owner__profile__base_type=Profile.TYPE_CHOICES.NCO)


class BannedProjectManager(models.Manager):
    def get_queryset(self):
        return ProjectQuerySet(self.model, using=self.db).banned()


class DraftProjectManager(models.Manager):
    def get_queryset(self):
        return ProjectQuerySet(self.model, using=self.db).drafts().filter(
            owner__profile__base_type=Profile.TYPE_CHOICES.NCO)
