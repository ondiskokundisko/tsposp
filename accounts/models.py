from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    is_premium = models.BooleanField(default=False)
    premium_until = models.DateField(null=True, blank=True)
    bio = models.TextField(blank=True)

    def __str__(self):
        return f"Profil: {self.user.username}"

    class Meta:
        verbose_name = 'Profil uživatele'
        verbose_name_plural = 'Profily uživatelů'
