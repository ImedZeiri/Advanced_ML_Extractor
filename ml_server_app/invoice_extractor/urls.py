from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import InvoiceViewSet, InvoiceTemplateViewSet, TrainingDataViewSet

# Création du router
router = DefaultRouter()
router.register(r'invoices', InvoiceViewSet)
router.register(r'templates', InvoiceTemplateViewSet)
router.register(r'training-data', TrainingDataViewSet)

# URLs de l'API
urlpatterns = [
    path('', include(router.urls)),
]