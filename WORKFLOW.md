# 完整量測與 Excel 曲線報表：初版

原 `rd_sweep.py` 保留，在視窗底部新增「完整量測／P1dB 分析／Excel 曲線報表」入口。新流程主程式為 `pa_workflow.py`，須與 `workflow.example.json` 一起下載；建議下載整個 GitHub ZIP。此初版使用可編輯 JSON 設定面板，尚未提供每一欄專用表單。

## Windows 使用

1. 安裝 Python 3.10+（含 tkinter）。
2. 在解壓縮資料夾開終端機執行 `python -m pip install -r requirements.txt`。
3. 雙擊 `start_workflow.bat`，或 `python pa_workflow.py`。
4. 預設為 `mode: simulation`。編輯偏壓組合、頻率、Vdd、波形、負載說明、RF 起終點／步距及 analysis 條件。
5. 按「執行量測／生成含曲線 Excel」，選輸出父資料夾。每次建立新時間戳子資料夾，保護既有檔案。

命令列：

```bash
python pa_workflow.py --config workflow.example.json --output-dir results/my-first-workflow
```

範例 9 組候選偏壓，RF 命令功率 0～40 dBm、1 dB 步距，共 9 靜態點＋369 RF 點。可設 0～50 dBm。偏壓清單 `bias_points` 可手動增減，RD 界限為 `limits`。此流程不會自動掃描所有偏壓網格；可使用原工具探索偏壓後選代表點，填入此清單。

## 四項整合

- **cmdline 介面**：simulation 使用明確標示的任意模型；hardware 使用使用者提供的本機 argv 命令，不使用 shell。
- **完整工作點**：設定／讀回 Main、Peaking Vgs、各支路 Vds／Idd、總電流、溫度、UTC 時間、RF 設定值／Pin／Pout、Gain、兩側 ACLR，附頻率、波形、負載資訊。原始 CSV 每點 flush；例外保留部分資料。
- **P1dB**：以實際讀回 Pin 排序，前 `baseline_points` 點平均 Gain 作小訊號基準；若增益差超過容差則標記 `baseline_not_flat`。找到相對基準下降 1 dB 的相鄰點才做線性插值，輸出輸入／輸出 P1dB。無夾住、重複 Pin、點數不足，均不捏造結果。小訊號區由使用者確認，程式無法從已全面壓縮但平坦的數據證明它是小訊號。
- **相同 Pout 比較**：以 `target_pout_dbm` 為目標，單調 Pout 曲線內插總 Idd 與 ACLR；不外推、不處理多值輸出。`min_p1db_output_dbm` 是最低要求（不是最接近目標）；兩側負 dBc ACLR 的較差值須 <= `aclr_limit_dbc`。合格點以總 Idd 排名。條件 null 表示未設定，只列暫定結果、不產生合格排名。

此流程本身會量測 RF 壓縮與操作點，因此不是從無 RF 靜態電流直接推導 P1dB。模擬 P1dB／ACLR 都是假設資料，不能當作 PA 性能結論。模擬固定 Vds／溫度，尚未模擬自熱或真實負載調變。

## Excel 檔案（含真正可編輯的圖表）

`report.xlsx` 包含說明與模式、靜態資料、RF 資料、電流事件、工作點比較，及：

1. Main Vgs–總 Iddq 曲線族（固定各 Peaking Vgs）。
2. Peaking Vgs–總 Iddq 曲線族（固定各 Main Vgs）。
3. 不同偏壓的 Pin–Gain 壓縮曲線族。
4. Pin–Pout 曲線族。
5. Pout–總 Idd 曲線族。
6. Pout–下鄰道 ACLR。
7. Pout–上鄰道 ACLR。

圖表以 Excel 數據儲存格為資料來源，不是貼圖片；最多顯示前 40 組曲線以維持可讀性，全部數據仍在工作表。工作點表另列 P1dB 與排名，尚未把 P1dB 圓點額外疊到曲線。原 `rd_sweep.py` 的既有匯出仍是 CSV／HTML；Excel 完整報表請用新增的流程入口。

一起產生 `measurements.csv`、`config.json`、`run_status.json`。可參考 `docs/workflow/demo_simulation_report.xlsx`，其中所有性能數據均為 simulation。

## 實機待接入契約

實機命令尚待提供；初版沒有內建 AMC7836 或 IQxel 專屬驅動。將 `mode` 設成 hardware 前，所有 `REPLACE_...` 必須替換。命令為陣列，每個元素是一個 argv 參數，例如使用自有 wrapper（以下名稱與參數只是介面範例，不是現成硬體命令）：

```json
{
  "set_bias": ["python", "board_wrapper.py", "set", "--main", "{main}", "--peaking", "{peaking}"],
  "read_dc": ["python", "board_wrapper.py", "read-json"],
  "rf_on": ["python", "iqxel_wrapper.py", "on"],
  "rf_off": ["python", "iqxel_wrapper.py", "off"],
  "set_rf": ["python", "iqxel_wrapper.py", "set-power", "{power}"],
  "read_rf": ["python", "iqxel_wrapper.py", "read-json"],
  "safe_bias": ["python", "board_wrapper.py", "safe"]
}
```

`read_dc` stdout 必須是單一 JSON object，欄位全部為數值：

```json
{"main_vgs_v":-2.79,"peaking_vgs_v":-4.978,"main_vds_v":28,"peaking_vds_v":28,"main_idd_a":1.2,"peaking_idd_a":0.1,"temperature_c":35}
```

`read_rf` stdout：

```json
{"pin_dbm":20,"pout_dbm":38,"aclr_lower_dbc":-45,"aclr_upper_dbc":-44}
```

數值單位：V、A、°C、dBm、負 dBc。舊命令若輸出純文字，需要 wrapper 轉成上述 JSON，不可拿設定功率冒充量測功率。`rf_set_dbm` 是送給 set_rf 的命令值；預設範例按輸入功率解讀，若要設定輸出功率，wrapper 必須負責實際閉迴路控制並獨立讀回 Pin／Pout。波形、頻率、Vdd 的實機初始化由 wrapper／儀器端準備，JSON 記錄本身不會設定這些硬體條件。`safe_bias` 及兩支路設定順序由 RD 依實際板卡制定。

流程在切偏壓前執行 RF off；RF on 前先把 RF 設定到本次最低值。正常結束或錯誤時，嘗試 RF off 與 safe_bias。每點總電流 >=3 A **僅記錄，不停止**，符合目前需求；命令失敗／數據不合法仍會中止。這不取代硬體過流保護，工具也不修改硬體保護設定。

命令不得包含密碼／token；需要的憑證由本機環境或既有登入提供。不要把憑證放 JSON，因為設定會保存到輸出資料夾。

## 驗證範圍

34 項測試通過，涵蓋 P1dB 插值與失敗狀態、同 Pout 插值／不外推、條件不足不排名、9 組偏壓 Excel 7 張圖表、命令未設定拒絕執行、模擬命令失敗時清理與部分資料保存。Excel 已用 openpyxl 重新開啟並驗證圖表與數據引用；尚未在 Windows Excel 視覺檢查，也未連接真實 PA 或 IQxel。GUI 執行時同步等待，量測期間視窗可能暫時無回應；命令有 timeout，請勿重複啟動實機量測。

## 手動儲存設定

完整量測視窗新增「儲存設定 JSON」與「另存新檔」。首次儲存會詢問檔名；載入既有 JSON 後按儲存，則更新該檔案。另存新檔可建立不同 RD 設定版本。視窗顯示目前載入／儲存路徑。

儲存只檢查 JSON 格式及最外層物件，不執行量測或命令；尚未填好的實機命令也可保存為草稿。量測前仍會執行完整設定檢查。無效 JSON 不會覆蓋原設定。修改後須手動按儲存，關閉視窗不會自動儲存。
