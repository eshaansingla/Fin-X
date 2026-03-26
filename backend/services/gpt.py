# backend/services/gpt.py
import os, json, re, time, datetime
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(override=True)
from database import db_fetchall, db_fetchone, db_execute

# ── API keys ─────────────────────────────────────────────────
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if not GEMINI_API_KEY:
    print('[WARN] GEMINI_API_KEY missing — Gemini calls will use OpenAI fallback or return stub responses')

# Only configure Gemini if key present
_genai = None
try:
    if GEMINI_API_KEY:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        _genai = genai
except Exception as e:
    print(f'[WARN] Gemini configure error: {e}')

MODEL_NAME = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash-lite')

# Gemini free-tier quota management (default values from project notes).
GEMINI_DAILY_LIMIT = int(os.getenv('GEMINI_DAILY_LIMIT', '20'))
# When used-calls >= this threshold, we switch to OpenAI to avoid Gemini exhaustion.
GEMINI_NEAR_THRESHOLD = int(os.getenv('GEMINI_NEAR_THRESHOLD', '15'))

def _utc_today_str() -> str:
    return datetime.datetime.utcnow().date().isoformat()

def _get_gemini_call_count_today() -> int:
    """Returns Gemini call_count for today (UTC). Returns 0 if unavailable."""
    today = _utc_today_str()
    try:
        row = db_fetchone('SELECT call_count FROM gemini_usage WHERE usage_date=?', (today,))
        if row and row.get('call_count') is not None:
            return int(row.get('call_count') or 0)
        # Ensure row exists for stable increments.
        db_execute(
            'INSERT OR IGNORE INTO gemini_usage (usage_date, call_count) VALUES (?, 0)',
            (today,)
        )
        row = db_fetchone('SELECT call_count FROM gemini_usage WHERE usage_date=?', (today,))
        return int(row.get('call_count') or 0) if row else 0
    except Exception:
        return 0

def _increment_gemini_call_count_today() -> None:
    """Atomically increments Gemini call_count for today (UTC)."""
    today = _utc_today_str()
    try:
        db_execute(
            '''UPDATE gemini_usage
               SET call_count = call_count + 1,
                   updated_at = datetime('now')
               WHERE usage_date=?''',
            (today,)
        )
    except Exception:
        # Best-effort only; quota tracking should never crash AI calls.
        pass

# ── Prompt loader ────────────────────────────────────────────
PROMPTS_DIR = Path(__file__).parent.parent / 'prompts'

def load_prompt(filename: str) -> str:
    try:
        with open(PROMPTS_DIR / filename, 'r') as f:
            return f.read().strip()
    except Exception as e:
        print(f'[WARN] Could not load prompt {filename}: {e}')
        return ''

# Load at import time — fast path for every request
SYSTEM_PROMPT = load_prompt('system.txt')
SIGNAL_PROMPT = load_prompt('signal.txt')
CARD_PROMPT   = load_prompt('card.txt')

# ── OpenAI fallback ──────────────────────────────────────────
def _openai_generate(prompt: str, max_tokens: int = 1024, temperature: float = 0.3) -> str:
    """Call OpenAI gpt-4o-mini as fallback when Gemini is unavailable."""
    if not OPENAI_API_KEY:
        print('[WARN] OPENAI_API_KEY missing — cannot use OpenAI fallback')
        raise RuntimeError('No AI API key configured')
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY, timeout=10)
        resp = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user',   'content': prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return resp.choices[0].message.content or ''
    except Exception as e:
        print(f'[OpenAI] Error: {e}')
        raise

def _openai_chat(messages: list, last_content: str) -> str:
    """Call OpenAI gpt-4o-mini for multi-turn chat fallback."""
    if not OPENAI_API_KEY:
        print('[WARN] OPENAI_API_KEY missing — cannot use OpenAI chat fallback')
        return 'AI service temporarily unavailable. Please check NSE India and ET Markets directly.'
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY, timeout=10)
        oai_messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]
        for m in messages[:-1]:
            oai_messages.append({'role': m['role'], 'content': m['content']})
        oai_messages.append({'role': 'user', 'content': last_content})
        resp = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=oai_messages,
            max_tokens=800,
            temperature=0.4,
        )
        return resp.choices[0].message.content or ''
    except Exception as e:
        print(f'[OpenAI Chat] Error: {e}')
        return 'I am having trouble connecting right now. Please check NSE India and ET Markets directly.'

# ── Core Gemini call with retry + backoff ────────────────────
def gemini_call(
    prompt:       str,
    json_mode:    bool = False,
    max_tokens:   int  = 1024,
    temperature:  float = 0.3,
) -> str:
    """
    Core Gemini call with 3-attempt retry + exponential backoff.
    Falls back to OpenAI if Gemini key is missing.
    """
    if not _genai:
        print('[Gemini] Not configured — using OpenAI fallback')
        return _openai_generate(prompt, max_tokens=max_tokens, temperature=temperature)

    # Gemini quota management: avoid near-exhaustion by switching to OpenAI.
    try:
        used_calls = _get_gemini_call_count_today()
        if used_calls >= GEMINI_NEAR_THRESHOLD or used_calls >= GEMINI_DAILY_LIMIT:
            # OpenAI is the "safe" path when Gemini is near exhaustion.
            return _openai_generate(prompt, max_tokens=max_tokens, temperature=temperature)
        # Count the Gemini call before execution (best-effort).
        _increment_gemini_call_count_today()
    except Exception:
        pass

    generation_config = _genai.types.GenerationConfig(
        temperature=temperature,
        max_output_tokens=max_tokens,
        **({"response_mime_type": "application/json"} if json_mode else {}),
    )

    model = _genai.GenerativeModel(
        model_name=MODEL_NAME,
        system_instruction=SYSTEM_PROMPT,
        generation_config=generation_config,
    )

    for attempt in range(3):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            err_msg = str(e)
            print(f'[Gemini] Attempt {attempt + 1} failed: {err_msg}')
            if attempt == 2:
                # Final attempt failed — try OpenAI fallback
                print('[Gemini] All retries exhausted — trying OpenAI fallback')
                try:
                    return _openai_generate(prompt, max_tokens=max_tokens, temperature=temperature)
                except Exception:
                    raise
            sleep_secs = 2 ** (attempt + 1)
            print(f'[Gemini] Retrying in {sleep_secs}s...')
            time.sleep(sleep_secs)
    return ''

# ── Safe JSON parser ─────────────────────────────────────────
def parse_json_response(text: str, fallback: dict = None) -> dict:
    """Parses Gemini/OpenAI JSON response safely. Returns fallback on failure."""
    if not text:
        return fallback or {}
    try:
        cleaned = re.sub(r'```(?:json)?', '', text).strip().rstrip('`').strip()
        # Direct parse first
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
        # Find the first {...} JSON object (handles leading/trailing prose)
        match = re.search(r'\{[\s\S]*\}', cleaned)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        print(f'[AI] JSON parse failed: {repr(text[:200])}')
        return fallback or {'error': 'Parse failed'}
    except Exception as e:
        print(f'[AI] JSON parse error: {e}')
        return fallback or {'error': 'Parse failed'}

# ── Live context builder ─────────────────────────────────────
def build_chat_context() -> str:
    """Builds live NSE context injected into every chat message."""
    try:
        from services.indicators import get_nifty_snapshot
        from services.news_fetcher import get_market_headlines

        nifty     = get_nifty_snapshot()
        headlines = get_market_headlines(4)
        signals   = db_fetchall(
            'SELECT symbol, signal_type, explanation '
            'FROM signals ORDER BY created_at DESC LIMIT 3'
        )

        today = datetime.date.today().isoformat()
        ctx   = f"\n\n--- LIVE NSE CONTEXT ({today}) ---\n"
        ctx  += f"Nifty 50: {nifty.get('nifty50', 'N/A')} "
        ctx  += f"({nifty.get('nifty50_change_pct', 'N/A')}% today)\n"
        ctx  += "\nOpportunity Radar — recent signals:\n"

        for i, s in enumerate(signals, 1):
            snippet = (s.get('explanation') or '')[:120]
            ctx += f"{i}. {s['symbol']} [{(s.get('signal_type') or 'neutral').upper()}]: {snippet}...\n"

        ctx += "\nLatest ET Markets headlines:\n"
        for h in headlines:
            ctx += f"• {h[:120]}\n"
        ctx += "--- END CONTEXT ---"
        return ctx
    except Exception as e:
        print(f'[Context] Error building context: {e}')
        return ''

# ── Stock context injector ───────────────────────────────────
def _build_stock_context(user_message: str) -> str:
    """
    Detect NSE symbols in user message, fetch live quotes, and return
    an injected context block. Returns empty string if nothing found
    or API fails — never raises.
    """
    try:
        from services.nse_service import extract_symbols_from_text, get_quote
        # uppercase so "reliance" → "RELIANCE" is detected
        candidates = extract_symbols_from_text(user_message.upper())
        if not candidates:
            return ''

        stock_blocks = []
        for sym in candidates[:3]:  # cap at 3 symbols per message
            q = get_quote(sym)
            if q and q.get('price') is not None:
                sign  = '+' if (q.get('change') or 0) >= 0 else ''
                pct   = q.get('percent_change')
                chg   = q.get('change')
                lines = [
                    f"Stock: {q['symbol']}",
                    f"Price: {q['price']}",
                    f"Change: {sign}{chg} ({sign}{pct}%)",
                ]
                if q.get('high')       is not None: lines.append(f"High: {q['high']}")
                if q.get('low')        is not None: lines.append(f"Low: {q['low']}")
                if q.get('prev_close') is not None: lines.append(f"Prev Close: {q['prev_close']}")
                if q.get('volume')     is not None: lines.append(f"Volume: {q['volume']:,}")
                stock_blocks.append('\n'.join(lines))

        if not stock_blocks:
            return ''

        return '\n\n[LIVE NSE DATA]\n' + '\n\n'.join(stock_blocks) + '\n[END LIVE DATA]'
    except Exception as e:
        print(f'[StockContext] Error: {e}')
        return ''

# ── Rule-based signal engine ──────────────────────────────────
def _rule_based_signal_explanation(deal: dict, stock_data: dict) -> dict:
    """
    Rule-based signal generation used when both Gemini + OpenAI are unavailable.
    The spec intentionally uses *only* RSI + EMA to derive `signal_type`.
    """
    symbol     = (deal.get('symbol') or stock_data.get('symbol') or 'UNKNOWN').upper()
    rsi = stock_data.get('rsi')
    ema_signal = (stock_data.get('ema_signal') or 'neutral').lower()
    ema_is_bullish = 'bullish' in ema_signal
    ema_is_bearish = 'bearish' in ema_signal

    # Spec-required signal type logic.
    signal_type = 'neutral'
    if rsi is not None:
        try:
            rsi_val = float(rsi)
            if rsi_val < 30 and ema_is_bullish:
                signal_type = 'bullish'
            elif rsi_val > 70:
                signal_type = 'bearish'
        except (TypeError, ValueError):
            signal_type = 'neutral'

    confidence = 45
    if signal_type == 'bullish':
        confidence = 65
    elif signal_type == 'bearish':
        confidence = 60

    # Lightweight risk mapping using RSI extremes.
    if signal_type == 'bearish':
        risk_level = 'high'
    elif signal_type == 'bullish':
        risk_level = 'medium'
    else:
        risk_level = 'low'

    rsi_part = f'RSI is {round(float(rsi), 1)}' if rsi is not None else 'RSI is unavailable'
    ema_part = f'EMA indicates {("upward" if ema_is_bullish else "downward" if ema_is_bearish else "neutral")} momentum'

    # Spec-required explanation shape: RSI zone + EMA momentum support.
    if signal_type == 'bullish':
        explanation = (
            f'{rsi_part} (oversold) and {ema_part} with bullish setup. '
            f'Rule-based fallback used because Gemini/OpenAI quota is exhausted. '
            f'No AI provider available for deeper analysis.'
        )
    elif signal_type == 'bearish':
        explanation = (
            f'{rsi_part} (overbought). {ema_part}. '
            f'Rule-based fallback used because Gemini/OpenAI quota is exhausted. '
            f'No AI provider available for deeper analysis.'
        )
    else:
        explanation = (
            f'{rsi_part}. {ema_part}. '
            f'Rule-based fallback used because Gemini/OpenAI quota is exhausted. '
            f'No AI provider available for deeper analysis.'
        )

    key_obs = (
        'Oversold + bullish EMA setup suggests potential mean-reversion.' if signal_type == 'bullish' else
        'Overbought RSI suggests potential pullback risk.' if signal_type == 'bearish' else
        'Mixed RSI/EMA conditions — treat as neutral until AI is available.'
    )

    return {
        'explanation': explanation,
        'signal_type': signal_type,
        'risk_level': risk_level,
        'confidence': confidence,
        'key_observation': key_obs,
        'ai_provider': 'rule_based',
        'disclaimer': 'For educational purposes only. Not financial advice.',
    }


# ── Public API ────────────────────────────────────────────────

def explain_signal(deal: dict, stock_data: dict) -> dict:
    """
    Explains a raw NSE bulk/block deal. Returns structured dict.
    Tries AI first; falls back to rule-based engine — never returns generic
    'Signal analysis temporarily unavailable.' text.
    """
    try:
        prompt = SIGNAL_PROMPT.format(
            deal_json  = json.dumps(deal,       indent=2),
            price_json = json.dumps(stock_data, indent=2),
        )
        raw    = gemini_call(prompt, json_mode=True, max_tokens=512)
        result = parse_json_response(raw, fallback=None)
        if result and result.get('explanation') and \
                result['explanation'] not in ('Signal analysis temporarily unavailable.', ''):
            # Ensure risk_level is one of the valid values
            if result.get('risk_level') not in ('low', 'medium', 'high'):
                result['risk_level'] = 'medium'
            return result
    except Exception as e:
        print(f'[AI] explain_signal error: {e}')

    # AI unavailable or returned bad data — use rule-based fallback
    print(f'[AI] Using rule-based fallback for {deal.get("symbol", "?")}')
    return _rule_based_signal_explanation(deal, stock_data)

def generate_signal_card(symbol: str, stock_data: dict, news: list) -> dict:
    """Generates a full NSE Signal Card for a stock ticker."""
    _fallback = {
        'symbol':              symbol.upper(),
        'sentiment':           'neutral',
        'sentiment_score':     50,
        'sentiment_reason':    'Analysis temporarily unavailable.',
        'technical_snapshot':  'Technical analysis unavailable.',
        'news_impact_score':   50,
        'news_impact_summary': 'News data unavailable.',
        'risk_flags':          [],
        'actionable_context':  'Please check NSE and ET Markets directly.',
        'disclaimer':          'For educational purposes only. Not financial advice.',
    }
    try:
        news_text = '\n'.join(f"- {n['headline']}" for n in news[:5]) \
                    or 'No recent news available.'
        prompt = CARD_PROMPT.format(
            symbol         = symbol.upper(),
            price_json     = json.dumps(stock_data, indent=2),
            news_headlines = news_text,
        )
        raw = gemini_call(prompt, json_mode=True, max_tokens=768)
        return parse_json_response(raw, fallback=_fallback)
    except Exception as e:
        print(f'[AI] generate_signal_card error: {e}')
        return _fallback

def chat_response(messages: list) -> str:
    """
    Multi-turn chat using Gemini (preferred) or OpenAI fallback.
    Never crashes — returns a safe fallback string on all failures.
    """
    context  = build_chat_context()
    last_msg = messages[-1] if messages else None

    if not last_msg or last_msg.get('role') != 'user':
        return 'I did not receive a valid message. Please try again.'

    # Inject live NSE stock data if a ticker is detected in the message
    stock_context = _build_stock_context(last_msg['content'])
    augmented_content = last_msg['content'] + stock_context + context

    # ── Try Gemini first ─────────────────────────────────────
    if _genai:
        def remap_role(role: str) -> str:
            return 'model' if role == 'assistant' else 'user'

        history = []
        for msg in messages[:-1]:
            history.append({
                'role':  remap_role(msg['role']),
                'parts': [{'text': msg['content']}],
            })

        # Gemini quota management for chat as well: switch to OpenAI when near exhaustion.
        try:
            used_calls = _get_gemini_call_count_today()
            if used_calls >= GEMINI_NEAR_THRESHOLD or used_calls >= GEMINI_DAILY_LIMIT:
                return _openai_chat(messages, augmented_content)
            _increment_gemini_call_count_today()
        except Exception:
            pass

        model = _genai.GenerativeModel(
            model_name=MODEL_NAME,
            system_instruction=SYSTEM_PROMPT,
            generation_config=_genai.types.GenerationConfig(
                temperature=0.4,
                max_output_tokens=800,
            ),
        )

        try:
            chat_session = model.start_chat(history=history)
            response = chat_session.send_message(augmented_content)
            return response.text
        except Exception as e:
            print(f'[Gemini Chat] Error: {e} — trying without context')
            try:
                chat_session2 = model.start_chat(history=history)
                response2 = chat_session2.send_message(last_msg['content'])
                return response2.text
            except Exception as e2:
                print(f'[Gemini Chat] Retry failed: {e2} — falling back to OpenAI')

    # ── OpenAI fallback ───────────────────────────────────────
    return _openai_chat(messages, augmented_content)
