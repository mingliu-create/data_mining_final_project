# DataMining Final Project

本專案用於 **ACM SIGSPATIAL GIS Cup 2025** 的日本城市人流軌跡分析與預測。

主要目標是以名古屋去識別化手機軌跡資料為基礎，完成：

- 資料載入與前處理
- 城市人流熱點與 POI 特徵工程
- 使用者移動穩定性分析
- baseline 軌跡預測
- Conditional VAE 軌跡生成
- GEO-BLEU 與 FDE 評估

主要入口：

```bash
python main.py --city-path raw_data/nagoya_challengedata.csv --run-baselines
```

原始大型資料請放在 `raw_data/`，該資料夾不會被 Git 追蹤。
