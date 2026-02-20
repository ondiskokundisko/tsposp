from django.urls import path
from . import views

app_name = 'practice'
urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('procvicovat/<str:dimension>/', views.practice_dimension, name='practice_dimension'),
    path('test/', views.test_list, name='test_list'),
    path('test/<int:test_id>/', views.take_test, name='take_test'),
    path('test/<int:test_id>/odeslat/', views.submit_test, name='submit_test'),
    path('vysledky/<int:attempt_id>/', views.results, name='results'),
    path('moje-vysledky/', views.my_results, name='my_results'),
    path('procvicovat/<str:dimension>/otazka/', views.practice_question, name='practice_question'),
    path('procvicovat/<str:dimension>/odpoved/', views.check_answer, name='check_answer'),
]
