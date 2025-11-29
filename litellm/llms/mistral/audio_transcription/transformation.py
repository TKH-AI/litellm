"""
Translates from OpenAI's `/v1/audio/transcriptions` to Mistral's `/v1/audio/transcriptions`

Mistral API docs: https://docs.mistral.ai/capabilities/audio_transcription
"""

from typing import List, Optional, Union

from httpx import Headers, Response

import litellm
from litellm.litellm_core_utils.audio_utils.utils import process_audio_file
from litellm.llms.base_llm.audio_transcription.transformation import (
    AudioTranscriptionRequestData,
    BaseAudioTranscriptionConfig,
)
from litellm.llms.base_llm.chat.transformation import BaseLLMException
from litellm.secret_managers.main import get_secret_str
from litellm.types.llms.openai import (
    AllMessageValues,
    OpenAIAudioTranscriptionOptionalParams,
)
from litellm.types.utils import FileTypes, TranscriptionResponse

from ..common_utils import MistralException


class MistralAudioTranscriptionConfig(BaseAudioTranscriptionConfig):
    """
    Configuration class for Mistral Audio Transcription API.

    Mistral's audio transcription endpoint accepts:
    - model: Model identifier (e.g., "voxtral-mini-2507", "voxtral-mini-latest")
    - file: Audio file (multipart form upload)
    - file_url: URL to audio file (alternative to file upload)
    - language: Language hint for transcription
    - timestamp_granularities: Request timing info (e.g., ["segment"])

    Note: timestamp_granularities is not compatible with language parameter.
    """

    @property
    def custom_llm_provider(self) -> str:
        return litellm.LlmProviders.MISTRAL.value

    def get_supported_openai_params(
        self, model: str
    ) -> List[OpenAIAudioTranscriptionOptionalParams]:
        return ["language", "timestamp_granularities"]

    def map_openai_params(
        self,
        non_default_params: dict,
        optional_params: dict,
        model: str,
        drop_params: bool,
    ) -> dict:
        supported_params = self.get_supported_openai_params(model)
        for k, v in non_default_params.items():
            if k in supported_params:
                optional_params[k] = v
        return optional_params

    def get_error_class(
        self, error_message: str, status_code: int, headers: Union[dict, Headers]
    ) -> BaseLLMException:
        return MistralException(
            message=error_message, status_code=status_code, headers=headers
        )

    def transform_audio_transcription_request(
        self,
        model: str,
        audio_file: FileTypes,
        optional_params: dict,
        litellm_params: dict,
    ) -> AudioTranscriptionRequestData:
        """
        Transforms the audio transcription request for Mistral API.

        Supports two modes:
        1. File upload: Standard multipart form with audio file
        2. URL mode: When 'file_url' is in optional_params, sends URL instead of file

        Returns:
            AudioTranscriptionRequestData: Structured data with form data and files
        """
        # Prepare form data with model
        form_data: dict = {"model": model}

        # Check if file_url is provided (Mistral-specific feature)
        file_url = optional_params.pop("file_url", None)

        # Add supported OpenAI parameters
        for key in self.get_supported_openai_params(model):
            if key in optional_params and optional_params[key] is not None:
                value = optional_params[key]
                # Handle timestamp_granularities as array
                if key == "timestamp_granularities" and isinstance(value, list):
                    # Mistral expects this as a JSON array string in form data
                    import json

                    form_data[key] = json.dumps(value)
                else:
                    form_data[key] = str(value)

        # Add provider-specific parameters
        provider_specific_params = self.get_provider_specific_params(
            model=model,
            optional_params=optional_params,
            openai_params=self.get_supported_openai_params(model),
        )
        for key, value in provider_specific_params.items():
            if key != "file_url":  # Already handled above
                form_data[key] = str(value)

        # Handle file_url mode vs file upload mode
        if file_url is not None:
            # URL mode: no file upload needed
            form_data["file_url"] = file_url
            return AudioTranscriptionRequestData(data=form_data, files=None)
        else:
            # File upload mode: process audio file
            processed_audio = process_audio_file(audio_file)
            files = {
                "file": (
                    processed_audio.filename,
                    processed_audio.file_content,
                    processed_audio.content_type,
                )
            }
            return AudioTranscriptionRequestData(data=form_data, files=files)

    def transform_audio_transcription_response(
        self,
        raw_response: Response,
    ) -> TranscriptionResponse:
        """
        Transforms the raw response from Mistral to the TranscriptionResponse format.

        Mistral response format:
        {
            "model": "voxtral-mini-2507",
            "text": "transcribed text...",
            "language": "en",
            "segments": [{"start": 0.0, "end": 2.5, "text": "..."}],
            "usage": {"prompt_audio_seconds": 10.5, ...}
        }
        """
        try:
            response_json = raw_response.json()

            # Extract the main transcript text
            text = response_json.get("text", "")

            # Create TranscriptionResponse object
            response = TranscriptionResponse(text=text)

            # Add metadata matching OpenAI format
            response["task"] = "transcribe"
            response["language"] = response_json.get("language", "unknown")

            # Extract duration from usage if available
            usage = response_json.get("usage", {})
            if "prompt_audio_seconds" in usage:
                response["duration"] = usage["prompt_audio_seconds"]

            # Map Mistral segments to words format for consistency
            # Note: These are segments (phrases), not individual words
            if "segments" in response_json:
                response["words"] = [
                    {
                        "word": segment.get("text", ""),
                        "start": segment.get("start", 0),
                        "end": segment.get("end", 0),
                    }
                    for segment in response_json["segments"]
                ]

            # Store full response in hidden params for debugging
            response._hidden_params = response_json

            return response

        except Exception as e:
            raise ValueError(
                f"Error transforming Mistral response: {str(e)}\nResponse: {raw_response.text}"
            )

    def get_complete_url(
        self,
        api_base: Optional[str],
        api_key: Optional[str],
        model: str,
        optional_params: dict,
        litellm_params: dict,
        stream: Optional[bool] = None,
    ) -> str:
        if api_base is None:
            api_base = (
                get_secret_str("MISTRAL_API_BASE")
                or get_secret_str("MISTRAL_AZURE_API_BASE")
                or "https://api.mistral.ai"
            )
        api_base = api_base.rstrip("/")

        # Mistral audio transcription endpoint
        return f"{api_base}/v1/audio/transcriptions"

    def validate_environment(
        self,
        headers: dict,
        model: str,
        messages: List[AllMessageValues],
        optional_params: dict,
        litellm_params: dict,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
    ) -> dict:
        api_key = (
            api_key
            or get_secret_str("MISTRAL_API_KEY")
            or get_secret_str("MISTRAL_AZURE_API_KEY")
        )
        if api_key is None:
            raise ValueError(
                "Mistral API key is required. Set MISTRAL_API_KEY environment variable."
            )

        # Mistral uses x-api-key header for authentication
        auth_header = {
            "x-api-key": api_key,
        }

        headers.update(auth_header)
        return headers
