from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action

from advertisements.filters import AdvertisementFilter
from advertisements.models import Advertisement, Favorite
from advertisements.serializers import AdvertisementSerializer


class IsOwnerOrAdmin(BasePermission):
    """Права на изменение/удаление только для автора или админа."""

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:  # Админ может всё
            return True
        return request.user == obj.creator  # Остальные только свои объявления


class AdvertisementViewSet(ModelViewSet):
    """ViewSet для объявлений."""

    queryset = Advertisement.objects.all()
    serializer_class = AdvertisementSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = AdvertisementFilter
    throttle_classes = [UserRateThrottle, AnonRateThrottle]

    def get_permissions(self):
        """Получение прав для действий."""
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsOwnerOrAdmin()]
        return []

    def get_queryset(self):
        """Фильтрация для черновиков (если добавить статус DRAFT)"""

        queryset = super().get_queryset()
        if not self.request.user.is_authenticated:
            return queryset.exclude(status="DRAFT")

        # Для авторизованных показываем все объявления, кроме чужих черновиков
        if not self.request.user.is_staff: # Админы видят все
            queryset = queryset.exclude(
                status="DRAFT",
                creator__ne=self.request.user
            )
        return queryset

    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk=None):
        ad = self.get_object()
        user = request.user

        if ad.creator == user:
            return Response(
                {"error": "Нельзя добавлять свои объявления в избранное"},
                status=400
            )

        if request.method == 'POST':
            Favorite.objects.get_or_create(user=user, advertisement=ad)
            return Response({"status": "added to favorites"})

        Favorite.objects.filter(user=user, advertisement=ad).delete()
        return Response({"status": "removed from favorites"})

    @action(detail=False)
    def favorites(self, request):
        favs = Favorite.objects.filter(user=request.user)
        ads = [fav.advertisement for fav in favs]
        serializer = self.get_serializer(ads, many=True)
        return Response(serializer.data)
