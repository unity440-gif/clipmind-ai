"""
ClipMind AI - FastAPI application entrypoint.
This file wires together routers, middleware, and startup/shutdown events.
Business logic never lives here — it lives in services/ and routes/ delegate to it.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.settings import settings
from api.routes import health
from api.routes import auth
from api.routes import projects
from api.routes import videos
from api.routes import ai_test
from api.routes import clips

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # your frontend's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers. Each new feature module adds one line here.
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(videos.router)
app.include_router(ai_test.router)
app.include_router(clips.router)

@app.get("/")
def root():
    return {"message": f"{settings.APP_NAME} API is running"}