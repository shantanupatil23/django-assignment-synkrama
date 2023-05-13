"""
Post models.
"""
from django.conf import settings
from django.db import models


class Post(models.Model):
    """Post object."""
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)

    def __str__(self):
        return self.title
