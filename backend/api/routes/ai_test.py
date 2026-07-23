"""
Temporary test route for confirming OpenRouter connectivity.
Not part of the final product — safe to delete once we build
the real hook-detection endpoint in a later module.
"""

from fastapi import APIRouter, HTTPException

from services.openrouter_service import call_openrouter

router = APIRouter(prefix="/ai-test", tags=["ai-test"])


@router.get("/ping")
def ping_openrouter():
    """
    Sends a trivial prompt to OpenRouter to confirm the API key
    and connection are working correctly.
    """
    try:
        result = call_openrouter("Reply with exactly the word: pong", model="claude-sonnet")
        return {"success": True, "response": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
