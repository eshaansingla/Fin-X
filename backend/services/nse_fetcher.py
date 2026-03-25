import time
from datetime import date

import requests

from database import db_execute, db_fetchone

NSE_BASE = "https://www.nseindia.com"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Referer": "https://www.nseindia.com/",
    "Connection": "keep-alive",
}

_session = None


def get_nse_session() -> requests.Session:
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update(HEADERS)
        try:
            _session.get(NSE_BASE, timeout=5)
            time.sleep(1)
            _session.get(f"{NSE_BASE}/market-data/bulk-deals", timeout=5)
            time.sleep(0.5)
            print("[NSE] Session warmed up successfully")
        except Exception as e:
            print(f"[NSE] Session warmup error: {e}")
    return _session


def reset_session():
    global _session
    _session = None
    print("[NSE] Session reset")


def fetch_bulk_deals(from_date: str = None, to_date: str = None, _retry: int = 0) -> list:
    """
    Fetch bulk deals from NSE.
    Priority: /api/bulk-deals (no date) → /api/bulk-deal-archives (with date).
    Max 3 retries on 403.
    """
    if _retry >= 3:
        print("[NSE] fetch_bulk_deals: max retries reached, returning []")
        return []
    session = get_nse_session()

    # ── Attempt 1: direct no-date endpoint (live deals, usually available) ──
    if from_date is None and to_date is None:
        try:
            resp = session.get(f"{NSE_BASE}/api/bulk-deals", timeout=8)
            if resp.status_code == 403:
                reset_session()
                return fetch_bulk_deals(from_date, to_date, _retry + 1)
            if resp.status_code == 200 and resp.content:
                data = resp.json().get("data", [])
                if data:
                    print(f"[NSE] /api/bulk-deals returned {len(data)} deals")
                    return data
        except Exception as e:
            print(f"[NSE] Direct bulk-deals error: {e}")

    # ── Attempt 2: archived endpoint with date range ──
    today = date.today().strftime("%d-%m-%Y")
    params = {"from": from_date or today, "to": to_date or today}
    try:
        resp = session.get(
            f"{NSE_BASE}/api/bulk-deal-archives", params=params, timeout=8
        )
        if resp.status_code == 403:
            print(f"[NSE] 403 received - resetting session (attempt {_retry + 1}/3)")
            reset_session()
            return fetch_bulk_deals(from_date, to_date, _retry + 1)
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        return resp.json().get("data", [])
    except Exception as e:
        print(f"[NSE] Bulk deals fetch error: {e}")
        return []


def fetch_bulk_deals_lookback(days: int = 7) -> list:
    """
    Fetch bulk deals from the past N calendar days.
    Used to seed the DB when today returns nothing.
    """
    from datetime import timedelta
    all_deals: list = []
    for offset in range(1, days + 1):
        d = date.today() - timedelta(days=offset)
        ds = d.strftime("%d-%m-%Y")
        deals = fetch_bulk_deals(ds, ds)
        if deals:
            all_deals.extend(deals)
            print(f"[NSE] Lookback {ds}: {len(deals)} deals")
            if len(all_deals) >= 30:   # enough to seed signals
                break
    return all_deals


def fetch_block_deals(_retry: int = 0) -> list:
    """Fetch block deals from NSE with max 3 retries on 403 and timeout=8."""
    if _retry >= 3:
        print("[NSE] fetch_block_deals: max retries reached, returning []")
        return []
    session = get_nse_session()
    today = date.today().strftime("%d-%m-%Y")
    try:
        resp = session.get(
            f"{NSE_BASE}/api/block-deal-archives",
            params={"from": today, "to": today},
            timeout=8,
        )
        if resp.status_code == 403:
            print(f"[NSE] 403 received (block) - resetting session (attempt {_retry + 1}/3)")
            reset_session()
            return fetch_block_deals(_retry + 1)
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        return resp.json().get("data", [])
    except Exception as e:
        print(f"[NSE] Block deals fetch error: {e}")
        return []


def save_bulk_deals_to_db(deals: list) -> int:
    count = 0
    for d in deals:
        try:
            raw_qty = str(d.get("quantityTraded", 0) or 0).replace(",", "")
            quantity = int(raw_qty) if raw_qty.isdigit() else 0
            existing = db_fetchone(
                "SELECT id FROM bulk_deals WHERE symbol=? AND deal_date=? AND quantity=?",
                (d.get("symbol", ""), d.get("dealDate", ""), quantity),
            )
            if not existing:
                db_execute(
                    """INSERT INTO bulk_deals
                       (symbol, client_name, deal_type, quantity, price, deal_date)
                       VALUES (?,?,?,?,?,?)""",
                    (
                        d.get("symbol", "").upper(),
                        d.get("clientName", ""),
                        d.get("buySellType", d.get("dealType", "")),
                        quantity,
                        float(str(d.get("tradePrice", 0) or 0).replace(",", "")),
                        d.get("dealDate", date.today().isoformat()),
                    ),
                )
                count += 1
        except Exception as e:
            print(f"[NSE] Error saving deal {d}: {e}")
            continue
    return count
