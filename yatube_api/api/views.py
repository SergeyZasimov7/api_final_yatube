from django.contrib.auth.models import User
from rest_framework import permissions, status, viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response

from api.serializers import (CommentSerializer, FollowSerializer,
                             GroupSerializer, PostSerializer)
from posts.models import Comment, Follow, Group, Post


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = LimitOffsetPagination

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def destroy(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)


class GroupViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        post = self.get_post()
        return Comment.objects.filter(post=post)

    def get_post(self):
        post_pk = self.kwargs.get('post_pk')
        return Post.objects.get(pk=post_pk)

    def perform_create(self, serializer):
        post = self.get_post()
        serializer.save(author=self.request.user, post=post)

    def update(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.author != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(
            comment,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.author != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(
            comment,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.author != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)


class FollowViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = FollowSerializer
    queryset = Follow.objects.all()

    def get_queryset(self):
        user = self.request.user
        queryset = self.queryset.filter(user=user)
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(following__username=search)
        return queryset

    def list(self, request):
        queryset = self.get_queryset()
        serializer = FollowSerializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        following_username = request.data.get('following')
        try:
            following_user = User.objects.get(username=following_username)
        except User.DoesNotExist:
            return Response(
                {"error": "User does not exist"},
                status=status.HTTP_400_BAD_REQUEST
            )
        if following_user == request.user:
            return Response(
                {"error": "You cannot follow yourself"},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            follow = Follow.objects.get(
                user=request.user,
                following=following_user
            )
            return Response(
                {"error": "You are already following this user"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Follow.DoesNotExist:
            follow = Follow.objects.create(
                user=request.user,
                following=following_user
            )
            serializer = FollowSerializer(follow)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
