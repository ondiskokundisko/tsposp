from django.db import models

DIMENSION_CHOICES = [
    ('NAM', 'Numericko-analytické myšlení'),
    ('UAJ', 'Uvažování v anglickém jazyce'),
    ('KM', 'Kritické myšlení'),
]

DIFFICULTY_CHOICES = [
    ('easy', 'Lehká'),
    ('medium', 'Střední'),
    ('hard', 'Těžká'),
]

class Question(models.Model):
    dimension = models.CharField(max_length=10, choices=DIMENSION_CHOICES)
    text = models.TextField()
    explanation = models.TextField(blank=True)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    image = models.ImageField(upload_to='questions/', blank=True, null=True)

    def __str__(self):
        return f"[{self.get_dimension_display()}] {self.text[:60]}"

    class Meta:
        verbose_name = 'Otázka'
        verbose_name_plural = 'Otázky'
        ordering = ['dimension', 'id']

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.TextField()
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{'✓' if self.is_correct else '✗'} {self.text[:50]}"

    class Meta:
        verbose_name = 'Odpověď'
        verbose_name_plural = 'Odpovědi'
        ordering = ['order']
