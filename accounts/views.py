from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg
from .models import UserProfile
from practice.models import TestAttempt

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            login(request, user)
            messages.success(request, 'Vítejte! Váš účet byl úspěšně vytvořen.')
            return redirect('practice:dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def profile(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    attempts = TestAttempt.objects.filter(user=request.user).order_by('-started_at')[:10]
    total_attempts = TestAttempt.objects.filter(user=request.user).count()
    avg_score = 0
    if total_attempts > 0:
        avg = TestAttempt.objects.filter(user=request.user, total_questions__gt=0).aggregate(
            avg=Avg('score')
        )['avg']
        avg_score = round(avg, 1) if avg else 0
    return render(request, 'accounts/profile.html', {
        'profile': profile,
        'attempts': attempts,
        'total_attempts': total_attempts,
        'avg_score': avg_score,
    })
