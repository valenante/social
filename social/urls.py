# auth_app/urls.py

from django.urls import path
from .views import RegisterView, update_user, user_details,UserPostsView, UserProfileView, CheckFollowStatusView,CommentCreateView, CommentDetailView ,CommentListView,CurrentUserView ,UserSearchView ,CreatePostView, AllPostsView, LikePostView, UnlikePostView, FollowUserView, UnfollowUserView, DeletePostView, PostLikesCountView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('update_user/', update_user, name='update_user'),
    path('user_details/', user_details, name='user_details'),
    path('create-post/', CreatePostView.as_view(), name='posts'),
    path('user-posts/', UserPostsView.as_view(), name='user-posts'),
    path('all-posts/', AllPostsView.as_view(), name='all-posts'),
    path('like/', LikePostView.as_view(), name='like'),
    path('unlike/', UnlikePostView.as_view(), name='unlike'),
    path('comments/', CommentCreateView.as_view(), name='comment'),
    path('comments/<int:comment_id>/', CommentDetailView.as_view(), name='comment-detail'),
    path('posts/<int:post_id>/comments/', CommentListView.as_view(), name='comment'),
    path('users/<int:user_id>/follow/', FollowUserView.as_view(), name='follow-user'),
    path('users/<int:user_id>/unfollow/', UnfollowUserView.as_view(), name='unfollow-user'),
    path('home-posts/', AllPostsView.as_view(), name='home-posts'),
    path('search-users/', UserSearchView.as_view(), name='search-users'),
    path('user/', CurrentUserView.as_view(), name='current-user'),
    path('posts/<int:post_id>/delete/', DeletePostView.as_view(), name='delete-post'),
    path('like-status/<int:post_id>/', LikePostView.as_view(), name='like-status'),
    path('post/<int:post_id>/likes-count/', PostLikesCountView.as_view(), name='likes-count'),
    path('follow-status/<int:user_id>/', CheckFollowStatusView.as_view(), name='follow-status'),
    path('users/<int:user_id>/', UserProfileView.as_view(), name='user-profile'),
]

