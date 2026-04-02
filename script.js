// 在此填寫後端網址 (編譯腳本會自動替換)
const BACKEND_URL = 'https://promise-biggest-their-mount.trycloudflare.com/api';

const locales = {
    en: {
        titleSuffix: "Backtester",
        subtitle: "Advanced Contract Grid Simulation Engine",
        config: "Configuration",
        symbol: "Symbol",
        customSymbol: "Custom...",
        startDate: "Start Date",
        endDate: "End Date",
        emptyToday: "empty=today",
        lowerBound: "Lower Bound",
        upperBound: "Upper Bound",
        investment: "Investment (USDT)",
        leverage: "Leverage (x)",
        compareGrids: "Compare Grids (comma separated)",
        runSimulation: "Run Simulation",
        poweredBy: "Powered by Pionex Real-Time API",
        readyTitle: "Ready to Simulate",
        readyDesc: "Enter your configuration on the left and run the backtest to see advanced metrics.",
        matchHistory: "Match History",
        timeRange: "Time Range",
        interval: "Interval",
        startPx: "Start Px",
        capital: "Capital",
        grids: "Grids",
        totalPnl: "Total PNL",
        gridProfit: "Grid Profit (Matched)",
        trendPnl: "Trend PNL (Floating)",
        arbitrageCount: "Arbitrage Count",
        qtyPerGrid: "Qty per Grid",
        gridGap: "Grid Gap",
        times: "times",
        noArbitrage: "No arbitrage executed yet.",
        networkError: "Network Error: Make sure backend is running.",
        unknownError: "Unknown Error from Server",
        langToggle: "中文"
    },
    zh: {
        titleSuffix: "網格回測",
        subtitle: "進階合約網格模擬與評估分析引擎",
        config: "參數設定",
        symbol: "交易對",
        customSymbol: "自訂...",
        startDate: "開始日期",
        endDate: "結束日期",
        emptyToday: "留空為今日",
        lowerBound: "網格下限",
        upperBound: "網格上限",
        investment: "總投資額 (USDT)",
        leverage: "槓桿倍數 (x)",
        compareGrids: "比較網格數 (用逗號分隔)",
        runSimulation: "開始回測",
        poweredBy: "資料來源: Pionex Real-Time API",
        readyTitle: "準備就緒",
        readyDesc: "請在左側輸入您的參數，點擊上方按鈕執行回測以查看進階數據。",
        matchHistory: "歷史套利紀錄",
        timeRange: "時間範圍",
        interval: "K線級別",
        startPx: "開倉價格",
        capital: "總資金",
        grids: "格",
        totalPnl: "總利潤 PNL",
        gridProfit: "網格利潤 (已掌握)",
        trendPnl: "浮動盈虧",
        arbitrageCount: "套利次數",
        qtyPerGrid: "每格數量",
        gridGap: "每格利潤差",
        times: "次",
        noArbitrage: "尚無套利紀錄",
        networkError: "網路錯誤：請確認後端伺服器是否正常運作。",
        unknownError: "來自伺服器的未知錯誤",
        langToggle: "English"
    }
};
let currentLang = 'en';

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

    const langToggle = document.getElementById('langToggle');
    function updateLanguage() {
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            if (locales[currentLang][key]) el.innerHTML = locales[currentLang][key];
        });
        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            if (locales[currentLang][key]) el.placeholder = locales[currentLang][key];
        });
        langToggle.textContent = locales[currentLang].langToggle;
    }
    langToggle.addEventListener('click', () => {
        currentLang = currentLang === 'en' ? 'zh' : 'en';
        updateLanguage();
    });
    updateLanguage();

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
                alert(data.error || locales[currentLang].unknownError);
                return;
            }

            renderResults(data);
        } catch (err) {
            alert(`${locales[currentLang].networkError}\n${err.message}`);
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
        const T = locales[currentLang];

        metaInfo.innerHTML = `
            <div class="meta-item"><span class="meta-label">${T.symbol}</span><span class="meta-val" style="color:var(--primary)">${m.symbol}</span></div>
            <div class="meta-item"><span class="meta-label">${T.timeRange}</span><span class="meta-val" style="font-size:0.95rem">${m.real_start} <br> ${m.real_end}</span></div>
            <div class="meta-item"><span class="meta-label">${T.interval}</span><span class="meta-val">${m.interval}</span></div>
            <div class="meta-item"><span class="meta-label">${T.startPx}</span><span class="meta-val">${Number(m.initial_price).toFixed(2)}</span></div>
            <div class="meta-item"><span class="meta-label">${T.capital}</span><span class="meta-val">${m.total_capital} USDT<br><span style="font-size:0.8rem;color:var(--text-muted)">(${m.investment}x${m.leverage})</span></span></div>
        `;

        resultsGrid.innerHTML = '';
        data.results.forEach((r, index) => {
            const isPos = r.total_pnl >= 0;
            const tClass = isPos ? 'pos' : 'neg';
            const bClass = isPos ? 'profit-pos' : 'profit-neg';
            const sign = isPos ? '+' : '';

            const card = document.createElement('div');
            card.className = 'result-card ' + (index === 0 ? 'fade-in' : '');
            if (index > 0) card.style.animationDelay = (index * 0.1) + 's';
            card.style.animationFillMode = 'both';
            card.classList.add('fade-in');

            card.innerHTML = `
                <div class="card-header">
                    <div class="grid-title">${r.grid_config} ${T.grids}</div>
                    <div class="roi-badge ${bClass}">${sign}${r.roi_percent}% ROI</div>
                </div>
                
                <div class="stat-row" style="margin-top: 0.5rem;">
                    <span class="stat-label">${T.totalPnl}</span>
                    <span class="stat-val val-big ${tClass}">${sign}${r.total_pnl.toFixed(2)} <span style="font-size:1rem;color:var(--text-muted)">USDT</span></span>
                </div>
                
                <div style="height:1px; background:rgba(255,255,255,0.05); margin: 0.5rem 0;"></div>
                
                <div class="stat-row">
                    <span class="stat-label">${T.gridProfit}</span>
                    <span class="stat-val pos">+${r.grid_profit.toFixed(2)}</span>
                </div>
                
                <div class="stat-row">
                    <span class="stat-label">${T.trendPnl}</span>
                    <span class="stat-val ${r.trend_pnl >= 0 ? 'pos' : 'neg'}">${r.trend_pnl > 0 ? '+' : ''}${r.trend_pnl.toFixed(2)}</span>
                </div>
                
                <div style="height:1px; background:rgba(255,255,255,0.05); margin: 0.5rem 0;"></div>
                
                <div class="stat-row">
                    <span class="stat-label">${T.arbitrageCount}</span>
                    <span class="stat-val" style="color:#fff">${r.matches} ${T.times}</span>
                </div>
                
                <div class="stat-row">
                    <span class="stat-label">${T.qtyPerGrid}</span>
                    <span class="stat-val">${r.qty_per_grid.toFixed(5)} ${r.base_coin}</span>
                </div>
                
                <div class="stat-row">
                    <span class="stat-label">${T.gridGap}</span>
                    <span class="stat-val">${r.gap.toFixed(2)} USDT</span>
                </div>
            `;

            card.addEventListener('click', () => showModal(r));

            resultsGrid.appendChild(card);
        });
    }

    function showModal(r) {
        const T = locales[currentLang];
        modalTitle.textContent = `${r.grid_config} ${T.grids} - ${T.matchHistory}`;
        modalBody.innerHTML = '';

        if (!r.match_history || r.match_history.length === 0) {
            modalBody.innerHTML = `<div class="history-empty">${T.noArbitrage}</div>`;
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
