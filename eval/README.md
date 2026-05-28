# eval

此資料夾放置評估相關程式。

- `metrics.py`：驗證生成軌跡格式，計算 GEO-BLEU 與 FDE，並輸出評估報告。
- `reports/`：模型分數、JSON 摘要、CSV 摘要與預測檔輸出位置。

評估輸出檔會被 Git 忽略，只保留 `reports/README.md` 追蹤資料夾用途。
