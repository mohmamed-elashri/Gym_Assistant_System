"""
Centralized ML model loading and caching with error handling.
Ensures models are loaded once, with proper validation and logging.
"""

import joblib
import os
import logging
from django.conf import settings
from .ml_exceptions import ModelLoadError

logger = logging.getLogger(__name__)


class ModelRegistry:
    """
    Central registry for all ML models.
    Handles loading, caching, and error management.
    """
    
    _models = {}
    _preprocessing_config = None
    
    MODEL_PATHS = {
        'fitness': 'models/fitness_level_model.pkl',
        'calorie': 'models/calories_model_final.pkl',
        'calorie_scaler': 'models/scaler_final.pkl',
        'calorie_features': 'models/features_list.pkl',
        'preprocessing': 'models/preprocessing_config.pkl',
    }
    
    @classmethod
    def get_model(cls, model_name):
        """
        Load and cache ML model with error handling.
        
        Args:
            model_name: 'fitness', 'calorie', or 'preprocessing'
        
        Returns:
            Loaded model object
        
        Raises:
            ModelLoadError: If file not found or corrupt
        """
        # Return cached model if available
        if model_name in cls._models:
            return cls._models[model_name]
        
        # Get full path
        model_path = cls._get_full_path(model_name)
        
        # Check file exists
        if not os.path.exists(model_path):
            error_msg = f"Model file not found: {model_path}"
            logger.error(f"❌ {error_msg}")
            raise ModelLoadError(model_name, error_msg)
        
        # Try to load
        try:
            model = joblib.load(model_path)
            logger.info(f"✅ Model loaded successfully: {model_name} from {model_path}")
            cls._models[model_name] = model
            return model
        
        except Exception as e:
            error_msg = f"Failed to load {model_name} from {model_path}: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise ModelLoadError(model_name, str(e))
    
    @classmethod
    def get_preprocessing_config(cls):
        """
        Load preprocessing configuration (gender mapping, fitness labels, etc).
        
        Returns:
            dict: Preprocessing configuration
        
        Raises:
            ModelLoadError: If config not found or corrupt
        """
        if cls._preprocessing_config is not None:
            return cls._preprocessing_config
        
        try:
            config_model = cls.get_model('preprocessing')
            cls._preprocessing_config = config_model
            logger.info("✅ Preprocessing config loaded")
            return config_model
        
        except ModelLoadError as e:
            logger.warning(f"⚠️ Preprocessing config not available: {str(e)}")
            # Return defaults if config not found
            defaults = {
                'version': '1.0',
                'gender_mapping': {'Male': 0, 'Female': 1},
                'fitness_labels': ['Poor', 'Fair', 'Good', 'Excellent'],  # Fallback
            }
            logger.warning(f"⚠️ Using default preprocessing config: {defaults}")
            cls._preprocessing_config = defaults
            return defaults
    
    EXPERIENCE_LEVEL_LABELS = {
        1: 'مبتدئ',
        2: 'متوسط',
        3: 'متقدم',
    }

    @classmethod
    def get_fitness_labels(cls):
        """
        Get fitness level label mapping.
        Returns from config if available, otherwise fallback to hardcoded.
        
        Returns:
            dict: maps model class values to human-readable labels
        """
        try:
            config = cls.get_preprocessing_config()
            labels = config.get('fitness_labels', [])
            
            if isinstance(labels, list):
                if labels and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in labels):
                    label_names = config.get('fitness_label_names', {})
                    if isinstance(label_names, dict) and label_names:
                        return {
                            int(key): str(value)
                            for key, value in label_names.items()
                        }
                    return {
                        int(value): cls.EXPERIENCE_LEVEL_LABELS.get(int(value), str(int(value)))
                        for value in labels
                    }
                return {i: label for i, label in enumerate(labels)}
            
            return labels
        
        except Exception as e:
            logger.warning(f"⚠️ Failed to get fitness labels from config: {str(e)}")
            defaults = {0: "Poor", 1: "Fair", 2: "Good", 3: "Excellent"}
            logger.warning(f"⚠️ Using fallback fitness labels: {defaults}")
            return defaults
    
    @classmethod
    def get_gender_mapping(cls):
        """
        Get gender mapping for encoding.
        
        Returns:
            dict: {'Male': 0, 'Female': 1, ...}
        """
        try:
            config = cls.get_preprocessing_config()
            mapping = config.get('gender_mapping', {})
            
            if mapping:
                return mapping
            
            defaults = {'Male': 0, 'Female': 1}
            logger.warning(f"⚠️ Using fallback gender mapping: {defaults}")
            return defaults
        
        except Exception as e:
            logger.warning(f"⚠️ Failed to get gender mapping: {str(e)}")
            defaults = {'Male': 0, 'Female': 1}
            return defaults
    
    @classmethod
    def _get_full_path(cls, model_name):
        """Get full file path for a model."""
        if model_name not in cls.MODEL_PATHS:
            raise ValueError(f"Unknown model: {model_name}")
        
        relative_path = cls.MODEL_PATHS[model_name]
        full_path = os.path.join(settings.BASE_DIR, relative_path)
        return full_path
    
    @classmethod
    def clear_cache(cls):
        """Clear cached models (useful for testing)."""
        cls._models.clear()
        cls._preprocessing_config = None
        logger.info("✅ Model cache cleared")
    
    @classmethod
    def validate_startup(cls):
        """
        Validate that all required models are available at startup.
        
        Raises:
            RuntimeError: If critical models unavailable
        """
        required_models = ['fitness', 'calorie']
        missing = []
        
        for model_name in required_models:
            try:
                cls.get_model(model_name)
                logger.info(f"✅ {model_name} model validated")
            except ModelLoadError as e:
                missing.append((model_name, str(e)))
                logger.warning(f"⚠️ {model_name} validation failed: {str(e)}")
        
        if missing:
            error_msg = f"CRITICAL: {len(missing)} models unavailable at startup:\n"
            for name, error in missing:
                error_msg += f"  - {name}: {error}\n"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        logger.info("✅ All models validated successfully at startup")
