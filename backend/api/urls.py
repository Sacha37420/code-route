from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    MeView, ThemeViewSet, FicheCoursViewSet, SiteExterneViewSet,
    IllustrationsDisponiblesView,
)

router = DefaultRouter()
router.register('themes', ThemeViewSet, basename='theme')
router.register('fiches', FicheCoursViewSet, basename='fiche')
router.register('sites-externes', SiteExterneViewSet, basename='site-externe')

urlpatterns = [
    path('me/', MeView.as_view()),
    path('illustrations-disponibles/', IllustrationsDisponiblesView.as_view()),
    path('', include(router.urls)),
]
