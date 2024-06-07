from django.contrib.auth.models import User
from posts.models import Comment, Follow, Group, Post
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class PostSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    class Meta:
        model = Post
        fields = '__all__'


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = '__all__'


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        read_only=True, slug_field='username'
    )

    class Meta:
        fields = '__all__'
        model = Comment
        read_only_fields = ('post',)


class FollowSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )
    following = serializers.SlugRelatedField(
        slug_field='username',
        queryset=User.objects.all()
    )

    def create(self, validated_data):
        user = self.context['request'].user
        follow = Follow.objects.create(user=user, **validated_data)
        return follow

    def validate(self, data):
        user = self.context['request'].user
        following_user = data['following']
        if user == following_user:
            raise ValidationError({'following': 'You cannot follow yourself.'})
        if Follow.objects.filter(user=user, following=following_user).exists():
            raise ValidationError(
                {'following': 'You are already following this user.'}
            )
        return data

    class Meta:
        model = Follow
        fields = '__all__'
