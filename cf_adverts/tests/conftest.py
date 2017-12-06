import binascii
import copy

import pytest
from unittest.mock import patch

from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile


from cf_users.models import (
    User, Profile
)

from cf_adverts.models import (
    Advert, Category,
    AdvertEstimate)

from cf_core.models import (
    Status,
    Location,
)


@pytest.fixture
def user(db):
    return User.objects.create_user('test@example.com', 'pass')


@pytest.fixture
def profile(db, user):
    user.profile.base_type = Profile.TYPE_CHOICES.NCO
    user.profile.save(update_fields=['base_type'])
    return user.profile


@pytest.fixture
def category(db):
    return Category.objects.create(
        name='IT'
    )


@pytest.fixture
def another_category(db):
    return Category.objects.create(
        name='Biology'
    )


@pytest.fixture
def start_status(db):
    return Status.objects.create(
        name='start',
        position=0,
        content_type=ContentType.objects.get_for_model(Advert)
    )


@pytest.fixture
def final_status(db):
    return Status.objects.create(
        name='final',
        position=2,
        content_type=ContentType.objects.get_for_model(Advert)
    )


@pytest.fixture
def location(db):
    return Location.objects.create(
        name='Rostov'
    )


@pytest.fixture
def another_location(db):
    return Location.objects.create(
        name='Moscow'
    )


@pytest.fixture
def advert(db, user, start_status, location, category):
    return Advert.objects.create(**{
        'title': 'test title',
        'status': start_status,
        'short_description': 'test description',
        'category': category,
        'location': location,
        'total_amount': 1000,
        'owner': user
    })


@pytest.fixture
def another_advert(db, user, start_status, location, category):
    return Advert.objects.create(**{
        'title': 'test2 title',
        'status': start_status,
        'short_description': 'test2 description',
        'category': category,
        'location': location,
        'total_amount': 1001,
        'owner': user
    })


@pytest.fixture
def available_advert(db, advert):
    """
    Published Advert.
    """

    advert.is_available = Advert.MODERATE_STATUS_CHOICES.ALLOWED
    advert.save()
    return advert


@pytest.fixture
def picture(faker):
    """
    Hexadecimal representation of the picture.
    Used to generate the image of the filed FileField.
    
    Source: http://stackoverflow.com/a/30290754
    """

    sequence = binascii.unhexlify(
        'FFD8FFE000104A46494600010101004800480000FFDB004300FFFFFFFFFFFFFFFFFFFF'
        'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'
        'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFC2000B080001000101011100FFC400'
        '14100100000000000000000000000000000000FFDA0008010100013F10')
    return ContentFile(bytes(sequence), faker.file_name(extension='jpg'))


@pytest.fixture
def text_file(faker):
    """
    Text file as fixture for reusable.
    """

    return ContentFile(b'test', faker.file_name(extension='txt'))


@pytest.fixture
def advert_estimates(db, advert):
    return [
        AdvertEstimate.objects.create(title='es1', amount=100, advert=advert),
        AdvertEstimate.objects.create(title='es2', amount=101, advert=advert),
        AdvertEstimate.objects.create(title='es3', amount=102, advert=advert),
        AdvertEstimate.objects.create(title='es4', amount=103, advert=advert)
    ]
