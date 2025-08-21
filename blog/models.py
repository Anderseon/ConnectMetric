from django.db import models

from django.contrib.auth.models import User

# El modelo Post para las publicaciones del blog.
class Post(models.Model):
   
    title = models.CharField(max_length=200, verbose_name="Título")
    
    content = models.TextField(verbose_name="Contenido")
    
    published_date = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Publicación")
    
    # ForeignKey para vincular el post a un autor.
    # Si el usuario se elimina, también se eliminarán sus posts.
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Autor")

    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "Publicación"
        verbose_name_plural = "Publicaciones"
        # Ordena las publicaciones por fecha de manera descendente
        ordering = ['-published_date']