"""
Whisper transcription service.
Uses faster-whisper (a fast CPU-friendly re-implementation of OpenAI's Whisper)
to convert an audio file into a timestamped transcript.
"""

from faster_whisper import WhisperModel

# Loading the model is slow (a few seconds to a minute depending on size),
# so we load it ONCE per worker process and reuse it for every job,
# rather than reloading it on every single transcription.
#
# "base" is a good balance of speed vs accuracy for CPU-only environments.
# Larger models (small/medium/large) are more accurate but much slower without a GPU.
_model = None


def get_model() -> WhisperModel:
    global _model
    if _model is None:
        _model = WhisperModel("base", device="cpu", compute_type="int8")
    return _model


def transcribe_audio(audio_path: str) -> str:
    """
    Transcribes an audio file and returns a single string with
    bracketed timestamps, e.g.:

    [00:00] Hello and welcome to the show. [00:04] Today we're talking about...

    This format matches exactly what our hook-detection prompt expects.
    """
    model = get_model()
    segments, _info = model.transcribe(audio_path, beam_size=5)

    lines = []
    for segment in segments:
        minutes = int(segment.start // 60)
        seconds = int(segment.start % 60)
        timestamp = f"[{minutes:02d}:{seconds:02d}]"
        lines.append(f"{timestamp} {segment.text.strip()}")

    return " ".join(lines)