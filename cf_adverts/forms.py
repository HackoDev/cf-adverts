from django import forms

from base.models import City
from .models import Project


class ProjectAuditorForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project')
        self.auditor = kwargs.pop('auditor')
        super(ProjectAuditorForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Project
        fields = (
            'auditor_notes',
            'auditor_approved'
        )


class ProjectAuditForm(forms.ModelForm):

    auditor_approved = forms.BooleanField(required=False)

    class Meta:
        model = Project
        fields = ('auditor_approved', 'auditor_notes')


class SearchProjectsForm(forms.Form):

    city = forms.ModelChoiceField(
        queryset=City.objects.all()
    )
