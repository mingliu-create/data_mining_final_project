# eval/reports

此資料夾放置評估流程產生的輸出。

預期檔案：

- `<method>.json`：包含 GEO-BLEU 與 FDE 的摘要報告。
- `<method>.csv`：精簡表格版報告。
- `cvae_predictions.csv`：執行 `main.py --run-cvae` 時產生的 CVAE 軌跡預測。

這些產生檔案會被 Git 忽略。
