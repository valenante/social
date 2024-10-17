#Post models

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth.models import AbstractUser

class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    image = models.ImageField(upload_to='posts/', null=True, blank=True)

    def __str__(self):
        return f'{self.user.username} - {self.created_at}'

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name='likes', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')  # Garantiza que un usuario solo pueda dar like a un post una vez

    def __str__(self):
        return f'{self.user.username} liked {self.post.id}'
    
class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'Comment by {self.user.username} on {self.post.id}'
    
class Follow(models.Model):
    follower = models.ForeignKey(User, related_name='following', on_delete=models.CASCADE)
    following = models.ForeignKey(User, related_name='followers', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('follower', 'following')
    
    def __str__(self):
        return f'{self.follower.username} follows {self.following.username}'
    
class User(AbstractUser):
    # Relación para los seguidores
    followers = models.ManyToManyField('self', related_name='following', symmetrical=False)

    # Cambiar el related_name de los grupos y permisos para evitar conflictos
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='social_user_set',  # Cambiar el related_name aquí
        blank=True,
        help_text='The groups this user belongs to.',
        related_query_name='social_user'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='social_user_permissions_set',  # Cambiar el related_name aquí
        blank=True,
        help_text='Specific permissions for this user.',
        related_query_name='social_user_permission'
    )