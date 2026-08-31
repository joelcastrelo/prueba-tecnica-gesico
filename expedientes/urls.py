from rest_framework.routers import DefaultRouter

from .views import ExpedienteViewSet

router = DefaultRouter()
router.register(r"expedientes", ExpedienteViewSet, basename="expediente")

urlpatterns = router.urls
