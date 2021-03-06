import logging

from django.db import transaction
from celery import shared_task

from cf_adverts.models import DraftAdvert

logger = logging.getLogger(__name__)


@shared_task()
def process_apply_draft_project(draft_id):
    """
    Apply draft changes to original.
    
    :param draft_id: int
    :return: 
    """

    with transaction.atomic():
        draft = DraftAdvert.objects.get(
            pk=draft_id,
            process_status=DraftAdvert.MODERATE_PROCESS_TYPES.APPLY
        )
        draft.apply_draft_to_origin()
        draft.delete()
