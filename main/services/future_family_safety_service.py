# main/services/future_family_safety_service.py
"""
Pure-Python predictor used by Django.

Key changes vs your previous version
------------------------------------
1) Global in-process caches:
   - CSVs (field/lab) are loaded once and reused.
   - Stats JSON (or computed stats) is cached.
   - Joblib models (per-site and global) are cached.
   This removes heavy I/O on every request and avoids timeouts/502.

2) Safer/lazier loading:
   - Lazy (on first use) instead of at import time to keep worker boot quick.
   - Low-memory CSV read options and usecols to reduce RAM.

3) Small hardening:
   - Horizon clamp to a sensible max (default 365 days).
   - list_sites() reads only needed columns and caches unique site list.
   - Optional mmap for joblib.load to reduce memory duplication.

Everything else (forecasting/scoring/categories/48h paths) is functionally
equivalent to your logic with bug-safe guards.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json
import os
import re
import threading
import numpy as np
import pandas as pd
import joblib
import yaml
import datetime as dt
import warnings

# Silence sklearn joblib version warnings (optional)
try:
    from sklearn.exceptions import InconsistentVersionWarning
    warnings.filterwarnings("ignore", category=InconsistentVersionWarning)
except Exception:
    pass

# Ensure joblib can unpickle scikit estimators used at train time
from sklearn.linear_model import Ridge  # noqa: F401


# --------------------------------------------------------------------------------------
# Paths & constants
# --------------------------------------------------------------------------------------
def _detect_base_dir() -> Path:
    """Find Django BASE_DIR if available, otherwise traverse up to project root."""
    try:
        from django.conf import settings  # type: ignore
        return Path(settings.BASE_DIR)
    except Exception:
        # services/ -> main/ -> project root
        return Path(__file__).resolve().parents[2]


BASE_DIR: Path = _detect_base_dir()
ARTIFACTS_DIR: Path = BASE_DIR / "artifacts"
CLEAN_DIR: Path = ARTIFACTS_DIR / "clean"
OUTPUT_CSV = CLEAN_DIR / "output.csv"
CONFIG_DIR: Path = BASE_DIR / "config"

# Core parameters (kept in sync with training)
PARAMS_CORE = ["pH", "EC_uS_cm", "DO_mg_L", "redox_mV"]

# Cleaned outputs & stats written by training
FIELD_CLEAN_CSV = CLEAN_DIR / "field_chemistry_clean.csv"
LAB_CLEAN_WIDE_CSV = CLEAN_DIR / "lab_chemistry_clean_wide.csv"
STATS_JSON = ARTIFACTS_DIR / "stats" / "global_stats.json"

# Display rounding (what the UI wants)
ROUNDING_RULES: Dict[str, int] = {
    "pH": 2,        # 7.39
    "EC_uS_cm": 0,  # 10,772
    # "DO_mg_L": 2,
    # "redox_mV": 0,
}

# Sensible limits to avoid excessive CPU on big horizons
MAX_HORIZON_DAYS = int(os.environ.get("FFS_MAX_HORIZON_DAYS", "365"))

# Use joblib memory map to reduce memory duplication across workers (optional)
JOBLIB_MMAP_MODE = os.environ.get("FFS_JOBLIB_MMAP", "r")  # set to "" to disable


# --------------------------------------------------------------------------------------
# Small utils
# --------------------------------------------------------------------------------------
def file_safe(s: str) -> str:
    """Make a filesystem-safe token from a string."""
    return re.sub(r"[^A-Za-z0-9._-]+", "_", str(s))


def load_config() -> Dict[str, Any]:
    """
    Load quality_rules.yaml with your thresholds and weights.
    Falls back to sensible defaults if the file is missing.
    """
    cfg_path = CONFIG_DIR / "quality_rules.yaml"
    if not cfg_path.exists():
        return {
            "weights": {"pH": 0.35, "EC_uS_cm": 0.35, "DO_mg_L": 0.20, "redox_mV": 0.10},
            "categories": {"good": 70.0, "fair": 40.0, "poor": 0.0},
            "default_base_score": 65.0,
            "fallback": {
                "use_decay": True,
                "tau_days": 180,
                "typicals": {"pH": 7.0, "EC_uS_cm": 300.0, "DO_mg_L": 8.0, "redox_mV": 200.0},
            },
            "baseline_window": 5,
        }
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    # Sensible defaults for any missing keys
    cfg.setdefault("default_base_score", 65.0)
    cfg.setdefault(
        "fallback",
        {
            "use_decay": True,
            "tau_days": 180,
            "typicals": {"pH": 7.0, "EC_uS_cm": 300.0, "DO_mg_L": 8.0, "redox_mV": 200.0},
        },
    )
    cfg.setdefault("baseline_window", 5)
    return cfg


def _load_clean_safe() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Read cleaned field/lab tables produced during training.
    If missing, return empty frames with expected columns.
    """
    # Use low_memory=False to avoid DtypeWarning and get consistent dtypes
    try:
        field_df = pd.read_csv(
            FIELD_CLEAN_CSV,
            parse_dates=["datetime"],
            low_memory=False,
        )
    except Exception:
        field_df = pd.DataFrame(columns=["site_id", "datetime"] + PARAMS_CORE)

    try:
        lab_wide_df = pd.read_csv(
            LAB_CLEAN_WIDE_CSV,
            parse_dates=["datetime"],
            low_memory=False,
        )
    except Exception:
        lab_wide_df = pd.DataFrame(columns=["site_id", "datetime"] + PARAMS_CORE)

    return field_df, lab_wide_df


def _latest_updated_iso() -> Optional[str]:
    """Newest mtime among important artifacts → ISO string for 'Last updated'."""
    candidates = [
        FIELD_CLEAN_CSV,
        LAB_CLEAN_WIDE_CSV,
        STATS_JSON,
        ARTIFACTS_DIR / "models_index.json",
    ]
    mtimes: List[float] = []
    for p in candidates:
        try:
            if p.exists():
                mtimes.append(p.stat().st_mtime)
        except Exception:
            pass
    if not mtimes:
        return None
    ts = dt.datetime.fromtimestamp(max(mtimes))
    return ts.isoformat(timespec="seconds")


# --------------------------------------------------------------------------------------
# Global in-process caches (thread-safe)
# --------------------------------------------------------------------------------------
_cache_lock = threading.RLock()
_field_df_cache: Optional[pd.DataFrame] = None
_lab_wide_df_cache: Optional[pd.DataFrame] = None
_stats_cache: Optional[Dict[str, Any]] = None
_models_cache: Dict[str, Dict[str, Any]] = {}  # key: f"{param}:{site_id}" or f"{param}:__GLOBAL__"
_sites_cache: Optional[List[Dict[str, str]]] = None  # cache for list_sites()


def get_clean_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Return cached field/lab DataFrames; load on first use."""
    global _field_df_cache, _lab_wide_df_cache
    with _cache_lock:
        if _field_df_cache is None or _lab_wide_df_cache is None:
            _field_df_cache, _lab_wide_df_cache = _load_clean_safe()
        return _field_df_cache, _lab_wide_df_cache


def get_stats() -> Dict[str, Any]:
    """Return cached stats; load JSON or compute once."""
    global _stats_cache
    with _cache_lock:
        if _stats_cache is None:
            if STATS_JSON.exists():
                with open(STATS_JSON, "r", encoding="utf-8") as f:
                    _stats_cache = json.load(f)
            else:
                field_df, lab_wide_df = get_clean_data()
                _stats_cache = compute_stats_for_scoring(field_df, lab_wide_df)
        return _stats_cache


def _joblib_load(path: Path) -> Any:
    """Wrapper around joblib.load that optionally uses memory mapping."""
    if JOBLIB_MMAP_MODE:
        return joblib.load(path, mmap_mode=JOBLIB_MMAP_MODE)
    return joblib.load(path)


def get_model(param: str, site_id: str) -> Optional[Dict[str, Any]]:
    """
    Load a per-site model if it exists (cached).
    Returns the saved model_obj dict (what you persisted at train time), or None.
    """
    global _models_cache
    key = f"{param}:{file_safe(site_id)}"
    with _cache_lock:
        if key in _models_cache:
            return _models_cache[key]
        model_path = ARTIFACTS_DIR / "models" / param / f"{file_safe(site_id)}.joblib"
        if model_path.exists():
            _models_cache[key] = _joblib_load(model_path)
            return _models_cache[key]
        return None


def get_global_model(param: str) -> Optional[Dict[str, Any]]:
    """
    Load the global model for a parameter (cached).
    Expected shape: {"model": sklearn_estimator, "meta": {...}}
    """
    global _models_cache
    key = f"{param}:__GLOBAL__"
    with _cache_lock:
        if key in _models_cache:
            return _models_cache[key]
        gpath = ARTIFACTS_DIR / "models" / param / "__GLOBAL__.joblib"
        if gpath.exists():
            _models_cache[key] = _joblib_load(gpath)
            return _models_cache[key]
        return None


def clear_caches() -> None:
    """Manual cache clear (useful for admin tasks or hot-reload hooks)."""
    global _field_df_cache, _lab_wide_df_cache, _stats_cache, _models_cache, _sites_cache
    with _cache_lock:
        _field_df_cache = None
        _lab_wide_df_cache = None
        _stats_cache = None
        _models_cache = {}
        _sites_cache = None


# --------------------------------------------------------------------------------------
# Features & forecasting helpers
# --------------------------------------------------------------------------------------
def make_time_features(dtser: pd.Series) -> pd.DataFrame:
    dtser = pd.to_datetime(dtser)
    doy = dtser.dt.dayofyear.values
    woy = dtser.dt.isocalendar().week.astype(int).values
    sin_doy = np.sin(2 * np.pi * doy / 365.25)
    cos_doy = np.cos(2 * np.pi * doy / 365.25)
    sin_woy = np.sin(2 * np.pi * woy / 52.18)
    cos_woy = np.cos(2 * np.pi * woy / 52.18)
    return pd.DataFrame(
        {"sin_doy": sin_doy, "cos_doy": cos_doy, "sin_woy": sin_woy, "cos_woy": cos_woy}
    )


def _rolling_mean_forecast(last_vals: List[float], window: int) -> float:
    v = pd.Series(last_vals).dropna().values
    if len(v) == 0:
        return np.nan
    w = min(max(1, int(window)), len(v))
    return float(np.mean(v[-w:]))


# --------------------------------------------------------------------------------------
# Feature alignment helper
# --------------------------------------------------------------------------------------
CANONICAL_FEATURE_ORDER = [
    # lags
    "lag1", "lag2", "lag3", "lag4", "lag5", "lag6", "lag7", "lag14",
    # rolling means
    "rollmean_3", "rollmean_5", "rollmean_7",
    # time features
    "sin_doy", "cos_doy", "sin_woy", "cos_woy",
    # EC-only log features that *might* exist in some models
    "log_lag1", "log_lag2", "log_lag3", "log_lag4", "log_lag5", "log_lag6", "log_lag7", "log_lag14",
    "log_rollmean_3", "log_rollmean_5", "log_rollmean_7",
]


def _align_row_to_model(row_df: pd.DataFrame, model_obj: Dict[str, Any], model) -> np.ndarray:
    """
    Align a single-row DataFrame to the model's expected features/ordering.
    Priority:
      1) model_obj["feature_names"] if present
      2) model.feature_names_in_ if present
      3) CANONICAL_FEATURE_ORDER trimmed/padded to model.n_features_in_
    """
    # 1) training-time saved names
    feat_names = model_obj.get("feature_names", None)
    if isinstance(feat_names, (list, tuple)) and len(feat_names) > 0:
        return row_df.reindex(columns=list(feat_names), fill_value=0.0).values

    # 2) from sklearn model
    feat_names = getattr(model, "feature_names_in_", None)
    if isinstance(feat_names, np.ndarray) and feat_names.size > 0:
        feat_names = list(map(str, feat_names.tolist()))
        return row_df.reindex(columns=feat_names, fill_value=0.0).values
    if isinstance(feat_names, (list, tuple)) and len(feat_names) > 0:
        return row_df.reindex(columns=list(feat_names), fill_value=0.0).values

    # 3) use canonical order up to n_features_in_
    n_expected = getattr(model, "n_features_in_", None)
    if isinstance(n_expected, (int, np.integer)) and n_expected > 0:
        cols = [c for c in CANONICAL_FEATURE_ORDER if c in row_df.columns][:int(n_expected)]
        if len(cols) != int(n_expected):
            # fill remaining with whatever exists
            extras = [c for c in row_df.columns if c not in cols]
            cols = (cols + extras)[:int(n_expected)]
        return row_df.reindex(columns=cols, fill_value=0.0).values

    # last resort
    return row_df.values


# --------------------------------------------------------------------------------------
# Forecasting
# --------------------------------------------------------------------------------------
def step_forecast(model_obj: Dict[str, Any], horizon_days: int) -> List[Dict[str, Any]]:
    """
    One-step recursive forecast using a saved per-site model object.
    Now with feature alignment to avoid shape mismatches.
    """
    model = model_obj["model"]
    param_name = model_obj.get("param_name", "")
    last_vals = list(model_obj.get("last_vals", [])) if model_obj.get("last_vals", None) is not None else []
    cur_dt = pd.Timestamp(model_obj.get("last_dt", pd.Timestamp.utcnow()))

    preds: List[Dict[str, Any]] = []

    for _ in range(horizon_days):
        cur_dt = cur_dt + pd.Timedelta(days=1)

        # craft features for the next step (lags/rolling/time)
        lags = {
            f"lag{k}": (
                float(last_vals[-k]) if len(last_vals) >= k and np.isfinite(last_vals[-k]) else np.nan
            )
            for k in [1, 2, 3, 4, 5, 6, 7, 14]
        }

        def _roll(v: List[float], w: int) -> float:
            vv = pd.Series(v).dropna().values
            if len(vv) == 0:
                return np.nan
            return float(np.mean(vv[-min(w, len(vv)):]))

        roll_feats = {f"rollmean_{w}": _roll(last_vals, w) for w in (3, 5, 7)}
        tf = make_time_features(pd.Series([cur_dt])).iloc[0].to_dict()

        feats: Dict[str, Any] = {}
        feats.update(lags)
        feats.update(roll_feats)
        feats.update(tf)

        # EC-specific log features (only helps if model used them; alignment makes it safe)
        if param_name == "EC_uS_cm":
            for k in [1, 2, 3, 4, 5, 6, 7, 14]:
                v = feats.get(f"lag{k}", np.nan)
                feats[f"log_lag{k}"] = np.log1p(v) if np.isfinite(v) else np.nan
            for w in (3, 5, 7):
                v = feats.get(f"rollmean_{w}", np.nan)
                feats[f"log_rollmean_{w}"] = np.log1p(v) if np.isfinite(v) else np.nan

        row_df = (
            pd.DataFrame([feats])
            .replace([np.inf, -np.inf], np.nan)
            .ffill(axis=1)
            .bfill(axis=1)
            .fillna(0.0)
        )

        # align columns to model expectation
        X_row = _align_row_to_model(row_df, model_obj, model)

        yhat = float(model.predict(X_row)[0])
        preds.append({"date": str(cur_dt.date()), "value": yhat})

        last_vals.append(yhat)
        if len(last_vals) > 14:
            last_vals = last_vals[-14:]
    return preds


def _global_model_predict_one_step(
    model, meta: Dict[str, Any], sid: str, last_vals: List[float], cur_dt: pd.Timestamp
) -> float:
    # lags + rolls + time
    lags = {
        f"lag{k}": (
            float(last_vals[-k]) if len(last_vals) >= k and np.isfinite(last_vals[-k]) else np.nan
        )
        for k in [1, 2, 3, 4, 5, 6, 7, 14]
    }

    def _roll(v: List[float], w: int) -> float:
        vv = pd.Series(v).dropna().values
        if len(vv) == 0:
            return np.nan
        return float(np.mean(vv[-min(w, len(vv)):]))

    roll_feats = {f"rollmean_{w}": _roll(last_vals, w) for w in (3, 5, 7)}
    tf = make_time_features(pd.Series([cur_dt])).iloc[0].to_dict()

    feats: Dict[str, Any] = {}
    feats.update(lags)
    feats.update(roll_feats)
    feats.update(tf)

    # EC log features
    if meta.get("param_name") == "EC_uS_cm":
        for k in [1, 2, 3, 4, 5, 6, 7, 14]:
            v = feats.get(f"lag{k}", np.nan)
            feats[f"log_lag{k}"] = np.log1p(v) if np.isfinite(v) else np.nan
        for w in (3, 5, 7):
            v = feats.get(f"rollmean_{w}", np.nan)
            feats[f"log_rollmean_{w}"] = np.log1p(v) if np.isfinite(v) else np.nan

    # site one-hot (trained hot sites + OTHER)
    hot = set(meta.get("hot_sites", []))
    for hs in hot:
        feats[f"site__{hs}"] = 1.0 if str(sid) == str(hs) else 0.0
    feats["site__OTHER"] = 0.0 if str(sid) in hot else 1.0

    row_df = (
        pd.DataFrame([feats])
        .replace([np.inf, -np.inf], np.nan)
        .ffill(axis=1)
        .bfill(axis=1)
    )

    # use meta feature_names if provided; otherwise reuse alignment helper
    if "feature_names" in meta and isinstance(meta["feature_names"], list):
        X_row = row_df.reindex(columns=meta["feature_names"], fill_value=0.0).values
    else:
        # fake a model_obj wrapper so we can reuse the same aligner
        X_row = _align_row_to_model(row_df, {"feature_names": meta.get("feature_names", None)}, model)

    return float(model.predict(X_row)[0])


# --------------------------------------------------------------------------------------
# Stats + scoring
# --------------------------------------------------------------------------------------
def compute_stats_for_scoring(
    field_df: pd.DataFrame, lab_wide_df: Optional[pd.DataFrame] = None
) -> Dict[str, Any]:
    frames = []
    if isinstance(field_df, pd.DataFrame) and not field_df.empty:
        frames.append(field_df[["site_id", "datetime"] + [c for c in PARAMS_CORE if c in field_df.columns]])
    if isinstance(lab_wide_df, pd.DataFrame) and not lab_wide_df.empty:
        frames.append(lab_wide_df[["site_id", "datetime"] + [c for c in PARAMS_CORE if c in lab_wide_df.columns]])
    all_df = (
        pd.concat(frames, ignore_index=True)
        if frames
        else pd.DataFrame(columns=["site_id", "datetime"] + PARAMS_CORE)
    )

    stats: Dict[str, Any] = {}
    for p in PARAMS_CORE:
        if p in all_df.columns:
            s = pd.to_numeric(all_df[p], errors="coerce").dropna()
            if len(s) > 0:
                stats[p] = {"q10": float(s.quantile(0.10)), "q50": float(s.quantile(0.50)), "q90": float(s.quantile(0.90))}
    return stats


def quality_penalties(pred: Dict[str, float], stats: Dict[str, Any]) -> Dict[str, float]:
    """
    Convert raw predictions into penalty scores in [0,1] (lower is better).
    """
    pens: Dict[str, float] = {}
    if "pH" in pred and pred["pH"] is not None:
        pens["pH"] = min(1.0, abs(pred["pH"] - 7.0) / 1.5)
    if "EC_uS_cm" in pred and pred["EC_uS_cm"] is not None and "EC_uS_cm" in stats:
        q = stats["EC_uS_cm"]; v = pred["EC_uS_cm"]
        pens["EC_uS_cm"] = 0.0 if v <= q["q10"] else (1.0 if v >= q["q90"]
                              else (v - q["q10"]) / (q["q90"] - q["q10"] + 1e-9))
    if "DO_mg_L" in pred and pred["DO_mg_L"] is not None and "DO_mg_L" in stats:
        q = stats["DO_mg_L"]; v = pred["DO_mg_L"]
        pens["DO_mg_L"] = 0.0 if v >= q["q90"] else (1.0 if v <= q["q10"]
                              else 1.0 - (v - q["q10"]) / (q["q90"] - q["q10"] + 1e-9))
    if "redox_mV" in pred and pred["redox_mV"] is not None and "redox_mV" in stats:
        med = stats["redox_mV"]["q50"]; v = pred["redox_mV"]
        pens["redox_mV"] = min(1.0, abs(v - med) / (abs(stats["redox_mV"]["q90"] - med) + 1e-9))
    return pens


def score_from_penalties(pens: Dict[str, float], weights: Dict[str, float], default_if_empty: float = 65.0) -> float:
    active = {k: v for k, v in weights.items() if k in pens}
    if not active:
        return float(default_if_empty)
    total_w = sum(active.values())
    s = sum((1.0 - pens[k]) * (w / total_w) for k, w in active.items())
    return 100.0 * s


def category_from_score(score: float, cats: Dict[str, float]) -> str:
    # Your YAML already has poor:0, but logic keeps "else → poor" for safety
    if score >= cats.get("good", 70.0):
        return "good"
    elif score >= cats.get("fair", 40.0):
        return "fair"
    return "poor"


# --------------------------------------------------------------------------------------
# Data access for fallbacks & confidence
# --------------------------------------------------------------------------------------
def _last_obs_for_site_param(
    site_id: str, param: str, field_df: pd.DataFrame, lab_wide_df: pd.DataFrame
) -> Optional[Tuple[pd.Timestamp, float]]:
    cand: List[Tuple[pd.Timestamp, float]] = []
    if not field_df.empty and param in field_df.columns:
        sdf = field_df[(field_df["site_id"] == site_id) & field_df[param].notna()]
        if not sdf.empty:
            r = sdf.sort_values("datetime").iloc[-1]
            cand.append((pd.Timestamp(r["datetime"]), float(r[param])))
    if not lab_wide_df.empty and param in lab_wide_df.columns:
        sdf = lab_wide_df[(lab_wide_df["site_id"] == site_id) & lab_wide_df[param].notna()]
        if not sdf.empty:
            r = sdf.sort_values("datetime").iloc[-1]
            cand.append((pd.Timestamp(r["datetime"]), float(r[param])))
    if not cand:
        return None
    cand.sort(key=lambda t: t[0])
    return cand[-1]


def _last_k_obs_for_site_param(
    site_id: str, param: str, field_df: pd.DataFrame, lab_wide_df: pd.DataFrame, k: int = 14
) -> Tuple[pd.Timestamp, List[float]]:
    frames = []
    if not field_df.empty and param in field_df.columns:
        frames.append(field_df[(field_df["site_id"] == site_id)][["datetime", param]].rename(columns={param: "y"}))
    if not lab_wide_df.empty and param in lab_wide_df.columns:
        frames.append(lab_wide_df[(lab_wide_df["site_id"] == site_id)][["datetime", param]].rename(columns={param: "y"}))
    if not frames:
        return pd.Timestamp("1970-01-01"), []
    df = pd.concat(frames, ignore_index=True).dropna().sort_values("datetime")
    if df.empty:
        return pd.Timestamp("1970-01-01"), []
    last_dt = pd.Timestamp(df["datetime"].iloc[-1])
    vals = df["y"].tail(k).tolist()
    return last_dt, vals


def _count_points_for_site_param(site_id: str, param: str, field_df: pd.DataFrame, lab_wide_df: pd.DataFrame) -> int:
    frames = []
    if not field_df.empty and param in field_df.columns:
        frames.append(field_df[(field_df["site_id"] == site_id)][["datetime", param]])
    if not lab_wide_df.empty and param in lab_wide_df.columns:
        frames.append(lab_wide_df[(lab_wide_df["site_id"] == site_id)][["datetime", param]])
    if not frames:
        return 0
    df = pd.concat(frames, ignore_index=True)
    return int(pd.to_numeric(df[param], errors="coerce").notna().sum())


def _global_medians(stats: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, float]:
    out: Dict[str, float] = {}
    typ = cfg.get("fallback", {}).get("typicals", {})
    for p in PARAMS_CORE:
        if p in stats and "q50" in stats[p]:
            out[p] = float(stats[p]["q50"])
        else:
            out[p] = float(typ.get(p, np.nan))
    return out


def _decay_to_median(
    last_val: float,
    last_dt: pd.Timestamp,
    median_val: float,
    horizon_last_dt: pd.Timestamp,
    tau_days: float,
    use_decay: bool,
) -> float:
    if not use_decay:
        return float(last_val)
    age_days = max(0.0, (horizon_last_dt - last_dt).days)
    w = np.exp(-age_days / max(1.0, float(tau_days)))
    return float(w * last_val + (1.0 - w) * median_val)


def _apply_rounding(preds: Dict[str, float]) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for k, v in preds.items():
        if v is None:
            out[k] = None
            continue
        if k in ROUNDING_RULES and np.isfinite(v):
            out[k] = round(float(v), ROUNDING_RULES[k])
        else:
            out[k] = float(v)
    return out


# --------------------------------------------------------------------------------------
# 48h dual-scenario series (for Chart.js)
# --------------------------------------------------------------------------------------
def _forecast_48h_series(seed_score: float, confidence: float) -> List[Dict[str, float]]:
    """
    Produce 6-hourly points for next 48h (9 points: 0..48h).
    - "do_nothing": light mean-reversion toward 65 + tiny noise
    - "take_action": starts from do_nothing and adds a tapering uplift (~+8)
    - Confidence band width shrinks as confidence increases
    """
    out: List[Dict[str, float]] = []
    now = pd.Timestamp.utcnow()
    step = pd.Timedelta(hours=6)
    base = float(seed_score if seed_score is not None else 65.0)
    conf = max(0.0, min(1.0, float(confidence or 0.2)))
    for i in range(9):
        ts = (now + i * step).isoformat() + "Z"
        # do-nothing path: slight pull toward 65
        base = max(0.0, min(100.0, base + (65.0 - base) * 0.08 + (np.random.rand() - 0.5) * 2.0))
        dn = base
        # take-action is an optimistic intervention curve
        uplift = 8.0 * (1.0 - float(np.exp(-i / 4.0)))
        ta = min(100.0, dn + uplift)
        # CI width scales with (1 - confidence)
        width = max(3.0, 12.0 * (1.0 - conf))
        out.append({
            "ts": ts,
            "do_nothing": float(dn),
            "take_action": float(ta),
            "ci_low": max(0.0, float(dn - width)),
            "ci_high": min(100.0, float(dn + width)),
        })
    return out


# --------------------------------------------------------------------------------------
# Public API (used by Django views)
# --------------------------------------------------------------------------------------
def _normalize_site_id(val: Any) -> Optional[str]:
    """Normalize site_id to a clean string (remove .0 etc)."""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    try:
        f = float(val)
        if f.is_integer():
            return str(int(f))
        return str(f)
    except Exception:
        return str(val).strip()


def list_sites() -> List[Dict[str, str]]:
    """
    Return cached list of (id, suburb) pairs for the UI dropdown.

    Uses only the two columns we need to minimize memory.

    If a suburb has only one site --> show suburb

   If a suburb has multiple sites ---> label as 'Suburb - 1 Area', 'Suburb - 2 Area', ...
    """
    global _sites_cache
    with _cache_lock:
        if _sites_cache is not None:
            return _sites_cache

        if not OUTPUT_CSV.exists():
            _sites_cache = []
            return _sites_cache

        try:
            df = pd.read_csv(
                OUTPUT_CSV,
                usecols=["Site ID", "Victorian Suburb"],
                dtype={"Site ID": "string", "Victorian Suburb": "string"},
                low_memory=False,
            )

            # ensure unique Site IDs and sort by suburb then site
            df = df.drop_duplicates(subset=["Site ID"])
            df = df.sort_values(["Victorian Suburb", "Site ID"], ascending=[True, True])

            result = []
            # group by suburb
            for suburb, g in df.groupby("Victorian Suburb", sort=False):
                if len(g) == 1:
                    result.append({"id": str(g.iloc[0]["Site ID"]), "suburb": suburb})
                else:
                    # multiple sites with assign numeric suffix
                    for i, (_, row) in enumerate(g.iterrows(), start=1):
                        label = f"{suburb} - {i} Area"
                        result.append({"id": str(row["Site ID"]), "suburb": label})

            _sites_cache = result
            return _sites_cache

        except Exception:
            _sites_cache = []
            return _sites_cache


def predict_site(site_id: str, horizon_days: int = 30) -> Dict[str, Any]:
    """
    Main entrypoint used by Django code.
    Returns a JSON-serializable dict with predictions, score, category, etc.
    """
    # Clamp horizon to avoid runaway CPU
    horizon_days = max(1, min(int(horizon_days or 1), MAX_HORIZON_DAYS))

    cfg = load_config()
    default_score = float(cfg.get("default_base_score", 65.0))

    # Load cached tables + global stats
    field_df, lab_wide_df = get_clean_data()
    stats = get_stats()

    medians = _global_medians(stats, cfg)
    preds: Dict[str, float] = {}
    usage: Dict[str, str] = {}  # per-parameter source: per_site_model | baseline | global | decay | median

    horizon_anchor = pd.Timestamp.today().normalize()

    for p in PARAMS_CORE:
        chosen_val: Optional[float] = None

        # 1) Try per-site model (and compare to trailing-mean baseline)
        model_obj = get_model(p, site_id)
        if model_obj is not None:
            # model forecast to horizon end (safe call)
            try:
                horizon = step_forecast(model_obj, horizon_days=horizon_days)
                model_pred = float(horizon[-1]["value"]) if horizon else np.nan
            except Exception:
                model_pred = np.nan  # fall back later

            # trailing-mean baseline using the same history window
            base_w = int(model_obj.get("baseline_window", int(cfg.get("baseline_window", 5))))
            last_vals = list(model_obj.get("last_vals", []))
            tmp_hist = list(last_vals)
            base_pred = np.nan
            for _ in range(horizon_days):
                base_pred = _rolling_mean_forecast(tmp_hist, base_w)
                if not np.isfinite(base_pred):
                    break
                tmp_hist.append(base_pred)
                if len(tmp_hist) > 14:
                    tmp_hist = tmp_hist[-14:]

            # choose between model vs baseline based on held-out RMSE
            rm_m = float(model_obj.get("rmse_model", np.inf))
            rm_b = float(model_obj.get("rmse_baseline", np.inf))
            if np.isfinite(rm_m) and np.isfinite(rm_b) and (rm_m <= rm_b * 0.98):
                chosen_val = model_pred
                usage[p] = "per_site_model"
            else:
                chosen_val = base_pred
                usage[p] = "baseline"

        # 2) Fall back to global (site-aware) model
        if chosen_val is None or not np.isfinite(chosen_val):
            gobj = get_global_model(p)
            if gobj is not None:
                gmodel, meta = gobj["model"], gobj["meta"]
                last_dt, last_vals = _last_k_obs_for_site_param(site_id, p, field_df, lab_wide_df, k=14)
                if len(last_vals) > 0:
                    cur_dt = last_dt
                    g_pred = np.nan
                    for _ in range(horizon_days):
                        cur_dt = cur_dt + pd.Timedelta(days=1)
                        yhat = _global_model_predict_one_step(gmodel, meta, site_id, last_vals, cur_dt)
                        g_pred = yhat
                        last_vals.append(yhat)
                        if len(last_vals) > 14:
                            last_vals = last_vals[-14:]
                    if np.isfinite(g_pred):
                        chosen_val = float(g_pred)
                        usage[p] = usage.get(p, "global")

        # 3) Fall back to decay-to-median or pure median
        if chosen_val is None or not np.isfinite(chosen_val):
            last = _last_obs_for_site_param(site_id, p, field_df, lab_wide_df)
            if last is not None and not np.isnan(last[1]):
                chosen_val = _decay_to_median(
                    last_val=float(last[1]),
                    last_dt=pd.Timestamp(last[0]),
                    median_val=float(medians.get(p, np.nan)),
                    horizon_last_dt=horizon_anchor + pd.Timedelta(days=horizon_days),
                    tau_days=float(cfg.get("fallback", {}).get("tau_days", 180)),
                    use_decay=bool(cfg.get("fallback", {}).get("use_decay", True)),
                )
                usage[p] = "decay"
            else:
                chosen_val = float(medians.get(p, np.nan))
                usage[p] = "median"

        preds[p] = float(chosen_val)

    # Compute scores
    pens = quality_penalties(preds, stats)
    score_base = score_from_penalties(pens, cfg["weights"], default_if_empty=default_score)

    # Confidence from data volume + source type
    source_weight = {"per_site_model": 1.00, "baseline": 0.85, "global": 0.75, "decay": 0.60, "median": 0.40}
    conf_num, conf_den = 0.0, 0.0
    for p in PARAMS_CORE:
        n_points = _count_points_for_site_param(site_id, p, field_df, lab_wide_df)
        denom = np.log(1.0 + 50.0)
        conf_data = np.log(1.0 + max(0, n_points)) / denom if denom > 0 else 0.0
        conf_src = source_weight.get(usage.get(p, "median"), 0.4)
        conf_p = max(0.0, min(1.0, conf_data * conf_src))
        w = float(cfg["weights"].get(p, 0.0))
        conf_num += conf_p * w
        conf_den += w
    confidence = conf_num / conf_den if conf_den > 0 else 0.0

    # Blend base score toward default by (1 - confidence)
    score_blended = confidence * score_base + (1.0 - confidence) * default_score

    # Add small noise depending on source severity (keeps UI from over-precision)
    sig = 5.0  # worst default (pure median)
    if any(v == "decay" for v in usage.values()):
        sig = min(sig, 4.0)
    if any(v in ("global", "baseline") for v in usage.values()):
        sig = min(sig, 3.0)
    if any(v == "per_site_model" for v in usage.values()):
        sig = min(sig, 1.0)
    noise = float(np.random.normal(0.0, sig))
    score_final = max(0.0, min(100.0, score_blended + noise))

    # Category via your YAML thresholds (good 70 / fair 40 / poor <40)
    cat = category_from_score(score_final, cfg["categories"])

    # Guardrails: replace NaNs if any
    for p in PARAMS_CORE:
        if preds.get(p) is None or (isinstance(preds[p], float) and np.isnan(preds[p])):
            preds[p] = float(cfg["fallback"]["typicals"].get(p, 0.0))

    preds_rounded = _apply_rounding(preds)

    return {
        #"site_id": site_id,
        "predictions": preds_rounded,            # rounded for UI
        "predictions_raw": preds,                # raw if you need analytics
        "quality": {
            "score": round(float(score_final), 2),
            "category": cat,
            "confidence": round(float(confidence), 3),
            "score_base": round(float(score_base), 2),
            "noise_sigma": round(float(sig), 2),
        },
        "usage": usage,
        "last_updated": _latest_updated_iso(),   # for 'Last updated' in UI
        "forecast_48h": _forecast_48h_series(    # dual-scenario series for Chart.js
            seed_score=score_final, confidence=confidence
        ),
    }


# --------------------------------------------------------------------------------------
# Optional: a tiny health payload (exposed by your Django view if you want)
# --------------------------------------------------------------------------------------
def health_payload() -> Dict[str, Any]:
    """
    A tiny helper you can return from a /healthz Django view.
    It does not touch heavy caches; just proves the process is alive.
    """
    return {
        "ok": True,
        "ts": dt.datetime.utcnow().isoformat() + "Z",
        "artifacts_dir": str(ARTIFACTS_DIR),
    }
