from django.conf import settings

from ai.providers.openai_providers import (
    MockLLMProvider,
    MockTranscriptionProvider,
    OpenAILLMProvider,
    OpenAITranscribeDiarizeProvider,
)


def get_transcription_provider():
    if settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("sk-your"):
        return OpenAITranscribeDiarizeProvider()
    return MockTranscriptionProvider()


def get_llm_provider():
    if settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("sk-your"):
        return OpenAILLMProvider()
    return MockLLMProvider()
