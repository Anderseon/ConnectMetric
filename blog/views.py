from django.shortcuts import render
from .models import Post 

def dashboard(request):
    return render(request, 'blog/dashboard.html')

def post_list(request):
    # Obtiene todas las publicaciones de la base de datos
    posts = Post.objects.all()
    return render(request, 'blog/post_list.html', {'posts': posts})