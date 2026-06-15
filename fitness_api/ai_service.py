"""
AI Service with multiple API key fallback support.

Supports Gemini and OpenRouter APIs with automatic fallback mechanism.
Keys are read from .env file and tried sequentially until one succeeds.
"""

import os
import logging
import time
from typing import Optional, List
from dotenv import load_dotenv
import google.genai as genai

import requests

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class AIService:
    """
    AI Service that supports multiple API keys with automatic fallback.
    
    Attempts to use Gemini keys first, then OpenRouter keys if all Gemini keys fail.
    Returns a static fallback response if all API calls fail.
    """
    
    # Configuration constants
    GEMINI_KEY_TIMEOUT = 10  # seconds
    OPENROUTER_KEY_TIMEOUT = 10  # seconds
    STATIC_FALLBACK_RESPONSE = (
        "I'm currently experiencing technical difficulties with my AI service. "
        "Please try again later or contact support if the problem persists."
    )
    
    # HTTP error codes that indicate a failed key
    FAILURE_HTTP_CODES = {401, 429, 500, 503}
    
    def __init__(self):
        """Initialize AIService and load API keys from .env file."""
        self.gemini_keys = self._load_gemini_keys()
        self.openrouter_keys = self._load_openrouter_keys()
        self.gemini_model = os.getenv("GENAI_MODEL", "models/gemini-2.0-flash").strip() or "models/gemini-2.0-flash"
        self.openrouter_model = os.getenv("OPENROUTER_MODEL", "openrouter/auto").strip() or "openrouter/auto"
        self.current_key_index = 0
        self.current_provider = None
        
        logger.info(f"AIService initialized with {len(self.gemini_keys)} Gemini keys "
                   f"and {len(self.openrouter_keys)} OpenRouter keys")
    
    def _load_gemini_keys(self) -> List[str]:
        """
        Load Gemini API keys from environment variables.
        
        Returns:
            List of non-empty Gemini API keys in order.
        """
        keys = []
        for i in range(1, 10):  # GEMINI_KEY_1 to GEMINI_KEY_9
            key = os.getenv(f"GEMINI_KEY_{i}", "").strip()
            if key:
                keys.append(key)
        return keys
    
    def _load_openrouter_keys(self) -> List[str]:
        """
        Load OpenRouter API keys from environment variables.
        
        Returns:
            List of non-empty OpenRouter API keys in order.
        """
        keys = []
        for i in range(1, 12):  # OPENROUTER_KEY_1 to OPENROUTER_KEY_11
            key = os.getenv(f"OPENROUTER_KEY_{i}", "").strip()
            if key:
                keys.append(key)
        return keys
    
    def get_response(self, prompt: str) -> str:
        """
        Get AI response for the given prompt using fallback mechanism.
        
        Tries Gemini keys first, then OpenRouter keys, then returns static fallback.
        
        Args:
            prompt: The user's prompt/question.
            
        Returns:
            AI-generated response or static fallback response if all APIs fail.
        """
        if not prompt or not prompt.strip():
            logger.warning("Empty prompt provided to get_response")
            return "Please provide a valid prompt."
        
        # Try Gemini keys
        response = self._try_gemini_keys(prompt)
        if response:
            return response
        
        # Try OpenRouter keys
        response = self._try_openrouter_keys(prompt)
        if response:
            return response
        
        # All keys failed, return static fallback
        logger.error("All API keys failed. Returning static fallback response.")
        return self.STATIC_FALLBACK_RESPONSE
    
    def _try_gemini_keys(self, prompt: str) -> Optional[str]:
        """
        Try Gemini API keys sequentially until one succeeds.
        
        Args:
            prompt: The user's prompt.
            
        Returns:
            Response string if successful, None if all keys fail.
        """
        if not self.gemini_keys:
            logger.warning("No Gemini keys configured in environment")
            return None
        
        for index, key in enumerate(self.gemini_keys):
            try:
                logger.info(f"Attempting Gemini key {index + 1}/{len(self.gemini_keys)}")
                
                # Create client and get response with timeout
                client = genai.Client(api_key=key)
                
                start_time = time.time()
                response = client.models.generate_content(model=self.gemini_model, contents=prompt)

                elapsed_time = time.time() - start_time
                
                # Check for timeout
                if elapsed_time > self.GEMINI_KEY_TIMEOUT:
                    logger.warning(
                        f"Gemini key {index + 1} timed out after {elapsed_time:.2f}s"
                    )
                    continue
                
                # Check for empty response
                if not response or not response.text or not response.text.strip():
                    logger.warning(f"Gemini key {index + 1} returned empty response")
                    continue
                
                logger.info(f"Gemini key {index + 1} succeeded (response: {len(response.text)} chars)")
                self.current_key_index = index
                self.current_provider = "gemini"
                return response.text.strip()
                
            except Exception as e:
                error_msg = str(e)
                logger.warning(
                    f"Gemini key {index + 1} failed: {type(e).__name__}: {error_msg}"
                )
                
                # Check for specific failure reasons
                if "401" in error_msg or "authentication" in error_msg.lower():
                    logger.warning(f"Gemini key {index + 1}: Authentication failed (401)")
                elif "429" in error_msg or "quota" in error_msg.lower():
                    logger.warning(f"Gemini key {index + 1}: Quota exceeded (429)")
                elif "500" in error_msg or "503" in error_msg:
                    logger.warning(f"Gemini key {index + 1}: Server error")
                
                continue
        
        logger.warning("All Gemini keys exhausted")
        return None
    
    def _try_openrouter_keys(self, prompt: str) -> Optional[str]:
        """
        Try OpenRouter API keys sequentially until one succeeds.
        
        Args:
            prompt: The user's prompt.
            
        Returns:
            Response string if successful, None if all keys fail.
        """
        if not self.openrouter_keys:
            logger.warning("No OpenRouter keys configured in environment")
            return None
        
        openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
        
        for index, key in enumerate(self.openrouter_keys):
            try:
                logger.info(
                    f"Attempting OpenRouter key {index + 1}/{len(self.openrouter_keys)}"
                )
                
                headers = {
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://gymassistant.local",
                }
                
                payload = {
                    "model": self.openrouter_model,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.7,
                }
                
                start_time = time.time()
                response = requests.post(
                    openrouter_url,
                    json=payload,
                    headers=headers,
                    timeout=self.OPENROUTER_KEY_TIMEOUT
                )
                elapsed_time = time.time() - start_time
                
                # Check HTTP status codes
                if response.status_code in self.FAILURE_HTTP_CODES:
                    logger.warning(
                        f"OpenRouter key {index + 1} failed with HTTP {response.status_code}"
                    )
                    continue
                
                # Raise for other HTTP errors
                response.raise_for_status()
                
                # Parse response
                data = response.json()
                
                # Check for error in response
                if "error" in data:
                    logger.warning(
                        f"OpenRouter key {index + 1} returned error: {data['error']}"
                    )
                    continue
                
                # Extract message content
                if (
                    "choices" in data
                    and len(data["choices"]) > 0
                    and "message" in data["choices"][0]
                    and "content" in data["choices"][0]["message"]
                ):
                    content = data["choices"][0]["message"]["content"].strip()
                    
                    if not content:
                        logger.warning(f"OpenRouter key {index + 1} returned empty content")
                        continue
                    
                    logger.info(
                        f"OpenRouter key {index + 1} succeeded in {elapsed_time:.2f}s "
                        f"(response: {len(content)} chars)"
                    )
                    self.current_key_index = index
                    self.current_provider = "openrouter"
                    return content
                else:
                    logger.warning(
                        f"OpenRouter key {index + 1} response has unexpected format"
                    )
                    continue
                    
            except requests.Timeout:
                logger.warning(
                    f"OpenRouter key {index + 1} timed out after "
                    f"{self.OPENROUTER_KEY_TIMEOUT}s"
                )
                continue
            except requests.RequestException as e:
                logger.warning(
                    f"OpenRouter key {index + 1} network error: {type(e).__name__}: {str(e)}"
                )
                continue
            except Exception as e:
                logger.warning(
                    f"OpenRouter key {index + 1} failed: {type(e).__name__}: {str(e)}"
                )
                continue
        
        logger.warning("All OpenRouter keys exhausted")
        return None
    
    def get_last_used_key_info(self) -> dict:
        """
        Get information about the last successfully used API key.
        
        Returns:
            Dictionary with provider and key index information.
        """
        return {
            "provider": self.current_provider,
            "key_index": self.current_key_index + 1 if self.current_provider else None
        }


# Module-level instance for convenience
_ai_service_instance = None


def get_ai_service() -> AIService:
    """
    Get singleton instance of AIService.
    
    Returns:
        AIService instance.
    """
    global _ai_service_instance
    if _ai_service_instance is None:
        _ai_service_instance = AIService()
    return _ai_service_instance

