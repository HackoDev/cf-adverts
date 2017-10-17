import logging

from .event import Event
from ..signals import (
    project_created, project_edited, project_approved
)

logger = logging.getLogger(__name__)


def handle_logger_event(advert, base_type, description, percent):
    event = Event.objects.create(
        advert=advert,
        base_type=base_type,
        description=description,
        percent=percent
    )
    logger.info(
        "New event #{pk}. "
        "Type: '{base_type}'. "
        "Project: {advert}. "
        "Description: {description}. "
        "Percent: {percent}".format(
            pk=event.id,
            advert=advert,
            base_type=base_type,
            description=description,
            percent=percent
        )
    )


def payment_signal_receiver(**kwargs):
    payment = kwargs.get('sender')
    description = '{full_name} внес пожертвование'.format(
        full_name=payment.full_name or payment.email
    )
    event_kwargs = {
        'advert': payment.project,
        'base_type': Event.TYPE_CHOICES.PAYMENT_RECEIVED,
        'description': description,
        'percent': payment.project.get_collected_percent()
    }
    handle_logger_event(**event_kwargs)


def resource_signal_receiver(**kwargs):
    resource = kwargs.get('sender')
    description = '{full_name} помог ресурсами/материалами'.format(
        full_name=resource.full_name or resource.email
    )

    event_kwargs = dict(
        advert=resource.project,
        base_type=Event.TYPE_CHOICES.RESOURCE_RECEIVED,
        description=description,
        percent=resource.project.get_collected_percent()
    )

    handle_logger_event(**event_kwargs)


def percent_signal_receiver(**kwargs):
    payment, percent = kwargs.get('sender'), kwargs.get('percent')
    if percent == 100:
        description = '{percent} Цель достигнута'.format(
            percent=percent
        )
    else:
        description = '{percent} процентов цели было достигнуто'.format(
            percent=percent
        )
    event_kwargs = dict(
        base_type=Event.TYPE_CHOICES.PERCENT_CHANGED,
        advert=payment.project,
        description=description,
        percent=percent
    )

    handle_logger_event(**event_kwargs)


def project_create_receiver(**kwargs):
    project = kwargs.get('sender')
    description = 'Проект создан'

    event_kwargs = dict(
        base_type=Event.TYPE_CHOICES.PROJECT_CREATED,
        advert=project,
        description=description,
        percent=project.get_collected_percent()
    )

    handle_logger_event(**event_kwargs)


def project_edit_receiver(**kwargs):
    advert = kwargs.get('sender')
    description = 'Проект отредактирован'

    event_kwargs = dict(
        base_type=Event.TYPE_CHOICES.PROJECT_EDITED,
        advert=advert,
        description=description,
        percent=advert.get_collected_percent()
    )

    handle_logger_event(**event_kwargs)


def role_join_receiver(**kwargs):
    role = kwargs.get('sender')
    description = '{short_name} присоединился к проекту в качестве {role_name}'.format(
        short_name=role.user.get_short_name(),
        role_name='{}а'.format(role.get_role_name())
    )

    event_kwargs = dict(
        base_type=Event.TYPE_CHOICES.PROJECT_EDITED,
        advert=role.project,
        description=description,
        percent=role.project.get_collected_percent()
    )

    handle_logger_event(**event_kwargs)


def project_approve_receiver(**kwargs):
    role = kwargs.get('sender')
    description = 'Проект прошел проверку'

    event_kwargs = dict(
        base_type=Event.TYPE_CHOICES.PROJECT_EDITED,
        advert=role.project,
        description=description,
        percent=role.project.get_collected_percent()
    )

    handle_logger_event(**event_kwargs)


project_edited.connect(receiver=project_edit_receiver)
project_created.connect(receiver=project_create_receiver)
project_approved.connect(receiver=project_approve_receiver)
