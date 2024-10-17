from rest_framework import status, views
from rest_framework.response import Response
from django.contrib.auth.models import User
from .serializers import UserSerializer
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, permissions
from .models import Post
from .serializers import PostSerializer
from rest_framework.views import APIView
from .models import Like, Follow
from .serializers import LikeSerializer
from .models import Comment
from .serializers import CommentSerializer
from .serializers import FollowSerializer
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
import logging
User = get_user_model()

class CurrentUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }
        return Response(user_data, status=status.HTTP_200_OK)

class RegisterView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

class LoginView(views.APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        
        if user is not None:
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
            return Response({
                'access': access_token,
                'refresh': refresh_token,
                'user_id': user.id
            }, status=status.HTTP_200_OK)
        return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_user(request):
    serializer = UserSerializer(request.user, data=request.data, partial=True, context={'request': request})
    if serializer.is_valid():
        user = serializer.save()
        return Response({"detail": "Detalles del usuario actualizados con éxito."}, status=status.HTTP_200_OK)
    else:
        print(serializer.errors)  # Añade esta línea para depurar errores
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_details(request):
    user = request.user
    serializer = UserSerializer(user)
    return Response(serializer.data)


class CreatePostView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data.copy()
        data['user'] = request.user.id
        serializer = PostSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)
    
class UserPostsView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Post.objects.filter(user=user)
    
class AllPostsView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            # Obtener los IDs de los usuarios que el usuario está siguiendo
            following_users_ids = user.following.values_list('following_id', flat=True)
            
            # Obtener los posts de los usuarios seguidos
            following_posts = Post.objects.filter(user_id__in=following_users_ids)
            
            # Obtener los posts del propio usuario
            user_posts = Post.objects.filter(user=user)
            
            # Unir los dos conjuntos de resultados
            return following_posts.union(user_posts)
        else:
            # Si no está autenticado, no se devuelven posts
            return Post.objects.none()
        

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            posts = Post.objects.filter(user=user)  # Obtener los posts del usuario
            serialized_posts = PostSerializer(posts, many=True)  # Serializar los posts
            
            data = {
                'username': user.username,
                'email': user.email,
                'is_followed': user.followers.filter(id=request.user.id).exists(),
                'followers_count': user.followers.count(),  # Contar los seguidores
                'following_count': user.following.count(),  # Contar los seguidos
                'posts': serialized_posts.data
            }
            return Response(data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User does not exist'}, status=status.HTTP_404_NOT_FOUND)


class LikePostView(generics.CreateAPIView):
    queryset = Like.objects.all()
    serializer_class = LikeSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        post_id = request.data.get('post_id')
        post = Post.objects.get(id=post_id)

        if Like.objects.filter(user=user, post=post).exists():
            return Response({"detail": "You already liked this post."}, status=status.HTTP_400_BAD_REQUEST)
        
        Like.objects.create(user=user, post=post)
        return Response({"detail": "Post liked successfully."}, status=status.HTTP_201_CREATED)
    
    def get(self, request, post_id):
        user = request.user
        try:
            post = Post.objects.get(id=post_id)
            has_liked = Like.objects.filter(user=user, post=post).exists()
            return Response({'liked': has_liked})
        except Post.DoesNotExist:
            return Response({'error': 'Post not found'}, status=404)
        
class PostLikesCountView(APIView):
    def get(self, request, post_id):
        # Obtener el post
        post = get_object_or_404(Post, id=post_id)
        
        # Contar el número de "likes" asociados con el post
        likes_count = Like.objects.filter(post=post).count()
        
        # Devolver la cantidad de likes en la respuesta
        return Response({'likesCount': likes_count}, status=status.HTTP_200_OK)

class UnlikePostView(generics.DestroyAPIView):
    queryset = Like.objects.all()
    serializer_class = LikeSerializer
    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        user = request.user
        post_id = request.data.get('post_id')
        post = Post.objects.get(id=post_id)

        like = Like.objects.filter(user=user, post=post).first()
        if like:
            like.delete()
            return Response({"detail": "Post unliked successfully."}, status=status.HTTP_204_NO_CONTENT)
        return Response({"detail": "You haven't liked this post."}, status=status.HTTP_400_BAD_REQUEST)
    
class CommentDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        comment_id = kwargs.get('comment_id')
        try:
            comment = Comment.objects.get(id=comment_id)
        except Comment.DoesNotExist:
            return Response({'error': 'Comment not found'}, status=status.HTTP_404_NOT_FOUND)

        post = comment.post
        user = request.user

        # Verificar si el usuario es el autor del comentario o el autor del post
        if comment.user == user or post.user == user:
            comment.delete()
            return Response({'status': 'Comment deleted'}, status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({'error': 'You do not have permission to delete this comment'}, status=status.HTTP_403_FORBIDDEN)
    
# En tu vista para añadir comentarios
class CommentCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = CommentSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            serializer.save(user=request.user)  # Pasamos el usuario actual al save
            return Response(serializer.data, status=201)
        
        return Response(serializer.errors, status=400)



class CommentListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, post_id):
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response({"error": "Post not found"}, status=404)

        comments = Comment.objects.filter(post=post)
        serializer = CommentSerializer(comments, many=True)

        response_data = {
            'post_owner_id': post.user.id,  # ID del dueño del post
            'comments': serializer.data,  # Comentarios con los IDs del dueño de cada comentario
            'current_user_id': request.user.id  # ID del usuario en sesión
        }

        return Response(response_data)

class FollowUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        follower = request.user  # Usuario autenticado
        user_id_to_follow = kwargs['user_id']  # ID del usuario que queremos seguir

        # Registro para verificar el ID del usuario a seguir
        logging.info(f"User ID to follow: {user_id_to_follow}")

        if follower.id == user_id_to_follow:
            return Response({'error': 'You cannot follow yourself'}, status=400)

        try:
            following = User.objects.get(id=user_id_to_follow)
        except User.DoesNotExist:
            return Response({'error': 'User does not exist'}, status=404)

        # Verifica si la relación ya existe
        if Follow.objects.filter(follower=follower, following=following).exists():
            return Response({'error': 'You are already following this user'}, status=400)

        serializer = FollowSerializer(data={'follower': follower.id, 'following': following.id})

        if serializer.is_valid():
            serializer.save()
            return Response({'status': 'following'}, status=201)
        return Response(serializer.errors, status=400)
    

class DeletePostView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, post_id):
        try:
            post = Post.objects.get(id=post_id, user=request.user)
        except Post.DoesNotExist:
            return Response({'error': 'Post not found or you do not have permission to delete it.'}, status=404)

        post.delete()
        return Response({'message': 'Post deleted successfully'}, status=204)


class UnfollowUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        follower = request.user
        try:
            following = User.objects.get(id=kwargs['user_id'])
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)

        follow_instance = Follow.objects.filter(follower=follower, following=following)
        if follow_instance.exists():
            follow_instance.delete()
            return Response({'status': 'unfollowed'}, status=204)
        return Response({'status': 'not_following'}, status=400)
    
class UserSearchView(generics.ListAPIView):
    serializer_class = UserSerializer
    
    def get_queryset(self):
        query = self.request.query_params.get('query', '')
        return User.objects.filter(username__icontains=query)
    
class CheckFollowStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user_id_to_check = kwargs['user_id']
        follower = request.user  # Usuario autenticado

        try:
            following = User.objects.get(id=user_id_to_check)
        except User.DoesNotExist:
            return Response({'error': 'User does not exist'}, status=404)

        is_followed = Follow.objects.filter(follower=follower, following=following).exists()
        return Response({'is_followed': is_followed}, status=200)
