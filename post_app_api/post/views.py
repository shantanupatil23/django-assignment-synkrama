"""
Views for the post APIs
"""
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from post.models import Post
from post import serializers


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
        """Create a new post."""
        serializer.save(author=self.request.user)
