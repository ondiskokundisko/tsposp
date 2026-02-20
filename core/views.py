from django.shortcuts import render
from questions.models import Question


def home(request):
    stats = {
        'question_count': Question.objects.filter(is_active=True).count(),
    }
    dimensions = [
        {
            'code': 'NAM',
            'name': 'Numericko-analytické myšlení',
            'description': '15 otázek, 45 minut. Zlomky, zebrové úlohy, procenta, posloupnosti, permutace a smyšlené operace.',
            'icon': '🔢',
            'color': 'blue',
            'count': Question.objects.filter(dimension='NAM', is_active=True).count(),
        },
        {
            'code': 'UAJ',
            'name': 'Uvažování v anglickém jazyce',
            'description': '15 otázek, 20 minut. Porozumění textu, synonyma, metafory a analýza anglických textů.',
            'icon': '🌍',
            'color': 'green',
            'count': Question.objects.filter(dimension='UAJ', is_active=True).count(),
        },
        {
            'code': 'KM',
            'name': 'Kritické myšlení',
            'description': '15 otázek, 45 minut. Analýza tvrzení, vyplývání z textu, logické závěry.',
            'icon': '🧠',
            'color': 'purple',
            'count': Question.objects.filter(dimension='KM', is_active=True).count(),
        },
    ]
    return render(request, 'core/home.html', {'stats': stats, 'dimensions': dimensions})


def about(request):
    return render(request, 'core/about.html')


def pricing(request):
    return render(request, 'core/pricing.html')


def contact(request):
    return render(request, 'core/contact.html')
