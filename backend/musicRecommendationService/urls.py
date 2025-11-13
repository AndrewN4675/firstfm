from django.urls import path
from .views import lastfm_start, lastfm_callback, itsMe, csrfTokenView, RecommendationView

urlpatterns = [
    path('csrf/', csrfTokenView, name='csrf_token'),
    path('lastfm/start/', lastfm_start, name='lastfm_start'),
    path('lastfm/callback/', lastfm_callback, name='lastfm_callback'),
    path('itsme/', itsMe, name='its_me'),
    path('recommendation/', RecommendationView.as_view(), name='recommendation'),
]