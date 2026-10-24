# Doherty PA Idd 掃描工具（模擬版）

Windows 使用方式：下載 ZIP 後先全部解壓縮，再雙擊 `start.bat`。執行結束後視窗會保留，便於查看結果或錯誤。預設 CSV 與 SVG 會存入程式旁的 `results` 資料夾，每次使用不同時間戳記，避免重複執行失敗。`1.py` 是相容啟動入口，主程式為 `idd_sweep.py`。

使用 Python 3.10+，無第三方依賴。此版本不連接硬體，電流是示意模型，不能用於選定真實 PA 偏壓。

```bash
cd /workspace/HH
python3 idd_sweep.py --output /tmp/my-sweep.csv
python3 -m unittest discover -s tests -v
```

透過 `--main-start/stop/step` 與 `--peaking-start/stop/step` 設定二維掃描：固定 Main 後逐點改變 Peaking，再移到下一個 Main。輸出 CSV 與 SVG 電流曲線；SVG 橫軸是掃描序號，每一序號對應 CSV 的 Vgs 組合。既有 CSV 不會被覆寫。

目前參考偏壓 Main=-2.79 V、Peaking=-4.978 V。預設範圍只供模擬展示，不是安全建議。模擬採 AMC7836 的 -5～0 V DAC 範圍；資料表亦列出 -10～0 V、0～5 V、0～10 V。實際範圍取決於 DAC 設定、供電及板卡電路，不能據此推定 PA 的安全範圍。

`--current-limit` 預設 3 A，允許降低、不允許提高。總 Idd 達到門檻時記錄該點並停止後續掃描。這是軟體流程示範，不是硬體過流保護。1～3 A 是目前關注的量測區間；低於 1 A 的資料仍保留，以呈現完整工作曲線。

CSV 保留 `aclr_lower_db`、`aclr_upper_db`、`rf_output_dbm` 欄位供後續 IQxel 5G 量測整合。模擬版不產生假 ACLR，也不宣稱最佳工作點。尚未設定 ACLR 門檻，無法判定合格；未來比較須記錄相同 RF 輸出功率與波形條件。

## 實機整合所需資訊

AMC7836 資料表描述晶片 SPI 協定，並未定義你板卡的主機 cmdline。需要實際的「設定 Main Vgs」、「設定 Peaking Vgs」、「讀取 Idd」命令及其輸出格式、單位、錯誤碼；請提供去除敏感資訊的範例。此外需要通道對應、PA 安全偏壓範圍、偏壓穩定時間、量測總電流或各支路電流的定義、故障時安全回復命令，以及 IQxel 5G 現有控制方式。

未完成以上資訊前，本工具僅執行模擬。每個雲端任務已有隔離環境，直接使用現有 checkout，不需要另建 Git worktree。

## 兩階段工具 two_stage_idd.py

此工具目前僅模擬；雙擊預設執行 static 階段並保留視窗。

```bash
python two_stage_idd.py static --output static.csv
python two_stage_idd.py rf --input static.csv --rf-output-dbm 30 --waveform demo --output rf.csv
```

第一階段掃描無 RF 偏壓與靜態總電流。第二階段讀取第一階段 CSV 的候選點，模擬指定輸出功率下的工作電流。可複製並刪除 static CSV 中不想測試的資料列來挑選候選點，保留表頭。兩階段均在 Main + Peaking **總電流 >= 3 A** 時記錄該點並停止。軟體停止不等同硬體過流保護。

模擬曲線與 RF 電流模型是任意示意，不預測真實 PA。`--rf-output-dbm` 僅設定模擬條件，沒有實際控制 RF 功率。ACLR 欄位留白；沒有連接 IQxel、沒有合格判定與最佳點排名。實機仍需 cmdline 範例、安全範圍、RF 控制與量測協定。

## RD 範圍設定視窗（rd_sweep.py）

安裝含 tkinter 的 Python 3.10+，執行 `python rd_sweep.py` 或雙擊 `start_rd.bat`。`rd_sweep.py` 是獨立檔案，不依賴其他專案模組。

視窗可分別設定 Main／Peaking 的 RD 安全下限、上限、掃描起點、終點與步距。所有預設值僅供模擬展示，非實機安全規格。可儲存／載入 JSON 設定，開始前檢查範圍並顯示確認畫面。總電流上限固定為 3 A。輸出 CSV 旁同時存放本次 `.settings.json` 設定，方便追溯；既有 CSV 不覆寫。

第一階段執行雙支路組合掃描；將某支路起點與終點設為相同即可固定該支路。第二階段選擇第一階段 CSV，依 CSV 偏壓逐點執行，並重新檢查 RD 安全上下限；第二階段不依視窗掃描起終點篩選候選點。可先另存一份 CSV，刪除不需要的資料列並保留表頭。

命令列也可使用：

```bash
python rd_sweep.py static --config rd_config.example.json --output static.csv
python rd_sweep.py rf --config rd_config.example.json --input static.csv --rf-output-dbm 30 --waveform demo --output rf.csv
```

目前仍是模擬；RF 功率只是模擬參數，無實際 RF 控制。ACLR 未量測，不判定合格或最佳點。這個版本未加入量測等待時間、多次平均或實機 cmdline。實機整合須另行確認。CLI 及範圍驗證已測試；雲端沒有圖形顯示環境，未驗證 Windows 視窗實際操作。

### 遞減掃描修正

`rd_sweep.py` 支援遞增與遞減，步距一律填正數。例：起點 -1 V、終點 -5 V、步距 0.05 V，順序為 -1、-1.05、-1.10……-5 V。模擬電壓範圍支援 -10～0 V，起點與終點均須在各支路 RD 安全範圍內。這不代表實際 DAC 已切換量程，也不表示 PA 可安全使用這些偏壓。

以 -1 V 作為起點，在目前任意示意模型中會立即超過 3 A，因此只記錄第一點就停止；這是總電流停止規則，不是掃描方向錯誤。實際偏壓順序與範圍必須依 PA 規格制定。


### v2.1 模擬模型保護

`rd_sweep.py` 不再允許對局部示意模型任意外推。RD 上下限仍可在 -10～0 V 內編輯，但實際模擬偏壓僅支援 Main -2.95～-2.65 V、Peaking -5～-4.95 V；這些都是未校準的示範範圍，不是實機規格。所有候選點在輸出前檢查，超範圍直接拒絕，不產生不合理電流、不將電流硬截成 3 A。RF 模擬條件限制為 20～35 dBm，46 dBm 不再外推。這些限制只屬於示意模型，並不是實機安全或效能規格。

視窗新增「恢復模擬範例」，可恢復可執行的起終點及 30 dBm 條件。舊版只有過流點的 CSV 需重做第一階段，不能修改狀態來繞過檢查。新版會顯示中文原因，並保留 Main+Peaking 總電流 >=3 A 即停止的規則。設定快照包含模型版本。單元測試與兩階段 CLI 已驗證，Windows GUI 仍需本機驗證。請使用 rd_sweep.py；較早的 two_stage_idd.py 為歷史模擬工具。

### v2.2：寬範圍有界示意模型（取代 v2.1 模型限制）

最新版 `rd_sweep.py` 支援 Main -5～-1 V、Peaking -10～-1 V，預設從 -1 V 遞減，兩支路步距均為 0.05 V。完整組合共 81×181＝14661 點。RD 上下限與掃描區間仍可編輯，實際掃描須同時落在 RD 範圍與模型範圍。

電流改用單調、有飽和特性的 sigmoid 示意曲線，不再外推原平方公式。Main 1.6 A、Peaking 0.8 A 是任意示意模型的漸近值，**不是實測、不是 PA 額定或硬體保護上限**。僅用於展示流程，不能用此模型推定實機 Vgs/Iddq 對應。3 A 總電流保護獨立判斷，RF 示意工作電流仍可能超過並觸發停止，未將結果截成 3 A。

點選「恢復模擬範例」即可載入寬範圍預設。RF 模型仍僅支援 20～35 dBm；截圖的 46 dBm 尚不支援。v2.1 舊 CSV 請重做第一階段，勿將不同模型資料混用。已測試全範圍 14661 點靜態與 30 dBm RF 流程；Windows GUI 未實機驗證。模擬掃描順序不構成實機偏壓操作建議。

### v2.3：RF 功率掃描與僅記錄事件

GUI 可設定 RF 起點、終點（0～50 dBm）與正數步距（dB），預設 0→50、步距 1。每個 CSV 候選偏壓組合都掃描完整 RF 功率序列，支援遞減。起終點差不是步距整數倍時，最後一點是區間內的最後網格點，不強加終點。GUI 儲存／載入 RD JSON 時也保存 RF 掃描設定；舊 JSON 仍可使用。

```bash
python rd_sweep.py rf --config rd_config.example.json --input static.csv --rf-start 0 --rf-stop 50 --rf-step 1 --waveform FR1 --output rf.csv
```

`--rf-output-dbm 46` 保留舊版單點模式；未指定 RF 參數預設掃描 0～50 dBm。組合超過 1,000,000 點會要求減少點數。總電流 >=3 A 僅以每筆 CSV 的 `status=total_current_limit` 記錄，兩階段都不停止、不截斷電流；第二階段不再因該狀態排除候選點。設定快照記錄全部 RF 功率點與 record-only 策略。

所有事件只是示意公式計算後的標記，沒有實機電流偵測、RF 設定、AMC 控制或硬體保護變更。原 RF 電流公式仍是任意示意，50 dBm 下的數值不代表真實 PA，不能用作工作點預測。ACLR 欄位仍留白。

### v2.4：第一階段彩色曲線、P1dB 工作點交接

第一階段完成後自動在 CSV 旁產生 `.curves.html`，使用瀏覽器開啟，不需安裝繪圖套件。視窗的「第一階段 CSV → 曲線」可將舊檔繪圖並交由瀏覽器開啟。Main／Peaking 圖分別可用選單指定另一支路固定電壓，藍線顯示該支路 Iddq，橘線顯示總 Iddq；來源仍是模擬資料。視窗內容可垂直捲動。

P1dB 無法由無 RF 的 Iddq 推算。此版本暫以 **輸出 P1dB（dBm）量測表匯入**作為流程，不產生假的 P1dB。RD 在視窗設定目標 P1dB 與 ±dB 容差，按「匯入 P1dB 表 → 匯出工作點」，依序選第一階段 CSV、P1dB 量測表、輸出工作點 CSV。

P1dB 表需含 `main_vgs_v,peaking_vgs_v,p1db_output_dbm` 三欄；空白模板為 `p1db_measurements.template.csv`，請填入真正數據。所有列應為相同頻率、Vds、溫度、負載與量測條件，每組偏壓只允許一筆。偏壓配對精度為小數點後 6 位，僅從第一階段已存在的偏壓中選點，不做插值。

選點規則：目標 ±容差內，先選最接近目標者，差距相同再選靜態總 Iddq 最低者。這是明確的目標配對規則，不代表全域最佳效率或 ACLR。若希望「達到最低 P1dB 後最低電流」等其他準則，需另定義。

匯出的工作點 CSV 含 Main／Peaking Vgs、原第一階段電流、P1dB 值與來源、目標／容差、選點規則；可直接在第二階段選取，固定該偏壓後掃描 RF。注意第一階段電流仍為模擬，即使 P1dB 來源是真實量測，也不會把靜態電流改標為實測。P1dB 目標可隨 RD 設定檔保存。沒有合格匹配時清楚提示、不輸出假工作點。

目前仍不控制 RF output on、AMC7836 或 IQxel；RF sweep 仍為模擬，ACLR 留白。27 項測試涵蓋工作點篩選及第二階段交接，GUI／瀏覽器視覺顯示尚未在 Windows 驗證。

## 完整量測與 Excel 初版

請參考 [WORKFLOW.md](WORKFLOW.md)。以 `start_workflow.bat` 或 `python pa_workflow.py` 啟動；先安裝 `python -m pip install -r requirements.txt`。原 RD 視窗底部也有完整報表入口。預設模擬可輸出包含 7 張可編輯曲線圖的 `report.xlsx`；實機命令待提供後才能連接。
