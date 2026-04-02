# Pionex Grid Backtester

Advanced Contract Grid Simulation Engine based on real-time K-lines.

## 🚀 Deployment Guide / 部署指南

This project consists of a **Python FastAPI Backend** (hosted locally via Docker + Cloudflare Tunnel) and a **Vanilla JS Frontend** (hosted on GitHub Pages).

### Prerequisites / 事前準備

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.
- (Optional) Git installed for pushing frontend updates.

---

### 1️⃣ Backend Deployment (Local + Cloudflare Tunnel)

We use Docker Compose to run both the FastAPI Backend and Cloudflare Tunnel together. 這完美解決了學校實驗室 24 小時不關機的電腦要對外開放連線的問題！

1. **Navigate to the backend directory:**
    ```bash
    cd backend
    ```

2. **Start the services:**
    ```bash
    docker-compose up -d
    ```

3. **Get the Public URL:**
    Since we are using a Quick Tunnel, the URL changes every time you restart. View the logs to find the assigned `https://` URL.
    ```bash
    docker-compose logs cloudflared
    ```
    Look for a line like:
    > `https://xxxx-xxxx-xxxx.trycloudflare.com`

*(註：這段自動生成的 Cloudflare 網址已經具備 HTTPS 高強度加密，而且能完美打穿實驗室防火牆！)*

---

### 2️⃣ Frontend Deployment (GitHub Pages)

The frontend uses a zero-conflict deployment script (Option C), compiling to a `gh-pages` branch locally without dirtying your `main` branch.

1. **Update the API URL:**
    打開 `frontend/.env.production`，將您在上一步拿到的 Cloudflare 網址貼在這個隱藏檔裡面（記得網址最後要加上 `/api`）。這個檔案是不會被同步到 Github 上的，所以兩台電腦可以分別設定不同網址！

    ```env
    VITE_API_BASE_URL=https://xxxx-xxxx-xxxx.trycloudflare.com/api
    ```

2. **Deploy to GitHub Pages:**
    進入 `frontend` 目錄並執行部署腳本，腳本會自動替您完成打包上傳，並且「只」推送到 `gh-pages` 分支發佈最新的站點！

    ```bash
    cd frontend
    npm run deploy
    ```

3. **Visit your site:**
    大約不到 1 分鐘，您的 App 就能於全世界任何地方訪問囉：
    > [https://whyer123.github.io/CryptoGrid_backtester/](https://whyer123.github.io/CryptoGrid_backtester/)

---

### 🛑 如何關閉後端伺服器？

當您不想再開放別人使用您的實驗室電腦時，只需要在電腦的終端機執行關閉指令：

1. 確保您在 `backend` 資料夾下：
   ```bash
   cd backend
   ```
2. 執行關閉指令（這會自動關閉 API 和 Cloudflare 通道）：
   ```bash
   docker-compose down
   ```

---

### 🛠️ 其他常用指令

- **重啟後台 (Restart Backend):** `cd backend && docker-compose restart`
- **查看隧道與新網址 (View Tunnel Logs):** `cd backend && docker-compose logs -f cloudflared`
