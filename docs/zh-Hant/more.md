# 專案資訊

## 開發分支

Pawchive v1 在準備成為預設發佈線之前，維護於 [`pawchive`](https://github.com/Ljzd-PRO/KToolBox/tree/pawchive) 分支。

變更按契約、用戶端、專案遷移、測試、文件和發佈中繼資料拆分為專注的提交。原始 Pawchive OpenAPI 檔案保持不變，以便根據標準化契約稽核產生程式碼的變更。

## 品質政策

預設測試套件完全離線，並阻止意外的網路存取。手寫 API 層必須保持 100% 的行與分支覆蓋率，產生模型不計入統計，完整專案覆蓋率不得低於 85%。

CI 還會在支援的 Python 版本上驗證 OpenAPI 文件、確定性模型產生、Ruff、API 層嚴格 Mypy、Python 位元組碼編譯、套件建置和嚴格 MkDocs 建置。

## 授權條款

KToolBox 採用 [BSD 3-Clause License](https://github.com/Ljzd-PRO/KToolBox/blob/master/LICENSE)。

Copyright © 2023 by Ljzd-PRO.
