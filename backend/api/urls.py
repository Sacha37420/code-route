from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    MeView, ThemeViewSet, FicheCoursViewSet, SiteExterneViewSet,
    IllustrationsDisponiblesView, QuestionViewSet,
    QuizDemarrerView, QuizRepondreView, QuizTerminerView,
    QuizHistoriqueView, QuizSessionDetailView,
)

router = DefaultRouter()
router.register('themes', ThemeViewSet, basename='theme')
router.register('fiches', FicheCoursViewSet, basename='fiche')
router.register('sites-externes', SiteExterneViewSet, basename='site-externe')
router.register('questions', QuestionViewSet, basename='question')

urlpatterns = [
    path('me/', MeView.as_view()),
    path('illustrations-disponibles/', IllustrationsDisponiblesView.as_view()),

    path('quiz/demarrer/', QuizDemarrerView.as_view()),
    path('quiz/historique/', QuizHistoriqueView.as_view()),
    path('quiz/<int:session_id>/', QuizSessionDetailView.as_view()),
    path('quiz/<int:session_id>/repondre/', QuizRepondreView.as_view()),
    path('quiz/<int:session_id>/terminer/', QuizTerminerView.as_view()),

    path('', include(router.urls)),
]
