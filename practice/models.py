from django.db import models
from django.contrib.auth.models import User
from questions.models import Question, DIMENSION_CHOICES

class PracticeTest(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    questions = models.ManyToManyField(Question, blank=True)
    time_limit_minutes = models.PositiveIntegerField(default=45)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Zkušební test'
        verbose_name_plural = 'Zkušební testy'

class TestAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attempts')
    test = models.ForeignKey(PracticeTest, on_delete=models.CASCADE, related_name='attempts', null=True, blank=True)
    dimension = models.CharField(max_length=10, choices=DIMENSION_CHOICES, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.PositiveIntegerField(default=0)
    total_questions = models.PositiveIntegerField(default=0)
    attempt_type = models.CharField(
        max_length=20,
        choices=[('practice', 'Procvičování'), ('test', 'Test')],
        default='practice'
    )

    def __str__(self):
        return f"{self.user.username} - {self.started_at.strftime('%Y-%m-%d')}"

    @property
    def percentage(self):
        if self.total_questions == 0:
            return 0
        return round((self.score / self.total_questions) * 100)

    class Meta:
        verbose_name = 'Pokus'
        verbose_name_plural = 'Pokusy'
        ordering = ['-started_at']

class UserAnswer(models.Model):
    attempt = models.ForeignKey(TestAttempt, on_delete=models.CASCADE, related_name='user_answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answer = models.ForeignKey('questions.Answer', on_delete=models.CASCADE, null=True, blank=True)
    is_correct = models.BooleanField(default=False)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Odpověď uživatele'
        verbose_name_plural = 'Odpovědi uživatelů'
