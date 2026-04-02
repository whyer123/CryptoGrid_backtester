import time
import datetime
import os
from typing import List, Dict, Tuple
from pionex_api import public_get

def fetch_history_klines(symbol: str, interval: str, start_dt: datetime.datetime, end_dt: datetime.datetime) -> List[Dict]:
    limit = 500
    all_klines = []
    
    current_end_ms = int(end_dt.timestamp() * 1000)
    start_ms = int(start_dt.timestamp() * 1000)
    
    print(f"Fetching {interval} klines for {symbol} from {start_dt.date()} to {end_dt.date()}...")
    
    while True:
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit,
            "endTime": current_end_ms
        }
        res = public_get("/api/v1/market/klines", params=params)
        
        if not res.get("result", False):
            print(f"Error fetching klines: {res}")
            break
            
        data = res["data"]["klines"]
        if not data:
            break
            
        data.sort(key=lambda k: k["time"])
        chunk = [k for k in data if k["time"] >= start_ms and k["time"] < current_end_ms]
        
        if not chunk:
            if data[-1]["time"] < start_ms:
                break
            if data[0]["time"] < current_end_ms:
                current_end_ms = data[0]["time"]
                continue
            else:
                break
            
        all_klines = chunk + all_klines
        
        current_end_ms = data[0]["time"]  
        if current_end_ms <= start_ms:
            break
            
        time.sleep(0.1)
        
    return all_klines

def get_best_interval(start_dt: datetime.datetime, end_dt: datetime.datetime) -> str:
    limit = 9000  # API limit 10000
    minutes = (end_dt - start_dt).total_seconds() / 60
    
    if minutes <= limit * 1: return "1M"
    elif minutes <= limit * 5: return "5M"
    elif minutes <= limit * 15: return "15M"
    elif minutes <= limit * 30: return "30M"
    elif minutes <= limit * 60: return "60M"
    elif minutes <= limit * 240: return "4H"
    elif minutes <= limit * 480: return "8H"
    elif minutes <= limit * 720: return "12H"
    else: return "1D"

def simulate_grid(symbol: str, lower: float, upper: float, grid_count: int, capital: float, klines: List[Dict], maker_fee: float = 0.0002) -> dict:
    if grid_count < 2 or lower >= upper or not klines:
        return {}
        
    gap = (upper - lower) / (grid_count - 1)
    lines = [lower + i * gap for i in range(grid_count)]
    
    open_p = float(klines[0]['open'])
    final_p = float(klines[-1]['close'])
    
    buys_pending = [0] * grid_count
    sells_pending = [0] * grid_count
    initial_sells_pending = [0] * grid_count
    
    buy_prices = []
    num_sells = 0
    for i in range(grid_count):
        if lines[i] < open_p:
            buys_pending[i] = 1
            buy_prices.append(lines[i])
        else:
            initial_sells_pending[i] = 1
            num_sells += 1
            
    # Calculate fixed quantity per grid based on required capital deployment
    req = open_p * num_sells + sum(buy_prices)
    qty = capital / req if req > 0 else 0
    
    current_usdt = capital
    current_base = 0.0
    
    # Initial coin purchase cost & fee
    initial_base_req = num_sells * qty
    cost = initial_base_req * open_p
    fee = cost * maker_fee
    current_usdt -= (cost + fee)
    current_base += initial_base_req
    
    match_count = 0
    total_grid_profit = 0.0
    match_history = []
    
    for k in klines:
        o = float(k['open'])
        c = float(k['close'])
        h = float(k['high'])
        l = float(k['low'])
        
        # Approximate path using 1 min candles
        if o < c: path = [l, h, c]
        else: path = [h, l, c]
            
        last_p = o
        for target_p in path:
            if target_p < last_p:
                for i in range(grid_count - 1, -1, -1):
                    if target_p <= lines[i] <= last_p and buys_pending[i] > 0:
                        b_count = buys_pending[i]
                        buys_pending[i] = 0
                        if i + 1 < grid_count: 
                            sells_pending[i+1] += b_count
                            
                        trade_cost = lines[i] * qty * b_count
                        trade_fee = trade_cost * maker_fee
                        current_usdt -= (trade_cost + trade_fee)
                        current_base += (qty * b_count)
                        
            elif target_p > last_p:
                for i in range(grid_count):
                    if target_p >= lines[i] >= last_p:
                        
                        # Process Initial Sells
                        if initial_sells_pending[i] > 0:
                            s_count = initial_sells_pending[i]
                            initial_sells_pending[i] = 0
                            if i - 1 >= 0: buys_pending[i-1] += s_count
                            
                            revenue = lines[i] * qty * s_count
                            trade_fee = revenue * maker_fee
                            current_usdt += (revenue - trade_fee)
                            current_base -= (qty * s_count)
                            
                        # Process Normal Grid Sells (Matches)
                        if sells_pending[i] > 0:
                            s_count = sells_pending[i]
                            sells_pending[i] = 0
                            if i - 1 >= 0: buys_pending[i-1] += s_count
                            
                            revenue = lines[i] * qty * s_count
                            trade_fee = revenue * maker_fee
                            current_usdt += (revenue - trade_fee)
                            current_base -= (qty * s_count)
                            
                            target_buy_p = lines[i-1]
                            trade_cost = target_buy_p * qty * s_count
                            buy_fee = trade_cost * maker_fee
                            
                            # Realized Grid Profit for this cycle
                            profit = (revenue - trade_fee) - (trade_cost + buy_fee)
                            total_grid_profit += profit
                            match_count += s_count
                            
                            # Record the arbitrage event
                            k_time = datetime.datetime.fromtimestamp(k['time']/1000).strftime('%Y/%m/%d %H:%M:%S')
                            for _ in range(s_count):
                                match_history.append((k_time, profit / s_count))
                                
            last_p = target_p
            
    final_value = current_usdt + current_base * final_p
    total_pnl = final_value - capital
    trend_pnl = total_pnl - total_grid_profit
    
    return {
        "gap": gap,
        "qty_per_grid": qty,
        "matches": match_count,
        "grid_profit": total_grid_profit,
        "trend_pnl": trend_pnl,
        "total_pnl": total_pnl,
        "match_history": match_history
    }

def main():
    print("=== Pionex 網格回測工具 (精確合約版) ===")
    
    print("選擇交易對:")
    print("1) BTC_USDT")
    print("2) ETH_USDT")
    print("3) SOL_USDT")
    print("4) SUI_USDT")
    print("5) 手動輸入")
    
    choice = input("請選擇 (預設 1): ").strip()
    
    if choice == '2':
        symbol = "ETH_USDT"
        def_lower, def_upper = 2000.0, 4500.0
    elif choice == '3':
        symbol = "SOL_USDT"
        def_lower, def_upper = 100.0, 250.0
    elif choice == '4':
        symbol = "SUI_USDT"
        def_lower, def_upper = 0.5, 2.5
    elif choice == '5':
        symbol = input("輸入完整交易對 (例如 DOGE_USDT): ").strip().upper()
        def_lower, def_upper = 0.0, 0.0
    else:
        symbol = "BTC_USDT"
        def_lower, def_upper = 54000.0, 78000.0
    
    print(f"\n目前選擇: {symbol}")
    
    start_str = input("輸入開始時間 YYYYMMDD (預設 20260303): ").strip() or "20260303"
    start_dt = datetime.datetime.strptime(start_str, "%Y%m%d")
        
    end_str = input("輸入結束時間 YYYYMMDD (預設今天): ").strip()
    if end_str and len(end_str) == 8:
        end_dt = datetime.datetime.strptime(end_str, "%Y%m%d")
    else:
        end_dt = datetime.datetime.now()
        
    if start_dt >= end_dt:
        print("開始時間必須早於結束時間！")
        return
        
    if def_lower > 0 and def_upper > 0:
        lower_str = input(f"輸入區間下限 (預設 {def_lower}): ").strip()
        lower = float(lower_str) if lower_str else def_lower
        
        upper_str = input(f"輸入區間上限 (預設 {def_upper}): ").strip()
        upper = float(upper_str) if upper_str else def_upper
    else:
        # 手動輸入時沒有預設值，強迫使用者輸入
        lower = float(input("輸入區間下限: ").strip())
        upper = float(input("輸入區間上限: ").strip())
    
    inv_str = input("輸入投資本金 USDT (預設 240): ").strip()
    investment = float(inv_str) if inv_str else 240.0
    
    lev_str = input("輸入合約槓桿倍數 (現貨請輸入 1，預設 5): ").strip()
    leverage = float(lev_str) if lev_str else 5.0
    
    total_capital = investment * leverage
    
    grids_str = input("輸入想比較的網格數，用逗號分隔 (預設 6,12,24): ").strip()
    if grids_str:
        configs = [int(x.strip()) for x in grids_str.split(',')]
    else:
        configs = [6, 12, 24]
        
    interval = get_best_interval(start_dt, end_dt)
    print(f"\n[系統] 自動判定避開 API 限制的最佳 K 線區間為: {interval}")
    
    klines = fetch_history_klines(symbol, interval, start_dt, end_dt)
    print(f"\nTotal K-lines fetched: {len(klines)}")
    
    if not klines:
        print("未獲取到 K 線資料")
        return
        
    real_start = datetime.datetime.fromtimestamp(klines[0]['time']/1000).strftime('%Y-%m-%d %H:%M:%S')
    real_end = datetime.datetime.fromtimestamp(klines[-1]['time']/1000).strftime('%Y-%m-%d %H:%M:%S')
    
    report = []
    report.append("=== Pionex 網格回測詳細報告 ===")
    report.append(f"交易對: {symbol}")
    report.append(f"時間範圍: {real_start} -> {real_end}")
    report.append(f"初始建倉開盤價: {klines[0]['open']}  |  期末收盤價: {klines[-1]['close']}")
    report.append(f"設定投入本金: {investment} USDT | 槓桿: {leverage}x | 總操作資金: {total_capital} USDT")
    report.append("-" * 60)
    
    print("-" * 60)
    for grids in configs:
        res = simulate_grid(symbol, lower, upper, grids, total_capital, klines)
        if not res: continue
        
        # Terminal Summary
        print(f"【 {grids:2d} 格網格 】區間: {lower}-{upper} (每格間距: {res['gap']:.2f})")
        print(f"  - 單格掛單數量: {res['qty_per_grid']:.5f} {symbol.split('_')[0]}")
        print(f"  - 刷單次數: {res['matches']} 次")
        print(f"  - 總盈利 PNL: {res['total_pnl']:.2f} USDT (網格 {res['grid_profit']:.2f} + 浮動 {res['trend_pnl']:.2f})")
        print("-" * 60)
        
        # File Report Log
        report.append(f"\n【 {grids} 格網格 (區間: {lower}-{upper}) 】")
        report.append(f"  - 每格間距: {res['gap']:.2f} USDT")
        report.append(f"  - 每格掛單數量: {res['qty_per_grid']:.6f} {symbol.split('_')[0]}")
        report.append(f"  - 總套利次數: {res['matches']} 次")
        report.append(f"  - 網格利潤 (已扣除掛單手續費0.02%): {res['grid_profit']:.2f} USDT")
        report.append(f"  - 趨勢盈虧 (浮動盈虧): {res['trend_pnl']:.2f} USDT")
        report.append(f"  - 總盈利 (總 PNL): {res['total_pnl']:.2f} USDT")
        report.append(f"  - 總收益率: {(res['total_pnl']/investment)*100:.2f}%")
        
        report.append("\n  [ 歷次刷單時間明細 ]")
        if res['match_history']:
            for i, (t_str, p) in enumerate(res['match_history'], 1):
                report.append(f"    #{i:<4} {t_str}   +{p:.4f} USDT")
        else:
            report.append("    無套利紀錄")
            
    output_file = f"backtest_report_{start_dt.strftime('%m%d')}_{end_dt.strftime('%m%d')}.txt"
    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_file)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(report))
        
    print(f"✅ 完整回測報告已寫出至: {file_path}")

if __name__ == "__main__":
    main()
