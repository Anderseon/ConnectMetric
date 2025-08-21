from django.shortcuts import render
from .models import Profile

def view_profile(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = None

    return render(request, 'user/profile.html', {'profile': profile})