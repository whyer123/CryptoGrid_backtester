// 填入您架設後端伺服器的網址 (如果是放在 GitHub Pages，這裡必須填寫您真實的伺服器 IP 或網域)
// 例如: const BACKEND_URL = 'http://134.xxx.xxx.xxx:8080';
const BACKEND_URL = ''; // 留空則預設為當前網域

document.addEventListener('DOMContentLoaded', () => {
    const defaultBounds = {
        'BTC_USDT': [54000, 78000],
        'ETH_USDT': [2000, 4500],
        'SOL_USDT': [50, 250],
        'SUI_USDT': [0.5, 3.0]
    };

    const symbolSelect = document.getElementById('symbol');
    const customSymbol = document.getElementById('customSymbol');
    const lowerInput = document.getElementById('lower');
    const upperInput = document.getElementById('upper');

    const modal = document.getElementById('historyModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.getElementById('modalBody');
    const closeModal = document.getElementById('closeModal');

    closeModal.addEventListener('click', () => modal.classList.remove('active'));
    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.classList.remove('active');
    });

    symbolSelect.addEventListener('change', (e) => {
        const val = e.target.value;
        if (val === 'CUSTOM') {
            customSymbol.classList.remove('hidden');
            lowerInput.value = '';
            upperInput.value = '';
        } else {
            customSymbol.classList.add('hidden');
            if (defaultBounds[val]) {
                lowerInput.value = defaultBounds[val][0];
                upperInput.value = defaultBounds[val][1];
            }
        }
    });

    const form = document.getElementById('backtestForm');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        let sym = symbolSelect.value;
        if (sym === 'CUSTOM') sym = customSymbol.value.trim().toUpperCase();
        
        const payload = {
            symbol: sym,
            start_time: document.getElementById('start_time').value,
            end_time: document.getElementById('end_time').value,
            lower: document.getElementById('lower').value,
            upper: document.getElementById('upper').value,
            capital: document.getElementById('capital').value,
            leverage: document.getElementById('leverage').value,
            grids: document.getElementById('grids').value
        };

        const btnText = document.querySelector('.btn-text');
        const spinner = document.getElementById('spinner');
        btnText.classList.add('hidden');
        spinner.classList.remove('hidden');
        
        try {
            const apiUrl = BACKEND_URL ? `${BACKEND_URL}/api/backtest` : '/api/backtest';
            const res = await fetch(apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            
            if (!res.ok || !data.success) {
                alert(data.error || "Unknown Error from Server");
                return;
            }
            
            renderResults(data);
        } catch (err) {
            alert("Network Error: Make sure backend is running.\n" + err.message);
        } finally {
            btnText.classList.remove('hidden');
            spinner.classList.add('hidden');
        }
    });

    function renderResults(data) {
        document.getElementById('initialPrompt').classList.add('hidden');
        const metaInfo = document.getElementById('metaInfo');
        const resultsGrid = document.getElementById('resultsGrid');
        
        metaInfo.classList.remove('hidden');
        resultsGrid.classList.remove('hidden');
        
        const m = data.metadata;
        metaInfo.innerHTML = `
            <div class="meta-item"><span class="meta-label">Symbol</span><span class="meta-val" style="color:var(--primary)">${m.symbol}</span></div>
            <div class="meta-item"><span class="meta-label">Time Range</span><span class="meta-val" style="font-size:0.95rem">${m.real_start} <br> ${m.real_end}</span></div>
            <div class="meta-item"><span class="meta-label">Interval</span><span class="meta-val">${m.interval}</span></div>
            <div class="meta-item"><span class="meta-label">Start Px</span><span class="meta-val">${Number(m.initial_price).toFixed(2)}</span></div>
            <div class="meta-item"><span class="meta-label">Capital</span><span class="meta-val">${m.total_capital} USDT<br><span style="font-size:0.8rem;color:var(--text-muted)">(${m.investment}x${m.leverage})</span></span></div>
        `;
        
        resultsGrid.innerHTML = '';
        data.results.forEach((r, index) => {
            const isPos = r.total_pnl >= 0;
            const tClass = isPos ? 'pos' : 'neg';
            const bClass = isPos ? 'profit-pos' : 'profit-neg';
            const sign = isPos ? '+' : '';
            
            const card = document.createElement('div');
            card.className = 'result-card ' + (index === 0 ? 'fade-in' : '');
            if(index > 0) card.style.animationDelay = (index * 0.1) + 's';
            card.style.animationFillMode = 'both';
            card.classList.add('fade-in');
            
            card.innerHTML = `
                <div class="card-header">
                    <div class="grid-title">${r.grid_config} Grids</div>
                    <div class="roi-badge ${bClass}">${sign}${r.roi_percent}% ROI</div>
                </div>
                
                <div class="stat-row" style="margin-top: 0.5rem;">
                    <span class="stat-label">Total PNL</span>
                    <span class="stat-val val-big ${tClass}">${sign}${r.total_pnl.toFixed(2)} <span style="font-size:1rem;color:var(--text-muted)">USDT</span></span>
                </div>
                
                <div style="height:1px; background:rgba(255,255,255,0.05); margin: 0.5rem 0;"></div>
                
                <div class="stat-row">
                    <span class="stat-label">Grid Profit (Matched)</span>
                    <span class="stat-val pos">+${r.grid_profit.toFixed(2)}</span>
                </div>
                
                <div class="stat-row">
                    <span class="stat-label">Trend PNL (Floating)</span>
                    <span class="stat-val ${r.trend_pnl >= 0 ? 'pos' : 'neg'}">${r.trend_pnl > 0 ? '+' : ''}${r.trend_pnl.toFixed(2)}</span>
                </div>
                
                <div style="height:1px; background:rgba(255,255,255,0.05); margin: 0.5rem 0;"></div>
                
                <div class="stat-row">
                    <span class="stat-label">Arbitrage Count</span>
                    <span class="stat-val" style="color:#fff">${r.matches} times</span>
                </div>
                
                <div class="stat-row">
                    <span class="stat-label">Qty per Grid</span>
                    <span class="stat-val">${r.qty_per_grid.toFixed(5)} ${r.base_coin}</span>
                </div>
                
                <div class="stat-row">
                    <span class="stat-label">Grid Gap</span>
                    <span class="stat-val">${r.gap.toFixed(2)} USDT</span>
                </div>
            `;
            
            card.addEventListener('click', () => showModal(r));
            
            resultsGrid.appendChild(card);
        });
    }

    function showModal(r) {
        modalTitle.textContent = `${r.grid_config} Grids - Match History`;
        modalBody.innerHTML = '';
        
        if (!r.match_history || r.match_history.length === 0) {
            modalBody.innerHTML = '<div class="history-empty">No arbitrage executed yet.</div>';
        } else {
            const history = [...r.match_history].reverse();
            history.forEach((h, i) => {
                const item = document.createElement('div');
                item.className = 'history-item';
                item.innerHTML = `
                    <span class="history-time"><span style="opacity:0.4;margin-right:0.5rem;font-size:0.85em">#${history.length - i}</span> ${h[0]}</span>
                    <span class="history-profit">+${h[1].toFixed(4)} USDT</span>
                `;
                modalBody.appendChild(item);
            });
        }
        
        modal.classList.add('active');
    }
});
