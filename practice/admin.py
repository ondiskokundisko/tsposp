from django.contrib import admin
from .models import PracticeTest, TestAttempt, UserAnswer

class UserAnswerInline(admin.TabularInline):
    model = UserAnswer
    extra = 0
    readonly_fields = ['question', 'selected_answer', 'is_correct', 'answered_at']

@admin.register(PracticeTest)
class PracticeTestAdmin(admin.ModelAdmin):
    list_display = ['name', 'time_limit_minutes', 'question_count', 'is_active', 'created_at']
    filter_horizontal = ['questions']

    def question_count(self, obj):
        return obj.questions.count()
    question_count.short_description = 'Počet otázek'

@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):
    list_display = ['user', 'test', 'dimension', 'score', 'total_questions', 'percentage_display', 'started_at']
    list_filter = ['attempt_type', 'dimension']
    inlines = [UserAnswerInline]

    def percentage_display(self, obj):
        return f"{obj.percentage}%"
    percentage_display.short_description = 'Skóre'
