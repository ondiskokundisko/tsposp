import json
import random
import uuid
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from questions.models import Question, Answer
from .models import TestAttempt, UserAnswer, QuestionProgress

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

# Order dimensions are shown in the full random test
DIMENSION_ORDER = ['NAM', 'UAJ', 'KM']

FREE_QUESTION_LIMIT = 10  # Free users can access first N questions per dimension
TEST_QUESTION_COUNT = 15  # Questions per dimension in random test


def _is_premium(user):
    """Return True if the user has premium access.

    Premium is granted when either:
      - the user belongs to the PREMIUM_GROUP_NAME Django group, OR
      - their UserProfile.is_premium flag is True.
    Both routes are honoured so the admin can use whichever is most convenient.
    """
    try:
        if user.groups.filter(name=settings.PREMIUM_GROUP_NAME).exists():
            return True
        return user.profile.is_premium
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

def _group_attempts_into_sessions(attempts):
    """Group a queryset/list of TestAttempts by session_key.

    Returns a list of dicts ordered newest-first:
      {session_key, attempts (sorted NAM/UAJ/KM), date, total_score,
       total_questions, percentage, percentage_clamped}
    """
    from collections import defaultdict
    session_map = defaultdict(list)
    for a in attempts:
        key = a.session_key or f'solo_{a.id}'
        session_map[key].append(a)

    sessions = []
    for key, dims in session_map.items():
        total_score = sum(a.score for a in dims)
        total_questions = sum(a.total_questions for a in dims)
        percentage = round((total_score / total_questions) * 100, 1) if total_questions else 0
        dims_sorted = sorted(
            dims,
            key=lambda a: DIMENSION_ORDER.index(a.dimension) if a.dimension in DIMENSION_ORDER else 99,
        )
        sessions.append({
            'session_key': key,
            'attempts': dims_sorted,
            'date': min(a.started_at for a in dims),
            'total_score': round(total_score, 2),
            'total_questions': total_questions,
            'percentage': percentage,
            'percentage_clamped': max(0.0, min(100.0, percentage)),
            'is_complete': len(dims) == len(DIMENSION_ORDER) and all(
                d in [a.dimension for a in dims] for d in DIMENSION_ORDER
            ),
        })
    sessions.sort(key=lambda s: s['date'], reverse=True)
    return sessions


@login_required
def dashboard(request):
    premium = _is_premium(request.user)
    dimensions = []
    for code in DIMENSION_ORDER:
        name = DIMENSION_NAMES[code]
        total = Question.objects.filter(dimension=code, is_active=True).count()
        accessible = total if premium else min(total, FREE_QUESTION_LIMIT)
        completed = QuestionProgress.objects.filter(
            user=request.user, question__dimension=code, is_completed=True
        ).count()
        best = TestAttempt.objects.filter(
            user=request.user, dimension=code
        ).order_by('-score').first()
        dimensions.append({
            'code': code,
            'name': name,
            'total': total,
            'accessible': accessible,
            'completed': completed,
            'best': best,
            'time': DIMENSION_TIMES[code],
        })

    all_recent = list(TestAttempt.objects.filter(user=request.user).order_by('-started_at')[:30])
    recent_sessions = _group_attempts_into_sessions(all_recent)[:5]

    return render(request, 'practice/dashboard.html', {
        'dimensions': dimensions,
        'recent_sessions': recent_sessions,
        'premium': premium,
    })


# ---------------------------------------------------------------------------
# Practice (creative / study) mode
# ---------------------------------------------------------------------------

@login_required
def practice_list(request, dimension):
    """Ordered list of all questions in a dimension – the 'creative mode'."""
    if dimension not in DIMENSION_NAMES:
        return redirect('practice:dashboard')

    premium = _is_premium(request.user)
    all_questions = list(
        Question.objects.filter(dimension=dimension, is_active=True)
        .prefetch_related('answers')
        .order_by('id')
    )

    # Build progress map
    progress_qs = QuestionProgress.objects.filter(
        user=request.user, question__in=all_questions
    )
    completed_ids = {p.question_id for p in progress_qs if p.is_completed}

    # Free users only see first FREE_QUESTION_LIMIT
    accessible_count = len(all_questions) if premium else min(len(all_questions), FREE_QUESTION_LIMIT)

    questions_with_state = []
    for i, q in enumerate(all_questions):
        locked = i >= accessible_count
        questions_with_state.append({
            'question': q,
            'index': i,
            'number': i + 1,
            'is_completed': q.id in completed_ids,
            'locked': locked,
        })

    # Find resume index: last completed accessible question + 1
    resume_index = 0
    for i in range(accessible_count - 1, -1, -1):
        if all_questions[i].id in completed_ids:
            resume_index = min(i + 1, accessible_count - 1)
            break

    return render(request, 'practice/practice_list.html', {
        'dimension': dimension,
        'dimension_name': DIMENSION_NAMES[dimension],
        'questions': questions_with_state,
        'accessible_count': accessible_count,
        'resume_index': resume_index,
        'premium': premium,
        'time_minutes': DIMENSION_TIMES[dimension],
    })


@login_required
def practice_question_detail(request, dimension, index):
    """Show a single question in practice (study) mode."""
    if dimension not in DIMENSION_NAMES:
        return redirect('practice:dashboard')

    premium = _is_premium(request.user)
    questions = list(
        Question.objects.filter(dimension=dimension, is_active=True)
        .prefetch_related('answers')
        .order_by('id')
    )

    accessible_count = len(questions) if premium else min(len(questions), FREE_QUESTION_LIMIT)

    if index < 0 or index >= accessible_count:
        return redirect('practice:practice_list', dimension=dimension)

    question = questions[index]

    # Mark as visited/update last_visited
    progress, _ = QuestionProgress.objects.get_or_create(
        user=request.user, question=question
    )

    is_completed = progress.is_completed
    prev_index = index - 1 if index > 0 else None
    next_index = index + 1 if index < accessible_count - 1 else None

    return render(request, 'practice/practice_question.html', {
        'dimension': dimension,
        'dimension_name': DIMENSION_NAMES[dimension],
        'question': question,
        'index': index,
        'number': index + 1,
        'total': accessible_count,
        'is_completed': is_completed,
        'prev_index': prev_index,
        'next_index': next_index,
        'premium': premium,
    })


@login_required
def toggle_complete(request, question_id):
    """AJAX: toggle a question's completed state."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        question = Question.objects.get(id=question_id, is_active=True)
    except Question.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)

    progress, _ = QuestionProgress.objects.get_or_create(
        user=request.user, question=question
    )
    progress.is_completed = not progress.is_completed
    progress.save()
    return JsonResponse({'is_completed': progress.is_completed})


# ---------------------------------------------------------------------------
# Random test
# ---------------------------------------------------------------------------

@login_required
def start_random_test(request):
    """Landing page for starting a new random test (premium only)."""
    premium = _is_premium(request.user)
    if not premium:
        return render(request, 'practice/test_locked.html')

    if request.method == 'POST':
        # Generate random question IDs for each dimension
        session_key = uuid.uuid4().hex[:20]
        ids = {}
        for dim in DIMENSION_ORDER:
            pool = list(
                Question.objects.filter(dimension=dim, is_active=True)
                .values_list('id', flat=True)
                .order_by('id')
            )
            count = min(TEST_QUESTION_COUNT, len(pool))
            ids[dim] = random.sample(pool, count) if pool else []

        request.session['rtest'] = {
            'session_key': session_key,
            'ids': ids,
            'answers': {d: {} for d in DIMENSION_ORDER},
            'done': [],
        }
        return redirect('practice:take_test_dimension', dimension='NAM')

    # GET: show landing page with info
    counts = {dim: Question.objects.filter(dimension=dim, is_active=True).count()
              for dim in DIMENSION_ORDER}
    return render(request, 'practice/start_random_test.html', {
        'counts': counts,
        'dimension_names': DIMENSION_NAMES,
        'dimension_times': DIMENSION_TIMES,
        'dimension_order': DIMENSION_ORDER,
        'test_count': TEST_QUESTION_COUNT,
    })


@login_required
def take_test_dimension(request, dimension):
    """The actual test page for one dimension, with navigation and timer."""
    premium = _is_premium(request.user)
    if not premium:
        return redirect('practice:start_random_test')

    rtest = request.session.get('rtest')
    if not rtest:
        return redirect('practice:start_random_test')

    if dimension in rtest.get('done', []):
        # Already submitted this dimension – find next
        idx = DIMENSION_ORDER.index(dimension)
        next_dim = DIMENSION_ORDER[idx + 1] if idx + 1 < len(DIMENSION_ORDER) else None
        if next_dim:
            return redirect('practice:test_break', next_dim=next_dim)
        return redirect('practice:test_complete')

    question_ids = rtest['ids'].get(dimension, [])
    if not question_ids:
        return redirect('practice:start_random_test')

    questions = list(
        Question.objects.filter(id__in=question_ids)
        .prefetch_related('answers')
    )
    # Preserve the random order chosen at start
    id_index = {qid: i for i, qid in enumerate(question_ids)}
    questions.sort(key=lambda q: id_index[q.id])

    # Saved answers so far (question_id str -> answer_id)
    saved_answers = rtest['answers'].get(dimension, {})

    return render(request, 'practice/take_test_dimension.html', {
        'dimension': dimension,
        'dimension_name': DIMENSION_NAMES[dimension],
        'time_seconds': DIMENSION_TIMES[dimension] * 60,
        'questions': questions,
        'saved_answers': json.dumps(saved_answers),
        'question_count': len(questions),
        'dimension_order': DIMENSION_ORDER,
        'dimension_names': DIMENSION_NAMES,
        'dimension_times': DIMENSION_TIMES,
    })


@login_required
def save_test_answer(request, dimension):
    """AJAX: save an answer during the test (can be changed before submitting)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    rtest = request.session.get('rtest')
    if not rtest:
        return JsonResponse({'error': 'No active test'}, status=400)

    data = json.loads(request.body)
    question_id = str(data.get('question_id'))
    answer_id = str(data.get('answer_id'))

    if dimension not in rtest['answers']:
        rtest['answers'][dimension] = {}
    rtest['answers'][dimension][question_id] = answer_id
    request.session['rtest'] = rtest
    request.session.modified = True

    return JsonResponse({'saved': True})


@login_required
def submit_test_dimension(request, dimension):
    """Submit one dimension of the test, save results, redirect to break or final."""
    if request.method != 'POST':
        return redirect('practice:take_test_dimension', dimension=dimension)

    premium = _is_premium(request.user)
    if not premium:
        return redirect('practice:start_random_test')

    rtest = request.session.get('rtest')
    if not rtest:
        return redirect('practice:start_random_test')

    # Also accept answers submitted via form (timer auto-submit)
    for key, value in request.POST.items():
        if key.startswith('q_'):
            qid = key[2:]
            rtest['answers'].setdefault(dimension, {})[qid] = value
    request.session['rtest'] = rtest
    request.session.modified = True

    question_ids = rtest['ids'].get(dimension, [])
    saved_answers = rtest['answers'].get(dimension, {})
    session_key = rtest.get('session_key', '')

    # Create attempt record
    attempt = TestAttempt.objects.create(
        user=request.user,
        dimension=dimension,
        question_ids=json.dumps(question_ids),
        session_key=session_key,
        completed_at=timezone.now(),
        attempt_type='test',
    )

    questions = Question.objects.filter(id__in=question_ids).prefetch_related('answers')
    score = 0.0
    total = len(question_ids)

    for question in questions:
        answer_id = saved_answers.get(str(question.id))
        selected = None
        is_correct = False
        if answer_id:
            try:
                selected = Answer.objects.get(id=int(answer_id), question=question)
                is_correct = selected.is_correct
                if is_correct:
                    score += 1.0
                else:
                    score -= 0.2          # TSP penalty for wrong answer
            except Answer.DoesNotExist:
                pass
        UserAnswer.objects.update_or_create(
            attempt=attempt,
            question=question,
            defaults={'selected_answer': selected, 'is_correct': is_correct},
        )

    attempt.score = round(score, 2)
    attempt.total_questions = total
    attempt.save()

    # Mark dimension done
    rtest['done'].append(dimension)
    rtest.setdefault('attempt_ids', {})[dimension] = attempt.id
    request.session['rtest'] = rtest
    request.session.modified = True

    # Navigate to next dimension or completion
    idx = DIMENSION_ORDER.index(dimension)
    if idx + 1 < len(DIMENSION_ORDER):
        next_dim = DIMENSION_ORDER[idx + 1]
        return redirect('practice:test_break', next_dim=next_dim)
    return redirect('practice:test_complete')


@login_required
def test_break(request, next_dim):
    """Break screen shown between test dimensions."""
    premium = _is_premium(request.user)
    if not premium:
        return redirect('practice:start_random_test')
    rtest = request.session.get('rtest')
    if not rtest:
        return redirect('practice:start_random_test')
    return render(request, 'practice/test_break.html', {
        'next_dim': next_dim,
        'next_name': DIMENSION_NAMES.get(next_dim, ''),
        'next_time': DIMENSION_TIMES.get(next_dim, 0),
    })


@login_required
def test_complete(request):
    """Final results page showing all 3 dimension attempts from this session."""
    rtest = request.session.get('rtest')
    attempt_ids = {}
    if rtest:
        attempt_ids = rtest.get('attempt_ids', {})
        # Clean session
        del request.session['rtest']
        request.session.modified = True

    attempts = []
    total_score = 0
    total_questions = 0
    for dim in DIMENSION_ORDER:
        aid = attempt_ids.get(dim)
        if aid:
            try:
                a = TestAttempt.objects.get(id=aid, user=request.user)
                attempts.append(a)
                total_score += a.score
                total_questions += a.total_questions
            except TestAttempt.DoesNotExist:
                pass

    overall_pct = round((total_score / total_questions) * 100, 1) if total_questions else 0
    total_score = round(total_score, 2)

    return render(request, 'practice/test_complete.html', {
        'attempts': attempts,
        'total_score': total_score,
        'total_questions': total_questions,
        'overall_pct': overall_pct,
        'dimension_names': DIMENSION_NAMES,
    })


@login_required
def test_session_detail(request, session_key):
    """Full detail for one test session: all 3 dimensions with per-question breakdown."""
    attempts = list(
        TestAttempt.objects.filter(user=request.user, session_key=session_key)
        .prefetch_related('user_answers__question__answers', 'user_answers__selected_answer')
    )
    if not attempts:
        return redirect('practice:my_results')

    attempts_sorted = sorted(
        attempts,
        key=lambda a: DIMENSION_ORDER.index(a.dimension) if a.dimension in DIMENSION_ORDER else 99,
    )
    total_score = round(sum(a.score for a in attempts), 2)
    total_questions = sum(a.total_questions for a in attempts)
    percentage = round((total_score / total_questions) * 100, 1) if total_questions else 0

    return render(request, 'practice/test_session_detail.html', {
        'session_key': session_key,
        'attempts': attempts_sorted,
        'total_score': total_score,
        'total_questions': total_questions,
        'percentage': percentage,
        'percentage_clamped': max(0.0, min(100.0, percentage)),
        'dimension_names': DIMENSION_NAMES,
        'date': min(a.started_at for a in attempts),
    })


@login_required
def results(request, attempt_id):
    attempt = get_object_or_404(TestAttempt, id=attempt_id, user=request.user)
    user_answers = attempt.user_answers.select_related(
        'question', 'selected_answer'
    ).prefetch_related('question__answers')
    return render(request, 'practice/results.html', {
        'attempt': attempt,
        'user_answers': user_answers,
        'dimension_names': DIMENSION_NAMES,
    })


@login_required
def my_results(request):
    all_attempts = list(TestAttempt.objects.filter(user=request.user).order_by('-started_at'))
    sessions = _group_attempts_into_sessions(all_attempts)
    return render(request, 'practice/my_results.html', {
        'sessions': sessions,
        'dimension_names': DIMENSION_NAMES,
        'dimension_order': DIMENSION_ORDER,
    })
