# Pionex Grid Backtester (Web App Edition)

這是一個具有極簡現代、高級玻璃擬物視覺 (Glassmorphism) 的 Pionex 網格回測工具。它整合了準確的 Pionex 歷史 K 線、精準的網格獲利與浮動盈虧運算。

**分離式架構**：目前的設計可以完美支援「前端託管於 GitHub Pages」同時「後端執行於自己的遠端 Server」的情境！專案已經分為 `frontend` 與 `backend` 兩個資料夾。

---

## 🚀 前端已成功部屬 (GitHub Pages)

您的前端網站現已成功上線於：
👉 **[https://whyer123.github.io/CryptoGrid_backtester/](https://whyer123.github.io/CryptoGrid_backtester/)**

目前 GitHub Pages 會透過 `.github/workflows/deploy-pages.yml` 自動將 `frontend` 資料夾發佈。要讓這個精美的網頁順利運作，必須讓它連上您的「後端伺服器」。

### 如何修改程式綁定您的後端伺服器？
1. 打開專案中的 `frontend/script.js` 檔案。
2. 找到最上方的 `BACKEND_URL` 變數。
3. 將它替換成您**真實伺服器的 IP 與通訊埠**（必須包含 `http://` 或 `https://`）。
   ```javascript
   const BACKEND_URL = 'http://130.xxx.xxx.xxx:8080'; 
   ```
4. 存檔後，在終端機推送到 GitHub：
   ```bash
   git add frontend/script.js
   git commit -m "Update BACKEND_URL"
   git push origin main
   ```
5. GitHub Action 背景跑完後 (約 1 分鐘)，重新整理您的網頁，前端就會自動把計算任務交給您的伺服器了！

---

## 🛠️ 在自己的伺服器上部署後端 (API)

後端位於 `backend` 資料夾，負責調用 Pionex API 並執行網格試算。

### 1. 構建映像檔
將 `backend` 資料夾上傳到伺服器上。進入該目錄後，執行：
```bash
cd backend
docker build -t pionex-backtester .
```

### 2. 啟動後端容器
```bash
docker run -p 8080:8080 -d --name pionex-web pionex-backtester
```
> ※ 注意您的伺服器防火牆要打開 `8080` port，讓 GitHub Pages 上的網頁可以順利 Call 到您的 API。如果您有綁定網域，將網域指向這個 IP 即可加上 HTTPS。

### 3. 未來想要重啟或更新後端？
若您修改了 Python 程式，必須強制關閉舊容器再重新構建並啟動：
```bash
docker rm -f pionex-web
docker build -t pionex-backtester .
docker run -p 8080:8080 -d --name pionex-web pionex-backtester
```

*(註：為了安全起見，我在 `backend/app.py` 中已經將 CORS Origins 鎖定為 `https://whyer123.github.io`，確保只有您專屬的前端網址有權限呼叫這個伺服器的運算資源！)*

---

## 💻 本地環境測試腳本

如果在自己電腦上想要開發或測試，可進入 `backend` 直接執行：
```bash
python3 grid_backtest.py
```
