from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin

from cf_core.router import router
from cf_adverts.api.views import AdvertViewSet, EstimateViewSet, EventsViewSet

router.register('adverts', AdvertViewSet, base_name='adverts')
router.register('estimates', EstimateViewSet, base_name='estimates')
router.register('events', EventsViewSet, base_name='events')


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^api/v1/', include(router.get_urls(), namespace='api')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
