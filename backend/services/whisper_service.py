"""
Whisper transcription service.
Uses faster-whisper (a fast CPU-friendly re-implementation of OpenAI's Whisper)
to convert an audio file into a timestamped transcript, and also returns
segment-level timing data used later for burning captions onto clips.
"""

from faster_whisper import WhisperModel

_model = None


def get_model() -> WhisperModel:
    global _model
    if _model is None:
        _model = WhisperModel("base", device="cpu", compute_type="int8")
    return _model


def transcribe_audio(audio_path: str) -> dict:
    """
    Transcribes an audio file. Returns a dict with:
    - "text": the full transcript as a single string with [MM:SS] timestamps
              (used by the hook-detection prompt)
    - "segments": a list of {"start": float, "end": float, "text": str}
                  (used later to burn captions onto individual clips)
    """
    model = get_model()
    segments_iter, _info = model.transcribe(audio_path, beam_size=5)

    lines = []
    segments = []

    for segment in segments_iter:
        minutes = int(segment.start // 60)
        seconds = int(segment.start % 60)
        timestamp = f"[{minutes:02d}:{seconds:02d}]"
        text = segment.text.strip()

        lines.append(f"{timestamp} {text}")
        segments.append({
            "start": segment.start,
            "end": segment.end,
            "text": text,
        })

    return {
        "text": " ".join(lines),
        "segments": segments,
    }