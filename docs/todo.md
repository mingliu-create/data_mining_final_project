# 待辦事項

**專案**：日本城市人流特性分析與軌跡預測（ACM SIGSPATIAL GIS Cup 2025）  
**最後更新**：2026-05-28

---

## 已完成

- [x] 撰寫規格書：`docs/proposal.md`
- [x] 撰寫概要設計文件：`docs/high-level-design.md`
- [x] 撰寫詳細設計文件：`docs/detail-design.md`
- [x] 實作 `data/loader.py`
  - 讀取 `uid,d,t,x,y` 格式 CSV
  - 驗證必要欄位
  - 過濾異常座標與時間
  - 支援 train/test 切分
  - 支援 train/validation/test 切分
  - 支援競賽資料中的 `x=999` prediction template
- [x] 實作 `data/preprocessing.py`
  - K-means 平假日標記
  - `day_of_week` / `working_day` 輔助欄位
  - grid heatmap
  - `grid_to_latlon`
  - `build_grid_latlon_table`
- [x] 產出 `data/grid_to_latlon.csv`
- [x] 確認座標系統
  - `x(0→199)` = 南→北
  - `y(0→199)` = 西→東
- [x] 實作 `analysis/eda.py`
  - `plot_unique_users_map`
  - `plot_spatial_heatmap`
  - `build_trajectory_density`
  - `plot_trajectory_map`
  - `plot_daily_active_users`
- [x] 建立資料夾說明文件
  - `README.md`
  - `analysis/README.md`
  - `data/README.md`
  - `eval/README.md`
  - `eval/reports/README.md`
  - `models/README.md`
  - `models/checkpoints/README.md`
  - `output/figures/README.md`

---

## 優先序 1：評估流程

- [x] 實作 `eval/metrics.py`
  - [x] `validate_submission()`：驗證 uid、t、x、y 合法性
  - [x] `compute_geobleu()`：封裝 GEO-BLEU，支援 `calc_geobleu_bulk` 與 per-user fallback
  - [x] `compute_fde()`：Final Displacement Error
  - [x] `generate_report()`：輸出 JSON + CSV 到 `eval/reports/`
- [x] 完成最小案例驗證
  - 相同軌跡 FDE = `0.0`
  - 相同軌跡 GEO-BLEU = `1.0`

---

## 優先序 2：Baseline 模型

- [x] 實作 `models/baseline.py`
  - [x] `predict_per_user_mode()`：依 `(weekday, t)` 取眾數，含三層 fallback
  - [x] `predict_per_user_mean()`：依 `(weekday, t)` 取平均，含 fallback
  - [x] `predict_bigram()`：轉移表預測，支援 `top_p` sampling
  - [x] `run_all_baselines()`：執行 baseline 並輸出 GEO-BLEU/FDE 報告
- [ ] 使用完整真實資料復現 Per-User Mode 約 `0.10789`

---

## 優先序 3：特徵工程

- [x] 實作 `analysis/clustering.py`
  - [x] `compute_grid_density()`：統計每格出現次數
  - [x] `run_hdbscan()`：HDBSCAN 分群；本機未安裝 `hdbscan` 時 fallback 到 DBSCAN
  - [x] `assign_user_hotspots()`：每人 top-N hotspot ID
  - [x] `fetch_poi_from_osm()`：Overpass API 查詢 POI
  - [x] `assign_poi_to_grid()`：POI 對齊最近網格
  - [x] `build_grid_poi_features()`：輸出 `data/grid_poi_features.csv`
- [x] 實作 `analysis/trajectory.py`
  - [x] `compute_location_repeat_rate()`：同 `(weekday, t)` 回到同格比例
  - [x] `compute_day_type_entropy()`：平日/假日移動分布熵與差異
  - [x] `classify_mobility_type()`：K-means 移動類型分群
  - [x] `build_user_stability_features()`：輸出 `data/user_stability_features.csv`

---

## 優先序 4：深度模型

- [x] 實作 `models/cvae.py`
  - [x] `TrajectoryEncoder`
  - [x] `TrajectoryDecoder`
  - [x] `CVAE`
  - [x] `cvae_loss()`
  - [x] `build_condition_vector()`
  - [x] `build_condition_table()`
  - [x] `train_cvae()`
  - [x] `predict_trajectories()`
- [x] 實作 `main.py`
  - [x] `run_preprocessing()`
  - [x] `run_feature_engineering()`
  - [x] `run_baselines()`
  - [x] `run_cvae()`
  - [x] CLI flags：`--city-path`、`--run-baselines`、`--run-cvae`、`--cvae-epochs`、`--batch-size`

---

## 已確認

- [x] `task1_dataset_kotae.csv` 可以讀取
- [x] `task1_dataset_kotae.csv` 欄位符合專案格式：`uid,d,t,x,y`
- [x] `task1_dataset_kotae.csv` 天數看起來符合 `d=0–74`
- [x] `uv sync` 已完成
- [x] `geobleu`、`hdbscan`、`torch` 可正常 import

---

## 尚未完成

- [ ] 將 `task1_dataset_kotae.csv` 納入正式執行流程
  - 目前檔案在專案外層：`D:\新增資料夾 (7)\資料探勘\task1_dataset_kotae.csv`
  - 可直接用完整路徑執行
- [ ] 使用完整真實資料執行 baseline
- [ ] 確認 Per-User Mode 是否能復現官方約 `0.10789`
- [ ] 執行完整 feature engineering
- [ ] 執行 CVAE smoke run
- [ ] 決定 CVAE 訓練資料規模
  - 選項 A：使用全體約 100,000 名使用者
  - 選項 B：只取活躍天數 >= 30 天的子集
- [x] 新增 chunk/抽樣讀取模式
  - `task1_dataset_kotae.csv` 約 2.2GB
  - `load_city()` 支援 `max_users`、`sample_users`、`random_seed`、`chunksize`
  - `main.py` 支援 `--max-users`、`--sample-users`、`--random-seed`、`--chunksize`
- [x] 新增 POI 執行選項
  - `analysis/clustering.py` 已有 POI 查詢、網格對齊、特徵表建立函式
  - `main.py --fetch-poi` 會實際呼叫 Overpass API
  - 未加 `--fetch-poi` 時會產生全 0 POI 特徵表，避免每次跑流程都打網路 API
- [x] 完成小樣本 baseline smoke test
  - 指令：`--max-users 5 --chunksize 1000000 --skip-features --run-baselines`
  - train rows = `6,544`
  - test rows = `1,721`
  - Per-User Mode GEO-BLEU = `0.196355`
  - Per-User Mean GEO-BLEU = `0.104883`
  - Bigram GEO-BLEU = `0.222613`
  - Bigram top-p 0.7 GEO-BLEU = `0.205013`
- [x] 完成小樣本 feature engineering smoke test
  - 指令：`--max-users 5 --chunksize 1000000`
  - 不抓 POI 時流程可跑通，會產生全 0 POI 特徵表

---

## 下一步指令

先跑 baseline：

```bash
python main.py --city-path "D:\新增資料夾 (7)\資料探勘\task1_dataset_kotae.csv" --skip-features --run-baselines
```

用 1,000 個使用者先跑 smoke test：

```bash
python main.py --city-path "D:\新增資料夾 (7)\資料探勘\task1_dataset_kotae.csv" --max-users 1000 --chunksize 1000000 --skip-features --run-baselines
```

baseline 正常後，再跑特徵工程與短輪 CVAE：

```bash
python main.py --city-path "D:\新增資料夾 (7)\資料探勘\task1_dataset_kotae.csv" --run-cvae --cvae-epochs 1
```

---

## 目標分數

| 方法 | GEO-BLEU |
|------|----------|
| 官方最佳 Baseline（Per-User Mode） | 0.10789 |
| 目標（CVAE） | > 0.10789 |
