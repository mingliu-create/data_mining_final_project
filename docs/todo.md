# 待辦事項

**專案**：日本城市人流特性分析與軌跡預測（ACM SIGSPATIAL GIS Cup 2025）  
**最後更新**：2026-05-28

---

## 已完成 ✅

- [x] 撰寫規格書（`docs/proposal.md`）
- [x] 撰寫概要設計文件（`docs/high-level-design.md`）
- [x] 撰寫詳細設計文件（`docs/detail-design.md`）
- [x] 實作 `data/loader.py`：讀取 CSV、過濾異常值、切分訓練／測試集
- [x] 實作 `data/preprocessing.py`：平假日 K-means 標記、座標轉換公式、`build_grid_latlon_table`
- [x] 產出 `data/grid_to_latlon.csv`（40,000 行，含中心點與邊界框）
- [x] 確認座標系統：`x(0→199)` = 南→北，`y(0→199)` = 西→東；邊界框已知
- [x] 實作 `analysis/eda.py`：
  - `plot_unique_users_map`（白底，Reds，log 正規化透明度）
  - `plot_spatial_heatmap`（log scale，hot colormap）
  - `build_trajectory_density`（Bresenham 線段累積）
  - `plot_trajectory_map`（黑底，hot colormap）
  - `plot_daily_active_users`（折線圖，d=60 切分線）
- [x] 產出 `output/figures/unique_users_map.png`（方向已確認正確）

---

## 待完成 ⏳

### 優先序 1 — 評估流程（盡早驗通）

- [ ] 實作 `eval/metrics.py`
  - `validate_submission()`：呼叫 geobleu validator
  - `compute_geobleu()`：Beta=0.5, n=5，`calc_geobleu_bulk()`
  - `compute_fde()`：Final Displacement Error
  - `generate_report()`：JSON + CSV 格式

### 優先序 2 — Baseline 模型（取得本地基準分）

- [ ] 實作 `models/baseline.py`
  - `predict_per_user_mode()`：依 (weekday, t) 取眾數，三層 fallback
  - `predict_per_user_mean()`：依 (weekday, t) 取平均
  - `predict_bigram()`：轉移表，支援 top_p sampling
  - `run_all_baselines()`：執行全部並輸出 GEO-BLEU 報告
  - 目標：在本地復現 Per-User Mode ≈ 0.10789

### 優先序 3 — 特徵工程

- [ ] 實作 `analysis/clustering.py`（HDBSCAN）
  - `compute_grid_density()`：統計每格出現次數
  - `run_hdbscan()`：以密度網格執行 HDBSCAN
  - `assign_user_hotspots()`：每人 top-N 熱點 ID
  - `fetch_poi_from_osm()`：以 Overpass API 查詢名古屋 POI
  - `assign_poi_to_grid()`：POI 對齊最近網格
  - `build_grid_poi_features()`：每格各類 POI 數量，輸出 `data/grid_poi_features.csv`

- [ ] 實作 `analysis/trajectory.py`（個人移動規律）
  - `compute_location_repeat_rate()`：同 (weekday, t) 回到同格的比例
  - `compute_day_type_entropy()`：工作日／假日移動分布熵
  - `classify_mobility_type()`：K-means 移動類型分群（k=4）
  - `build_user_stability_features()`：輸出 `data/user_stability_features.csv`

### 優先序 4 — 深度模型

- [ ] 實作 `models/cvae.py`（Conditional VAE）
  - `TrajectoryEncoder`：LSTM encoder → (mu, log_var)
  - `TrajectoryDecoder`：LSTM decoder → 重建軌跡
  - `CVAE`：整合 encoder/decoder，`reparameterize`，`sample`
  - `cvae_loss()`：MSE + beta * KL
  - `build_condition_vector()`：組裝條件向量 y（熱點 ID + POI + 穩定性 + is_holiday + weekday）
  - `train_cvae()`：訓練迴圈，每 epoch 儲存 checkpoint
  - `predict_trajectories()`：推論 Days 61–75

- [ ] 實作 `main.py`：串接所有模組的完整執行入口

---

## 待確認 ⚠️

- [ ] **訓練資料規模**：是否使用全體 ~100,000 名使用者，或取活躍天數 ≥ 30 天的子集？  
  影響：`loader.py` 過濾邏輯、CVAE 訓練時間與記憶體

## 已確認（設計決策）✅

- **資料切分策略（2026-05-28 確認）**：
  - `Days 1–50`：訓練集（train）
  - `Days 51–60`：驗證集（validation），用於超參數調整
  - `Days 61–75`：競賽測試集（test），僅用於最終 GEO-BLEU 評估
  - 最終提交前，以 Days 1–60 全量重新訓練一次
  - 需在 `data/loader.py` 新增 `split_train_val_test()` 函式

- **CVAE 訓練流程（2026-05-28 確認）**：
  - 本地完成所有模組的實作與單元測試（不含實際訓練）
  - 透過 GitHub 推送至有 GPU 的訓練機器
  - 訓練機器執行 `uv sync` 安裝依賴後，以 `main.py` 啟動訓練
  - checkpoint 存於 `models/checkpoints/`，訓練結果與評估報告存於 `eval/reports/`

---

## 目標分數

| 方法 | GEO-BLEU |
|------|----------|
| 官方最佳 Baseline（Per-User Mode） | 0.10789 |
| **我們的目標（CVAE）** | **> 0.10789** |
