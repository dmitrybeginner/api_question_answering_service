"""
Настройки административной панели Django для моделей вопросов и ответов.
Определяет отображение моделей в админке, фильтры и поиск.
"""
from django.contrib import admin

from .models import Answer, Question


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """
    Настройки отображения вопросов в админке Django.
    Позволяет просматривать, искать и фильтровать вопросы.
    """

    # Отображаемые колонки в списке
    list_display = ("id", "text", "created_at")
    
    # Поля для поиска
    search_fields = ("text",)
    
    # Фильтры в боковой панели
    list_filter = ("created_at",)
    
    # Сортировка по умолчанию (сначала новые)
    ordering = ("-created_at",)
    
    # Только для чтения (автоматически заполняемые поля)
    readonly_fields = ("created_at",)


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    """
    Настройки отображения ответов в админке Django.
    Позволяет просматривать, искать и фильтровать ответы.
    """

    # Отображаемые колонки в списке
    list_display = ("id", "question", "user_id", "created_at")
    
    # Поля для поиска
    search_fields = ("text", "user_id")
    
    # Фильтры в боковой панели
    list_filter = ("user_id", "created_at")
    
    # Сортировка по умолчанию (сначала старые)
    ordering = ("created_at",)
    
    # Использование raw_id_fields для ForeignKey (удобнее при большом количестве вопросов)
    raw_id_fields = ("question",)
    
    # Только для чтения (автоматически заполняемые поля)
    readonly_fields = ("created_at",)



