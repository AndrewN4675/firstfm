from django.db import models
from django.conf import settings

# Create your models here.
# Database schema for linking last.fm accounts to website users
class LastfmLinking(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    lastfm_username = models.CharField(max_length=50, unique=True)
    sk = models.CharField(max_length=200)
    linked_at = models.DateTimeField(auto_now_add=True)