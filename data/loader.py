from __future__ import annotations

from pathlib import Path

import pandas as pd

GRID_SIZE = 200
TRAIN_DAYS = 60
REQUIRED_COLUMNS = ["uid", "d", "t", "x", "y"]


def load_city(path: str | Path) -> pd.DataFrame:
    """Load a city trajectory CSV and normalize it to the project schema."""
    df = pd.read_csv(
        path,
        usecols=lambda col: col in REQUIRED_COLUMNS,
        dtype={"uid": "int64", "d": "int16", "t": "int8", "x": "int16", "y": "int16"},
    )
    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    df = df[REQUIRED_COLUMNS].copy()
    valid_t = df["t"].between(0, 47)
    real_xy = df["x"].ne(999)
    valid_xy = df["x"].between(0, GRID_SIZE - 1) & df["y"].between(0, GRID_SIZE - 1)
    df = df[valid_t & (~real_xy | valid_xy)].reset_index(drop=True)
    return df


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
