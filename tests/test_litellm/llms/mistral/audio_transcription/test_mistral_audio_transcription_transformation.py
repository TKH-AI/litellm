import io
import os
import sys
from unittest.mock import MagicMock

import pytest

sys.path.insert(
    0, os.path.abspath("../../../../..")
)  # Adds the parent directory to the system path

from litellm.llms.base_llm.audio_transcription.transformation import (
    AudioTranscriptionRequestData,
)
from litellm.llms.mistral.audio_transcription.transformation import (
    MistralAudioTranscriptionConfig,
)
from litellm.llms.mistral.common_utils import MistralException
from litellm.types.utils import TranscriptionResponse


@pytest.fixture
def handler():
    return MistralAudioTranscriptionConfig()


@pytest.fixture
def test_bytes():
    return b"test audio content", b"test audio content"


@pytest.fixture
def test_io_bytes(test_bytes):
    return io.BytesIO(test_bytes[0]), test_bytes[1]


class TestGetSupportedOpenAIParams:
    def test_returns_expected_params(self, handler):
        """Test that get_supported_openai_params returns the correct parameters"""
        params = handler.get_supported_openai_params("voxtral-mini-2507")
        assert "language" in params
        assert "timestamp_granularities" in params
        assert len(params) == 2


class TestMapOpenAIParams:
    def test_maps_language_parameter(self, handler):
        """Test that language parameter is mapped correctly"""
        result = handler.map_openai_params(
            non_default_params={"language": "en"},
            optional_params={},
            model="voxtral-mini-2507",
            drop_params=False,
        )
        assert result["language"] == "en"

    def test_maps_timestamp_granularities(self, handler):
        """Test that timestamp_granularities parameter is mapped correctly"""
        result = handler.map_openai_params(
            non_default_params={"timestamp_granularities": ["segment"]},
            optional_params={},
            model="voxtral-mini-2507",
            drop_params=False,
        )
        assert result["timestamp_granularities"] == ["segment"]

    def test_ignores_unsupported_params(self, handler):
        """Test that unsupported parameters are ignored"""
        result = handler.map_openai_params(
            non_default_params={"unsupported_param": "value", "language": "fr"},
            optional_params={},
            model="voxtral-mini-2507",
            drop_params=False,
        )
        assert "unsupported_param" not in result
        assert result["language"] == "fr"


class TestGetErrorClass:
    def test_returns_mistral_exception(self, handler):
        """Test that get_error_class returns MistralException"""
        error = handler.get_error_class(
            error_message="Test error",
            status_code=400,
            headers={"Content-Type": "application/json"},
        )
        assert isinstance(error, MistralException)
        assert error.message == "Test error"
        assert error.status_code == 400


class TestGetCompleteURL:
    def test_default_api_base(self, handler):
        """Test URL generation with default API base"""
        url = handler.get_complete_url(
            api_base=None,
            api_key=None,
            model="voxtral-mini-2507",
            optional_params={},
            litellm_params={},
        )
        assert url == "https://api.mistral.ai/v1/audio/transcriptions"

    def test_custom_api_base(self, handler):
        """Test URL generation with custom API base"""
        url = handler.get_complete_url(
            api_base="https://custom.mistral.ai",
            api_key=None,
            model="voxtral-mini-2507",
            optional_params={},
            litellm_params={},
        )
        assert url == "https://custom.mistral.ai/v1/audio/transcriptions"

    def test_custom_api_base_with_trailing_slash(self, handler):
        """Test URL generation with custom API base that has trailing slash"""
        url = handler.get_complete_url(
            api_base="https://custom.mistral.ai/",
            api_key=None,
            model="voxtral-mini-2507",
            optional_params={},
            litellm_params={},
        )
        assert url == "https://custom.mistral.ai/v1/audio/transcriptions"


class TestValidateEnvironment:
    def test_with_api_key_parameter(self, handler):
        """Test validate_environment with API key passed as parameter"""
        headers = handler.validate_environment(
            headers={},
            model="voxtral-mini-2507",
            messages=[],
            optional_params={},
            litellm_params={},
            api_key="test-api-key",
        )
        assert headers["x-api-key"] == "test-api-key"

    def test_without_api_key_raises_error(self, handler, monkeypatch):
        """Test that missing API key raises ValueError"""
        # Clear any environment variables
        monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
        monkeypatch.delenv("MISTRAL_AZURE_API_KEY", raising=False)

        with pytest.raises(ValueError) as exc_info:
            handler.validate_environment(
                headers={},
                model="voxtral-mini-2507",
                messages=[],
                optional_params={},
                litellm_params={},
                api_key=None,
            )
        assert "Mistral API key is required" in str(exc_info.value)


class TestTransformAudioTranscriptionRequest:
    def test_with_bytes_audio_file(self, handler, test_bytes):
        """Test request transformation with bytes audio file"""
        audio_file, _ = test_bytes
        result = handler.transform_audio_transcription_request(
            model="voxtral-mini-2507",
            audio_file=audio_file,
            optional_params={},
            litellm_params={},
        )

        assert isinstance(result, AudioTranscriptionRequestData)
        assert result.data["model"] == "voxtral-mini-2507"
        assert result.files is not None
        assert "file" in result.files

    def test_with_io_bytes_audio_file(self, handler, test_io_bytes):
        """Test request transformation with BytesIO audio file"""
        audio_file, _ = test_io_bytes
        result = handler.transform_audio_transcription_request(
            model="voxtral-mini-2507",
            audio_file=audio_file,
            optional_params={},
            litellm_params={},
        )

        assert isinstance(result, AudioTranscriptionRequestData)
        assert result.data["model"] == "voxtral-mini-2507"
        assert result.files is not None
        assert "file" in result.files

    def test_with_file_url(self, handler):
        """Test request transformation with file_url (Mistral-specific feature)"""
        result = handler.transform_audio_transcription_request(
            model="voxtral-mini-2507",
            audio_file=b"dummy",  # Not used when file_url is provided
            optional_params={"file_url": "https://example.com/audio.mp3"},
            litellm_params={},
        )

        assert isinstance(result, AudioTranscriptionRequestData)
        assert result.data["model"] == "voxtral-mini-2507"
        assert result.data["file_url"] == "https://example.com/audio.mp3"
        assert result.files is None  # No file upload when using URL

    def test_with_language_parameter(self, handler, test_bytes):
        """Test request transformation with language parameter"""
        audio_file, _ = test_bytes
        result = handler.transform_audio_transcription_request(
            model="voxtral-mini-2507",
            audio_file=audio_file,
            optional_params={"language": "en"},
            litellm_params={},
        )

        assert result.data["model"] == "voxtral-mini-2507"
        assert result.data["language"] == "en"

    def test_with_timestamp_granularities(self, handler, test_bytes):
        """Test request transformation with timestamp_granularities parameter"""
        audio_file, _ = test_bytes
        result = handler.transform_audio_transcription_request(
            model="voxtral-mini-2507",
            audio_file=audio_file,
            optional_params={"timestamp_granularities": ["segment"]},
            litellm_params={},
        )

        assert result.data["model"] == "voxtral-mini-2507"
        # timestamp_granularities is serialized as JSON string
        assert "timestamp_granularities" in result.data


class TestTransformAudioTranscriptionResponse:
    def test_basic_response(self, handler):
        """Test basic response transformation"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "model": "voxtral-mini-2507",
            "text": "Hello, this is a test transcription.",
            "language": "en",
        }

        result = handler.transform_audio_transcription_response(mock_response)

        assert isinstance(result, TranscriptionResponse)
        assert result.text == "Hello, this is a test transcription."
        assert result["task"] == "transcribe"
        assert result["language"] == "en"

    def test_response_with_segments(self, handler):
        """Test response transformation with segments"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "model": "voxtral-mini-2507",
            "text": "Hello world. How are you?",
            "language": "en",
            "segments": [
                {"start": 0.0, "end": 1.5, "text": "Hello world."},
                {"start": 1.5, "end": 3.0, "text": "How are you?"},
            ],
        }

        result = handler.transform_audio_transcription_response(mock_response)

        assert isinstance(result, TranscriptionResponse)
        assert result.text == "Hello world. How are you?"
        assert len(result["words"]) == 2
        assert result["words"][0]["word"] == "Hello world."
        assert result["words"][0]["start"] == 0.0
        assert result["words"][0]["end"] == 1.5
        assert result["words"][1]["word"] == "How are you?"

    def test_response_with_usage(self, handler):
        """Test response transformation with usage information"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "model": "voxtral-mini-2507",
            "text": "Test transcription.",
            "language": "en",
            "usage": {
                "prompt_audio_seconds": 10.5,
                "prompt_tokens": 150,
                "completion_tokens": 25,
                "total_tokens": 175,
            },
        }

        result = handler.transform_audio_transcription_response(mock_response)

        assert isinstance(result, TranscriptionResponse)
        assert result["duration"] == 10.5

    def test_response_stores_hidden_params(self, handler):
        """Test that full response is stored in _hidden_params"""
        mock_response = MagicMock()
        original_json = {
            "model": "voxtral-mini-2507",
            "text": "Test.",
            "language": "en",
            "extra_field": "extra_value",
        }
        mock_response.json.return_value = original_json

        result = handler.transform_audio_transcription_response(mock_response)

        assert result._hidden_params == original_json

    def test_response_with_missing_language(self, handler):
        """Test response transformation when language is missing"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "model": "voxtral-mini-2507",
            "text": "Test transcription.",
        }

        result = handler.transform_audio_transcription_response(mock_response)

        assert result["language"] == "unknown"

    def test_invalid_response_raises_error(self, handler):
        """Test that invalid response raises ValueError"""
        mock_response = MagicMock()
        mock_response.json.side_effect = Exception("Invalid JSON")
        mock_response.text = "Invalid response body"

        with pytest.raises(ValueError) as exc_info:
            handler.transform_audio_transcription_response(mock_response)
        assert "Error transforming Mistral response" in str(exc_info.value)


class TestCustomLLMProvider:
    def test_custom_llm_provider_property(self, handler):
        """Test that custom_llm_provider returns 'mistral'"""
        assert handler.custom_llm_provider == "mistral"
