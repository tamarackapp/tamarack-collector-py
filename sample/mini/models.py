from django.db import models
from django.contrib.auth.models import User

class NewsItem(models.Model):
    title = models.CharField(max_length=255)
    body_text = models.TextField()

    created_by = models.ForeignKey(User)
