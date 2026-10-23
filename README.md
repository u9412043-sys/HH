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
