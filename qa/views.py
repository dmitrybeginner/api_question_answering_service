"""
API представления для работы с вопросами и ответами.
Используют generic views из Django REST Framework для стандартных CRUD операций.
"""
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .models import Answer, Question
from .permissions import IsOwnerOrReadOnly
from .serializers import (
    AnswerCreateSerializer,
    AnswerSerializer,
    QuestionSerializer,
)


class QuestionListCreateView(generics.ListCreateAPIView):
    """
    GET /questions/ - список всех вопросов
    POST /questions/ - создать новый вопрос
    """
    queryset = Question.objects.prefetch_related("answers").all()
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        """Привязываем вопрос к пользователю или создаем технического."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Если пользователь авторизован - используем его
        if self.request.user.is_authenticated:
            user = self.request.user
        else:
            # Иначе создаем/используем технического пользователя
            user, _ = User.objects.get_or_create(
                username='anonymous',
                defaults={'email': 'anonymous@example.com'}
            )
        
        serializer.save(user=user)


class QuestionRetrieveDeleteView(generics.RetrieveDestroyAPIView):
    """
    GET /questions/{id} - получить вопрос и все ответы на него
    DELETE /questions/{id} - удалить вопрос (вместе с ответами)
    """
    queryset = Question.objects.prefetch_related("answers").all()
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]


class AnswerCreateView(generics.CreateAPIView):
    """
    POST /questions/{id}/answers/ - добавить ответ к вопросу
    """
    serializer_class = AnswerCreateSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        """Привязываем ответ к вопросу из URL и устанавливаем user_id из запроса."""
        question = get_object_or_404(Question, pk=self.kwargs["question_id"])
        # user_id передается в сериализаторе из запроса
        serializer.save(question=question)


class AnswerRetrieveDeleteView(generics.RetrieveDestroyAPIView):
    """
    GET /answers/{id} - получить конкретный ответ
    DELETE /answers/{id} - удалить ответ
    """
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
