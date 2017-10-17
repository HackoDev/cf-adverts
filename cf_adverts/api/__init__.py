from cf_core.models import Status
from django.db import transaction
from rest_framework import status, mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import APIException
from rest_framework.decorators import detail_route, list_route
from django_filters.rest_framework.backends import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from cf_core.api import PageNumberPaginator

from cf_adverts.api.permissions import HasEstimatePermission
from .filters import ProjectFilter, ProjectEventFilter, AdvertEstimateFilter
from .serializers import (
    AdvertDetailSerializer, AdvertUpdateSerializer, AdvertListDetailSerializer,
    AdvertCreateSerializer, ProjectEventSerializer,
    EstimateCreateSerializer, EstimateListUpdateSerializer,
    EstimateDetailSerializer)
from ..models import AdvertEstimate, Event, PublishedAdvert, Advert


class SerializerSchemaMixin(object):
    """
    Базовый класс для маршрутизации сериалайзеров 
    в зависимости от текущего action.
    """

    serializer_schema = {}

    def get_serializer_class(self):
        """
        Возвращает serializer class из словаря `serializer_schema`.
        :return: type Serializer
        """

        serializer_class = self.serializer_schema.get(
            self.action,
            self.serializer_class
        )
        return serializer_class


class AdvertViewSet(SerializerSchemaMixin, ModelViewSet):
    model = Advert
    serializer_class = AdvertDetailSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = ProjectFilter
    permission_classes = (IsAuthenticated,)
    pagination_class = PageNumberPaginator
    serializer_schema = {
        'create': AdvertCreateSerializer,
        'retrieve': AdvertDetailSerializer,
        'update': AdvertUpdateSerializer,
        'search': AdvertListDetailSerializer,
        'list': AdvertListDetailSerializer,
    }

    def get_object(self):
        obj = super(AdvertViewSet, self).get_object()
        if obj.is_available:
            if not obj.has_draft() and self.action == 'destroy':
                return obj
            draft = obj.get_draft()
            if draft and draft.process_status != \
                    Advert.MODERATE_PROCESS_TYPES.DONE:
                raise self.permission_denied(
                    self.request,
                    "Идет модерация, повторите запрос через несколько минут"
                )
            obj = obj.get_or_create_draft()
        return obj

    @transaction.atomic
    def perform_create(self, serializer):
        serializer.save(
            owner_id=self.request.user.id,
            status=Status.get_for_model(self.model).first()
        )

    @transaction.atomic
    def perform_update(self, serializer):
        serializer.save()

    def get_queryset(self):
        return self.model.objects.filter(owner_id=self.request.user.id)

    @detail_route(methods=['post'])
    def send_to_moderation(self, request, pk):
        """
        Отправка объявления на модерацию.
        """
        obj = self.get_object()
        if obj.process_status in [
            Advert.MODERATE_PROCESS_TYPES.CHECK,
            Advert.MODERATE_PROCESS_TYPES.APPLY
        ]:
            raise APIException(
                detail='Проект уже отправлен на модерацию',
                code=status.HTTP_400_BAD_REQUEST
            )
        obj.process_status = Advert.MODERATE_PROCESS_TYPES.CHECK
        obj.save(update_fields=['process_status', 'modified'])
        return Response(status=status.HTTP_200_OK)

    @list_route(methods=['get'], permission_classes=())
    def search(self, request):
        """
        Поиск обявлений из списка опубликованных.
        """

        queryset = self.filter_queryset(
            PublishedAdvert.objects.all()
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class EstimateViewSet(SerializerSchemaMixin, ModelViewSet):
    permission_classes = (IsAuthenticated, HasEstimatePermission)
    serializer_class = EstimateDetailSerializer
    queryset = AdvertEstimate.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filter_class = AdvertEstimateFilter

    serializer_schema = {
        'create': EstimateCreateSerializer,
        'list_update': EstimateListUpdateSerializer
    }

    @list_route(methods=['post'])
    def list_update(self, request):
        """
        Обнволение списка сметы проекта.
        """
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class EventsViewSet(GenericViewSet, mixins.ListModelMixin):
    pagination_class = PageNumberPaginator
    filter_backends = (DjangoFilterBackend,)
    filter_class = ProjectEventFilter
    queryset = Event.objects.all()
    serializer_class = ProjectEventSerializer
