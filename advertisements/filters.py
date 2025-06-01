from django_filters import rest_framework as filters, DateFromToRangeFilter

from advertisements.models import Advertisement


class AdvertisementFilter(filters.FilterSet):
    """Фильтры для объявлений."""

    created_at = DateFromToRangeFilter()
    status = filters.CharFilter()
    favorites = filters.BooleanFilter(method='filter_favorites')

    class Meta:
        model = Advertisement
        fields = ['status', 'created_at', 'creator']

    def filter_favorites(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorited_by__user=self.request.user)
        return queryset
