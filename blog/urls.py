from django.urls import path
from . import views

# El 'app_name' es importante para usar namespaces en tus plantillas
# Por ejemplo: {% url 'blog:post_list' %}
app_name = 'blog'

urlpatterns = [
    path('publicaciones/', views.post_list, name='publicaciones'),

    path('', views.dashboard, name='dashboard'),
]