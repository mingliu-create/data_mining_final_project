from __future__ import annotations

from pathlib import Path

import pandas as pd

GRID_SIZE = 200
TRAIN_DAYS = 60
REQUIRED_COLUMNS = ["uid", "d", "t", "x", "y"]
DTYPES = {"uid": "int64", "d": "int16", "t": "int8", "x": "int16", "y": "int16"}


def _normalize_city_frame(df: pd.DataFrame) -> pd.DataFrame:
    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    df = df[REQUIRED_COLUMNS].copy()
    valid_t = df["t"].between(0, 47)
    real_xy = df["x"].ne(999)
    valid_xy = df["x"].between(0, GRID_SIZE - 1) & df["y"].between(0, GRID_SIZE - 1)
    return df[valid_t & (~real_xy | valid_xy)].reset_index(drop=True)


def _select_uids(
    uids: pd.Series,
    max_users: int | None = None,
    sample_users: int | None = None,
    random_seed: int = 42,
) -> set[int] | None:
    unique_uids = pd.Index(uids.drop_duplicates()).sort_values()
    if sample_users is not None:
        if sample_users <= 0:
            raise ValueError("sample_users must be positive")
        selected = unique_uids.to_series().sample(
            n=min(sample_users, len(unique_uids)),
            random_state=random_seed,
        )
        return set(selected.astype(int).tolist())
    if max_users is not None:
        if max_users <= 0:
            raise ValueError("max_users must be positive")
        return set(unique_uids[:max_users].astype(int).tolist())
    return None


def load_city(
    path: str | Path,
    max_users: int | None = None,
    sample_users: int | None = None,
    random_seed: int = 42,
    chunksize: int | None = None,
) -> pd.DataFrame:
    """Load a city trajectory CSV and normalize it to the project schema."""
    if chunksize is None:
        df = pd.read_csv(path, usecols=lambda col: col in REQUIRED_COLUMNS, dtype=DTYPES)
        selected_uids = _select_uids(df["uid"], max_users, sample_users, random_seed)
        if selected_uids is not None:
            df = df[df["uid"].isin(selected_uids)]
        return _normalize_city_frame(df)

    selected_uids = None
    if max_users is not None or sample_users is not None:
        uid_chunks = pd.read_csv(path, usecols=["uid"], dtype={"uid": "int64"}, chunksize=chunksize)
        all_uids = pd.concat((chunk["uid"].drop_duplicates() for chunk in uid_chunks), ignore_index=True)
        selected_uids = _select_uids(all_uids, max_users, sample_users, random_seed)

    frames = []
    for chunk in pd.read_csv(
        path,
        usecols=lambda col: col in REQUIRED_COLUMNS,
        dtype=DTYPES,
        chunksize=chunksize,
    ):
        if selected_uids is not None:
            chunk = chunk[chunk["uid"].isin(selected_uids)]
        if not chunk.empty:
            frames.append(_normalize_city_frame(chunk))
    if not frames:
        return pd.DataFrame(columns=REQUIRED_COLUMNS).astype(DTYPES)
    return pd.concat(frames, ignore_index=True)


def split_train_test(
    df: pd.DataFrame,
    train_days: int = TRAIN_DAYS,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split into train (d < train_days) and test (d >= train_days)."""
    real = df["x"].ne(999)
    train = df[real & (df["d"] < train_days)].reset_index(drop=True)
    test = df[real & (df["d"] >= train_days)].reset_index(drop=True)
    return train, test


def split_train_val_test(
    df: pd.DataFrame,
    val_start: int = 50,
    test_start: int = TRAIN_DAYS,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split into train, validation, and test by zero-based day index."""
    real = df["x"].ne(999)
    clean = df[real]
    train = clean[clean["d"] < val_start].reset_index(drop=True)
    val = clean[(clean["d"] >= val_start) & (clean["d"] < test_start)].reset_index(drop=True)
    test = clean[clean["d"] >= test_start].reset_index(drop=True)
    return train, val, test


def get_prediction_template(df: pd.DataFrame) -> pd.DataFrame:
    """Return competition rows whose x/y are hidden as 999."""
    return (
        df[df["x"].eq(999)][["uid", "d", "t"]]
        .sort_values(["uid", "d", "t"])
        .reset_index(drop=True)
    )


def split_observed_and_hidden(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return observed rows and hidden prediction template rows."""
    observed = df[df["x"].ne(999)].reset_index(drop=True)
    hidden = get_prediction_template(df)
    return observed, hidden
