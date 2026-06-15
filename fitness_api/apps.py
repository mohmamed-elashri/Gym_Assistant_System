from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class FitnessApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'fitness_api'
    
    def ready(self):
        """
        ✅ NEW: Validate ML models on startup.
        Ensures models are available before accepting requests.
        """
        try:
            from .model_manager import ModelRegistry
            logger.info("🔍 Validating ML models at startup...")
            ModelRegistry.validate_startup()
            logger.info("✅ All ML models validated successfully!")
        except Exception as e:
            logger.warning(f"⚠️ ML model validation failed at startup: {str(e)}")
            logger.warning("⚠️ Some features may be unavailable, but Django will continue to load.")
            # Don't raise here - allow Django to start even if models missing
            # The endpoints will return 503 if models not found
