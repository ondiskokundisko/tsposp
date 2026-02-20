from django.contrib import admin
from django.utils.html import format_html
from .models import Question, Answer

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 4
    fields = ['text', 'is_correct', 'order']

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['id', 'dimension_badge', 'short_text', 'difficulty', 'answer_count', 'is_active', 'created_at']
    list_filter = ['dimension', 'difficulty', 'is_active']
    search_fields = ['text']
    inlines = [AnswerInline]
    list_editable = ['is_active']
    list_per_page = 25

    def short_text(self, obj):
        return obj.text[:80] + '...' if len(obj.text) > 80 else obj.text
    short_text.short_description = 'Text otázky'

    def dimension_badge(self, obj):
        colors = {'NAM': '#3B82F6', 'UAJ': '#10B981', 'KM': '#8B5CF6'}
        color = colors.get(obj.dimension, '#6B7280')
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;border-radius:10px;font-size:11px">{}</span>',
            color, obj.get_dimension_display()
        )
    dimension_badge.short_description = 'Dimenze'

    def answer_count(self, obj):
        return obj.answers.count()
    answer_count.short_description = 'Odpovědi'
