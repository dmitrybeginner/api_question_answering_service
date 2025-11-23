from django.apps import AppConfig


class QaConfig(AppConfig):
    """Регистрируем приложение в Django"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "qa"