from rest_framework import serializers
from .models import Post, Like, User, Comment, Follow
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password


class UserSerializer(serializers.ModelSerializer):
    new_password = serializers.CharField(write_only=True, required=False)
    current_password = serializers.CharField(write_only=True, required=False)
    confirm_password = serializers.CharField(write_only=True, required=False)
    is_followed = serializers.SerializerMethodField()


    class Meta:
        model = User
        fields = ('id','username', 'email', 'password', 'new_password', 'confirm_password', 'current_password', 'is_followed')  # Incluye solo los campos del modelo User

    def validate(self, data):
        user = self.context['request'].user
        
        if 'new_password' in data:
            if not user.check_password(data.get('current_password')):
                raise serializers.ValidationError({"current_password": "La contraseña actual no es correcta."})
            if data.get('new_password') != data.get('confirm_password'):
                raise serializers.ValidationError({"confirm_password": "Las nuevas contraseñas no coinciden."})
            try:
                validate_password(data.get('new_password'))
            except ValidationError as e:
                raise serializers.ValidationError({"new_password": e.messages})
                
        return data
    
    def get_is_followed(self, obj):
        # Devuelve True si el usuario autenticado sigue a este usuario
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.followers.filter(id=request.user.id).exists()
        return False
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = super().create(validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
        if 'new_password' in validated_data:
            instance.set_password(validated_data['new_password'])
            validated_data.pop('new_password', None)
            validated_data.pop('confirm_password', None)
        return super().update(instance, validated_data)

class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = '__all__'

class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)  # Incluye el serializer del usuario para devolver el nombre de usuario
    post_id = serializers.PrimaryKeyRelatedField(source='post', queryset=Post.objects.all())  # Acepta el ID del post
    user_id = serializers.IntegerField(source='user.id', read_only=True)  # ID del usuario que hizo el comentario

    class Meta:
        model = Comment
        fields = ['id', 'content', 'created_at', 'post_id', 'user', 'user_id']  # Incluye el usuario y el post ID

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user  # Asigna el usuario actual al comentario
        return super().create(validated_data)

class PostSerializer(serializers.ModelSerializer):
    likes = serializers.SerializerMethodField()
    username = serializers.CharField(source='user.username', read_only=True)  # Campo de solo lectura
    comments = CommentSerializer(many=True, read_only=True)  # Incluye los comentarios
    image = serializers.ImageField(max_length=None, use_url=True, required=False)

    class Meta:
        model = Post
        fields = ('id', 'username', 'content', 'created_at', 'image', 'user', 'likes', 'comments')  # Incluye 'likes'

    def get_likes(self, obj):
        from .serializers import LikeSerializer  # Local import to avoid circular dependency
        likes = Like.objects.filter(post=obj)
        return LikeSerializer(likes, many=True).data
    
    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            return request.build_absolute_uri(obj.image.url)
        return None
    
class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = '__all__'

    def create(self, validated_data):
        follow, created = Follow.objects.get_or_create(
            follower=validated_data['follower'],
            following=validated_data['following']
        )
        return follow
    
    def validate(self, data):
        if data['follower'] == data['following']:
            raise serializers.ValidationError("No puedes seguirte a ti mismo.")
        return data
    
    