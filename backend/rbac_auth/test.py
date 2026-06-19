from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rbac_auth.models import CustomUser

class AuthTests(APITestCase):
    """
    Автотесты для проверки логики авторизации и безопасности
    """
    def setUp(self):
        # Перед каждым тестом создаем в тестовой базе одного пользователя
        self.user = CustomUser.objects.create_user(
            username='test_ivan', 
            password='correct_password123'
        )
        # Получаем URL для логина из urls.py по имени маршрута
        self.login_url = reverse('api_login')

    def test_successful_login_returns_token(self):
        """Проверяем, что при верном пароле выдается Токен"""
        data = {'username': 'test_ivan', 'password': 'correct_password123'}
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data) # Проверяем, что токен есть в JSON!

    def test_blocked_user_cannot_login(self):
        """Проверяем, что заблокированный пользователь получает отказ (403)"""
        # Блокируем Ивана
        self.user.is_blocked = True
        self.user.save()

        data = {'username': 'test_ivan', 'password': 'correct_password123'}
        response = self.client.post(self.login_url, data, format='json')
        
        # Система должна выдать 403 Forbidden, а не токен!
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertNotIn('token', response.data)
