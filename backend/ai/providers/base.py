from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TranscriptSegmentResult:
    speaker_label: str
    text: str
    start_time_seconds: float | None = None
    end_time_seconds: float | None = None


@dataclass
class TranscriptionResult:
    segments: list[TranscriptSegmentResult]
    raw: dict[str, Any] = field(default_factory=dict)
    duration_seconds: float | None = None


class TranscriptionProvider(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str) -> TranscriptionResult:
        raise NotImplementedError


class DiarizationProvider(ABC):
    @abstractmethod
    def diarize(self, audio_path: str) -> TranscriptionResult:
        raise NotImplementedError


class LLMProvider(ABC):
    @abstractmethod
    def generate_structured(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def verify_entailment(self, claim: str, evidence: str) -> dict[str, Any]:
        raise NotImplementedError
