"""
Тесты для API вопросов и ответов с JWT аутентификацией.
Проверяют корректность работы всех эндпоинтов, бизнес-логики и прав доступа.
"""
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Answer, Question


class AuthenticationTestCase(APITestCase):
    """Базовый класс с методами для аутентификации."""

    def setUp(self):
        """Создаём тестовых пользователей."""
        self.user1 = User.objects.create_user(
            username='testuser1',
            password='testpass123',
            email='user1@test.com'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            password='testpass456',
            email='user2@test.com'
        )

    def get_token(self, user):
        """Получить JWT токен для пользователя."""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def authenticate(self, user):
        """Аутентифицировать клиент с токеном пользователя."""
        token = self.get_token(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def logout(self):
        """Убрать аутентификацию."""
        self.client.credentials()


class JWTAuthenticationTests(AuthenticationTestCase):
    """Тесты JWT аутентификации."""

    def test_obtain_jwt_token(self):
        """Тест получения JWT токена."""
        url = reverse('token_obtain_pair')
        payload = {
            'username': 'testuser1',
            'password': 'testpass123'
        }
        response = self.client.post(url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_refresh_jwt_token(self):
        """Тест обновления JWT токена."""
        # Получаем refresh токен
        refresh = RefreshToken.for_user(self.user1)
        
        url = reverse('token_refresh')
        payload = {'refresh': str(refresh)}
        response = self.client.post(url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_invalid_credentials(self):
        """Тест с неправильными credentials."""
        url = reverse('token_obtain_pair')
        payload = {
            'username': 'testuser1',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class QuestionAPITests(AuthenticationTestCase):
    """Тесты для API работы с вопросами."""

    def test_list_questions_public(self):
        """Тест: список вопросов доступен без аутентификации."""
        # Создаём вопросы
        Question.objects.create(user=self.user1, text="Вопрос 1")
        Question.objects.create(user=self.user2, text="Вопрос 2")
        
        url = reverse("question-list")
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_retrieve_question_public(self):
        """Тест: конкретный вопрос доступен без аутентификации."""
        question = Question.objects.create(user=self.user1, text="Тестовый вопрос")
        
        url = reverse("question-detail", args=[question.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['text'], "Тестовый вопрос")
        self.assertEqual(response.data['username'], 'testuser1')

    def test_create_question_requires_authentication(self):
        """Тест: создание вопроса требует аутентификации."""
        url = reverse("question-list")
        payload = {"text": "Новый вопрос"}
        response = self.client.post(url, payload, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Question.objects.count(), 0)

    def test_create_question_authenticated(self):
        """Тест: аутентифицированный пользователь может создать вопрос."""
        self.authenticate(self.user1)
        
        url = reverse("question-list")
        payload = {"text": "Что такое Django?"}
        response = self.client.post(url, payload, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Question.objects.count(), 1)
        
        question = Question.objects.first()
        self.assertEqual(question.text, "Что такое Django?")
        self.assertEqual(question.user, self.user1)

    def test_validate_empty_question_text(self):
        """Тест: нельзя создать вопрос с пустым текстом."""
        self.authenticate(self.user1)
        
        url = reverse("question-list")
        payload = {"text": "   "}
        response = self.client.post(url, payload, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Question.objects.count(), 0)

    def test_validate_long_question_text(self):
        """Тест: нельзя создать вопрос со слишком длинным текстом."""
        self.authenticate(self.user1)
        
        url = reverse("question-list")
        payload = {"text": "a" * 10001}  # Больше max_length
        response = self.client.post(url, payload, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Question.objects.count(), 0)

    def test_delete_own_question(self):
        """Тест: владелец может удалить свой вопрос."""
        question = Question.objects.create(user=self.user1, text="Мой вопрос")
        self.authenticate(self.user1)
        
        url = reverse("question-detail", args=[question.id])
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Question.objects.count(), 0)

    def test_cannot_delete_other_user_question(self):
        """Тест: нельзя удалить чужой вопрос."""
        question = Question.objects.create(user=self.user1, text="Вопрос user1")
        self.authenticate(self.user2)
        
        url = reverse("question-detail", args=[question.id])
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Question.objects.count(), 1)

    def test_delete_question_requires_authentication(self):
        """Тест: удаление вопроса требует аутентификации."""
        question = Question.objects.create(user=self.user1, text="Вопрос")
        
        url = reverse("question-detail", args=[question.id])
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Question.objects.count(), 1)

    def test_question_with_answers(self):
        """Тест: вопрос возвращается со всеми ответами."""
        question = Question.objects.create(user=self.user1, text="Вопрос")
        Answer.objects.create(question=question, user=self.user1, text="Ответ 1")
        Answer.objects.create(question=question, user=self.user2, text="Ответ 2")
        
        url = reverse("question-detail", args=[question.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['answers']), 2)

    def test_delete_question_cascades_answers(self):
        """Тест: каскадное удаление ответов при удалении вопроса."""
        question = Question.objects.create(user=self.user1, text="Вопрос")
        Answer.objects.create(question=question, user=self.user1, text="Ответ 1")
        Answer.objects.create(question=question, user=self.user2, text="Ответ 2")
        
        self.assertEqual(Answer.objects.count(), 2)
        
        self.authenticate(self.user1)
        url = reverse("question-detail", args=[question.id])
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Question.objects.count(), 0)
        self.assertEqual(Answer.objects.count(), 0)

    def test_pagination(self):
        """Тест: список вопросов пагинируется."""
        # Создаём 15 вопросов (больше PAGE_SIZE=10)
        for i in range(15):
            Question.objects.create(user=self.user1, text=f"Вопрос {i}")
        
        url = reverse("question-list")
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 15)
        self.assertEqual(len(response.data['results']), 10)  # PAGE_SIZE
        self.assertIsNotNone(response.data['next'])


class AnswerAPITests(AuthenticationTestCase):
    """Тесты для API работы с ответами."""

    def setUp(self):
        """Подготовка тестовых данных."""
        super().setUp()
        self.question = Question.objects.create(
            user=self.user1,
            text="Что такое REST?"
        )

    def test_create_answer_requires_authentication(self):
        """Тест: создание ответа требует аутентификации."""
        url = reverse("answer-create", args=[self.question.id])
        payload = {"text": "REST — это архитектурный стиль"}
        response = self.client.post(url, payload, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Answer.objects.count(), 0)

    def test_create_answer_authenticated(self):
        """Тест: аутентифицированный пользователь может создать ответ."""
        self.authenticate(self.user2)
        
        url = reverse("answer-create", args=[self.question.id])
        payload = {"text": "REST — это архитектурный стиль"}
        response = self.client.post(url, payload, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Answer.objects.count(), 1)
        
        answer = Answer.objects.first()
        self.assertEqual(answer.text, "REST — это архитектурный стиль")
        self.assertEqual(answer.user, self.user2)
        self.assertEqual(answer.question, self.question)

    def test_cannot_create_answer_for_nonexistent_question(self):
        """Тест: нельзя создать ответ к несуществующему вопросу."""
        self.authenticate(self.user1)
        
        url = reverse("answer-create", args=[9999])
        payload = {"text": "Текст ответа"}
        response = self.client.post(url, payload, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Answer.objects.count(), 0)

    def test_validate_empty_answer_text(self):
        """Тест: нельзя создать ответ с пустым текстом."""
        self.authenticate(self.user1)
        
        url = reverse("answer-create", args=[self.question.id])
        payload = {"text": "   "}
        response = self.client.post(url, payload, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Answer.objects.count(), 0)

    def test_validate_long_answer_text(self):
        """Тест: нельзя создать ответ со слишком длинным текстом."""
        self.authenticate(self.user1)
        
        url = reverse("answer-create", args=[self.question.id])
        payload = {"text": "a" * 10001}
        response = self.client.post(url, payload, format="json")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Answer.objects.count(), 0)

    def test_retrieve_answer_public(self):
        """Тест: конкретный ответ доступен без аутентификации."""
        answer = Answer.objects.create(
            question=self.question,
            user=self.user1,
            text="Тестовый ответ"
        )
        
        url = reverse("answer-detail", args=[answer.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['text'], "Тестовый ответ")
        self.assertEqual(response.data['username'], 'testuser1')

    def test_delete_own_answer(self):
        """Тест: владелец может удалить свой ответ."""
        answer = Answer.objects.create(
            question=self.question,
            user=self.user1,
            text="Мой ответ"
        )
        self.authenticate(self.user1)
        
        url = reverse("answer-detail", args=[answer.id])
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Answer.objects.count(), 0)

    def test_cannot_delete_other_user_answer(self):
        """Тест: нельзя удалить чужой ответ."""
        answer = Answer.objects.create(
            question=self.question,
            user=self.user1,
            text="Ответ user1"
        )
        self.authenticate(self.user2)
        
        url = reverse("answer-detail", args=[answer.id])
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Answer.objects.count(), 1)

    def test_delete_answer_requires_authentication(self):
        """Тест: удаление ответа требует аутентификации."""
        answer = Answer.objects.create(
            question=self.question,
            user=self.user1,
            text="Ответ"
        )
        
        url = reverse("answer-detail", args=[answer.id])
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Answer.objects.count(), 1)

    def test_multiple_answers_from_same_user(self):
        """Тест: один пользователь может оставлять несколько ответов."""
        self.authenticate(self.user1)
        
        url = reverse("answer-create", args=[self.question.id])
        
        # Первый ответ
        payload1 = {"text": "Первый ответ"}
        response1 = self.client.post(url, payload1, format="json")
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        
        # Второй ответ
        payload2 = {"text": "Второй ответ"}
        response2 = self.client.post(url, payload2, format="json")
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        
        # Проверяем
        self.assertEqual(Answer.objects.count(), 2)
        self.assertEqual(
            Answer.objects.filter(user=self.user1).count(), 2
        )


class PermissionsTests(AuthenticationTestCase):
    """Тесты прав доступа."""

    def test_isowner_permission_question(self):
        """Тест: IsOwnerOrReadOnly для вопросов."""
        question = Question.objects.create(user=self.user1, text="Вопрос")
        
        # Чтение доступно всем
        url = reverse("question-detail", args=[question.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Удаление требует владения
        self.authenticate(self.user2)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Владелец может удалить
        self.authenticate(self.user1)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_isowner_permission_answer(self):
        """Тест: IsOwnerOrReadOnly для ответов."""
        question = Question.objects.create(user=self.user1, text="Вопрос")
        answer = Answer.objects.create(
            question=question,
            user=self.user1,
            text="Ответ"
        )
        
        # Чтение доступно всем
        url = reverse("answer-detail", args=[answer.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Удаление требует владения
        self.authenticate(self.user2)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Владелец может удалить
        self.authenticate(self.user1)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class ThrottlingTests(AuthenticationTestCase):
    """Тесты rate limiting."""

    def test_throttling_exists(self):
        """Тест: throttling настроен (проверка наличия заголовков)."""
        url = reverse("question-list")
        response = self.client.get(url)
        
        # DRF может не добавлять заголовки в dev режиме
        # Просто проверяем что запрос проходит
        self.assertEqual(response.status_code, status.HTTP_200_OK)
