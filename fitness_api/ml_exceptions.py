"""
Custom exceptions for ML model operations.
Provides clear error messages and logging for ML-related failures.
"""

import logging

logger = logging.getLogger(__name__)


class MLException(Exception):
    """Base exception for ML operations."""
    def __init__(self, message, error_code=None, internal_error=None):
        self.message = message
        self.error_code = error_code or 'ML_ERROR'
        self.internal_error = internal_error
        super().__init__(message)
        
        if internal_error:
            logger.error(f"{self.error_code}: {message} | Internal: {str(internal_error)}")
        else:
            logger.warning(f"{self.error_code}: {message}")


class ModelLoadError(MLException):
    """Failed to load ML model."""
    def __init__(self, model_name, internal_error=None):
        message = f"Failed to load model: {model_name}"
        super().__init__(message, error_code='MODEL_LOAD_FAILED', internal_error=internal_error)


class PredictionError(MLException):
    """ML prediction failed."""
    def __init__(self, details, internal_error=None):
        message = f"Prediction failed: {details}"
        super().__init__(message, error_code='PREDICTION_FAILED', internal_error=internal_error)


class InputValidationError(MLException):
    """Input validation failed."""
    def __init__(self, field_name, details):
        message = f"Invalid input for {field_name}: {details}"
        super().__init__(message, error_code='INVALID_INPUT')


class DataAlignmentError(MLException):
    """Data alignment/unit mismatch."""
    def __init__(self, details):
        message = f"Data alignment error: {details}"
        super().__init__(message, error_code='DATA_MISMATCH')


class PreprocessingError(MLException):
    """Preprocessing or encoding failed."""
    def __init__(self, details):
        message = f"Preprocessing error: {details}"
        super().__init__(message, error_code='PREPROCESSING_FAILED')
