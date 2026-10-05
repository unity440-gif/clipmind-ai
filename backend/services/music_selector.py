"""
Simple keyword-based background music selector.
Matches a clip's hook/summary/reason text against mood keyword lists
to pick a fitting track from the music_tracks table — no AI call needed.
"""

import random

MOOD_KEYWORDS = {
    "dramatic": [
        "shocking", "intense", "danger", "betrayal", "secret", "revealed",
        "truth", "warning", "crisis", "fear", "threat", "disaster",
    ],
    "upbeat": [
        "funny", "hilarious", "amazing", "win", "success", "celebration",
        "exciting", "energy", "hype", "fun", "awesome", "epic",
    ],
    "calm": [
        "peaceful", "relax", "gentle", "story", "reflect", "quiet",
        "thoughtful", "explain", "understand", "learn",
    ],
}


def pick_mood_for_clip(hook: str | None, summary: str | None, reason: str | None) -> str:
    """
    Looks at a clip's text fields and returns the best-matching mood
    ("dramatic", "upbeat", "calm") based on keyword presence. Falls back
    to "calm" if nothing matches — a safe, unobtrusive default.
    """
    combined_text = " ".join(filter(None, [hook, summary, reason])).lower()

    scores = {mood: 0 for mood in MOOD_KEYWORDS}
    for mood, keywords in MOOD_KEYWORDS.items():
        for keyword in keywords:
            if keyword in combined_text:
                scores[mood] += 1

    best_mood = max(scores, key=scores.get)
    if scores[best_mood] == 0:
        return "calm"

    return best_mood


def pick_track_for_mood(db, mood: str):
    """
    Returns a random MusicTrack matching the given mood, or None if no
    tracks exist for that mood yet.
    """
    from models.music_track import MusicTrack

    tracks = db.query(MusicTrack).filter(MusicTrack.mood == mood).all()
    if not tracks:
        return None
    return random.choice(tracks)
