import pandas as pd

GRID_SIZE  = 200
TRAIN_DAYS = 60   # d=1~60 訓練；d=61~75 預測目標（競賽定義，1-indexed）


def load_city(path: str) -> tuple[pd.DataFrame, int]:
    """
    讀取城市軌跡 CSV，識別預測目標使用者（x=999）並回傳 split_point。

    資料結構：
      - x_users（uid < split_point）：d=1~75 全有真實資料，可用於本地訓練與驗證
      - y_users（uid >= split_point）：d=1~60 真實資料；d=61~75 為 x=y=999 佔位行（待預測）

    回傳：
      - df：保留全部記錄（含 x=999 佔位行），僅過濾 t 超出範圍的異常
      - split_point：y_users 的最小 uid
    """
    df = pd.read_csv(
        path,
        dtype={"uid": "int32", "d": "int16", "t": "int8", "x": "int16", "y": "int16"},
    )

    y_mask = df["x"] == 999
    if not y_mask.any():
        raise ValueError("[loader] 資料中無 x=999 記錄，無法識別預測目標使用者")
    split_point = int(df.loc[y_mask, "uid"].min())

    # 只過濾 t 超出範圍；x=999 的佔位行保留
    invalid_t = ~(y_mask | df["t"].between(0, 47))
    n_dropped = int(invalid_t.sum())
    if n_dropped > 0:
        print(f"[loader] 過濾無效 t：{n_dropped} 筆")
    df = df[~invalid_t].reset_index(drop=True)

    n_x = int((df["uid"] < split_point).sum())
    n_y = int((df["uid"] >= split_point).sum())
    print(f"[loader] split_point={split_point} | x_users={n_x:,} 筆 | y_users={n_y:,} 筆")
    return df, split_point


def split_users(df: pd.DataFrame, split_point: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    依 split_point 切出 x_users 與 y_users 的真實軌跡（去除 x=999 佔位行）。

    - x_df：x_users（uid < split_point），d=1~75，用於本地訓練／驗證
    - y_df：y_users（uid >= split_point），d=1~60，用於訓練
    """
    real = df["x"] != 999
    x_df = df[(df["uid"] < split_point) & real].reset_index(drop=True)
    y_df = df[(df["uid"] >= split_point) & real].reset_index(drop=True)
    return x_df, y_df


def get_prediction_template(df: pd.DataFrame, split_point: int) -> pd.DataFrame:
    """
    取得需要填入預測結果的 (uid, d, t) 結構（y_users 的 x=999 佔位行）。
    將預測值填入此 DataFrame 的 x, y 欄後即可直接繳交。
    """
    template = (
        df[(df["uid"] >= split_point) & (df["x"] == 999)][["uid", "d", "t"]]
        .sort_values(["uid", "d", "t"])
        .reset_index(drop=True)
    )
    return template


def split_train_test(
    df: pd.DataFrame,
    train_days: int = TRAIN_DAYS,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    按天數切分（適用於 x_users 做本地驗證）。
      train: d <= train_days  (Days 1–60)
      test:  d >  train_days  (Days 61–75)
    """
    train = df[df["d"] <= train_days].reset_index(drop=True)
    test  = df[df["d"] >  train_days].reset_index(drop=True)
    return train, test


def split_train_val_test(
    df: pd.DataFrame,
    val_start: int = 51,
    train_days: int = TRAIN_DAYS,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    三路切分（適用於 x_users 做超參數調整）。
      train:      d < val_start              (Days 1–50)
      validation: val_start <= d <= train_days  (Days 51–60)
      test:       d > train_days             (Days 61–75)
    """
    train = df[df["d"] < val_start].reset_index(drop=True)
    val   = df[(df["d"] >= val_start) & (df["d"] <= train_days)].reset_index(drop=True)
    test  = df[df["d"] > train_days].reset_index(drop=True)
    return train, val, test
