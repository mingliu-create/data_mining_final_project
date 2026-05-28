# 概要設計文件：日本城市人流特性分析與軌跡預測

**版本**：v1.0  
**日期**：2026-05-28  
**對應需求文件**：[docs/proposal.md](proposal.md)

---

## 1. 系統概覽

本系統以名古屋市去識別化手機 GPS 軌跡為輸入，分兩個階段處理：

- **Phase 1 — 特徵探勘**：從原始軌跡萃取空間熱點、地點語意、個人移動規律等特徵。
- **Phase 2 — 軌跡生成**：以 Conditional VAE 整合上述特徵，預測並生成 Days 61–75 的個人移動軌跡。

最終輸出以 GEO-BLEU（Beta=0.5, n=5）評估，目標超越官方 baseline 最高分（Per-User Mode：0.10789）。

---

## 2. 模組一覽

| 模組 | 路徑 | 職責 | 狀態 |
|------|------|------|------|
| 資料載入 | `data/loader.py` | 讀取原始 CSV，切分訓練／預測集 | ✅ 完成 |
| 資料前處理 | `data/preprocessing.py` | 時間離散化、平假日標記、空間座標處理 | ✅ 完成 |
| 探索性分析 | `analysis/eda.py` | 資料分布視覺化，不產出模型特徵 | ✅ 完成（基本函式）|
| 空間分群 | `analysis/clustering.py` | HDBSCAN 識別移動熱點，產出使用者熱點標籤 | ⏳ 待實作 |
| 地點語意 | `analysis/clustering.py`（語意部分） | POI 語意分類（Overpass API） | ⏳ 待實作 |
| 個人軌跡分析 | `analysis/trajectory.py` | 量化個人移動規律，產出穩定性特徵 | ⏳ 待實作 |
| Baseline 模型 | `models/baseline.py` | Per-User Mode、Bigram 等，建立本地基準分數 | ⏳ 待實作 |
| CVAE 模型 | `models/cvae.py` | 條件式生成預測軌跡 | ⏳ 待實作 |
| 評估 | `eval/metrics.py` | GEO-BLEU、FDE 計算與報告產出 | ⏳ 待實作 |

---

## 3. 模組詳細說明

### 3.1 資料載入（`data/loader.py`）

**職責**：讀取 `raw_data/nagoya_challengedata.csv`，依天數切分成訓練集與預測集。

- **輸入**：原始 CSV 檔案路徑
- **輸出**：
  - 訓練集：Days 1–60 的所有 `(uid, d, t, x, y)` 記錄
  - 預測集（ground truth）：Days 61–75 的記錄，僅用於評估
- **說明**：資料欄位為 `uid`、`d`（天）、`t`（30 分鐘時間步，0–47）、`x`、`y`（500m 網格座標）

---

### 3.2 資料前處理（`data/preprocessing.py`）

**職責**：對載入後的資料進行時間與空間兩個維度的清洗與轉換，產出後續模組可直接使用的標準化資料。

#### 時間處理

- **時間離散化**：將一天切成 48 個時階段（每段 30 分鐘），以 `t ∈ [0, 47]` 表示。
- **平假日標記**：
  1. 以 K-means（k=2）對每日全體人流量分群，初步區分工作日與假日。
  2. 比對日本國定假日曆及特殊事件（颱風、大型展覽）修正邊界案例。
  3. 為每個 `d` 附加 `is_holiday` 布林標籤。

#### 空間處理

- **座標驗證**：確認 x, y 均落在 200×200 網格範圍內，過濾異常值。
- **熱力圖生成**：將所有 (x, y) 記錄繪製成人流密度熱力圖，供後續視覺疊圖使用。
- **座標系統（✅ 已確認）**：
  - 邊界框：SW=(34.4990°N, 136.5021°E)，NE=(35.5047°N, 137.4986°E)
  - `x`（0→199）：南→北（緯度遞增）
  - `y`（0→199）：西→東（經度遞增）
  - 轉換公式：`lat = BBOX_SOUTH + x * LAT_STEP`，`lon = BBOX_WEST + y * LON_STEP`
  - 產出 `data/grid_to_latlon.csv`（40,000 行，含中心點與邊界框）供 POI 查詢使用。

- **輸入**：訓練集原始記錄
- **輸出**：
  - 附有 `is_holiday` 標籤的標準化軌跡表
  - `data/grid_to_latlon.csv`：每個 (x, y) 網格對應的中心點 (lat, lon) 與邊界框

---

### 3.3 探索性分析（`analysis/eda.py`）

**職責**：視覺化呈現資料特性，輔助後續模組設計決策，不產出供其他模組使用的特徵。

主要產出：

- 每日活躍使用者數趨勢圖（識別假日低谷）
- x/y 熱力圖（城市人流密度分布）
- 個別使用者的活躍天數分布（篩選資料足夠的使用者）
- 每日人流量的平假日對比圖

- **輸入**：標準化軌跡表
- **輸出**：圖表檔案（PNG）

---

### 3.4 空間分群（`analysis/clustering.py`）

**職責**：以 HDBSCAN 對空間座標進行分群，識別城市移動熱點，並為每位使用者標記其主要活動熱點群集 ID。

#### HDBSCAN 分群

- 對所有出現過的 (x, y) 網格點計算相互可達距離，建構最小生成樹，依穩定度自動萃取群集。
- 無需預設 K 值，可處理密度差異大的區域（如繁忙車站 vs 稀疏郊區）。

#### 使用者熱點標記

- 統計每位使用者在各群集的停留次數，取前 N 個最常出現的熱點作為其空間特徵。

#### 地點語意標記（POI）

- **流程**：
  1. 以 `grid_to_latlon.csv` 取得每格的真實經緯度邊界框。
  2. 以 OpenStreetMap Overpass API 批次查詢名古屋範圍內的 POI，關注類型：`amenity=station`、`amenity=school`、`shop=*`、`leisure=*` 等。
  3. 將每筆 POI 對齊至最近網格，統計每格各類 POI 數量，形成語意特徵向量。
- **前置條件**：需先完成空間仿射轉換（`preprocessing.py` 產出 `grid_to_latlon.csv`），且需人工提供 2–3 組視覺疊圖對應點。

- **輸入**：標準化軌跡表、`grid_to_latlon.csv`
- **輸出**：
  - 每個 (x, y) 網格的熱點群集 ID
  - 每位使用者的主要熱點 ID 清單
  - 每個網格的 POI 語意特徵向量（`grid_poi_features.csv`）

---

### 3.5 個人軌跡分析（`analysis/trajectory.py`）

**職責**：分析每位使用者跨天的移動重複性，產出量化的「軌跡穩定性」特徵，作為 CVAE 的條件輸入之一。

主要分析：

- **地點重複率**：計算使用者在相同時段回到相同網格的頻率（如：每天 8:00–9:00 都出現在同一格）。
- **日型分群**：依使用者的工作日／假日軌跡模式差異，將使用者分為「規律通勤型」、「彈性型」等類別。
- **軌跡繪製**：將每個分群的代表性軌跡依時序繪製成城市地圖，輔助人工驗證。

- **輸入**：標準化軌跡表、`is_holiday` 標籤
- **輸出**：每位使用者的穩定性特徵向量（標量或多維）；代表性軌跡圖

---

### 3.6 Baseline 模型（`models/baseline.py`）

**職責**：實作多個統計 baseline，建立本地 GEO-BLEU 基準分數，作為 CVAE 的比較基準。

實作方法（依官方競賽定義）：

| 方法 | 說明 |
|------|------|
| Per-User Mode | 每位使用者在每個 (d mod 7, t) 組合下，取歷史出現最頻繁的 (x, y) 作為預測 |
| Per-User Mean | 每位使用者在每個 (d mod 7, t) 組合下，取歷史 (x, y) 的平均值 |
| Bigram Model | 以前一個時間步的位置為條件，取歷史最常見的下一步位置 |
| Bigram (top_p=0.7) | Bigram 加入 nucleus sampling，從累積機率前 70% 的候選中隨機抽樣 |

- **輸入**：訓練集（Days 1–60）
- **輸出**：Days 61–75 的預測軌跡；各方法的 GEO-BLEU 分數

---

### 3.7 CVAE 模型（`models/cvae.py`）

**職責**：以條件變分自編碼器（Conditional VAE）整合空間、語意與規律性特徵，預測並生成 Days 61–75 的個人移動軌跡。

- **訓練輸入**：
  - 軌跡序列 x：使用者某日的 48 個時間步座標序列
  - 條件標籤 y：HDBSCAN 熱點 ID、⚠️ 地點語意標籤（待確認）、軌跡穩定性特徵、`is_holiday`
- **推論輸入**：條件標籤 y（不需要 x）
- **輸出**：預測的 48 步軌跡序列 `(t, x, y)`，格式與原始資料一致

> 內部架構（Encoder/Decoder 層數、latent dim 等）於詳細設計階段定義。

---

### 3.8 評估（`eval/metrics.py`）

**職責**：封裝 GEO-BLEU 與 FDE 計算，接受任意模型的預測輸出，產出標準化評估報告。

- **輸入**：
  - 預測軌跡：`(uid, d, t, x, y)` 格式
  - 真實軌跡：Days 61–75 的 ground truth
- **輸出**：各使用者的 GEO-BLEU 分數、全體平均分、FDE；彙整成報告檔
- **說明**：
  - GEO-BLEU 參數固定為 Beta=0.5, n=5，使用 `geobleu.calc_geobleu_bulk()`
  - 提交前可呼叫 `geobleu.validator` 檢查輸出格式合規性

---

## 4. 模組依賴關係

```text
loader
  └─→ preprocessing
          ├─→ eda           （獨立，隨時可跑，不影響其他模組）
          ├─→ clustering    ──┐
          ├─→ trajectory    ──┼─→ cvae ─→ metrics
          └─→ baseline ───────┘
```

**關鍵路徑**：`loader → preprocessing → clustering + trajectory → cvae → metrics`

---

## 5. 資料流

```text
nagoya_challengedata.csv
    │
    ▼ loader
(uid, d, t, x, y) 原始記錄
    │
    ▼ preprocessing
(uid, d, t, x, y, is_holiday) 標準化記錄
    │
    ├─▶ clustering ──▶ 每格熱點 ID、每人熱點清單、[語意標籤 ⚠️]
    │
    ├─▶ trajectory ──▶ 每人穩定性特徵向量
    │
    ├─▶ baseline   ──▶ 預測軌跡（統計方法）──▶ metrics ──▶ GEO-BLEU / FDE 報告
    │
    └─▶ cvae（訓練）
            輸入：軌跡序列 + 熱點 ID + [語意標籤] + 穩定性特徵 + is_holiday
            推論輸出：Days 61-75 預測軌跡 ──▶ metrics ──▶ GEO-BLEU / FDE 報告
```

---

## 6. 待確認事項

1. **座標系統與 POI 資料取得**：
   座標系統已確認（見 3.2 節），`data/grid_to_latlon.csv` 已產出（40,000 行）。
   下一步：以 Overpass API 批次查詢名古屋邊界框內的 POI，對齊至最近網格。
   影響模組：`analysis/clustering.py`。
   狀態：✅ 座標確認完成；⏳ POI 查詢待實作

2. **訓練資料規模**：是否使用全體 ~100,000 名使用者，或取子集訓練。
   影響模組：`loader.py`、`cvae.py`（記憶體 / 訓練時間）。
   狀態：⚠️ 待確認
