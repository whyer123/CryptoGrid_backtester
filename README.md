# Pionex Grid Backtester (Web App Edition)

這是一個具有極簡現代、高級玻璃擬物視覺 (Glassmorphism) 的 Pionex 網格回測工具。它整合了準確的 Pionex 歷史 K 線、精準的網格獲利與浮動盈虧運算。

**分離式架構**：目前的設計可以完美支援「前端託管於 GitHub Pages」同時「後端執行於自己的遠端 Server」的情境！專案已經分為 `frontend` 與 `backend` 兩個資料夾。

---

## 🚀 部署前端至 GitHub Pages

`frontend` 資料夾包含了純靜態的 HTML / CSS / JS，不需要任何編譯。

1. **建立 Repo 並上傳**：在 GitHub 上建立一個新的 Repository，然後把 `frontend` 資料夾**裡面**的所有檔案（而不是整個 frontend 資料夾哦！）上傳到該 Repository 的主目錄。
2. **修改後端 IP**：打開您上傳好的 `script.js`，將第一行的 `BACKEND_URL` 改成您遠端後端伺服器的 IP 與通訊埠（例如 `http://130.xxx.xxx.xxx:8080`）。
3. **開啟 GitHub Pages**：前往該 Repository 的 `Settings` -> 左側選單的 `Pages` -> Source 選擇 `Deploy from a branch` -> Branch 選擇 `main` (或 `master`) 並按下 Save。
4. 等待幾分鐘後，上方就會出現該網站的專屬網址囉！

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

### 3. 重啟與更新
若您修改了 Python 程式，必須強制關閉舊容器再重啟：
```bash
docker rm -f pionex-web
docker run -p 8080:8080 -d --name pionex-web pionex-backtester
```

---

## 💻 本地環境測試腳本

如果在自己電腦上想要開發或測試，可進入 `backend` 直接執行：
```bash
python3 grid_backtest.py
```
