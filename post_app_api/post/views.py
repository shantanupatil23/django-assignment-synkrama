"""
Views for the post APIs
"""
from django.core.signals import Signal
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings

from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from post.models import Post
from post import serializers

post_created = Signal()


@receiver(post_created)
def send_post_created_email(post, **kwargs):
    subject = 'New post created'
    message=f'Hi Django User {post.author.email},\n\n'
    message+=f'Your post "{post.title}" has been created successfully.'
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [post.author.email]

    send_mail(subject, message, from_email, recipient_list)


class PostViewSet(viewsets.ModelViewSet):
    """View for manage post APIs."""
    serializer_class = serializers.PostSerializer
    queryset = Post.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve posts for authenticated user."""
        return self.queryset.filter(author=self.request.user).order_by('-id')

    def perform_create(self, serializer):
        """Create a new post and send signal."""
        post = serializer.save(author=self.request.user)

        post_created.send(sender=self.__class__, post=post)
