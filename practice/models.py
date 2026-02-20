from django.db import models
from django.contrib.auth.models import User
from questions.models import Question, DIMENSION_CHOICES


class QuestionProgress(models.Model):
    """Tracks which questions a user has completed in practice (creative) mode."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='question_progress')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='progress')
    is_completed = models.BooleanField(default=False)
    last_visited = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'question']
        verbose_name = 'Postup u otázky'
        verbose_name_plural = 'Postup u otázek'


class TestAttempt(models.Model):
    """One dimension of a random test, or a full practice session."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attempts')
    dimension = models.CharField(max_length=10, choices=DIMENSION_CHOICES, blank=True)
    # JSON list of question IDs randomly selected for this attempt
    question_ids = models.TextField(default='[]')
    # Groups 3-dimension attempts that belong to one full random test session
    session_key = models.CharField(max_length=40, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    # Float to support TSP scoring: +1 correct, -0.2 wrong, 0 unanswered
    score = models.FloatField(default=0.0)
    total_questions = models.PositiveIntegerField(default=0)
    attempt_type = models.CharField(
        max_length=20,
        choices=[('test', 'Test')],
        default='test',
    )

    def __str__(self):
        return f"{self.user.username} – {self.get_dimension_display()} – {self.started_at.strftime('%Y-%m-%d')}"

    @property
    def percentage(self):
        if self.total_questions == 0:
            return 0
        return round((self.score / self.total_questions) * 100, 1)

    @property
    def percentage_clamped(self):
        """Percentage clamped to 0–100 for use as a progress bar width."""
        return max(0.0, min(100.0, self.percentage))

    class Meta:
        verbose_name = 'Pokus'
        verbose_name_plural = 'Pokusy'
        ordering = ['-started_at']


class UserAnswer(models.Model):
    attempt = models.ForeignKey(TestAttempt, on_delete=models.CASCADE, related_name='user_answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answer = models.ForeignKey('questions.Answer', on_delete=models.CASCADE, null=True, blank=True)
    is_correct = models.BooleanField(default=False)
    answered_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['attempt', 'question']
        verbose_name = 'Odpověď uživatele'
        verbose_name_plural = 'Odpovědi uživatelů'

    @property
    def points(self):
        """Points awarded for this answer: +1 correct, -0.2 wrong, 0 unanswered."""
        if self.is_correct:
            return 1
        if self.selected_answer is not None:
            return -0.2
        return 0
