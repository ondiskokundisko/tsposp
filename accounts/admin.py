from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name = 'Profil'
    verbose_name_plural = 'Profil'
    fields = ['is_premium', 'premium_until', 'bio']


class UserAdmin(BaseUserAdmin):
    """Extends the default User admin with the UserProfile inline."""
    inlines = [UserProfileInline]
    list_display = BaseUserAdmin.list_display + ('is_premium_display',)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('groups', 'profile')

    def is_premium_display(self, obj):
        in_group = any(
            g.name == settings.PREMIUM_GROUP_NAME for g in obj.groups.all()
        )
        try:
            flag = obj.profile.is_premium
        except UserProfile.DoesNotExist:
            flag = False
        return in_group or flag
    is_premium_display.boolean = True
    is_premium_display.short_description = 'Prémiový'


# Re-register User with the extended admin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_premium', 'premium_until']
    list_filter = ['is_premium']

