import json
import random
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from questions.models import Question, Answer
from .models import PracticeTest, TestAttempt, UserAnswer

DIMENSION_NAMES = {
    'NAM': 'Numericko-analytické myšlení',
    'UAJ': 'Uvažování v anglickém jazyce',
    'KM': 'Kritické myšlení',
}

DIMENSION_TIMES = {
    'NAM': 45,
    'UAJ': 20,
    'KM': 45,
}

@login_required
def dashboard(request):
    dimensions = []
    for code, name in DIMENSION_NAMES.items():
        count = Question.objects.filter(dimension=code, is_active=True).count()
        attempts = TestAttempt.objects.filter(user=request.user, dimension=code)
        best = attempts.order_by('-score').first() if attempts.exists() else None
        dimensions.append({'code': code, 'name': name, 'count': count, 'best': best, 'time': DIMENSION_TIMES[code]})

    recent_attempts = TestAttempt.objects.filter(user=request.user).order_by('-started_at')[:5]
    practice_tests = PracticeTest.objects.filter(is_active=True)

    return render(request, 'practice/dashboard.html', {
        'dimensions': dimensions,
        'recent_attempts': recent_attempts,
        'practice_tests': practice_tests,
    })

@login_required
def practice_dimension(request, dimension):
    if dimension not in DIMENSION_NAMES:
        return redirect('practice:dashboard')
    questions = list(Question.objects.filter(dimension=dimension, is_active=True).prefetch_related('answers'))
    if not questions:
        return render(request, 'practice/no_questions.html', {'dimension': DIMENSION_NAMES[dimension]})
    return render(request, 'practice/practice_dimension.html', {
        'dimension': dimension,
        'dimension_name': DIMENSION_NAMES[dimension],
        'questions': questions,
        'time_minutes': DIMENSION_TIMES[dimension],
        'question_count': len(questions),
    })

@login_required
def practice_question(request, dimension):
    if dimension not in DIMENSION_NAMES:
        return redirect('practice:dashboard')
    questions = list(Question.objects.filter(dimension=dimension, is_active=True).prefetch_related('answers'))
    if not questions:
        return JsonResponse({'error': 'No questions'}, status=404)
    q = random.choice(questions)
    answers = list(q.answers.all())
    return JsonResponse({
        'id': q.id,
        'text': q.text,
        'explanation': q.explanation,
        'answers': [{'id': a.id, 'text': a.text} for a in answers],
    })

@login_required
def check_answer(request, dimension):
    if request.method == 'POST':
        data = json.loads(request.body)
        question_id = data.get('question_id')
        answer_id = data.get('answer_id')
        try:
            question = Question.objects.get(id=question_id)
            answer = Answer.objects.get(id=answer_id)
            correct_answer = question.answers.filter(is_correct=True).first()
            return JsonResponse({
                'is_correct': answer.is_correct,
                'correct_answer_id': correct_answer.id if correct_answer else None,
                'correct_answer_text': correct_answer.text if correct_answer else '',
                'explanation': question.explanation,
            })
        except (Question.DoesNotExist, Answer.DoesNotExist):
            return JsonResponse({'error': 'Not found'}, status=404)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

@login_required
def test_list(request):
    tests = PracticeTest.objects.filter(is_active=True).prefetch_related('questions')
    return render(request, 'practice/test_list.html', {'tests': tests})

@login_required
def take_test(request, test_id):
    test = get_object_or_404(PracticeTest, id=test_id, is_active=True)
    questions = list(test.questions.filter(is_active=True).prefetch_related('answers'))
    if not questions:
        return render(request, 'practice/no_questions.html', {'dimension': test.name})
    return render(request, 'practice/take_test.html', {
        'test': test,
        'questions': questions,
        'time_limit': test.time_limit_minutes * 60,
    })

@login_required
def submit_test(request, test_id):
    if request.method != 'POST':
        return redirect('practice:test_list')

    test = get_object_or_404(PracticeTest, id=test_id)

    attempt = TestAttempt.objects.create(
        user=request.user,
        test=test,
        attempt_type='test',
        completed_at=timezone.now(),
    )

    questions = test.questions.filter(is_active=True).prefetch_related('answers')
    score = 0
    total = questions.count()

    for question in questions:
        answer_id = request.POST.get(f'question_{question.id}')
        selected_answer = None
        is_correct = False
        if answer_id:
            try:
                selected_answer = Answer.objects.get(id=answer_id, question=question)
                is_correct = selected_answer.is_correct
                if is_correct:
                    score += 1
            except Answer.DoesNotExist:
                pass
        UserAnswer.objects.create(
            attempt=attempt,
            question=question,
            selected_answer=selected_answer,
            is_correct=is_correct,
        )

    attempt.score = score
    attempt.total_questions = total
    attempt.save()

    return redirect('practice:results', attempt_id=attempt.id)

@login_required
def results(request, attempt_id):
    attempt = get_object_or_404(TestAttempt, id=attempt_id, user=request.user)
    user_answers = attempt.user_answers.select_related('question', 'selected_answer').prefetch_related('question__answers')
    return render(request, 'practice/results.html', {
        'attempt': attempt,
        'user_answers': user_answers,
    })

@login_required
def my_results(request):
    attempts = TestAttempt.objects.filter(user=request.user).order_by('-started_at')
    return render(request, 'practice/my_results.html', {'attempts': attempts})
