from django.urls import path
from . import views

app_name = 'practice'
urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Practice (creative / study) mode
    path('procvicovat/<str:dimension>/seznam/', views.practice_list, name='practice_list'),
    path('procvicovat/<str:dimension>/otazka/<int:index>/', views.practice_question_detail, name='practice_question_detail'),
    path('procvicovat/oznacit/<int:question_id>/', views.toggle_complete, name='toggle_complete'),

    # Random test
    path('test/nahodny/', views.start_random_test, name='start_random_test'),
    path('test/dimenze/<str:dimension>/', views.take_test_dimension, name='take_test_dimension'),
    path('test/dimenze/<str:dimension>/odpoved/', views.save_test_answer, name='save_test_answer'),
    path('test/dimenze/<str:dimension>/odeslat/', views.submit_test_dimension, name='submit_test_dimension'),
    path('test/prestávka/<str:next_dim>/', views.test_break, name='test_break'),
    path('test/konec/', views.test_complete, name='test_complete'),

    # Results / history
    path('vysledky/<int:attempt_id>/', views.results, name='results'),
    path('test/<str:session_key>/detail/', views.test_session_detail, name='test_session_detail'),
    path('moje-vysledky/', views.my_results, name='my_results'),
]
