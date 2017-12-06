from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from cf_core.admin import ModerationNoteInLine, BaseModerationModelAdmin
from cf_adverts.models import (
    DraftAdvert, BannedAdvert, NewAdvert, PublishedAdvert, Category, Event
)


class ProjectAdmin(BaseModerationModelAdmin):

    list_display = ('id', 'title', 'get_owner_url', 'get_owner_approved')
    list_display_links = ('id', 'title')
    readonly_fields = ('get_owner_url',)
    change_form_template = 'admin/projects/change_form_project.html'

    def get_owner_approved(self, obj):
        return obj.owner.profile.is_available
    get_owner_approved.boolean = True
    get_owner_approved.short_description = _('profile has approved')

    def get_owner_url(self, obj):
        return '<a href="{url}">{name}</a>'.format(
            url=reverse('admin:users_profile_change', args=[obj.owner.profile.id]),
            name=obj.owner.profile.title or obj.owner.get_full_name()
        )
    get_owner_url.short_description = _('owner')
    get_owner_url.allow_tags = True

    def get_origin(self, obj):
        if obj.origin_id:
            return '<a href="{url}">{text}</a>'.format(
                text=_('original'),
                url=reverse('admin:projects_publishedproject_change', args=[obj.origin_id])
            )
    get_origin.short_description = _('original')
    get_origin.allow_tags = True

    def get_form(self, request, obj=None, **kwargs):
        form = super(ProjectAdmin, self).get_form(request, obj=obj, **kwargs)
        form.base_fields['status'].queryset = form.base_fields['status'].\
            queryset.filter(
            content_type=ContentType.objects.get_for_model(self.model)
        )
        return form

    inlines = [
        ModerationNoteInLine
    ]


class DraftProjectAdmin(ProjectAdmin):

    readonly_fields = ('get_owner_url', 'get_origin')
    exclude = ('origin',)

    save_as_continue = False
    save_as = False
    inlines = [
        ModerationNoteInLine
    ]


class PublishedProjectAdmin(ProjectAdmin):

    pass


admin.site.register(PublishedAdvert, PublishedProjectAdmin)
admin.site.register(NewAdvert, ProjectAdmin)
admin.site.register(BannedAdvert, ProjectAdmin)
admin.site.register(DraftAdvert, DraftProjectAdmin)
admin.site.register(Event)
admin.site.register(Category)
