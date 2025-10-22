from django.urls import path
from .views import lastfm_start, lastfm_callback, itsMe, csrfTokenView

urlpatterns = [
    path('lastfm/start/', lastfm_start, name='lastfm_start'),
    path('lastfm/callback/', lastfm_callback, name='lastfm_callback'),
    path('csrf/', csrfTokenView, name='csrf_token'),
    path('itsme/', itsMe, name='its_me'),
]