from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InvoiceViewSet, InvoiceAnnotationViewSet, TrainingJobViewSet
from .ml_views import model_info, export_annotations

router = DefaultRouter()
router.register(r'invoices', InvoiceViewSet)
router.register(r'annotations', InvoiceAnnotationViewSet)
router.register(r'training-jobs', TrainingJobViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('ml/model-info/', model_info, name='model-info'),
    path('ml/export-annotations/', export_annotations, name='export-annotations'),
]