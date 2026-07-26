# 命名格式

KToolBox v1 的命名設定屬於目前專案。CLI 與 WebUI 共同讀取 `ktoolbox.toml` 中的 `[naming]`；命名欄位不再作為全域 dotenv 設定編輯。

## 設定目錄結構

在 WebUI 開啟**命名格式**，可設定：

- 一個或多個下載根目錄；
- 作者、作品、修訂、年份和月份目錄範本；
- 主檔案與附件檔案範本；
- 作品內部的附件、修訂、正文與外部連結名稱；
- 年月分組、混合作品與附件順序命名。

範本只能使用欄位旁列出的變數 Chip，例如 `{creator_name}`、`{creator_id}`、`{service}`、`{title}`、`{post_id}`、`{revision_id}`、`{year}` 和 `{month}`。路徑分隔符號、父目錄跳轉、未知變數與不安全名稱會在掃描前被拒絕。

![深色主題下的命名範本](../assets/webui/34-naming-templates-desktop-dark.png)

## 預覽已下載內容

按下**掃描並預覽**後，KToolBox 會掃描實際下載根目錄，不依賴工作歷程，也不會存取 Pawchive。它透過作者目錄身分、`creator-indices.ktoolbox` 與 `post.json` 識別內容，並拒絕跟隨越出根目錄的符號連結。

預覽會顯示每位作者的新舊路徑、作品數、檔案數、總大小、略過項目和衝突。**轉換已下載作者**預設啟用；所有可安全轉換的作者預設選取，也可逐項取消。

![行動版命名轉換預覽](../assets/webui/35-naming-conversion-mobile-light.png)

KToolBox 不會覆寫或合併目標目錄。掃描結果過期、設定變更、相關工作正在活動、目標重複或檔案系統變化時，都必須重新掃描。

## 套用與復原

啟用轉換時，KToolBox 會先儲存待生效設定快照，再以背景轉換工作移動檔案。只有全部選定操作成功後，新命名格式才會生效。取消、寫入失敗或處理程序中斷會反向復原已完成移動，並繼續使用舊設定。

轉換進度與歷程儲存在 `.ktoolbox/webui.sqlite3`。成功後會清除暫存操作記錄；完成歷程會保留到使用者手動刪除。轉換會移除已空的舊來源目錄，但不會刪除無關檔案。

停用轉換時只儲存新格式；舊下載保持原位，之後的 CLI 與 WebUI 下載使用新的專案格式。

## 首次啟動遷移

首次啟動 WebUI 時，KToolBox 會在建立預設專案設定前遷移 `.env` 和 `prod.env` 中的舊命名鍵：

1. 將最終生效值寫入 `ktoolbox.toml`；
2. 備份至 `.ktoolbox/migrations/project-naming-v2/`；
3. 移除舊 dotenv 鍵；
4. 在終端機輸出摘要；
5. 登入後顯示一次性 WebUI 通知。

![一次性命名遷移通知](../assets/webui/36-naming-migration-notice-light.png)

CLI 同樣使用專案命名設定。舊專案尚未完成遷移時，請啟動一次該專案的 WebUI，以完成具有備份的原子遷移。
