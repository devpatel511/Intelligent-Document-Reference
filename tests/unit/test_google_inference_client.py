from pathlib import Path

import model_clients.google_client as google_client_module
from model_clients.google_client import GoogleInferenceClient


class _DummyPart:
    @staticmethod
    def from_text(text: str):
        return {"kind": "text", "text": text}

    @staticmethod
    def from_bytes(data: bytes, mime_type: str):
        return {"kind": "bytes", "size": len(data), "mime": mime_type}


class _DummyTypes:
    Part = _DummyPart


class _Response:
    def __init__(self, text: str):
        self.text = text


class _FakeModels:
    def __init__(self):
        self.calls = []
        self.last_contents = None

    def generate_content(self, *, model: str, contents):
        self.calls.append(model)
        self.last_contents = contents
        if model == "gemini-primary":
            raise Exception("503 UNAVAILABLE: high demand")
        return _Response("transcribed text")


class _FakeClient:
    def __init__(self):
        self.models = _FakeModels()


def test_transcribe_audio_retries_and_falls_back(tmp_path: Path, monkeypatch) -> None:
    mp3_file = tmp_path / "clip.mp3"
    mp3_file.write_bytes(b"ID3\x04\x00\x00\x00\x00\x00\x00")

    monkeypatch.setattr(google_client_module, "types", _DummyTypes)

    client = GoogleInferenceClient.__new__(GoogleInferenceClient)
    client.client = _FakeClient()
    client.model = "gemini-primary"

    text = client.transcribe_audio(
        str(mp3_file),
        fallback_models=["gemini-fallback"],
        retries_per_model=2,
    )

    assert text == "transcribed text"
    # Primary gets 2 retries, then fallback succeeds.
    assert client.client.models.calls == [
        "gemini-primary",
        "gemini-primary",
        "gemini-fallback",
    ]


def test_transcribe_audio_uses_wav_mime_type(tmp_path: Path, monkeypatch) -> None:
    wav_file = tmp_path / "clip.wav"
    wav_file.write_bytes(b"RIFF\x00\x00\x00\x00WAVE")

    monkeypatch.setattr(google_client_module, "types", _DummyTypes)

    client = GoogleInferenceClient.__new__(GoogleInferenceClient)
    client.client = _FakeClient()
    client.model = "gemini-fallback"

    text = client.transcribe_audio(str(wav_file), retries_per_model=1)

    assert text == "transcribed text"
    assert client.client.models.last_contents[1]["mime"] == "audio/wav"
