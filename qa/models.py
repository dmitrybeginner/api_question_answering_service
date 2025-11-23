from django.contrib.auth.models import User
from django.db import models


class Question(models.Model):
    """Модель вопроса, хранит текст, дату и автора"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор", related_name="questions")
    text = models.TextField("Текст вопроса")
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"Вопрос #{self.pk}: {self.text[:30]}"


class Answer(models.Model):
    """
    Модель ответа.
    user_id - строковый идентификатор пользователя (например UUID).
    Связь с Question через ForeignKey с каскадным удалением.
    """

    question = models.ForeignKey(Question, related_name="answers", on_delete=models.CASCADE, verbose_name="Вопрос")
    user_id = models.CharField("ID пользователя", max_length=255)
    text = models.TextField("Текст ответа")
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        ordering = ("created_at",)

    def __str__(self) -> str:
        return f"Ответ #{self.pk} от {self.user_id}"