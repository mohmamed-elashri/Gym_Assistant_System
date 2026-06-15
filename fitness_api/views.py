import os
import json
import logging
import re
from datetime import timedelta

from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import JsonResponse
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import UserFitnessData, WorkoutPlan
from .ai_service import get_ai_service
from .utils import prepare_fitness_model_input
from .model_manager import ModelRegistry
from .ml_exceptions import ModelLoadError, PredictionError, InputValidationError
from .calorie_predictor import predict_calories
from .nutrition_calculator import NutritionCalculator

# Custom DRF exception handler
def custom_exception_handler(exc, context):
    """Custom exception handler to avoid serialization errors"""
    from rest_framework.views import exception_handler
    response = exception_handler(exc, context)
    
    if response is None:
        # If DRF doesn't handle it, try to return a plain error
        return JsonResponse({'error': str(exc), 'success': False}, status=500)
    
    return response

# ✅ Chat history configuration
GENAI_MAX_CHAT_HISTORY = int(os.environ.get('GENAI_MAX_CHAT_HISTORY', '4'))

logger = logging.getLogger(__name__)


def _limit_chat_history(history, max_items=GENAI_MAX_CHAT_HISTORY):
    """Limit chat history to prevent context overflow."""
    if not isinstance(history, list):
        return []
    trimmed = []
    for item in history[-max_items:]:
        if isinstance(item, dict):
            role = str(item.get('role', 'user'))[:20]
            content = str(item.get('content', ''))[:500]
            trimmed.append({'role': role, 'content': content})
        else:
            trimmed.append({'role': 'user', 'content': str(item)[:500]})
    return trimmed


def build_chat_prompt(user_query, fitness_level='Unknown', burned_calories=None, profile_context=None, history=None, live_metrics=None):
    """Build a comprehensive prompt for the AI assistant."""
    profile_context = profile_context or {}
    live_metrics = live_metrics or {}
    history = _limit_chat_history(history)
    system_lines = [
        'You are an expert AI Gym Assistant.',
        'Give concise, safe, motivating fitness guidance.',
        'Use the saved nutrition profile and avoid repeating long boilerplate.',
        f"Fitness level: '{fitness_level}'."
    ]

    if profile_context:
        system_lines.append(
            'Saved user profile: '
            f"daily_calories={profile_context.get('daily_calories', 'unknown')}, "
            f"protein_grams={profile_context.get('protein_grams', 'unknown')}, "
            f"carbs_grams={profile_context.get('carbs_grams', 'unknown')}, "
            f"fats_grams={profile_context.get('fats_grams', 'unknown')}, "
            f"activity_level={profile_context.get('activity_level', 'unknown')}."
        )

    live_metric_parts = []
    for key in ['weight', 'height', 'age', 'activity_level', 'daily_calories', 'bmr']:
        value = live_metrics.get(key)
        if value not in [None, '', 'Unknown', '--']:
            live_metric_parts.append(f'{key}={value}')

    if live_metric_parts:
        system_lines.append('Live analysis metrics: ' + ', '.join(live_metric_parts) + '.')

    prompt_parts = ['\n'.join(system_lines)]

    if history:
        prompt_parts.append('Recent chat history (last messages only):')
        for item in history:
            prompt_parts.append(f"{item['role']}: {item['content']}")

    prompt_parts.append(f'User question: {user_query}')

    if burned_calories:
        prompt_parts.append(f'Workout estimate: user burned approximately {burned_calories} calories.')

    prompt_parts.append('Provide practical, personalized advice in Arabic when appropriate.')
    return '\n'.join(prompt_parts)


def get_fallback_response(prompt):
    """Generate fallback responses when AI is unavailable."""
    prompt_lower = prompt.lower()

    calories_match = re.search(r'burned approximately (\d+\.?\d*) calories', prompt)
    burned_calories = calories_match.group(1) if calories_match else None
    
    if burned_calories:
        return f"بناءً على تحليل تمرينك، حرقت حوالي {burned_calories} سعرة حرارية! هذا أداء رائع. استمر في التمارين بانتظام وتناول غذاء متوازن. 💪"
    
    if 'fitness_level' in prompt_lower:
        fitness_match = re.search(r"'(.*?)'", prompt)
        fitness_level = fitness_match.group(1) if fitness_match else 'ممتاز'
        return f"مرحباً! مستوى لياقتك البدنية '{fitness_level}' يبدو جيداً. تذكر دائماً استشارة الطبيب قبل البدء في أي برنامج رياضي، وابدأ بالتمارين التدريجية."
    
    return "مرحباً! أنا مساعدك الرياضي. حالياً الخدمة الذكية غير متاحة، لكن إليك نصائح عامة مفيدة:\n\n• اشرب 2-3 لتر ماء يومياً\n• تناول 1.6-2.2 جرام بروتين لكل كيلو من وزنك\n• تمرن 3-5 مرات أسبوعياً لمدة 30-60 دقيقة\n• احصل على 7-9 ساعات نوم يومياً\n\nابق قوياً! 💪"


def landing_page(request):
    return render(request, 'landing.html')


def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    for field in form.fields.values():
        field.widget.attrs.update({
            'class': 'w-full bg-slate-800/50 p-3 rounded-xl neon-border outline-none text-white',
            'placeholder': field.label
        })
    return render(request, 'signup.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    for field in form.fields.values():
        field.widget.attrs.update({
            'class': 'w-full bg-slate-800/50 p-3 rounded-xl neon-border outline-none text-white',
            'placeholder': field.label
        })
    return render(request, 'login.html', {'form': form})


@login_required(login_url='/landing/')
def index(request):
    return render(request, 'index.html')


@login_required(login_url='/landing/')
def user_dashboard(request):
    user_records = UserFitnessData.objects.filter(user=request.user).order_by('created_at')
    profile = user_records.last() if user_records.exists() else None

    weight_labels = []
    weight_values = []
    activity_log = []
    total_workouts = user_records.count()
    current_streak = 0
    achievements_count = 0
    # تهيئة البيانات بقيم صفرية بدلاً من نص فارغ لضمان عمل الرسم البياني دائماً
    macro_data = json.dumps({'protein': 0, 'carbs': 0, 'fats': 0})

    latest_plan = WorkoutPlan.objects.filter(user=request.user).first()

    if user_records.exists():
        weight_labels = [record.created_at.strftime('%d %b') for record in user_records]
        weight_values = [round(record.weight, 1) for record in user_records]

        recent_records = list(user_records.order_by('-created_at')[:10])
        activity_log = [
            {
                'date': record.created_at.strftime('%Y-%m-%d'),
                'activity': (
                    f"تحليل اللياقة: {record.weight} كجم — "
                    f"مستوى {record.fitness_level} — {record.daily_calories} سعرة"
                ),
            }
            for record in recent_records
        ]

        unique_dates = sorted({record.created_at.date() for record in user_records})
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        if unique_dates:
            last_activity = unique_dates[-1]
            # حساب الـ Streak فقط إذا كان المستخدم نشطاً اليوم أو أمس
            if last_activity >= yesterday:
                streak = 0
                check_date = last_activity
                while check_date in unique_dates:
                    streak += 1
                    check_date -= timedelta(days=1)
                current_streak = streak

    if profile:
        if total_workouts >= 1:
            achievements_count += 1
        if total_workouts >= 3:
            achievements_count += 1
        if current_streak >= 2:
            achievements_count += 1
        if profile.bmi_category == 'normal':
            achievements_count += 1
        if latest_plan:
            achievements_count += 1
            
        # تجهيز بيانات المغذيات للرسم البياني (Pie Chart)
        macro_data = json.dumps({
            'protein': float(profile.protein_grams or 0),
            'carbs': float(profile.carbs_grams or 0),
            'fats': float(profile.fats_grams or 0)
        })

    context = {
        'profile': profile,
        'weight_labels': json.dumps(weight_labels, ensure_ascii=False),
        'weight_values': json.dumps(weight_values),
        'macro_data': macro_data,
        'activity_log': activity_log,
        'total_workouts': total_workouts,
        'current_streak': current_streak,
        'achievements_count': achievements_count,
        'latest_plan': latest_plan,
        'has_weight_history': len(weight_values) > 1,
    }
    return render(request, 'dashboard.html', context)


def get_fitness_model():
    """Get cached fitness model with error handling."""
    try:
        return ModelRegistry.get_model('fitness')
    except ModelLoadError as e:
        logger.error(f"Failed to load fitness model: {str(e)}")
        raise


def get_fitness_labels():
    """Get fitness level labels from preprocessing config."""
    return ModelRegistry.get_fitness_labels()


@method_decorator(csrf_exempt, name='dispatch')
class FitnessPredictionView(APIView):
    def post(self, request):
        data = request.data
        try:
            # ✅ Validate required fields
            required_fields = ['age', 'gender', 'weight', 'height']
            missing = [field for field in required_fields 
                      if field not in data or data[field] in [None, '']]
            if missing:
                raise InputValidationError(
                    field_name=','.join(missing),
                    details="Required fields missing"
                )

            # ✅ Extract and validate inputs
            age = int(data['age'])
            gender = int(data['gender'])
            weight = float(data['weight'])
            height = float(data['height'])  # in meters
            
            # Validate ranges
            if not (1 <= age <= 150):
                raise InputValidationError('age', f"Age must be 1-150, got {age}")
            if gender not in [0, 1]:
                raise InputValidationError('gender', f"Gender must be 0 or 1, got {gender}")
            if not (10 <= weight <= 300):
                raise InputValidationError('weight', f"Weight must be 10-300 kg, got {weight}")
            if not (0.5 <= height <= 3.0):
                raise InputValidationError('height', f"Height must be 0.5-3.0 m, got {height}")
            
            # Optional fields with validation (no fake defaults!)
            avg_bpm = int(data.get('avg_bpm', 100)) if data.get('avg_bpm') else 100
            resting_bpm = int(data.get('resting_bpm', 70)) if data.get('resting_bpm') else 70
            fat_percentage = float(data.get('fat_percentage', 20)) if data.get('fat_percentage') else 20
            water_intake = float(data.get('water_intake', 3)) if data.get('water_intake') else 3
            workout_frequency = int(data.get('workout_frequency', 3)) if data.get('workout_frequency') else 3
            duration = float(data.get('duration', 30)) if data.get('duration') else 30  # in minutes
            
            activity_level = data.get('activity_level', 'moderate')
            valid_activity_levels = ['sedentary', 'light', 'moderate', 'active', 'very_active']
            if activity_level not in valid_activity_levels:
                activity_level = 'moderate'

            # ✅ Fitness level prediction using centralized helper
            try:
                fit_input = prepare_fitness_model_input(
                    age=age, gender=gender, weight_kg=weight, height_m=height,
                    max_bpm=220-age, avg_bpm=avg_bpm, resting_bpm=resting_bpm,
                    fat_percentage=fat_percentage, water_intake=water_intake,
                    workout_frequency=workout_frequency
                )
                fitness_model = get_fitness_model()
                fitness_idx = fitness_model.predict(fit_input)[0]
                
                # ✅ Use labels from config, not hardcoded!
                fitness_labels = get_fitness_labels()
                fitness_label = fitness_labels.get(fitness_idx, str(fitness_idx))
                
            except Exception as e:
                raise PredictionError("Fitness level classification failed", str(e))
            
            # ✅ Calorie prediction using CENTRALIZED helper with VALIDATION
            try:
                workout_calories = predict_calories(
                    gender=gender,
                    age=age,
                    height_cm=height * 100,
                    weight_kg=weight,
                    duration=duration,
                    heart_rate=avg_bpm
                )
            except Exception as e:
                raise PredictionError("Calorie prediction failed", str(e))
            
            # ✅ حساب التغذية الكاملة باستخدام الحاسبة المركزية لضمان دقة البيانات
            nutrition = NutritionCalculator.calculate_full_nutrition(
                weight_kg=weight,
                height_m=height,
                age_years=age,
                activity_level=activity_level,
                gender=gender
            )
            
            # ✅ حفظ في قاعدة البيانات مع تمرير كافة القيم المحسوبة
            fitness_data = UserFitnessData.objects.create(
                user=request.user if request.user.is_authenticated else None,
                gender=gender, 
                age=age, 
                weight=weight,
                height=height, 
                fitness_level=fitness_label,
                activity_level=activity_level,
                bmr=nutrition['bmr'],
                daily_calories=nutrition['daily_calories'],
                protein_grams=nutrition['protein_grams'],
                carbs_grams=nutrition['carbs_grams'],
                fats_grams=nutrition['fats_grams'],
                max_bpm=nutrition['max_bpm']
            )

            return Response({
                "status": "success",
                "fitness_level": fitness_label,
                "daily_calories": fitness_data.daily_calories,
                "bmr": fitness_data.bmr,
                "max_bpm": fitness_data.max_bpm,
                "protein": fitness_data.protein_grams,
                "carbs": fitness_data.carbs_grams,
                "fats": fitness_data.fats_grams,
                "macros": {
                    "protein": fitness_data.protein_grams,
                    "carbs": fitness_data.carbs_grams,
                    "fats": fitness_data.fats_grams
                },
                "workout_calories": f"{workout_calories:.2f}",
                "nutrition_plan": {
                    "description": f"خطة تغذية يومية لمستوى نشاط {activity_level}",
                    "recommendations": [
                        f"البروتين: {fitness_data.protein_grams} جرام يومياً",
                        f"الكاربوهيدرات: {fitness_data.carbs_grams} جرام يومياً", 
                        f"الدهون: {fitness_data.fats_grams} جرام يومياً"
                    ]
                },
                "nutrition_recommendations": "\n".join([
                    f"البروتين: {fitness_data.protein_grams} جرام يومياً",
                    f"الكاربوهيدرات: {fitness_data.carbs_grams} جرام يومياً",
                    f"الدهون: {fitness_data.fats_grams} جرام يومياً"
                ])
            })
        
        except InputValidationError as e:
            logger.warning(f"Input validation error: {str(e)}")
            return Response(
                {"error": e.message, "code": e.error_code},
                status=400
            )
        
        except ModelLoadError as e:
            logger.error(f"Model loading error: {str(e)}")
            return Response(
                {"error": "Model service unavailable. Please try again later.",
                 "code": e.error_code},
                status=503
            )
        
        except PredictionError as e:
            logger.error(f"Prediction error: {str(e)}")
            return Response(
                {"error": "Prediction failed. Please check your input.",
                 "code": e.error_code},
                status=400
            )
        
        except Exception as e:
            logger.error(f"Unexpected error in FitnessPredictionView: {str(e)}", exc_info=True)
            return Response(
                {"error": "An unexpected error occurred. Please contact support.",
                 "code": "UNEXPECTED_ERROR"},
                status=500
            )

# 4. Gym Chatbot (AI Assistant) with automatic key fallback
@method_decorator(csrf_exempt, name='dispatch')
class GymChatbotView(APIView):
    def post(self, request):
        """Get fitness advice from AI assistant with automatic provider fallback."""
        user_query = request.data.get('message')
        fitness_level = request.data.get('fitness_level', 'Unknown')
        history = request.data.get('history', [])
        live_metrics = {
            'weight': request.data.get('weight'),
            'height': request.data.get('height'),
            'age': request.data.get('age'),
            'activity_level': request.data.get('activity_level'),
            'daily_calories': request.data.get('daily_calories'),
            'bmr': request.data.get('bmr'),
        }
        
        # Extract duration and heart rate from message using regex
        duration_match = re.search(r'(\d+)\s*(?:دقيق|min|دقائق)', user_query)
        heart_rate_match = re.search(r'(\d+)\s*(?:نبض|heart|pulse)', user_query)
        
        burned_calories = None
        if duration_match and heart_rate_match:
            duration = float(duration_match.group(1))  # in minutes
            heart_rate = float(heart_rate_match.group(1))
            
            # If user is authenticated, try to get their profile data
            if request.user.is_authenticated:
                try:
                    user_profile = UserFitnessData.objects.filter(user=request.user).latest('created_at')
                    sex = user_profile.gender
                    age = user_profile.age
                    weight = user_profile.weight
                    height = user_profile.height  # in meters
                    
                    burned_calories = round(float(
                        predict_calories(
                            gender=sex,
                            age=age,
                            height_cm=height * 100,
                            weight_kg=weight,
                            duration=duration,
                            heart_rate=heart_rate
                        )
                    ), 2)
                except ValueError as e:
                    logger.warning("Calorie prediction validation failed in chat: %s", str(e))
                except UserFitnessData.DoesNotExist:
                    pass
                except Exception as e:
                    logger.warning(f"Calorie prediction failed in chat: {str(e)}")
        
        profile_context = {}
        if request.user.is_authenticated:
            latest_profile = UserFitnessData.objects.filter(user=request.user).order_by('-created_at').first()
            if latest_profile:
                profile_context = {
                    'daily_calories': latest_profile.daily_calories,
                    'protein_grams': latest_profile.protein_grams,
                    'carbs_grams': latest_profile.carbs_grams,
                    'fats_grams': latest_profile.fats_grams,
                    'activity_level': latest_profile.activity_level,
                }

        prompt = build_chat_prompt(
            user_query=user_query,
            fitness_level=fitness_level,
            burned_calories=burned_calories,
            profile_context=profile_context,
            history=history,
            live_metrics=live_metrics,
        )
        
        # ✅ Use AIService with automatic fallback
        try:
            ai_service = get_ai_service()
            response = ai_service.get_response(prompt)
            key_info = ai_service.get_last_used_key_info()
            logger.info(f"AI response generated using {key_info['provider']} key #{key_info['key_index']}")
            return Response({"assistant_response": response})
        except Exception as e:
            logger.error(f"Chatbot error: {str(e)}", exc_info=True)
            # Use fallback response if AI fails
            fallback_response = get_fallback_response(prompt)
            return Response({"assistant_response": fallback_response})






@csrf_exempt
def WorkoutCaloriePredictorView(request):
    """
    Predict calories burned during workout.
    ✅ FIXED: Uses centralized scaler-aware calorie predictor helper
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=400)
    
    try:
        # Parse JSON request
        data = json.loads(request.body)
        
        # Extract parameters
        duration = float(data.get('duration', 30))  # in minutes
        heart_rate = float(data.get('heart_rate', 140))
        weight = float(data.get('weight', 70))
        sex = int(data.get('gender', 0))
        age = int(data.get('age', 25))
        height = float(data.get('height', 1.75))  # in meters

        burned_calories = float(
            predict_calories(
                gender=sex,
                age=age,
                height_cm=height * 100,
                weight_kg=weight,
                duration=duration,
                heart_rate=heart_rate
            )
        )
        
        response_data = {
            'burned_calories': round(burned_calories, 2),
            'duration': float(duration),
            'heart_rate': float(heart_rate),
            'weight': float(weight),
            'success': True,
            'code': 'SUCCESS'
        }
        return JsonResponse(response_data)
    
    except ValueError as e:
        logger.warning("Input validation error in WorkoutCaloriePredictorView: %s", str(e))
        return JsonResponse({
            "error": f"Invalid input: {str(e)}",
            "code": "INPUT_VALIDATION_ERROR",
            "success": False
        }, status=400)
    
    except (ModelLoadError, PredictionError) as e:
        logger.error(f"ML error in WorkoutCaloriePredictorView: {str(e)}")
        return JsonResponse({
            "error": "Prediction service unavailable",
            "code": e.error_code,
            "success": False
        }, status=503)
    
    except InputValidationError as e:
        logger.warning(f"Input validation error: {str(e)}")
        return JsonResponse({
            "error": f"Invalid input: {e.message}",
            "code": e.error_code,
            "success": False
        }, status=400)
    
    except Exception as e:
        logger.error(f"Unexpected error in WorkoutCaloriePredictorView: {str(e)}", exc_info=True)
        # ✅ DO NOT leak error details!
        return JsonResponse({
            "error": "Prediction failed. Please try again.",
            "code": "UNEXPECTED_ERROR",
            "success": False
        }, status=500)
