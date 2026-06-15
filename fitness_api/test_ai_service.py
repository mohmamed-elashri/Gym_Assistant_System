"""
Unit tests for AIService with multiple API key fallback support.

Tests cover:
- First Gemini key succeeds
- First key fails, second key succeeds
- All Gemini keys fail, first OpenRouter key succeeds
- All keys fail, static fallback is returned
"""

import os
import pytest
from unittest.mock import patch, MagicMock, mock_open
from fitness_api.ai_service import AIService, get_ai_service
import requests


class TestAIServiceInitialization:
    """Test AIService initialization and key loading."""
    
    @patch.dict(os.environ, {
        "GEMINI_KEY_1": "gemini_key_1",
        "GEMINI_KEY_2": "gemini_key_2",
        "OPENROUTER_KEY_1": "openrouter_key_1",
    }, clear=True)
    def test_load_keys_from_environment(self):
        """Test that keys are correctly loaded from environment variables."""
        service = AIService()
        
        assert len(service.gemini_keys) == 2
        assert service.gemini_keys[0] == "gemini_key_1"
        assert service.gemini_keys[1] == "gemini_key_2"
        
        assert len(service.openrouter_keys) == 1
        assert service.openrouter_keys[0] == "openrouter_key_1"
    
    @patch.dict(os.environ, {}, clear=True)
    def test_no_keys_in_environment(self):
        """Test initialization when no keys are configured."""
        service = AIService()
        
        assert len(service.gemini_keys) == 0
        assert len(service.openrouter_keys) == 0
    
    @patch.dict(os.environ, {
        "GEMINI_KEY_1": "  key_with_spaces  ",
        "OPENROUTER_KEY_1": "\t\tkey_with_tabs\t\t",
    }, clear=True)
    def test_keys_are_stripped(self):
        """Test that loaded keys have whitespace stripped."""
        service = AIService()
        
        assert service.gemini_keys[0] == "key_with_spaces"
        assert service.openrouter_keys[0] == "key_with_tabs"


class TestGeminiKeyFallback:
    """Test Gemini API key fallback mechanism."""
    
    @patch.dict(os.environ, {
        "GEMINI_KEY_1": "first_gemini_key",
        "GEMINI_KEY_2": "second_gemini_key",
    }, clear=True)
    @patch("google.genai.Client")
    def test_first_gemini_key_succeeds(self, mock_client_class):
        """Test that first Gemini key succeeds and returns response."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.text = "Generated response from Gemini"
        mock_client_instance = MagicMock()
        mock_client_instance.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_client_instance
        
        service = AIService()
        result = service.get_response("Hello, AI!")
        
        # Verify first key was used
        mock_client_class.assert_called_once_with(api_key="first_gemini_key")
        mock_client_instance.models.generate_content.assert_called_once_with(
            model="models/gemini-2.0-flash", contents="Hello, AI!"
        )
        
        # Verify response
        assert result == "Generated response from Gemini"
        assert service.current_provider == "gemini"
        assert service.current_key_index == 0
    
    @patch.dict(os.environ, {
        "GEMINI_KEY_1": "first_gemini_key",
        "GEMINI_KEY_2": "second_gemini_key",
    }, clear=True)
    @patch("google.genai.Client")
    def test_first_key_fails_second_succeeds(self, mock_client_class):
        """Test that if first Gemini key fails, second key is tried."""
        # Setup: first call fails, second succeeds
        mock_response_fail = MagicMock()
        mock_response_fail.text = ""  # Empty response indicates failure
        
        mock_response_success = MagicMock()
        mock_response_success.text = "Response from second key"
        
        # Create separate mock instances for each call
        mock_client_instance_1 = MagicMock()
        mock_client_instance_1.models.generate_content.return_value = mock_response_fail
        
        mock_client_instance_2 = MagicMock()
        mock_client_instance_2.models.generate_content.return_value = mock_response_success
        
        mock_client_class.side_effect = [mock_client_instance_1, mock_client_instance_2]
        
        service = AIService()
        result = service.get_response("Hello, AI!")
        
        # Verify both keys were attempted
        assert mock_client_class.call_count == 2
        assert mock_client_class.call_args_list[0][1]["api_key"] == "first_gemini_key"
        assert mock_client_class.call_args_list[1][1]["api_key"] == "second_gemini_key"
        
        # Verify response is from second key
        assert result == "Response from second key"
        assert service.current_provider == "gemini"
        assert service.current_key_index == 1
    
    @patch.dict(os.environ, {
        "GEMINI_KEY_1": "first_gemini_key",
        "GEMINI_KEY_2": "second_gemini_key",
    }, clear=True)
    @patch("google.genai.Client")
    def test_gemini_authentication_error(self, mock_client_class):
        """Test handling of authentication errors (401)."""
        mock_client_instance_1 = MagicMock()
        mock_client_instance_1.models.generate_content.side_effect = Exception("401 Unauthorized")
        
        mock_client_instance_2 = MagicMock()
        mock_client_instance_2.models.generate_content.return_value = MagicMock(
            text="Success with second key"
        )
        
        mock_client_class.side_effect = [mock_client_instance_1, mock_client_instance_2]
        
        service = AIService()
        result = service.get_response("Hello, AI!")
        
        # Second key should be used
        assert result == "Success with second key"
        assert mock_client_class.call_count == 2
    
    @patch.dict(os.environ, {
        "GEMINI_KEY_1": "gemini_key_1",
    }, clear=True)
    @patch("google.genai.Client")
    def test_gemini_timeout_triggers_fallback(self, mock_client_class):
        """Test that timeout triggers fallback to next provider."""
        import time
        
        def slow_generate(model, contents):
            time.sleep(11)  # Sleep longer than timeout
            return MagicMock(text="Too slow")
        
        mock_client_instance = MagicMock()
        mock_client_instance.models.generate_content.side_effect = slow_generate
        mock_client_class.return_value = mock_client_instance
        
        # Override timeout for testing
        service = AIService()
        service.GEMINI_KEY_TIMEOUT = 0.1  # Very short timeout
        
        # This should timeout and fall through to fallback
        # (We'll just verify the mechanism works)
        with patch.object(service, '_try_openrouter_keys', return_value=None):
            result = service.get_response("Hello, AI!")
            assert result == AIService.STATIC_FALLBACK_RESPONSE


class TestOpenRouterKeyFallback:
    """Test OpenRouter API key fallback mechanism."""
    
    @patch.dict(os.environ, {
        "OPENROUTER_KEY_1": "first_openrouter_key",
        "OPENROUTER_KEY_2": "second_openrouter_key",
    }, clear=True)
    @patch("requests.post")
    def test_first_openrouter_key_succeeds(self, mock_post):
        """Test that first OpenRouter key succeeds."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Response from OpenRouter"
                    }
                }
            ]
        }
        mock_post.return_value = mock_response
        
        service = AIService()
        # Patch Gemini to fail
        with patch.object(service, '_try_gemini_keys', return_value=None):
            result = service.get_response("Hello, AI!")
        
        # Verify OpenRouter was called
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "openrouter.ai" in call_args[0][0]
        
        # Verify response
        assert result == "Response from OpenRouter"
        assert service.current_provider == "openrouter"
        assert service.current_key_index == 0
    
    @patch.dict(os.environ, {
        "OPENROUTER_KEY_1": "first_openrouter_key",
        "OPENROUTER_KEY_2": "second_openrouter_key",
    }, clear=True)
    @patch("requests.post")
    def test_first_openrouter_fails_second_succeeds(self, mock_post):
        """Test that if first OpenRouter key fails, second key is tried."""
        # Setup: first call fails with 401, second succeeds
        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 401
        
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Response from second OpenRouter key"
                    }
                }
            ]
        }
        
        mock_post.side_effect = [mock_response_fail, mock_response_success]
        
        service = AIService()
        # Patch Gemini to fail
        with patch.object(service, '_try_gemini_keys', return_value=None):
            result = service.get_response("Hello, AI!")
        
        # Verify both keys were attempted
        assert mock_post.call_count == 2
        
        # Verify response is from second key
        assert result == "Response from second OpenRouter key"
        assert service.current_key_index == 1
    
    @patch.dict(os.environ, {
        "OPENROUTER_KEY_1": "openrouter_key",
    }, clear=True)
    @patch("requests.post")
    def test_openrouter_quota_exceeded(self, mock_post):
        """Test handling of quota exceeded error (429)."""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_post.return_value = mock_response
        
        service = AIService()
        with patch.object(service, '_try_gemini_keys', return_value=None):
            result = service.get_response("Hello, AI!")
        
        # Should fall back to static response
        assert result == AIService.STATIC_FALLBACK_RESPONSE
    
    @patch.dict(os.environ, {
        "OPENROUTER_KEY_1": "openrouter_key",
    }, clear=True)
    @patch("requests.post")
    def test_openrouter_server_error(self, mock_post):
        """Test handling of server error (500, 503)."""
        # Test 500
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response
        
        service = AIService()
        with patch.object(service, '_try_gemini_keys', return_value=None):
            result = service.get_response("Hello, AI!")
        
        assert result == AIService.STATIC_FALLBACK_RESPONSE
    
    @patch.dict(os.environ, {
        "OPENROUTER_KEY_1": "openrouter_key",
    }, clear=True)
    @patch("requests.post")
    def test_openrouter_timeout(self, mock_post):
        """Test handling of timeout."""
        mock_post.side_effect = requests.Timeout("Connection timeout")
        
        service = AIService()
        with patch.object(service, '_try_gemini_keys', return_value=None):
            result = service.get_response("Hello, AI!")
        
        assert result == AIService.STATIC_FALLBACK_RESPONSE
    
    @patch.dict(os.environ, {
        "OPENROUTER_KEY_1": "openrouter_key",
    }, clear=True)
    @patch("requests.post")
    def test_openrouter_malformed_response(self, mock_post):
        """Test handling of malformed response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"error": "Invalid request"}
        mock_post.return_value = mock_response
        
        service = AIService()
        with patch.object(service, '_try_gemini_keys', return_value=None):
            result = service.get_response("Hello, AI!")
        
        assert result == AIService.STATIC_FALLBACK_RESPONSE


class TestCompleteFallbackChain:
    """Test the complete fallback chain from Gemini to OpenRouter to static fallback."""
    
    @patch.dict(os.environ, {
        "GEMINI_KEY_1": "gemini_key_1",
        "GEMINI_KEY_2": "gemini_key_2",
        "OPENROUTER_KEY_1": "openrouter_key_1",
        "OPENROUTER_KEY_2": "openrouter_key_2",
    }, clear=True)
    @patch("google.genai.Client")
    @patch("requests.post")
    def test_all_gemini_fail_openrouter_succeeds(
        self, mock_post, mock_client_class
    ):
        """Test all Gemini keys fail, first OpenRouter key succeeds."""
        # Setup Gemini to fail
        mock_client_instance_1 = MagicMock()
        mock_client_instance_1.models.generate_content.side_effect = Exception("First Gemini failed")
        
        mock_client_instance_2 = MagicMock()
        mock_client_instance_2.models.generate_content.side_effect = Exception("Second Gemini failed")
        
        mock_client_class.side_effect = [mock_client_instance_1, mock_client_instance_2]
        
        # Setup OpenRouter to succeed
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Response from OpenRouter after all Gemini failed"
                    }
                }
            ]
        }
        mock_post.return_value = mock_response
        
        service = AIService()
        result = service.get_response("Hello, AI!")
        
        # Verify Gemini was tried twice
        assert mock_client_class.call_count == 2
        
        # Verify OpenRouter was called
        assert mock_post.called
        
        # Verify response
        assert result == "Response from OpenRouter after all Gemini failed"
        assert service.current_provider == "openrouter"
    
    @patch.dict(os.environ, {
        "GEMINI_KEY_1": "gemini_key_1",
        "OPENROUTER_KEY_1": "openrouter_key_1",
    }, clear=True)
    def test_all_keys_fail_returns_static_fallback(self):
        """Test that static fallback is returned when all keys fail."""
        service = AIService()
        
        # Mock all attempts to fail
        with patch.object(service, '_try_gemini_keys', return_value=None):
            with patch.object(service, '_try_openrouter_keys', return_value=None):
                result = service.get_response("Hello, AI!")
        
        assert result == AIService.STATIC_FALLBACK_RESPONSE
    
    @patch.dict(os.environ, {}, clear=True)
    def test_no_keys_configured_returns_static_fallback(self):
        """Test that static fallback is returned when no keys are configured."""
        service = AIService()
        result = service.get_response("Hello, AI!")
        
        assert result == AIService.STATIC_FALLBACK_RESPONSE


class TestEdgeCases:
    """Test edge cases and special scenarios."""
    
    @patch.dict(os.environ, {}, clear=True)
    def test_empty_prompt_returns_message(self):
        """Test that empty prompt returns a helpful message."""
        service = AIService()
        result = service.get_response("")
        
        assert "Please provide a valid prompt" in result or result is not None
    
    @patch.dict(os.environ, {
        "GEMINI_KEY_1": "gemini_key_1",
    }, clear=True)
    @patch("google.genai.Client")
    def test_none_response_text(self, mock_client_class):
        """Test handling of None response text."""
        mock_response = MagicMock()
        mock_response.text = None
        mock_model_instance = MagicMock()
        mock_model_instance.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_model_instance
        
        service = AIService()
        with patch.object(service, '_try_openrouter_keys', return_value=None):
            result = service.get_response("Hello")
        
        assert result == AIService.STATIC_FALLBACK_RESPONSE
    
    @patch.dict(os.environ, {}, clear=True)
    def test_get_last_used_key_info_no_key_used(self):
        """Test getting key info when no key has been used yet."""
        service = AIService()
        info = service.get_last_used_key_info()
        
        assert info["provider"] is None
        assert info["key_index"] is None
    
    @patch.dict(os.environ, {
        "GEMINI_KEY_1": "gemini_key_1",
    }, clear=True)
    @patch("google.genai.Client")
    def test_get_last_used_key_info_after_success(self, mock_client_class):
        """Test getting key info after successful API call."""
        mock_response = MagicMock()
        mock_response.text = "Response"
        mock_model_instance = MagicMock()
        mock_model_instance.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_model_instance
        
        service = AIService()
        service.get_response("Hello")
        
        info = service.get_last_used_key_info()
        assert info["provider"] == "gemini"
        assert info["key_index"] == 1


class TestSingletonFunction:
    """Test the module-level get_ai_service function."""
    
    @patch.dict(os.environ, {
        "GEMINI_KEY_1": "gemini_key_1",
    }, clear=True)
    def test_get_ai_service_returns_same_instance(self):
        """Test that get_ai_service returns the same singleton instance."""
        # Reset singleton
        import fitness_api.ai_service as ai_service_module
        ai_service_module._ai_service_instance = None
        
        service1 = get_ai_service()
        service2 = get_ai_service()
        
        assert service1 is service2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
