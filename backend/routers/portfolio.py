from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, field_validator
from typing import Any, Dict, List

import json

from database import db_fetchall, db_fetchone, db_execute
from routers.auth import get_current_user


router = APIRouter()


SECTOR_HINTS = {
    "RELIANCE": "Energy",
    "TCS": "IT",
    "INFY": "IT",
    "HDFCBANK": "Finance",
    "ICICIBANK": "Finance",
    "AXISBANK": "Finance",
    "KOTAKBANK": "Finance",
    "WIPRO": "IT",
    "TATAMOTORS": "Auto",
    "SUNPHARMA": "Pharma",
    "ITC": "FMCG",
}


class Holding(BaseModel):
    symbol: str
    quantity: float = 0

    @field_validator("symbol")
    @classmethod
    def norm_symbol(cls, v: str) -> str:
        v = (v or "").strip().upper()
        if not v:
            raise ValueError("symbol required")
        return v


class PortfolioSubmitRequest(BaseModel):
    holdings: List[Holding]


@router.post("/portfolio")
def submit_portfolio(
    req: PortfolioSubmitRequest,
    user: Dict[str, Any] = Depends(get_current_user),
):
    holdings_json = json.dumps([h.model_dump() for h in req.holdings])
    db_execute(
        "INSERT OR REPLACE INTO user_portfolios (user_id, holdings_json) VALUES (?,?)",
        (int(user["id"]), holdings_json),
    )
    return {"success": True, "data": {"saved": True}, "error": None}


@router.get("/portfolio")
def get_portfolio(user: Dict[str, Any] = Depends(get_current_user)):
    row = db_fetchone(
        "SELECT holdings_json, updated_at FROM user_portfolios WHERE user_id=?",
        (int(user["id"]),),
    )
    if not row:
        return {
            "success": True,
            "data": {
                "analysis": {},
                "updated_at": None,
                "message": "No portfolio submitted yet.",
            },
            "error": None,
        }

    try:
        holdings = json.loads(row["holdings_json"] or "[]")
    except Exception:
        holdings = []

    if not holdings:
        return {"success": True, "data": {"analysis": {}, "updated_at": row.get("updated_at")}, "error": None}

    total_qty = sum(float(h.get("quantity") or 0) for h in holdings)
    if total_qty <= 0:
        weights = [1 / len(holdings) for _ in holdings]
    else:
        weights = [float(h.get("quantity") or 0) / total_qty for h in holdings]

    max_w = max(weights) if weights else 0
    diversification_score = int(max(0, min(100, (1 - max_w) * 100)))

    sector_conc: Dict[str, float] = {}
    for h, w in zip(holdings, weights):
        sym = str(h.get("symbol") or "").upper()
        sector = SECTOR_HINTS.get(sym.replace(".NS", "").replace(".BO", ""), "Other")
        sector_conc[sector] = sector_conc.get(sector, 0) + w * 100

    top_sectors = sorted(sector_conc.items(), key=lambda x: x[1], reverse=True)[:3]
    risk_factors = []
    if max_w >= 0.5:
        risk_factors.append("High concentration in a single holding.")
    if len(holdings) <= 3:
        risk_factors.append("Limited diversification (few holdings).")
    if not risk_factors:
        risk_factors.append("Diversification appears moderate based on provided quantities.")

    high_signals = db_fetchall(
        "SELECT symbol, signal_type FROM signals ORDER BY created_at DESC LIMIT 10"
    )
    high_set = {str(r.get("symbol") or "").upper() for r in high_signals if r.get("symbol")}
    overlap = [h.get("symbol") for h in holdings if str(h.get("symbol") or "").upper() in high_set][:5]

    analysis = {
        "sector_concentration_top": [{"sector": s, "pct": round(p, 2)} for s, p in top_sectors],
        "top_risk_factors": risk_factors,
        "diversification_score": diversification_score,
        "overlap_with_high_signal_stocks": overlap,
    }

    return {
        "success": True,
        "data": {"analysis": analysis, "updated_at": row.get("updated_at")},
        "error": None,
    }

