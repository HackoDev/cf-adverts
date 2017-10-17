import json

import copy
import mock
import pytest
from django.test.client import MULTIPART_CONTENT, BOUNDARY, encode_multipart
from django.urls import reverse

from rest_framework import status, exceptions, test
from rest_framework.test import force_authenticate

from cf_adverts.api import (
    AdvertViewSet,
    EstimateViewSet,
    EventsViewSet
)

from cf_adverts.api.serializers import (
    AdvertCreateSerializer, EstimateListUpdateSerializer
)

from cf_adverts.models import Advert

JSON_TYPE = 'application/json'


class BaseTestViewSetMixin(object):
    """
    Базовый класс для тестирвоание ViewSet-ов.
    """

    viewset = None

    def get_response_as_viewset(self, actions, request, **extra_kwargs):
        kwargs = {'request': request}
        if extra_kwargs:
            kwargs.update(extra_kwargs)
        response = self.viewset.as_view(actions)(**kwargs)
        response.render()
        return response


@pytest.mark.django_db
class TestProjectAPI(BaseTestViewSetMixin):
    viewset = AdvertViewSet

    def test_create_project(self, rf, profile, category, location,
                            picture, start_status):
        project_data = {
            'title': 'test title',
            'logo': copy.deepcopy(picture),
            'small_logo': copy.deepcopy(picture),
            'short_description': 'test description',
            'category': category.id,
            'location': location.id,
            'total_amount': 1000
        }
        req = rf.post('/api/v1/adverts/',
                      data=project_data,
                      content_type=MULTIPART_CONTENT)
        force_authenticate(req, user=profile.user)
        response = self.get_response_as_viewset({'post': 'create'}, req)

        expected_fields = set(AdvertCreateSerializer.Meta.fields)

        assert set(response.data.keys()) == expected_fields
        assert response.status_code == status.HTTP_201_CREATED

    def test_failed_file_create_project(self, rf, profile, start_status,
                                        category, location, text_file):
        project_data = {
            'title': 'test title',
            'short_description': 'test description',
            'category': category.id,
            'location': location.id,
            'total_amount': 1000,
            'logo': copy.deepcopy(text_file),
            'small_logo': copy.deepcopy(text_file),
        }
        req = rf.post(reverse('api:adverts-list'),
                      data=project_data,
                      content_type=MULTIPART_CONTENT)
        force_authenticate(req, user=profile.user)
        response = self.get_response_as_viewset({'post': 'create'}, req)

        assert response.data.keys() == {'logo', 'small_logo'}
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_fail_create_project(self, rf, user, category, start_status,
                                 location):
        req = rf.post(reverse('api:adverts-list'), data=json.dumps({}),
                      content_type=JSON_TYPE)
        force_authenticate(req, user=user)
        response = self.get_response_as_viewset({'post': 'create'}, req)
        expected_fields = set(AdvertCreateSerializer.Meta.fields) ^ {'id'}

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data.keys() == expected_fields

    def test_update_project(self, rf, profile, advert, another_location,
                            another_category,
                            text_file):
        project_data = {
            'description': 'test desc1',
            'short_description': 'test short desc1',
            'title': 'test title1',
            'location': another_location.id,
            'category': another_category.id
        }
        for key, value in project_data.items():
            req = rf.put(reverse('api:adverts-detail', args=[advert.id]),
                         data=json.dumps({key: value}),
                         content_type=JSON_TYPE)
            force_authenticate(req, user=profile.user)
            response = self.get_response_as_viewset({'put': 'update'}, req,
                                                    pk=advert.id)

            assert response.status_code == status.HTTP_200_OK
            assert response.data.get(key) == value
        assert Advert.objects.filter(**project_data).exists()

    def test_video_update_project(self, rf, profile, advert, text_file):
        project_data = {
            'video': 'test_invalid_url'
        }
        req = rf.put(reverse('api:adverts-detail',
                             args=[advert.id]).format(advert.id),
                     data=json.dumps(project_data),
                     content_type=JSON_TYPE)
        force_authenticate(req, user=profile.user)
        response = self.get_response_as_viewset({'put': 'update'}, req,
                                                pk=advert.id)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['video'] is not None

    def test_logo_update_project(self, rf, profile, advert, picture):
        project_data = {
            'logo': copy.deepcopy(picture)
        }
        req = rf.put(reverse('api:adverts-detail',
                             args=[advert.id]).format(advert.id),
                     data=encode_multipart(BOUNDARY, project_data),
                     content_type=MULTIPART_CONTENT)
        force_authenticate(req, user=profile.user)
        response = self.get_response_as_viewset({'put': 'update'}, req,
                                                pk=advert.id)

        assert response.status_code == status.HTTP_200_OK

    def test_small_logo_update_project(self, rf, profile, advert, picture):
        project_data = {
            'small_logo': copy.deepcopy(picture)
        }
        req = rf.put(reverse('api:adverts-detail',
                             args=[advert.id]).format(advert.id),
                     data=encode_multipart(BOUNDARY, project_data),
                     content_type=MULTIPART_CONTENT)
        force_authenticate(req, user=profile.user)
        response = self.get_response_as_viewset({'put': 'update'}, req,
                                                pk=advert.id)

    def test_small_logo_failed_update_project(self, rf, profile, advert, text_file):
        project_data = {
            'small_logo': copy.deepcopy(text_file)
        }
        req = rf.put(reverse('api:adverts-detail',
                             args=[advert.id]).format(advert.id),
                     data=encode_multipart(BOUNDARY, project_data),
                     content_type=MULTIPART_CONTENT)
        force_authenticate(req, user=profile.user)
        response = self.get_response_as_viewset({'put': 'update'}, req,
                                                pk=advert.id)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'small_logo' in response.data

    def test_get_project_as_draft(self, rf, profile, available_advert):
        req = rf.get(
            reverse('api:adverts-detail', args=[available_advert.id])
        )
        force_authenticate(req, user=profile.user)

        response = self.get_response_as_viewset({'get': 'retrieve'}, req,
                                                pk=available_advert.id)
        draft = available_advert.get_or_create_draft()

        assert response.data['id'] != available_advert.id
        assert response.data['id'] == draft.id

    def test_send_project_to_approve(self, rf, profile, available_advert):
        draft = available_advert.get_or_create_draft()

        assert draft.origin == available_advert

        req = rf.post(reverse('api:adverts-send-to-moderation',
                              args=[draft.id]))
        force_authenticate(req, user=profile.user)

        response = self.get_response_as_viewset({'post': 'send_to_moderation'},
                                                req, pk=draft.id)

        assert response.status_code == status.HTTP_200_OK

        draft.refresh_from_db()

        assert draft.process_status == Advert.MODERATE_PROCESS_TYPES.CHECK


@pytest.mark.django_db
class TestAdvertEstimate(BaseTestViewSetMixin):

    viewset = EstimateViewSet

    def test_get_advert_estimates(self, rf, profile, advert, another_advert,
                                  advert_estimates):

        test_data = (
            (advert.id, len(advert_estimates)),
            (another_advert.id, 0)
        )

        for advert_id, result_length in test_data:
            req = rf.get(reverse('api:estimates-list') + '?advert={}'.format(
                advert_id
            ))
            force_authenticate(req, profile.user)
            response = self.get_response_as_viewset({'get': 'list'}, req)

            assert response.status_code == 200
            assert isinstance(response.data, list)
            assert len(response.data) == result_length

    def test_get_filtered_estimates(self, rf, profile, advert, advert_estimates):

        request_data = EstimateListUpdateSerializer(advert_estimates,
                                                    many=True).data
        req = rf.post(
            reverse('api:estimates-list-update'),
            data=json.dumps(request_data),
            content_type=JSON_TYPE
        )
        force_authenticate(req, profile.user)
        response = self.get_response_as_viewset({'post': 'list_update'}, req)

        assert response.status_code == 200

        for est in advert_estimates:
            old_value = est.amount
            est.refresh_from_db()
            assert old_value == est.amount
