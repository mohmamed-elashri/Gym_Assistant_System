from django.urls import path
from .views import FitnessPredictionView, GymChatbotView, user_dashboard, WorkoutCaloriePredictorView
from .views_workoutplan import WorkoutPlanView

urlpatterns = [
    path('predict/', FitnessPredictionView.as_view(), name='fitness_predict'),
    path('chat/', GymChatbotView.as_view(), name='gym_chat'),
    path('dashboard/', user_dashboard, name='user_dashboard'),
    path('workout-calories/', WorkoutCaloriePredictorView, name='workout_calories'),
    path('workout-plan/', WorkoutPlanView.as_view(), name='workout_plan'),
]
