"""
URL маршруты для API приложения qa.
Определяют пути к эндпоинтам для работы с вопросами и ответами.
"""
from django.urls import path

from . import views

urlpatterns = [
    # Вопросы (Questions)
    path(
        "questions/",
        views.QuestionListCreateView.as_view(),
        name="question-list"
    ),
    path(
        "questions/<int:pk>/",
        views.QuestionRetrieveDeleteView.as_view(),
        name="question-detail"
    ),
    
    # Ответы (Answers)
    path(
        "questions/<int:question_id>/answers/",
        views.AnswerCreateView.as_view(),
        name="answer-create"
    ),
    path(
        "answers/<int:pk>/",
        views.AnswerRetrieveDeleteView.as_view(),
        name="answer-detail"
    ),
]



