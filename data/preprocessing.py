from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

GRID_SIZE = 200

BBOX = {
    "west": 136.50205100257344,
    "east": 137.49862964018885,
    "north": 35.50467287510108,
    "south": 34.49901520185085,
}

_LAT_STEP = (BBOX["north"] - BBOX["south"]) / (GRID_SIZE - 1)
_LON_STEP = (BBOX["east"] - BBOX["west"]) / (GRID_SIZE - 1)
_EXTRA_HOLIDAYS = {30, 34}  # zero-based equivalents of days 31 and 35


def label_holidays(df: pd.DataFrame) -> pd.DataFrame:
    """Add an is_holiday column using daily active users and calendar fallback."""
    out = df.copy()
    daily = out.groupby("d")["uid"].nunique().rename("active_users").reset_index()
    if len(daily) >= 2 and daily["active_users"].nunique() >= 2:
        labels = KMeans(n_clusters=2, random_state=42, n_init="auto").fit_predict(
            daily[["active_users"]]
        )
        daily["cluster"] = labels
        holiday_cluster = daily.groupby("cluster")["active_users"].mean().idxmin()
        holiday_days = set(daily.loc[daily["cluster"].eq(holiday_cluster), "d"].astype(int))
    else:
        holiday_days = set()

    weekdays = out["d"] % 7
    weekend_days = set(out.loc[weekdays.isin([5, 6]), "d"].astype(int))
    holiday_days |= weekend_days | _EXTRA_HOLIDAYS
    out["is_holiday"] = out["d"].isin(holiday_days)
    return out


def label_day_of_week(df: pd.DataFrame) -> pd.DataFrame:
    """Add day_of_week and working_day columns used by temp experiments."""
    out = df.copy()
    out["day_of_week"] = out["d"] % 7
    out["working_day"] = (~out["day_of_week"].isin([5, 6])).astype("int8")
    out.loc[out["d"].isin(_EXTRA_HOLIDAYS), "working_day"] = 0
    return out


def build_grid_heatmap(df: pd.DataFrame) -> np.ndarray:
    """Return density[y, x] visit counts for the 200x200 grid."""
    real = df[df["x"].ne(999)]
    density = np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.int64)
    counts = real.groupby(["x", "y"]).size()
    for (x, y), count in counts.items():
        if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
            density[int(y), int(x)] = int(count)
    return density


def grid_to_latlon(x: int, y: int) -> tuple[float, float]:
    """Convert grid coordinate (x, y) to center latitude and longitude."""
    lat = BBOX["south"] + x * _LAT_STEP
    lon = BBOX["west"] + y * _LON_STEP
    return lat, lon


def build_grid_latlon_table(save_path: str | Path = "data/grid_to_latlon.csv") -> pd.DataFrame:
    """Build and save the 200x200 grid latitude/longitude lookup table."""
    xs, ys = np.meshgrid(range(GRID_SIZE), range(GRID_SIZE), indexing="ij")
    xs = xs.ravel()
    ys = ys.ravel()
    lats = BBOX["south"] + xs * _LAT_STEP
    lons = BBOX["west"] + ys * _LON_STEP

    table = pd.DataFrame(
        {
            "x": xs,
            "y": ys,
            "lat": lats,
            "lon": lons,
            "lat_min": lats - _LAT_STEP / 2,
            "lat_max": lats + _LAT_STEP / 2,
            "lon_min": lons - _LON_STEP / 2,
            "lon_max": lons + _LON_STEP / 2,
        }
    )
    path = Path(save_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(path, index=False)
    return table
