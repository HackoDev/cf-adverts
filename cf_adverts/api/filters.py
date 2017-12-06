import django_filters
from cf_adverts import models


class NumberInFilter(django_filters.BaseInFilter, django_filters.NumberFilter):
    pass


class ProjectFilter(django_filters.FilterSet):

    base_type = django_filters.CharFilter(name='base_type', lookup_expr='in')
    is_draft = django_filters.BooleanFilter(method='get_is_draft')
    owned = django_filters.BooleanFilter(method='get_owned')
    category = NumberInFilter(name='category', lookup_expr='in')

    def get_is_draft(self, queryset, name, value):
        return queryset.exclude(origin_id__isnull=value)

    def get_owned(self, queryset, name, value):
        if value:
            return queryset.filter(owner_id=self.request.user.id)
        return queryset

    class Meta:
        model = models.Advert
        fields = ['category', 'status', 'is_draft', 'is_available', 'base_type']


class ProjectEventFilter(django_filters.FilterSet):

    class Meta:
        model = models.Event
        fields = ('advert',)


class AdvertEstimateFilter(django_filters.FilterSet):

    class Meta:
        model = models.AdvertEstimate
        fields = ('advert', )