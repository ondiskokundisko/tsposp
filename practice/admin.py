from django.contrib import admin
from .models import TestAttempt, UserAnswer, QuestionProgress


class UserAnswerInline(admin.TabularInline):
    model = UserAnswer
    extra = 0
    readonly_fields = ['question', 'selected_answer', 'is_correct', 'answered_at']


@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):
    list_display = ['user', 'dimension', 'score', 'total_questions', 'percentage_display', 'started_at']
    list_filter = ['dimension']
    readonly_fields = ['question_ids', 'session_key']
    inlines = [UserAnswerInline]

    def percentage_display(self, obj):
        return f"{obj.percentage}%"
    percentage_display.short_description = 'Skóre'


@admin.register(QuestionProgress)
class QuestionProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'question', 'is_completed', 'last_visited']
    list_filter = ['is_completed']
