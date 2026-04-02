# pionex_api.py
import time
import json
import hmac
import hashlib
import urllib.parse
import urllib.request
import urllib.error

from pionex_secrets import API_KEY, API_SECRET

BASE_URL = "https://api.pionex.com"

COMMON_HEADERS = {
    # 避免某些環境遇到 403
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "application/json,text/plain,*/*",
}

def now_ms() -> int:
    return int(time.time() * 1000)

def _read_json(resp) -> dict:
    raw = resp.read().decode("utf-8")
    return json.loads(raw)

def public_get(path: str, params: dict | None = None, timeout: int = 15) -> dict:
    qs = urllib.parse.urlencode(params or {})
    url = f"{BASE_URL}{path}" + (f"?{qs}" if qs else "")
    req = urllib.request.Request(url, method="GET", headers=COMMON_HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return _read_json(resp)

def _build_sign_query(params: dict) -> tuple[str, str]:
    # 文件要求：簽名用的 value 不要 URL encode，key 依 ASCII 升序排序並用 & 串起來（含 timestamp） [oai_citation:1‡pionex-doc.gitbook.io](https://pionex-doc.gitbook.io/apidocs/restful/general/authentication)
    items = sorted(params.items(), key=lambda kv: kv[0])
    sign_qs = "&".join([f"{k}={v}" for k, v in items])  # 簽名用（不 encode）
    send_qs = urllib.parse.urlencode(items)             # 真正送出用（會 encode）
    return sign_qs, send_qs

def _signature(method: str, path: str, sign_qs: str, body_str: str = "") -> str:
    # payload = METHOD + PATH_URL (+ body for POST/DELETE)  [oai_citation:2‡pionex-doc.gitbook.io](https://pionex-doc.gitbook.io/apidocs/restful/general/authentication)
    path_url = f"{path}?{sign_qs}" if sign_qs else path
    payload = f"{method.upper()}{path_url}"
    if method.upper() in ("POST", "DELETE") and body_str:
        payload += body_str

    mac = hmac.new(API_SECRET.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256)
    return mac.hexdigest()

def private_request(method: str, path: str, params: dict | None = None, body: dict | None = None, timeout: int = 20) -> dict:
    params = dict(params or {})
    params["timestamp"] = now_ms()  # 私有端點需要毫秒 timestamp  [oai_citation:3‡pionex-doc.gitbook.io](https://pionex-doc.gitbook.io/apidocs/restful/general/authentication)

    sign_qs, send_qs = _build_sign_query(params)

    headers = dict(COMMON_HEADERS)
    data_bytes = None
    body_str = ""

    if body is not None:
        body_str = json.dumps(body, separators=(",", ":"))  # 固定 JSON 格式，避免簽名不一致
        data_bytes = body_str.encode("utf-8")
        headers["Content-Type"] = "application/json"

    sig = _signature(method, path, sign_qs, body_str=body_str)

    url = f"{BASE_URL}{path}?{send_qs}"
    req = urllib.request.Request(url, data=data_bytes, method=method.upper(), headers=headers)
    req.add_header("PIONEX-KEY", API_KEY)
    req.add_header("PIONEX-SIGNATURE", sig)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return _read_json(resp)
    except urllib.error.HTTPError as e:
        body_txt = ""
        try:
            body_txt = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        raise RuntimeError(f"HTTP {e.code} {e.reason}\nURL: {url}\nBODY:\n{body_txt}") from e

# ===== API wrappers =====

def get_daily_klines(symbol: str, limit: int = 60, end_time_ms: int | None = None) -> list[dict]:
    # GET /api/v1/market/klines  interval=1D  [oai_citation:4‡pionex-doc.gitbook.io](https://pionex-doc.gitbook.io/apidocs/restful/markets/get-klines)
    params = {
        "symbol": symbol,
        "interval": "1D",
        "limit": int(limit),
    }
    if end_time_ms is not None:
        params["endTime"] = int(end_time_ms)

    r = public_get("/api/v1/market/klines", params=params)
    if not r.get("result", False):
        raise RuntimeError(f"Klines error: {r}")

    klines = r["data"]["klines"]
    # 保險：依 time 排序（不假設回傳順序）
    klines.sort(key=lambda k: k["time"])
    return klines

def get_balances() -> list[dict]:
    # GET /api/v1/account/balances  Permission: Read  [oai_citation:5‡pionex-doc.gitbook.io](https://pionex-doc.gitbook.io/apidocs/restful/account/get-balance)
    r = private_request("GET", "/api/v1/account/balances", params={}, body=None)
    if not r.get("result", False):
        raise RuntimeError(f"Balance error: {r}")
    return r["data"]["balances"]

def place_market_buy(symbol: str, amount_usdt: str, client_order_id: str) -> int:
    # POST /api/v1/trade/order  type=MARKET, side=BUY, amount required  [oai_citation:6‡pionex-doc.gitbook.io](https://pionex-doc.gitbook.io/apidocs/restful/orders/new-order)
    body = {
        "symbol": symbol,
        "side": "BUY",
        "type": "MARKET",
        "amount": str(amount_usdt),
        "clientOrderId": client_order_id,
    }
    r = private_request("POST", "/api/v1/trade/order", params={}, body=body)
    if not r.get("result", False):
        raise RuntimeError(f"Market BUY failed: {r}")
    return int(r["data"]["orderId"])

def place_market_sell(symbol: str, size: str, client_order_id: str) -> int:
    # MARKET SELL 需要 size  [oai_citation:7‡pionex-doc.gitbook.io](https://pionex-doc.gitbook.io/apidocs/restful/orders/new-order)
    body = {
        "symbol": symbol,
        "side": "SELL",
        "type": "MARKET",
        "size": str(size),
        "clientOrderId": client_order_id,
    }
    r = private_request("POST", "/api/v1/trade/order", params={}, body=body)
    if not r.get("result", False):
        raise RuntimeError(f"Market SELL failed: {r}")
    return int(r["data"]["orderId"])

def get_order(order_id: int) -> dict:
    # GET /api/v1/trade/order  (filledSize/filledAmount/status)  [oai_citation:8‡pionex-doc.gitbook.io](https://pionex-doc.gitbook.io/apidocs/restful/orders/get-order)
    r = private_request("GET", "/api/v1/trade/order", params={"orderId": int(order_id)}, body=None)
    if not r.get("result", False):
        raise RuntimeError(f"Get order failed: {r}")
    return r["data"]

def wait_order_closed(order_id: int, max_wait_sec: int = 20, poll_interval_sec: float = 0.5) -> dict:
    # 等 MARKET 單完成（一般很快，但保險）
    deadline = time.time() + max_wait_sec
    last = None
    while time.time() < deadline:
        last = get_order(order_id)
        if last.get("status") == "CLOSED":  # OPEN / CLOSED  [oai_citation:9‡pionex-doc.gitbook.io](https://pionex-doc.gitbook.io/apidocs/restful/orders/get-order)
            return last
        time.sleep(poll_interval_sec)
    # 逾時也回傳目前狀態（讓上層決定）
    return last or get_order(order_id)