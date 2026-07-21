"""
ClipMind AI - FastAPI application entrypoint.
This file wires together routers, middleware, and startup/shutdown events.
Business logic never lives here — it lives in services/ and routes/ delegate to it.
"""
from api.routes import auth
from fastapi import FastAPI

from config.settings import settings
from api.routes import health

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
)

# Register routers. Each new feature module will add one line here.
app.include_router(health.router)
app.include_router(auth.router)

@app.get("/")
def root():
    return {"message": f"{settings.APP_NAME} API is running"}
