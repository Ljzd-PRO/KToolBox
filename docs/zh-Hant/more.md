# 專案資訊

## 發佈狀態

KToolBox v1 是以 Pawchive 為基礎的全新發佈線。它與 v0 不相容，且尚未經過充分的實際使用驗證；在依賴大規模同步前，請先執行有範圍限制的下載。升級既有安裝時，請從[遷移至 v1](migration-v1.md)開始。

Kemono 已無法使用，Pawchive 是唯一支援的後端。原始 Pawchive OpenAPI 檔案保持不變，以便將產生用戶端的變更與正規化契約對照審查。

## 支援與資源

離開文件站前，請先使用站內搜尋和[常見問題](faq.md)。若仍找不到答案，可使用下列明確的專案外部連結：

- 透過 [Issue 追蹤器](https://github.com/Ljzd-PRO/KToolBox/issues)回報可重現缺陷；
- 在 [Discussions](https://github.com/Ljzd-PRO/KToolBox/discussions)中提出問題與建議；
- 從 [Releases](https://github.com/Ljzd-PRO/KToolBox/releases)查看發佈說明與產物；
- 在[原始碼儲存庫](https://github.com/Ljzd-PRO/KToolBox)查看程式碼與貢獻歷史。

## 品質與授權

預設測試套件完全離線，並阻擋意外網路存取。CI 會驗證 OpenAPI 契約、確定性產生、測試、Ruff、Mypy、Python 位元組碼編譯、套件產物、WebUI 建置與嚴格 MkDocs 建置。

KToolBox 採用 [BSD 3-Clause License](https://opensource.org/license/bsd-3-clause)。Copyright © 2023 by Ljzd-PRO。
