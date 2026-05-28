import numpy as np
import pandas as pd

GRID_SIZE = 200

# 已知邊界框（由人流地圖視覺疊圖確認，2026-05-28）
BBOX = {
    "west":  136.50205100257344,
    "east":  137.49862964018885,
    "north": 35.50467287510108,
    "south": 34.49901520185085,
}

# x(0→199) = 南→北（lat 遞增）；y(0→199) = 西→東（lon 遞增）
_LAT_STEP = (BBOX["north"] - BBOX["south"]) / (GRID_SIZE - 1)
_LON_STEP = (BBOX["east"]  - BBOX["west"])  / (GRID_SIZE - 1)

# 競賽資料中已確認的特殊假日（颱風 / 大型活動，d 為 1-indexed）
_EXTRA_HOLIDAYS = {31, 35}


# ── 時間處理 ──────────────────────────────────────────────────────────────────

def label_day_of_week(df: pd.DataFrame) -> pd.DataFrame:
    """
    為每筆記錄新增 day_of_week（0=日, 1=一, ..., 6=六）與 working_day（1=工作日, 0=假日）。

    規則（1-indexed，d=7 為星期五）：
      day_of_week = ((d - 7) % 7 + 5) % 7
      working_day = 0 if day_of_week in {0, 6} else 1
      額外假日（d=31, 35）強制 working_day = 0
    """
    d = df["d"]
    df = df.copy()
    df["day_of_week"] = ((d - 7) % 7 + 5) % 7
    df["working_day"] = (~df["day_of_week"].isin([0, 6])).astype("int8")
    df.loc[df["d"].isin(_EXTRA_HOLIDAYS), "working_day"] = 0
    return df


# ── 空間處理 ──────────────────────────────────────────────────────────────────

def grid_to_latlon(x: int, y: int) -> tuple[float, float]:
    """
    將單個網格座標 (x, y) 轉為中心點 (lat, lon)。
      x → 緯度（南→北）：lat = BBOX["south"] + x * _LAT_STEP
      y → 經度（西→東）：lon = BBOX["west"]  + y * _LON_STEP
    """
    lat = BBOX["south"] + x * _LAT_STEP
    lon = BBOX["west"]  + y * _LON_STEP
    return lat, lon


def build_grid_latlon_table(save_path: str = "data/grid_to_latlon.csv") -> pd.DataFrame:
    """
    建立全部 200×200 格子的座標對映表，存為 CSV。
    欄位：x, y, lat, lon, lat_min, lat_max, lon_min, lon_max
    """
    xs, ys = np.meshgrid(range(GRID_SIZE), range(GRID_SIZE), indexing="ij")
    xs = xs.ravel()
    ys = ys.ravel()

    lats = BBOX["south"] + xs * _LAT_STEP   # x=0 → south, x=199 → north
    lons = BBOX["west"]  + ys * _LON_STEP

    df = pd.DataFrame({
        "x": xs, "y": ys,
        "lat": lats, "lon": lons,
        "lat_min": lats - _LAT_STEP / 2,
        "lat_max": lats + _LAT_STEP / 2,
        "lon_min": lons - _LON_STEP / 2,
        "lon_max": lons + _LON_STEP / 2,
    })

    df.to_csv(save_path, index=False)
    print(f"[preprocessing] saved: {save_path}  ({len(df):,} rows)")
    return df


def build_grid_heatmap(df: pd.DataFrame) -> np.ndarray:
    """
    統計每個 (x, y) 格子的總出現次數（不含 x=999 佔位行）。
    回傳 shape (GRID_SIZE, GRID_SIZE)，density[y, x] = count。
    """
    real = df[df["x"] != 999]
    density = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.int64)
    counts = real.groupby(["x", "y"]).size()
    for (x, y), cnt in counts.items():
        density[y, x] = cnt
    return density
