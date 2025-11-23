"""
Сериализаторы для API вопросов и ответов.
Используются для валидации данных и преобразования моделей в JSON.
"""
from rest_framework import serializers

from .models import Answer, Question


class AnswerSerializer(serializers.ModelSerializer):
    """
    Полное представление ответа для чтения.
    Используется для GET-запросов получения ответа.
    """

    class Meta:
        model = Answer
        fields = ("id", "user_id", "text", "created_at")
        read_only_fields = ("id", "created_at")


class AnswerCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания ответа.
    Поле question берется из URL, user_id передается в запросе.
    Включает валидацию текста на пустоту и максимальную длину.
    """
    
    text = serializers.CharField(max_length=10000)
    user_id = serializers.CharField(max_length=255)

    class Meta:
        model = Answer
        fields = ("user_id", "text")

    def validate_text(self, value: str) -> str:
        """Валидация текста ответа."""
        if not value.strip():
            raise serializers.ValidationError("Текст ответа не может быть пустым.")
        return value
    
    def validate_user_id(self, value: str) -> str:
        """Валидация user_id."""
        if not value.strip():
            raise serializers.ValidationError("user_id не может быть пустым.")
        return value


class QuestionSerializer(serializers.ModelSerializer):
    """
    Полное представление вопроса со списком ответов.
    Используется для GET-запросов и POST-запросов создания вопроса.
    """

    # Вложенное представление всех ответов на вопрос (read-only)
    answers = AnswerSerializer(many=True, read_only=True)
    text = serializers.CharField(max_length=10000)

    class Meta:
        model = Question
        fields = ("id", "text", "created_at", "answers")
        read_only_fields = ("id", "created_at", "answers")

    def validate_text(self, value: str) -> str:
        """
        Валидация текста вопроса.
        Проверяет, что текст не является пустой строкой или состоит только из пробелов.
        
        Args:
            value: Текст вопроса для проверки
            
        Returns:
            str: Валидный текст вопроса
            
        Raises:
            ValidationError: Если текст пустой или превышает максимальную длину
        """
        if not value.strip():
            raise serializers.ValidationError("Текст вопроса не может быть пустым.")
        return value


