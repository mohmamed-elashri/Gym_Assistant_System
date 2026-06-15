from django.contrib import admin
from .models import UserFitnessData, WorkoutPlan


@admin.register(UserFitnessData)
class UserFitnessDataAdmin(admin.ModelAdmin):
    list_display = ('user', 'fitness_level', 'daily_calories', 'max_bpm', 'created_at')
    list_filter = ('fitness_level', 'gender', 'activity_level')
    search_fields = ('user__username', 'fitness_level')
    readonly_fields = (
        'max_bpm', 'bmr', 'daily_calories',
        'protein_grams', 'carbs_grams', 'fats_grams', 'created_at',
    )


@admin.register(WorkoutPlan)
class WorkoutPlanAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan_title', 'difficulty_level', 'is_active', 'generated_at')
    list_filter = ('difficulty_level', 'is_active')
    search_fields = ('user__username', 'plan_title')
    readonly_fields = ('generated_at',)
