"""
Views for the post APIs
"""
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
)

from django.core.signals import Signal
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings

from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated

from post.models import Post
from post import serializers

post_created = Signal()


@receiver(post_created)
def send_post_created_email(post, **kwargs):
    subject = 'New post created'
    message = (f"Hi Django User {post.author.email},"
               f"\n\nYour post \"{post.title}\""
               " has been created successfully.")
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [post.author.email]

    send_mail(subject, message, from_email, recipient_list)


class CustomPagination(PageNumberPagination):
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 50


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'title',
                OpenApiTypes.STR,
                description='Title to filter',
            ),
            OpenApiParameter(
                'body',
                OpenApiTypes.STR,
                description='Body to filter',
            ),
        ]
    )
)
class PostViewSet(viewsets.ModelViewSet):
    """View for manage post APIs."""
    serializer_class = serializers.PostSerializer
    queryset = Post.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination

    def get_queryset(self):
        """Retrieve posts for authenticated user."""
        title = self.request.query_params.get('title')
        body = self.request.query_params.get('body')
        queryset = self.queryset
        if title:
            queryset = queryset.filter(title=title)
        if body:
            queryset = queryset.filter(body=body)
        return queryset.filter(author=self.request.user).order_by('-id')

    def perform_create(self, serializer):
        """Create a new post and send signal."""
        post = serializer.save(author=self.request.user)

        post_created.send(sender=self.__class__, post=post)
