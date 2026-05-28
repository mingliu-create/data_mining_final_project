# models

此資料夾放置軌跡預測模型。

- `baseline.py`：Per-User Mode、Per-User Mean、Bigram、top-p Bigram baseline。
- `cvae.py`：LSTM-based Conditional VAE、條件向量建立、訓練與預測工具。
- `checkpoints/`：模型 checkpoint 輸出位置。

checkpoint 檔案通常較大且與訓練環境相關，因此會被 Git 忽略。
