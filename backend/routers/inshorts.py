# backend/routers/inshorts.py
"""Inshorts-style finance news cards API."""

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from services.inshorts_service import build_inshorts_payload

router = APIRouter()


@router.get("/inshorts")
def get_inshorts(force_refresh: bool = Query(False, description="Bypass short TTL cache")):
    try:
        data = build_inshorts_payload(force_refresh=force_refresh)
        return {"success": True, "data": data, "error": None}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "data": None, "error": str(e)},
        )
