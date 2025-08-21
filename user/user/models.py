from django.db import models
from django.contrib.auth.models import User

# creacion del perfil
class Profile(models.Model):
    #uso del perfil del mismo django
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    #agregar imagen
    profile_image = models.ImageField(upload_to='profile_pics', default='default.jpg')
    bio = models.TextField(max_length=500, blank=True)

    def __str__(self):
        return f'Perfil de {self.user.username}'