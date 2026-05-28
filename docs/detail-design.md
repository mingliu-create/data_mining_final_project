# 詳細設計文件：日本城市人流特性分析與軌跡預測

**版本**：v1.0  
**日期**：2026-05-28  
**對應文件**：[docs/proposal.md](proposal.md)、[docs/high-level-design.md](high-level-design.md)

---

## 1. 共用型別與常數

```python
# 型別別名
TrajectoryDF = pd.DataFrame  # 欄位：uid(int), d(int), t(int), x(int), y(int)
GridLatlonDF = pd.DataFrame  # 欄位：x, y, lat, lon, lat_min, lat_max, lon_min, lon_max
UserFeatureDF = pd.DataFrame # 欄位：uid + 各特徵欄位

# 常數
GRID_SIZE    = 200          # 網格邊長（格數）
CELL_METER   = 500          # 每格邊長（公尺）
TIME_STEPS   = 48           # 每日時間步數（每步 30 分鐘）
TRAIN_DAYS   = 60           # 訓練天數（d ∈ [0, 59]）
TOTAL_DAYS   = 75           # 資料總天數（d ∈ [0, 74]）
GEOBLEU_BETA = 0.5
GEOBLEU_N    = 5

# 座標系統（已確認，2026-05-28）
# 邊界框由人流地圖視覺疊圖確認
BBOX = {
    "west":  136.50205100257344,
    "east":  137.49862964018885,
    "north": 35.50467287510108,
    "south": 34.49901520185085,
}
# x(0→199) = 南→北（lat 遞增）；y(0→199) = 西→東（lon 遞增）
_LAT_STEP = (BBOX["north"] - BBOX["south"]) / (GRID_SIZE - 1)
_LON_STEP = (BBOX["east"]  - BBOX["west"])  / (GRID_SIZE - 1)
```

---

## 2. `data/loader.py`

### 職責

讀取城市 CSV，切分訓練集（d ∈ [0, 59]）與測試集（d ∈ [60, 74]）。

### 函式簽名

```python
def load_city(path: str) -> TrajectoryDF:
    """
    讀取城市軌跡 CSV，確認欄位完整性，回傳 DataFrame。
    - 欄位：uid, d, t, x, y（皆為 int）
    - 過濾 x, y 不在 [0, GRID_SIZE) 範圍內的異常記錄
    """

def split_train_test(
    df: TrajectoryDF,
    train_days: int = TRAIN_DAYS
) -> tuple[TrajectoryDF, TrajectoryDF]:
    """
    按天數切分資料集。
    - train: d < train_days  (Days 1–60)
    - test:  d >= train_days (Days 61–75，競賽預測目標)
    回傳 (train_df, test_df)
    """

def split_train_val_test(
    df: TrajectoryDF,
    val_start: int = 50,
    test_start: int = TRAIN_DAYS
) -> tuple[TrajectoryDF, TrajectoryDF, TrajectoryDF]:
    """
    三路切分，用於模型開發與超參數調整。
    - train:      d < val_start                  (Days 1–50)
    - validation: val_start <= d < test_start    (Days 51–60)
    - test:       d >= test_start                (Days 61–75)
    回傳 (train_df, val_df, test_df)
    """
```

### 輸出資料結構

| 欄位 | 型別 | 說明 |
|------|------|------|
| `uid` | int | 去識別化使用者 ID |
| `d` | int | 天數，0-based，範圍 [0, 74] |
| `t` | int | 時間步，範圍 [0, 47] |
| `x` | int | 網格橫座標，範圍 [0, 199] |
| `y` | int | 網格縱座標，範圍 [0, 199] |

---

## 3. `data/preprocessing.py`

### 職責

時間標記（平假日）、空間座標轉換、產出網格經緯度對映表。

### 函式簽名

```python
def label_holidays(df: TrajectoryDF) -> TrajectoryDF:
    """
    為每個 d 標記是否為假日，新增 is_holiday(bool) 欄位。

    步驟：
    1. 統計每日活躍使用者數（nunique uid per d）作為人流量代理指標。
    2. K-means（k=2）分群，人流量較低的群標記為假日。
    3. 比對日本國定假日修正邊界案例（需要外部假日清單）。

    回傳：含 is_holiday 欄位的 DataFrame
    """

def build_grid_heatmap(df: TrajectoryDF) -> np.ndarray:
    """
    統計所有記錄中每個 (x, y) 格子的出現總次數。

    回傳：shape (GRID_SIZE, GRID_SIZE) 的密度矩陣，density[y, x] = count
    """

def grid_to_latlon(x: int, y: int) -> tuple[float, float]:
    """
    將單個網格座標 (x, y) 轉為中心點 (lat, lon)。

    x → 緯度（南→北）：lat = BBOX["south"] + x * _LAT_STEP
    y → 經度（西→東）：lon = BBOX["west"]  + y * _LON_STEP
    """

def build_grid_latlon_table(
    save_path: str = "data/grid_to_latlon.csv"
) -> GridLatlonDF:
    """
    建立全部 200×200 格子的座標對映表，存為 CSV。（✅ 已完成，40,000 行）

    回傳 DataFrame 欄位：
        x, y        — 網格座標
        lat, lon    — 格子中心點經緯度
        lat_min, lat_max, lon_min, lon_max — 格子邊界框（±半格步長）
    """
```

### 平假日判斷補充說明

- K-means 輸入特徵：每日活躍 uid 數（標量）。
- 若 k=2 分群結果出現孤立極端值（如颱風日人流驟降），以 ±2σ 偵測並另行標記。
- 外部假日清單：使用 [`jpholiday`](https://github.com/Lalcs/jpholiday) 套件驗證。

---

## 4. `analysis/eda.py`

### 職責

資料視覺化，不產出供其他模組使用的特徵，所有函式皆為獨立可呼叫。

### 函式簽名

```python
def plot_daily_active_users(
    df: TrajectoryDF,
    save_path: str = "docs/figures/daily_active_users.png"
) -> None:
    """折線圖：每日活躍 uid 數，x 軸為 d，y 軸為 uid 數量。"""

def plot_spatial_heatmap(
    df: TrajectoryDF,
    save_path: str = "docs/figures/spatial_heatmap.png"
) -> None:
    """熱力圖：200×200 網格的人流密度，供視覺疊圖使用。"""

def plot_user_activity_distribution(
    df: TrajectoryDF,
    save_path: str = "docs/figures/user_activity_dist.png"
) -> None:
    """直方圖：每位使用者的活躍天數分布。"""

def plot_hourly_flow_by_daytype(
    df: TrajectoryDF,
    save_path: str = "docs/figures/hourly_flow_daytype.png"
) -> None:
    """折線圖：工作日 vs 假日的各時間步平均人流量對比（48 個時間步）。"""
```

---

## 5. `analysis/clustering.py`

### 職責

HDBSCAN 熱點分群（以人流密度網格為輸入），POI 資料取得與對齊，輸出每格熱點標籤與 POI 特徵向量。

### 函式簽名

```python
def compute_grid_density(df: TrajectoryDF) -> pd.DataFrame:
    """
    統計每個 (x, y) 網格的總出現次數。

    回傳 DataFrame 欄位：x, y, count
    """

def run_hdbscan(
    density_df: pd.DataFrame,
    min_cluster_size: int = 10,
    min_samples: int = 5
) -> pd.DataFrame:
    """
    對人流密度網格執行 HDBSCAN。

    輸入：density_df（x, y, count）
    處理：
        - 以 count 作為點的重複權重（對稀疏點不複製，改用 sample_weight）
        - 輸入特徵為 (x, y)
    回傳：density_df 加上 cluster_id(int) 欄位，-1 表示雜訊點
    """

def assign_user_hotspots(
    df: TrajectoryDF,
    cluster_map: pd.DataFrame,
    top_n: int = 3
) -> pd.DataFrame:
    """
    為每位使用者標記最常造訪的熱點群集 ID。

    步驟：
        1. 將 df 的 (x, y) join cluster_map 取得 cluster_id。
        2. 統計每位 uid 在各 cluster_id 的出現次數。
        3. 取前 top_n 個 cluster_id，不足補 -1。

    回傳 DataFrame 欄位：uid, hotspot_0, hotspot_1, ..., hotspot_{top_n-1}
    """

def fetch_poi_from_osm(
    grid_latlon: GridLatlonDF,
    poi_tags: dict[str, str | list[str]] | None = None
) -> pd.DataFrame:
    """
    以 Overpass API 查詢名古屋範圍內的 POI。

    參數：
        grid_latlon: 含邊界框的格子表，用於計算整體 bounding box
        poi_tags:    Overpass tag 過濾條件，預設為：
                     {
                       "amenity": ["station", "school", "hospital", "restaurant"],
                       "shop": True,
                       "leisure": True
                     }

    回傳 DataFrame 欄位：osm_id, poi_type, lat, lon
    """

def assign_poi_to_grid(
    poi_df: pd.DataFrame,
    grid_latlon: GridLatlonDF
) -> pd.DataFrame:
    """
    將每筆 POI 對齊至最近的網格。

    方法：對每筆 POI 的 (lat, lon) 計算與所有格中心的歐氏距離，取最近格。

    回傳 DataFrame 欄位：x, y, poi_type, osm_id
    """

def build_grid_poi_features(
    poi_grid: pd.DataFrame
) -> pd.DataFrame:
    """
    統計每格各類 POI 數量，轉為寬表格式。

    回傳 DataFrame 欄位：
        x, y,
        poi_station, poi_school, poi_hospital,
        poi_restaurant, poi_shop, poi_leisure,
        poi_total

    輸出：同時存為 data/grid_poi_features.csv
    """
```

---

## 6. `analysis/trajectory.py`

### 職責

量化每位使用者的移動規律性，產出穩定性特徵向量作為 CVAE 的條件輸入。

### 函式簽名

```python
def compute_location_repeat_rate(df: TrajectoryDF) -> pd.DataFrame:
    """
    計算每位使用者在同一 (weekday, t) 回到同一 (x, y) 的比例。

    步驟：
        1. 新增 weekday = d % 7。
        2. 對每個 (uid, weekday, t) 組合，計算出現最多的 (x, y) 佔該組合總記錄數的比例。
        3. 取所有組合的平均值作為該使用者的 repeat_rate。

    回傳 DataFrame 欄位：uid, repeat_rate(float, 範圍 [0, 1])
    """

def compute_day_type_entropy(df: TrajectoryDF) -> pd.DataFrame:
    """
    計算工作日與假日的移動分布熵，量化行為複雜度。

    步驟：
        1. 分別計算每位使用者在工作日、假日的 (x, y) 訪問頻率分布。
        2. 計算各分布的 Shannon Entropy。
        3. 計算工作日與假日 profile 的差異（Cosine Distance）。

    回傳 DataFrame 欄位：
        uid,
        weekday_entropy(float),
        holiday_entropy(float),
        profile_diff(float, 範圍 [0, 1])
    """

def classify_mobility_type(
    stability_df: pd.DataFrame,
    n_types: int = 4
) -> pd.DataFrame:
    """
    以 K-means 對穩定性特徵向量分群，識別使用者的移動類型。

    參數：
        stability_df: 包含 repeat_rate, weekday_entropy, holiday_entropy, profile_diff
        n_types:      分群數量，預設 4（規律通勤型、彈性工作型、假日出遊型、不規律型）

    回傳：stability_df 加上 mobility_type(int, 範圍 [0, n_types-1]) 欄位
    """

def build_user_stability_features(df: TrajectoryDF) -> UserFeatureDF:
    """
    整合所有穩定性指標，產出最終使用者特徵表。

    步驟：依序呼叫上述三個函式並 join on uid。

    回傳 DataFrame 欄位：
        uid,
        repeat_rate,
        weekday_entropy,
        holiday_entropy,
        profile_diff,
        mobility_type

    輸出：同時存為 data/user_stability_features.csv
    """
```

---

## 7. `models/baseline.py`

### 職責

實作統計 baseline 方法，以 **(weekday, t)** 組合為預測條件，建立本地 GEO-BLEU 基準分數。

### 函式簽名

```python
def predict_per_user_mode(
    train_df: TrajectoryDF,
    test_days: list[int]
) -> TrajectoryDF:
    """
    對每位使用者，依 (weekday, t) 組合預測最常出現的 (x, y)。

    步驟：
        1. 計算 weekday = d % 7。
        2. 對每個 (uid, weekday, t) 統計各 (x, y) 出現次數，取眾數。
        3. Fallback 層級（依序套用）：
            (a) 若 (uid, weekday, t) 無記錄 → 用 (uid, t) 的眾數
            (b) 若 (uid, t) 無記錄 → 用全體使用者在 (weekday, t) 的眾數
        4. 對 test_days 中每個 d 的每個 t 輸出預測。

    回傳 TrajectoryDF（uid, d, t, x, y）
    """

def predict_per_user_mean(
    train_df: TrajectoryDF,
    test_days: list[int]
) -> TrajectoryDF:
    """
    對每位使用者，依 (weekday, t) 組合預測平均 (x, y)（四捨五入至整數）。
    Fallback 邏輯同 predict_per_user_mode。

    回傳 TrajectoryDF（uid, d, t, x, y）
    """

def predict_bigram(
    train_df: TrajectoryDF,
    test_days: list[int],
    top_p: float = 1.0
) -> TrajectoryDF:
    """
    以前一時間步的位置為條件，預測下一時間步。

    步驟：
        1. 建立轉移表：(uid, x_prev, y_prev, t) → Counter{(x_next, y_next): count}
        2. 推論時逐步預測：
            - 每天 t=0 的起點：以 (uid, weekday, t=0) 的眾數初始化。
            - t=1..47：查轉移表取機率最高的下一步。
            - top_p < 1.0 時：對候選按機率排序，取累積機率 ≤ top_p 的子集，隨機抽樣。
        3. Fallback：若轉移表無對應記錄，退回 predict_per_user_mode。

    回傳 TrajectoryDF（uid, d, t, x, y）
    """

def run_all_baselines(
    train_df: TrajectoryDF,
    test_df: TrajectoryDF
) -> dict[str, float]:
    """
    執行所有 baseline 並回傳各方法的 GEO-BLEU 分數。

    回傳：{"per_user_mode": float, "per_user_mean": float,
           "bigram": float, "bigram_top_p07": float}
    """
```

---

## 8. `models/cvae.py`

### 職責

以 LSTM-based Conditional VAE 預測 Days 60–74 的個人移動軌跡。

### 條件向量（Label y）組成

```
condition = [
    hotspot_0, hotspot_1, hotspot_2,   # HDBSCAN 熱點 ID（one-hot 或 embedding，長度視群數而定）
    poi_station, poi_school, ...,       # POI 特徵（正規化後的各類 POI 數量，7 維）
    repeat_rate,                        # 移動規律性（1 維）
    weekday_entropy, holiday_entropy,   # 日型熵（2 維）
    profile_diff,                       # 工作日/假日差異（1 維）
    mobility_type,                      # 移動類型（one-hot，4 維）
    is_holiday,                         # 0 or 1（1 維）
    weekday_0, ..., weekday_6           # 星期幾（one-hot，7 維）
]
# 條件向量總維度：視 hotspot one-hot 大小而定，約 30–50 維
```

### 輸入序列格式

每筆訓練樣本為一位使用者某一天的軌跡：

```
x: shape (48, 2)  — 48 個時間步，每步為 (x_grid, y_grid)，正規化至 [0, 1]
y: shape (condition_dim,)  — 當日條件向量
```

### 模型類別與函式簽名

```python
class TrajectoryEncoder(nn.Module):
    """
    LSTM Encoder：將軌跡序列 x 與條件 y 編碼至潛在空間 (mu, log_var)。

    架構：
        condition_embed: Linear(condition_dim → hidden_dim)
        lstm:            LSTM(input_size=2, hidden_size=hidden_dim, num_layers=2, batch_first=True)
        fc_mu:           Linear(hidden_dim * 2 → latent_dim)   # *2：lstm 隱態 + condition embed
        fc_log_var:      Linear(hidden_dim * 2 → latent_dim)
    """
    def __init__(
        self,
        input_dim: int = 2,
        hidden_dim: int = 128,
        latent_dim: int = 64,
        condition_dim: int = 40
    ): ...

    def forward(
        self,
        x: Tensor,       # shape: (batch, 48, 2)
        condition: Tensor  # shape: (batch, condition_dim)
    ) -> tuple[Tensor, Tensor]:
        """回傳 (mu, log_var)，各 shape: (batch, latent_dim)"""


class TrajectoryDecoder(nn.Module):
    """
    LSTM Decoder：從潛在向量 z 與條件 y 解碼為軌跡序列。

    架構：
        input_embed: Linear(latent_dim + condition_dim → hidden_dim)
        lstm:        LSTM(input_size=hidden_dim, hidden_size=hidden_dim, num_layers=2, batch_first=True)
        fc_out:      Linear(hidden_dim → 2)
    """
    def __init__(
        self,
        latent_dim: int = 64,
        hidden_dim: int = 128,
        output_dim: int = 2,
        condition_dim: int = 40
    ): ...

    def forward(
        self,
        z: Tensor,         # shape: (batch, latent_dim)
        condition: Tensor  # shape: (batch, condition_dim)
    ) -> Tensor:
        """回傳重建軌跡，shape: (batch, 48, 2)"""


class CVAE(nn.Module):
    def __init__(
        self,
        input_dim: int = 2,
        hidden_dim: int = 128,
        latent_dim: int = 64,
        condition_dim: int = 40
    ): ...

    def reparameterize(self, mu: Tensor, log_var: Tensor) -> Tensor:
        """z = mu + eps * exp(0.5 * log_var)，eps ~ N(0, I)"""

    def forward(
        self,
        x: Tensor,
        condition: Tensor
    ) -> tuple[Tensor, Tensor, Tensor]:
        """回傳 (x_recon, mu, log_var)"""

    def sample(
        self,
        condition: Tensor,  # shape: (batch, condition_dim)
        n_samples: int = 1
    ) -> Tensor:
        """從先驗 N(0, I) 取樣，回傳 shape: (batch * n_samples, 48, 2)"""


def cvae_loss(
    x_recon: Tensor,
    x: Tensor,
    mu: Tensor,
    log_var: Tensor,
    beta: float = 1.0
) -> Tensor:
    """
    ELBO Loss = Reconstruction Loss + beta * KL Divergence
    - Reconstruction: MSE(x_recon, x)
    - KL: -0.5 * sum(1 + log_var - mu^2 - exp(log_var))
    """


def build_condition_vector(
    uid: int,
    d: int,
    user_hotspots: UserFeatureDF,
    user_stability: UserFeatureDF,
    grid_poi: pd.DataFrame,
    cluster_map: pd.DataFrame,
    n_clusters: int
) -> np.ndarray:
    """
    為指定使用者在指定天建構條件向量 y。

    回傳：shape (condition_dim,) 的 numpy array
    """


def train_cvae(
    train_df: TrajectoryDF,
    condition_df: pd.DataFrame,   # 每個 (uid, d) 對應的條件向量
    model: CVAE,
    epochs: int = 50,
    batch_size: int = 256,
    lr: float = 1e-3,
    beta: float = 1.0,
    checkpoint_path: str = "models/cvae_checkpoint.pt"
) -> CVAE:
    """
    訓練 CVAE，每 epoch 後儲存 checkpoint。
    回傳訓練完成的模型。
    """


def predict_trajectories(
    model: CVAE,
    condition_df: pd.DataFrame,
    test_days: list[int]
) -> TrajectoryDF:
    """
    以條件向量進行推論，對所有使用者生成 test_days 的軌跡預測。

    步驟：
        1. 對每個 (uid, d) 建構條件向量。
        2. 呼叫 model.sample(condition)，取 n_samples=1。
        3. 將正規化座標還原為網格整數座標（四捨五入並 clip 至 [0, GRID_SIZE-1]）。

    回傳 TrajectoryDF（uid, d, t, x, y）
    """
```

---

## 9. `eval/metrics.py`

### 職責

封裝 GEO-BLEU 與 FDE 計算，提供格式驗證與報告產出。

### 函式簽名

```python
def validate_submission(
    generated: TrajectoryDF,
    train_df: TrajectoryDF
) -> bool:
    """
    呼叫 geobleu.validator 檢查提交格式。
    - 確認所有 uid 皆在訓練集中出現過
    - 確認 t 範圍在 [0, 47]
    - 確認 x, y 在 [0, GRID_SIZE-1]
    回傳 True 表示格式合規。
    """


def compute_geobleu(
    generated: TrajectoryDF,
    reference: TrajectoryDF,
    processes: int = 4
) -> dict:
    """
    計算 GEO-BLEU（Beta=0.5, n=5）。

    步驟：
        1. 將 DataFrame 轉為 geobleu 所需的 (uid, d, t, x, y) tuple list。
        2. 呼叫 geobleu.calc_geobleu_bulk(generated, reference, processes)。

    回傳：
        {
            "mean": float,
            "per_user": {uid: float, ...}
        }
    """


def compute_fde(
    generated: TrajectoryDF,
    reference: TrajectoryDF
) -> dict:
    """
    計算 FDE（Final Displacement Error）：
    每個 (uid, d) 最後一個時間步的預測位置與真實位置的歐氏距離。

    回傳：
        {
            "mean": float,
            "per_user_day": {(uid, d): float, ...}
        }
    """


def generate_report(
    method_name: str,
    geobleu_result: dict,
    fde_result: dict,
    save_path: str = "eval/reports/"
) -> None:
    """
    儲存評估結果為 JSON 與 CSV 兩種格式。

    JSON 格式：
        {
            "method": str,
            "geobleu_mean": float,
            "fde_mean": float,
            "per_user_geobleu": {uid: float}
        }
    """
```

---

## 10. `main.py`

### 職責

串接所有模組的執行入口，依序執行完整 pipeline。

### 函式簽名

```python
def run_preprocessing(city_path: str) -> tuple[TrajectoryDF, TrajectoryDF, GridLatlonDF]:
    """載入、前處理、切分，回傳 (train_df, test_df, grid_latlon)"""

def run_feature_engineering(
    train_df: TrajectoryDF,
    grid_latlon: GridLatlonDF
) -> tuple[pd.DataFrame, UserFeatureDF, pd.DataFrame]:
    """
    執行 clustering + trajectory 分析。
    回傳 (cluster_map, user_stability, grid_poi_features)
    """

def run_baselines(
    train_df: TrajectoryDF,
    test_df: TrajectoryDF
) -> None:
    """執行所有 baseline 並輸出評估報告。"""

def run_cvae(
    train_df: TrajectoryDF,
    test_df: TrajectoryDF,
    cluster_map: pd.DataFrame,
    user_stability: UserFeatureDF,
    grid_poi: pd.DataFrame
) -> None:
    """訓練 CVAE 並輸出評估報告。"""
```

---

## 11. 模組測試策略

各模組設計為可獨立測試，建議測試資料使用 1,000 名使用者、10 天的子集。

| 模組 | 測試重點 |
|------|---------|
| `loader.py` | 欄位型別、異常值過濾、切分邊界（d=59/60） |
| `preprocessing.py` | K-means 假日標記結果、仿射轉換反算誤差 < 1 格 |
| `eda.py` | 圖表正常產出，不拋錯 |
| `clustering.py` | HDBSCAN 無 k=0 的空群集；POI join 後無孤立記錄 |
| `trajectory.py` | repeat_rate ∈ [0,1]；mobility_type 無超出範圍值 |
| `baseline.py` | Fallback 邏輯覆蓋；預測輸出 uid 集合與測試集一致 |
| `cvae.py` | Loss 單調下降；sample 輸出座標在合法範圍內 |
| `metrics.py` | GEO-BLEU 完全相同軌跡應 ≈ 1.0；FDE = 0 時兩軌跡完全一致 |

---

## 12. 待確認事項

1. **座標系統**：✅ 已確認（2026-05-28）。邊界框由人流地圖視覺疊圖確認，`data/grid_to_latlon.csv` 已產出。

2. **訓練資料規模**：名古屋資料集約 100,000 名使用者。訓練 CVAE 時是否使用全體，或取活躍天數 ≥ 30 天的子集，影響 `loader.py` 的過濾邏輯與訓練時間。  
   狀態：⚠️ 待確認
