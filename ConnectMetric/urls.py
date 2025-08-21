from django.contrib import admin
from django.urls import path, include
from blog import views as blogViews

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('blog.urls', namespace='blog')),
    path('user/', include('user.urls', namespace='user')),
     path('auth/', include('authentication.urls', namespace='authentication')),
]