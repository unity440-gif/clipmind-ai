"""
One-time script: uploads the starter music library to R2 and inserts
matching rows into the music_tracks table. Safe to run multiple times
(skips a track if one with the same storage_path already exists).
"""

import uuid
from pathlib import Path

from database.session import SessionLocal
from models.music_track import MusicTrack
from services.storage_service import upload_file

TRACKS = [
    {
        "local_path": "/Users/apple/Downloads/mickeyscat-moment-of-peace-mickeyscat-554494.mp3",
        "title": "Moment of Peace",
        "mood": "calm",
        "r2_key": "music/calm-moment-of-peace.mp3",
    },
    {
        "local_path": "/Users/apple/Downloads/musicdream-dramatic-cinematic-documentary-609202.mp3",
        "title": "Dramatic Cinematic Documentary",
        "mood": "dramatic",
        "r2_key": "music/dramatic-cinematic-documentary.mp3",
    },
    {
        "local_path": "/Users/apple/Downloads/lnplusmusic-suspense-tension-horror-trailer-323181.mp3",
        "title": "Suspense Tension Trailer",
        "mood": "dramatic",
        "r2_key": "music/dramatic-suspense-trailer.mp3",
    },
    {
        "local_path": "/Users/apple/Downloads/lnplusmusic-sport-sports-rock-music-597971.mp3",
        "title": "Sports Rock Music",
        "mood": "upbeat",
        "r2_key": "music/upbeat-sports-rock.mp3",
    },
]

db = SessionLocal()

for track in TRACKS:
    existing = db.query(MusicTrack).filter(MusicTrack.storage_path == track["r2_key"]).first()
    if existing:
        print(f"Skipping (already exists): {track['r2_key']}")
        continue

    if not Path(track["local_path"]).exists():
        print(f"WARNING: local file not found, skipping: {track['local_path']}")
        continue

    upload_file(track["local_path"], track["r2_key"])

    music_track = MusicTrack(
        id=uuid.uuid4(),
        title=track["title"],
        storage_path=track["r2_key"],
        mood=track["mood"],
    )
    db.add(music_track)
    print(f"Uploaded and added: {track['title']} ({track['mood']})")

db.commit()
db.close()
print("Done.")
