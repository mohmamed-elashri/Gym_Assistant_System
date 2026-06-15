import json
import numpy as np
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import UserFitnessData


class FitnessAppTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password123')

    def test_landing_page(self):
        """Test that the landing page loads correctly."""
        response = self.client.get(reverse('landing'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'landing.html')

    def test_model_str_method(self):
        """Test the __str__ method of UserFitnessData model."""
        fitness_data = UserFitnessData.objects.create(
            user=self.user,
            gender=0,
            age=25,
            weight=75.0,
            height=1.75,
            fitness_level='Good'
        )
        expected_str = f"testuser - Good ({fitness_data.created_at.strftime('%Y-%m-%d')})"
        self.assertEqual(str(fitness_data), expected_str)

        self.assertEqual(fitness_data.max_bpm, 220 - 25)
        self.assertIsNotNone(fitness_data.daily_calories)
        self.assertIsNotNone(fitness_data.protein_grams)
        self.assertIsNotNone(fitness_data.carbs_grams)
        self.assertIsNotNone(fitness_data.fats_grams)
        self.assertGreater(fitness_data.bmi, 0)

    @patch('fitness_api.views.predict_calories')
    @patch('fitness_api.views.get_fitness_model')
    def test_prediction_api_success(self, mock_get_fitness_model, mock_predict_calories):
        """Test the fitness prediction API with mocked ML models."""
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([2])
        mock_get_fitness_model.return_value = mock_model
        mock_predict_calories.return_value = 450.5

        self.client.login(username='testuser', password='password123')

        payload = {
            "age": 28,
            "gender": 0,
            "weight": 85.0,
            "height": 1.80
        }

        response = self.client.post(
            '/api/predict/',
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['fitness_level'], 'متوسط')
        self.assertIn('daily_calories', data)
        self.assertIn('bmr', data)
        self.assertIn('max_bpm', data)
        self.assertIn('macros', data)
        self.assertIn('nutrition_plan', data)
        self.assertIn('protein', data['macros'])

        saved_data = UserFitnessData.objects.filter(user=self.user).first()
        self.assertIsNotNone(saved_data)
        self.assertEqual(saved_data.max_bpm, 220 - 28)
        self.assertIsNotNone(saved_data.daily_calories)
        self.assertIsNotNone(saved_data.protein_grams)

    def test_prediction_api_missing_data(self):
        """Test prediction API error handling for missing fields."""
        self.client.login(username='testuser', password='password123')
        payload = {"age": 25}

        response = self.client.post(
            '/api/predict/',
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('Required fields missing', response.json()['error'])

    @patch('fitness_api.views.get_ai_service')
    def test_chatbot_api_success(self, mock_get_ai_service):
        """Test the chatbot API with mocked AI service response."""
        mock_service = MagicMock()
        mock_service.get_response.return_value = "Keep up the great work! Focus on protein intake."
        mock_get_ai_service.return_value = mock_service

        self.client.login(username='testuser', password='password123')

        payload = {
            "message": "Give me some motivation",
            "fitness_level": "Fair"
        }

        response = self.client.post(
            '/api/chat/',
            data=json.dumps(payload),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['assistant_response'],
            "Keep up the great work! Focus on protein intake."
        )

    @patch('fitness_api.views.get_ai_service')
    def test_chatbot_api_fallback_on_error(self, mock_get_ai_service):
        """Test chatbot API returns fallback response when AI service fails."""
        mock_service = MagicMock()
        mock_service.get_response.side_effect = Exception("RESOURCE_EXHAUSTED: Quota exceeded")
        mock_get_ai_service.return_value = mock_service

        self.client.login(username='testuser', password='password123')
        response = self.client.post(
            '/api/chat/',
            data=json.dumps({"message": "test"}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('assistant_response', response.json())
