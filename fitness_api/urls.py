from django.urls import path
from .views import (
    FitnessPredictionView,
    GymChatbotView,
    user_dashboard,
    WorkoutCaloriePredictorView,
)
from .views_workoutplan import WorkoutPlanView
from . import health
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("health/live/", health.live, name="health_live"),
    path("health/ready/", health.ready, name="health_ready"),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger_ui"),
    path("predict/", FitnessPredictionView.as_view(), name="fitness_predict"),
    path("chat/", GymChatbotView.as_view(), name="gym_chat"),
    path("dashboard/", user_dashboard, name="user_dashboard"),
    path("workout-calories/", WorkoutCaloriePredictorView, name="workout_calories"),
    path("workout-plan/", WorkoutPlanView.as_view(), name="workout_plan"),
]
