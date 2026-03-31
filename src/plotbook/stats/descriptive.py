"""Descriptive statistics computed row-wise on replicate data."""

from __future__ import annotations

import warnings

import numpy as np

# Suppress runtime warnings for all-NaN slices (empty rows)
warnings.filterwarnings("ignore", ".*Mean of empty slice.*", RuntimeWarning)
warnings.filterwarnings("ignore", ".*Degrees of freedom <= 0.*", RuntimeWarning)


def row_mean(data: np.ndarray) -> np.ndarray:
    """Per-row mean, ignoring NaN."""
    return np.nanmean(data, axis=1)


def row_sd(data: np.ndarray) -> np.ndarray:
    """Per-row sample standard deviation (ddof=1)."""
    return np.nanstd(data, axis=1, ddof=1)


def row_sem(data: np.ndarray) -> np.ndarray:
    """Per-row standard error of the mean."""
    n = np.sum(~np.isnan(data), axis=1).astype(float)
    n[n == 0] = np.nan
    return row_sd(data) / np.sqrt(n)


def row_ci(data: np.ndarray, confidence: float = 0.95) -> np.ndarray:
    """Per-row half-width of CI (uses t-distribution if scipy available)."""
    n = np.sum(~np.isnan(data), axis=1).astype(float)
    se = row_sem(data)
    result = np.full(len(n), np.nan)

    try:
        from scipy import stats as sp_stats
        for i in range(len(n)):
            if n[i] >= 2:
                t_crit = sp_stats.t.ppf((1 + confidence) / 2, df=n[i] - 1)
                result[i] = se[i] * t_crit
    except ImportError:
        # Fallback: normal approximation
        z = 1.96 if confidence == 0.95 else 2.576
        mask = n >= 2
        result[mask] = se[mask] * z

    return result


def row_ci95(data: np.ndarray) -> np.ndarray:
    return row_ci(data, 0.95)


def row_ci99(data: np.ndarray) -> np.ndarray:
    return row_ci(data, 0.99)


def row_range_half(data: np.ndarray) -> np.ndarray:
    """Per-row half of the range (max - min) / 2."""
    mins = np.nanmin(data, axis=1)
    maxs = np.nanmax(data, axis=1)
    return (maxs - mins) / 2.0


def quartiles(data: np.ndarray) -> tuple[float, float, float]:
    """Returns (Q1, median, Q3) from a 1D array."""
    clean = data[~np.isnan(data)]
    if len(clean) == 0:
        return (np.nan, np.nan, np.nan)
    q1, med, q3 = np.nanpercentile(clean, [25, 50, 75])
    return (float(q1), float(med), float(q3))


def column_stats(data: np.ndarray) -> dict:
    """Compute full stats for a 1D column of replicate values."""
    clean = data[~np.isnan(data)]
    n = len(clean)
    if n == 0:
        return {"n": 0, "mean": np.nan, "sd": np.nan, "sem": np.nan,
                "min": np.nan, "max": np.nan, "median": np.nan,
                "q1": np.nan, "q3": np.nan}

    sd_val = float(np.std(clean, ddof=1)) if n > 1 else 0.0
    sem_val = sd_val / np.sqrt(n) if n > 0 else np.nan
    q1, med, q3 = quartiles(data)

    return {
        "n": n,
        "mean": float(np.mean(clean)),
        "sd": sd_val,
        "sem": sem_val,
        "min": float(np.min(clean)),
        "max": float(np.max(clean)),
        "median": med,
        "q1": q1,
        "q3": q3,
    }
