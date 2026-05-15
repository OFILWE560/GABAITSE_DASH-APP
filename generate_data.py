"""
generate_data.py
────────────────
Generates a synthetic IIS-style log CSV for the AI-Solutions dashboard.
Run once:  python generate_data.py
Produces:  data/iis_logs.csv
"""

import os, random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from faker import Faker

fake = Faker()
random.seed(42)
np.random.seed(42)

# ── Configuration ─────────────────────────────────────────────────────────────
N_ROWS = 8_000
OUTPUT_DIR = "data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "iis_logs.csv")

# Endpoints with weighted probability
ENDPOINTS = {
    "/":                        0.30,
    "/schedule-demo":           0.18,
    "/ai-assistant":            0.22,
    "/events":                  0.12,
    "/pricing":                 0.10,
    "/about":                   0.05,
    "/contact":                 0.03,
}

# Countries with realistic weights
COUNTRIES = {
    "Botswana":        0.08,
    "South Africa":    0.12,
    "Zimbabwe":        0.06,
    "Zambia":          0.05,
    "Nigeria":         0.09,
    "Kenya":           0.07,
    "United Kingdom":  0.14,
    "United States":   0.16,
    "Germany":         0.07,
    "India":           0.09,
    "Australia":       0.04,
    "Brazil":          0.03,
}

COUNTRY_CONTINENT = {
    "Botswana": "Africa", "South Africa": "Africa", "Zimbabwe": "Africa",
    "Zambia": "Africa", "Nigeria": "Africa", "Kenya": "Africa",
    "United Kingdom": "Europe", "Germany": "Europe",
    "United States": "North America",
    "India": "Asia",
    "Australia": "Oceania",
    "Brazil": "South America",
}

HTTP_STATUS = {200: 0.72, 301: 0.06, 302: 0.04, 404: 0.10, 500: 0.05, 403: 0.03}

AGE_GROUPS   = ["18-24", "25-34", "35-44", "45-54", "55+"]
GENDERS      = ["Male", "Female", "Non-binary"]
METHODS      = ["GET", "POST"]
USER_AGENTS  = [
    "Chrome/Windows", "Chrome/Mac", "Firefox/Windows",
    "Safari/Mac", "Edge/Windows", "Chrome/Android", "Safari/iOS",
]

# ── Helper generators ─────────────────────────────────────────────────────────
def weighted_choice(mapping):
    keys   = list(mapping.keys())
    weights = list(mapping.values())
    return random.choices(keys, weights=weights, k=1)[0]

def random_timestamp(start, end):
    delta = end - start
    rand_sec = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=rand_sec)

def daypart(hour):
    if   5  <= hour < 12: return "Morning"
    elif 12 <= hour < 17: return "Afternoon"
    elif 17 <= hour < 21: return "Evening"
    else:                  return "Night"

# ── Generate rows ─────────────────────────────────────────────────────────────
start_dt = datetime(2025, 1, 1)
end_dt   = datetime(2025, 3, 31, 23, 59, 59)

records = []
for _ in range(N_ROWS):
    ts        = random_timestamp(start_dt, end_dt)
    country   = weighted_choice(COUNTRIES)
    endpoint  = weighted_choice(ENDPOINTS)
    status    = weighted_choice(HTTP_STATUS)
    method    = random.choices(METHODS, weights=[0.75, 0.25])[0]
    age_group = random.choices(AGE_GROUPS,  weights=[0.22, 0.30, 0.24, 0.14, 0.10])[0]
    gender    = random.choices(GENDERS,     weights=[0.48, 0.46, 0.06])[0]
    bytes_sent = random.randint(512, 65_536)
    duration_ms = random.randint(50, 3_000)

    records.append({
        "timestamp":    ts,
        "date":         ts.date(),
        "hour":         ts.hour,
        "daypart":      daypart(ts.hour),
        "day_of_week":  ts.strftime("%A"),
        "month":        ts.strftime("%B"),
        "month_num":    ts.month,
        "country":      country,
        "continent":    COUNTRY_CONTINENT[country],
        "endpoint":     endpoint,
        "method":       method,
        "status_code":  status,
        "bytes_sent":   bytes_sent,
        "duration_ms":  duration_ms,
        "age_group":    age_group,
        "gender":       gender,
        "ip_address":   fake.ipv4_public(),
        "user_agent":   random.choice(USER_AGENTS),
    })

df = pd.DataFrame(records).sort_values("timestamp").reset_index(drop=True)

os.makedirs(OUTPUT_DIR, exist_ok=True)
df.to_csv(OUTPUT_FILE, index=False)
print(f"✓ Generated {len(df):,} rows → {OUTPUT_FILE}")
print(df.dtypes)
print(df.head(3))
