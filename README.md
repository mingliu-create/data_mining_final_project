# DataMining Final Project

本專案用於 **ACM SIGSPATIAL GIS Cup 2025** 的日本城市人流軌跡分析與預測。

目前程式已完成可在不跑完整 2.2GB 資料的情況下驗證的部分，包含資料讀取抽樣、baseline、feature engineering、評估流程與 CVAE 基本流程。完整資料訓練與分數復現仍需另外執行。

## 專案內容

- 資料載入與前處理
- 大型 CSV chunk 讀取與使用者抽樣
- 城市人流熱點分群
- POI 查詢、對齊與特徵表建立
- 使用者移動穩定性分析
- baseline 軌跡預測
- Conditional VAE 軌跡生成
- GEO-BLEU 與 FDE 評估

## 目前已完成

- `data/loader.py`
  - 讀取 `uid,d,t,x,y` 格式 CSV
  - 支援 `--max-users`
  - 支援 `--sample-users`
  - 支援 `--random-seed`
  - 支援 `--chunksize`
- `data/preprocessing.py`
  - 平假日標記
  - 網格座標與經緯度轉換
  - `grid_to_latlon.csv`
- `analysis/clustering.py`
  - grid density
  - HDBSCAN/DBSCAN hotspot clustering
  - user hotspot assignment
  - POI fetch / grid alignment / feature table
- `analysis/trajectory.py`
  - repeat rate
  - day-type entropy
  - mobility type clustering
- `models/baseline.py`
  - Per-User Mode
  - Per-User Mean
  - Bigram
  - Bigram top-p
  - 稀疏 reference 對齊
- `models/cvae.py`
  - LSTM-based Conditional VAE
  - condition table
  - training helper
  - prediction helper
- `eval/metrics.py`
  - submission validation
  - GEO-BLEU
  - FDE
  - JSON/CSV report
- `main.py`
  - 串接 preprocessing、feature engineering、baseline、CVAE

## 已驗證

- `task1_dataset_kotae.csv` 可以讀取。
- 欄位符合專案格式：`uid,d,t,x,y`。
- 天數範圍符合 75 天設定：`d=0–74`。
- `uv sync` 已完成。
- `geobleu`、`hdbscan`、`torch` 可正常 import。
- 最小評估案例通過：
  - 相同軌跡 FDE = `0.0`
  - 相同軌跡 GEO-BLEU = `1.0`
- 小樣本 baseline smoke test 通過：
  - 指令：`--max-users 5 --chunksize 1000000 --skip-features --run-baselines`
  - train rows = `6,544`
  - test rows = `1,721`
  - Per-User Mode GEO-BLEU = `0.196355`
  - Per-User Mean GEO-BLEU = `0.104883`
  - Bigram GEO-BLEU = `0.222613`
  - Bigram top-p 0.7 GEO-BLEU = `0.205013`
- 小樣本 feature engineering smoke test 通過：
  - 指令：`--max-users 5 --chunksize 1000000`
  - 未加 `--fetch-poi` 時會產生全 0 POI 特徵表，流程可跑通。

## POI 狀態

POI 程式已完成，但真實 POI 資料尚未抓取。

- 未加 `--fetch-poi`：不打 Overpass API，產生全 0 POI 特徵表。
- 加上 `--fetch-poi`：會呼叫 OpenStreetMap Overpass API，輸出：
  - `data/osm_poi_raw.csv`
  - `data/osm_poi_grid.csv`
  - `data/grid_poi_features.csv`

範例：

```bash
python main.py --city-path "D:\新增資料夾 (7)\資料探勘\task1_dataset_kotae.csv" --max-users 1000 --chunksize 1000000 --fetch-poi
```

## 執行方式

先用小樣本跑 baseline：

```bash
python main.py --city-path "D:\新增資料夾 (7)\資料探勘\task1_dataset_kotae.csv" --max-users 1000 --chunksize 1000000 --skip-features --run-baselines
```

跑小樣本 feature engineering：

```bash
python main.py --city-path "D:\新增資料夾 (7)\資料探勘\task1_dataset_kotae.csv" --max-users 1000 --chunksize 1000000
```

跑 CVAE smoke run：

```bash
python main.py --city-path "D:\新增資料夾 (7)\資料探勘\task1_dataset_kotae.csv" --max-users 1000 --chunksize 1000000 --run-cvae --cvae-epochs 1
```

跑完整 baseline：

```bash
python main.py --city-path "D:\新增資料夾 (7)\資料探勘\task1_dataset_kotae.csv" --chunksize 1000000 --skip-features --run-baselines
```

## 尚未完成

- 尚未用完整資料跑 baseline。
- 尚未確認 Per-User Mode 是否能復現官方約 `0.10789`。
- 尚未用完整資料跑 feature engineering。
- 尚未跑 CVAE smoke run。
- 尚未決定 CVAE 訓練資料規模：
  - 全部約 100,000 users
  - 或活躍天數 >= 30 天的子集
- 尚未實際抓取 POI。

## 資料注意事項

大型原始 CSV 不追蹤進 Git。

目前確認的資料位置：

```text
D:\新增資料夾 (7)\資料探勘\task1_dataset_kotae.csv
```

該檔案約 2.2GB，建議先使用 `--max-users` 或 `--sample-users` 做 smoke test，再跑完整資料。
