const fs = require('fs-extra');
const path = require('path');
require('dotenv').config({ path: '.env.production' });

const srcDir = __dirname;
const distDir = path.join(__dirname, 'dist');
const filesToCopy = ['index.html', 'style.css'];

// 確保清理舊的 dist
fs.emptyDirSync(distDir);

// 複製靜態檔案
filesToCopy.forEach(file => {
    fs.copySync(path.join(srcDir, file), path.join(distDir, file));
});

// 處理 script.js
let scriptContent = fs.readFileSync(path.join(srcDir, 'script.js'), 'utf8');

const backendUrl = process.env.VITE_API_BASE_URL || '';
scriptContent = scriptContent.replace('__BACKEND_URL_PLACEHOLDER__', backendUrl);

fs.writeFileSync(path.join(distDir, 'script.js'), scriptContent);

console.log('Build completed! Files are in /dist with target URL:', backendUrl || '(no URL provided)');
