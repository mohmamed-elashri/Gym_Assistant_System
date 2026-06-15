from rest_framework.views import APIView
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import WorkoutPlan, UserFitnessData
from .ai_service import AIService, get_ai_service
from django.utils.html import strip_tags
import logging
import os


logger = logging.getLogger(__name__)
GENAI_DEBUG_MODE = os.environ.get('GENAI_DEBUG_MODE', 'false').lower() == 'true'
WORKOUT_PLAN_FALLBACK = "الخدمة الذكية غير متاحة حالياً. خطة تمارين عامة:\n\nأسبوع 1-4:\nيوم1: Full Body (Squat 3x12, Pushup 3x10, Pullup 3x8)\nيوم2: راحة\nيوم3: Upper Body\nيوم4: كارديو خفيف\nيوم5: Lower Body + Core\nيوم6: راحة\nيوم7: Mobility وتمدد"


def generate_workout_plan_text(prompt):
    if GENAI_DEBUG_MODE:
        return WORKOUT_PLAN_FALLBACK

    ai_service = get_ai_service()
    response = ai_service.get_response(prompt)
    if response == AIService.STATIC_FALLBACK_RESPONSE:
        return WORKOUT_PLAN_FALLBACK

    key_info = ai_service.get_last_used_key_info()
    logger.info(
        "Workout plan generated using %s key #%s",
        key_info["provider"],
        key_info["key_index"],
    )
    return response

@method_decorator(csrf_exempt, name='dispatch')
class WorkoutPlanView(APIView):
    def post(self, request):
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required."}, status=401)

        try:
            try:
                fitness_data = UserFitnessData.objects.filter(user=request.user).latest('created_at')
            except UserFitnessData.DoesNotExist:
                return Response(
                    {"error": "No fitness data found. Complete analysis first."},
                    status=400,
                )

            fitness_level = fitness_data.fitness_level
            activity_level = fitness_data.activity_level
            daily_calories = fitness_data.daily_calories
            age = fitness_data.age
            gender = 'ذكر' if fitness_data.gender == 0 else 'أنثى'

            # Gemini prompt for Arabic workout plan with compact context
            prompt = f"""
أنت مدرب جيم محترف. أنشئ خطة تمارين مخصصة لمدة 4 أسابيع.
بيانات العميل الأساسية:
- العمر: {age}
- الجنس: {gender}
- مستوى اللياقة: {fitness_level}
- مستوى النشاط: {activity_level}
- سعرات يومية مستهدفة: {daily_calories}

المطلوب باختصار:
- 4 إلى 5 أيام تمرين أسبوعياً
- تمارين قوة + كارديو + إحماء + تبريد
- تقدم أسبوعي بسيط
- نصائح أمان واستشفاء
- الرد بالعربية بشكل منظم ومختصر وعملي

هيكل الرد:
1. عنوان
2. نظرة عامة قصيرة
3. جدول أسبوعي
4. أهم التمارين بالمجموعات والتكرارات
5. نصائح تغذية وراحة قصيرة
            """

            plan_text = generate_workout_plan_text(prompt)
            # Ensure any HTML returned by AI is stripped to avoid XSS
            try:
                plan_text = strip_tags(plan_text)
            except Exception:
                # fallback: keep original text
                pass

            # Generate JSON structure (simplified)
            plan_json = {
                "weeks": 4,
                "days": 5,
                "difficulty": fitness_level.lower(),
                "exercises": [
                    {"name": "Squat", "sets": 3, "reps": 12},
                    {"name": "Bench Press", "sets": 3, "reps": 10}
                ]
            }

            # Save plan
            plan = WorkoutPlan.objects.create(
                user=request.user,
                fitness_data=fitness_data,
                plan_title=f"خطة {fitness_level} مخصصة",
                plan_json=plan_json,
                plan_text=plan_text,
                difficulty_level=fitness_level.lower(),
                equipment_needed="جيم/منزل"
            )

            return Response({
                "status": "success",
                "plan_id": plan.id,
                "workout_plan": plan.plan_text,
                "title": plan.plan_title,
                "difficulty": plan.difficulty_level
            })

        except Exception as e:
            logger.error("Workout plan generation failed: %s", str(e), exc_info=True)
            return Response({"error": "Failed to generate workout plan."}, status=500)
