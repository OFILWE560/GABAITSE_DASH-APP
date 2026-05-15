"""
data_engine.py
──────────────
Loads the CSV, computes all KPIs, and exposes helper functions used
by the chart callbacks.  Centralises all Pandas logic (FR1, FR6).
"""

import pandas as pd
import numpy as np
from pathlib import Path

CSV_PATH = Path(__file__).parent / "data" / "iis_logs.csv"

# ── Load & cache ───────────────────────────────────────────────────────────────
def load_data() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH, parse_dates=["timestamp"])
    df["date"] = pd.to_datetime(df["date"])
    return df

# Singleton – loaded once at startup
_df: pd.DataFrame = load_data()

def get_raw() -> pd.DataFrame:
    return _df.copy()

# ── KPI definitions ────────────────────────────────────────────────────────────
KPI_DEFINITIONS = {
    "Total Requests":       {"col": None,               "label": "Total Requests"},
    "Demo Requests":        {"col": "/schedule-demo",   "label": "Demo Requests"},
    "AI Assistant Hits":    {"col": "/ai-assistant",    "label": "AI Assistant Hits"},
    "Homepage Visits":      {"col": "/",                "label": "Homepage Visits"},
    "Events Page Visits":   {"col": "/events",          "label": "Events Page Visits"},
    "Pricing Page Visits":  {"col": "/pricing",         "label": "Pricing Page Visits"},
}

KPI_OPTIONS = [{"label": k, "value": k} for k in KPI_DEFINITIONS]

def filter_kpi(df: pd.DataFrame, kpi: str) -> pd.DataFrame:
    """Return rows matching the selected KPI."""
    defn = KPI_DEFINITIONS.get(kpi, {})
    endpoint = defn.get("col")
    if endpoint is None:
        return df          # Total Requests → all rows
    return df[df["endpoint"] == endpoint]

# ── Geographic helpers ─────────────────────────────────────────────────────────
GEO_OPTIONS = [
    {"label": "Country",   "value": "country"},
    {"label": "Continent", "value": "continent"},
]

def geo_distribution(df: pd.DataFrame, kpi: str, geo_level: str) -> pd.DataFrame:
    """Count of KPI hits grouped by geo_level, sorted descending."""
    subset = filter_kpi(df, kpi)
    return (
        subset.groupby(geo_level)
              .size()
              .reset_index(name="count")
              .sort_values("count", ascending=False)
    )

# ── Time-period helpers ────────────────────────────────────────────────────────
TIME_PERIOD_OPTIONS = [
    {"label": "Time of Day (Daypart)", "value": "daypart"},
    {"label": "Hour of Day",           "value": "hour"},
    {"label": "Day of Week",           "value": "day_of_week"},
    {"label": "Month",                 "value": "month"},
]

DAYPART_ORDER    = ["Morning", "Afternoon", "Evening", "Night"]
DOW_ORDER        = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTH_ORDER      = ["January","February","March","April","May","June",
                    "July","August","September","October","November","December"]

_ORDER_MAP = {
    "daypart":     DAYPART_ORDER,
    "day_of_week": DOW_ORDER,
    "month":       MONTH_ORDER,
}

def time_distribution(df: pd.DataFrame, kpi: str, time_dim: str) -> pd.DataFrame:
    subset = filter_kpi(df, kpi)
    result = (
        subset.groupby(time_dim)
              .size()
              .reset_index(name="count")
    )
    order = _ORDER_MAP.get(time_dim)
    if order:
        result[time_dim] = pd.Categorical(result[time_dim], categories=order, ordered=True)
        result = result.sort_values(time_dim)
    else:
        result = result.sort_values(time_dim)
    return result

# ── Demographic helpers ────────────────────────────────────────────────────────
DEMO_OPTIONS = [
    {"label": "Age Group", "value": "age_group"},
    {"label": "Gender",    "value": "gender"},
]

AGE_ORDER = ["18-24", "25-34", "35-44", "45-54", "55+"]

def demographic_distribution(df: pd.DataFrame, kpi: str, demo_dim: str) -> pd.DataFrame:
    subset = filter_kpi(df, kpi)
    result = (
        subset.groupby(demo_dim)
              .size()
              .reset_index(name="count")
              .sort_values("count", ascending=False)
    )
    if demo_dim == "age_group":
        result[demo_dim] = pd.Categorical(result[demo_dim], categories=AGE_ORDER, ordered=True)
        result = result.sort_values(demo_dim)
    return result

# ── Summary statistics (FR6) ───────────────────────────────────────────────────
def summary_stats(df: pd.DataFrame) -> dict:
    daily = df.groupby("date").size()
    total         = len(df)
    demo_hits     = len(df[df["endpoint"] == "/schedule-demo"])
    ai_hits       = len(df[df["endpoint"] == "/ai-assistant"])
    avg_daily     = daily.mean()
    std_daily     = daily.std()
    error_rate    = len(df[df["status_code"] >= 400]) / total * 100
    avg_duration  = df["duration_ms"].mean()

    return {
        "total_requests":  total,
        "demo_requests":   demo_hits,
        "ai_hits":         ai_hits,
        "avg_daily":       round(avg_daily,  1),
        "std_daily":       round(std_daily,  1),
        "error_rate":      round(error_rate, 2),
        "avg_duration_ms": round(avg_duration, 1),
        "unique_countries": df["country"].nunique(),
    }

# ── Endpoint overview ──────────────────────────────────────────────────────────
def endpoint_counts(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("endpoint")
          .size()
          .reset_index(name="count")
          .sort_values("count", ascending=False)
    )

def status_code_counts(df: pd.DataFrame) -> pd.DataFrame:
    df2 = df.copy()
    df2["status_str"] = df2["status_code"].astype(str)
    return (
        df2.groupby("status_str")
           .size()
           .reset_index(name="count")
           .sort_values("count", ascending=False)
    )

def hourly_traffic(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("hour")
          .size()
          .reset_index(name="count")
          .sort_values("hour")
    )

def daily_volume(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("date")
          .size()
          .reset_index(name="count")
          .sort_values("date")
    )

# ── Log table (FR5) ────────────────────────────────────────────────────────────
LOG_COLS = ["timestamp", "country", "endpoint", "method",
            "status_code", "bytes_sent", "duration_ms", "age_group", "gender"]

def get_log_table(df: pd.DataFrame, page: int = 0, page_size: int = 15):
    subset = df[LOG_COLS].sort_values("timestamp", ascending=False)
    start  = page * page_size
    return subset.iloc[start : start + page_size], len(subset)
