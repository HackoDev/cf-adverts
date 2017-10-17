import mock
import pytest

from cf_adverts.models import (
    Advert, DraftAdvert, Event
)


@pytest.mark.django_db
class TestProjectModel:

    def test_str_method(self, advert):
        assert str(advert) == advert.title

    def test_get_collected_amount_method(self, advert):
        advert.collected_amount = 123456789
        value = advert.get_collected_amount()
        assert isinstance(value, str)
        assert value == '123 456 789'

    def test_get_total_amount_method(self, advert):
        advert.total_amount = 123456789
        value = advert.get_total_amount()
        assert isinstance(value, str)
        assert value == '123 456 789'

    def test_create_draft_method(self, available_advert):

        draft = available_advert.get_or_create_draft()

        assert isinstance(draft, Advert)
        assert draft.id != available_advert.id

        for field in DraftAdvert._meta.fields:
            if field.name in DraftAdvert.exclude_fields:
                continue
            assert getattr(draft, field.name) == getattr(available_advert,
                                                         field.name)

    def test_draft_applying(self, available_advert):

        draft = available_advert.get_or_create_draft()

        values_data = {
            'title': 'new test title',
            'short_description': 'new test description',
            'total_amount': 999999
        }

        for field_name, new_value in values_data.items():
            setattr(draft, field_name, new_value)
            assert getattr(available_advert, field_name) != new_value

        draft.save()

        original = draft.apply_draft_to_origin()

        assert original.id == available_advert.id

        available_advert.refresh_from_db()

        for key in values_data.keys():
            assert getattr(available_advert, key) == getattr(draft, key)
