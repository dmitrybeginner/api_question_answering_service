"""
Кастомные права доступа для API вопросов и ответов.
Определяют, кто может просматривать, создавать, редактировать и удалять объекты.
"""
from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Кастомное право доступа:
    - Чтение (GET, HEAD, OPTIONS) доступно всем
    - Изменение и удаление (PUT, PATCH, DELETE) доступно только владельцу объекта
    
    Используется для защиты вопросов и ответов от изменения другими пользователями.
    """

    def has_object_permission(self, request, view, obj):
        """
        Проверяет права доступа к конкретному объекту.
        """
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Для Question проверяем владельца через ForeignKey
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # Для Answer проверяем user_id (строка) с username пользователя
        if hasattr(obj, 'user_id'):
            return obj.user_id == request.user.username
        
        return False


