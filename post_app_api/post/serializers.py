"""
Serializers for post APIs
"""
from rest_framework import serializers

from post.models import Post


class PostSerializer(serializers.ModelSerializer):
    """Serializer for posts."""

    class Meta:
        model = Post
        fields = ['id', 'title', 'body']
        read_only_fields = ['id']

    def create(self, validated_data):
        """Create a post."""
        post = Post.objects.create(**validated_data)

        return post

    def update(self, instance, validated_data):
        """Update post."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
