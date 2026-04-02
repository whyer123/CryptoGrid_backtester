from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import datetime
import uvicorn
import os

from grid_backtest import fetch_history_klines, get_best_interval, simulate_grid

app = FastAPI(title="Pionex Grid Backtest API")

app.add_middleware(
    CORSMiddleware,
    # 這裡填寫您的前端網址，確保只有您的網頁可以呼叫這個 API
    allow_origins=[
        "https://whyer123.github.io",
        "http://localhost:8080",
        "http://127.0.0.1:8080"
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Endpoint
@app.post("/api/backtest")
async def run_backtest(request: Request):
    data = await request.json()
    symbol = data.get("symbol", "BTC_USDT").upper()
    start_str = data.get("start_time")
    end_str = data.get("end_time")
    
    # 預設7天
    if start_str and len(start_str) == 8:
        start_dt = datetime.datetime.strptime(start_str, "%Y%m%d")
    else:
        start_dt = datetime.datetime.now() - datetime.timedelta(days=7)
        
    if end_str and len(end_str) == 8:
        end_dt = datetime.datetime.strptime(end_str, "%Y%m%d")
    else:
        end_dt = datetime.datetime.now()
        
    if start_dt >= end_dt:
        return JSONResponse(status_code=400, content={"error": "開始時間必須早於結束時間！"})
        
    lower = float(data.get("lower", 54000.0))
    upper = float(data.get("upper", 78000.0))
    investment = float(data.get("capital", 240.0))
    leverage = float(data.get("leverage", 5.0))
    grids_str = data.get("grids", "6,12,24")
    
    total_capital = investment * leverage
    
    configs = [int(x.strip()) for x in grids_str.split(',') if x.strip().isdigit()]
    if not configs:
        configs = [6, 12, 24]
        
    interval = get_best_interval(start_dt, end_dt)
    
    # 執行資料抓取與運算
    try:
        klines = fetch_history_klines(symbol, interval, start_dt, end_dt)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"API 擷取錯誤: {str(e)}"})
        
    if not klines:
        return JSONResponse(status_code=400, content={"error": f"抓取不到 {symbol} 在該區間的歷史資料。"})
        
    real_start = datetime.datetime.fromtimestamp(klines[0]['time']/1000).strftime('%Y-%m-%d %H:%M:%S')
    real_end = datetime.datetime.fromtimestamp(klines[-1]['time']/1000).strftime('%Y-%m-%d %H:%M:%S')
    
    results = []
    
    for grids in configs:
        res = simulate_grid(symbol, lower, upper, grids, total_capital, klines)
        if not res: continue
        res["grid_config"] = grids
        res["base_coin"] = symbol.split('_')[0]
        # Calculate yield relative to original margin (investment)
        res["roi_percent"] = round((res["total_pnl"] / investment) * 100, 2) if investment > 0 else 0
        results.append(res)
        
    return {
        "success": True,
        "metadata": {
            "symbol": symbol,
            "interval": interval,
            "real_start": real_start,
            "real_end": real_end,
            "initial_price": klines[0]['open'],
            "final_price": klines[-1]['close'],
            "total_capital": total_capital,
            "investment": investment,
            "leverage": leverage,
            "kline_count": len(klines)
        },
        "results": results
    }

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8080, workers=1)
