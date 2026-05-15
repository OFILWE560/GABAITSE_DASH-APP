# AI-Solutions IIS Dashboard
### CET333 – Ofilwe Gabaitse

A fully functional, interactive Python Dash analytics dashboard that visualises
synthetic IIS log data for the AI-Solutions sales and marketing team.

---

## Quick Start

```bash
# 1. Install dependencies (Anaconda environment recommended)
pip install -r requirements.txt

# 2. Generate the synthetic dataset (run once)
python generate_data.py

# 3. Launch the dashboard
python app.py

# 4. Open in browser
#    http://127.0.0.1:8050
```

---

## Demo Login Credentials (FR7)

| Username    | Password       | Role  | Access                              |
|-------------|----------------|-------|-------------------------------------|
| `analyst`   | `analyst123`   | Admin | All pages + Admin panel             |
| `sales`     | `sales123`     | Basic | Overview, Geo, Time, Demo, Logs     |
| `marketing` | `marketing123` | Basic | Overview, Geo, Time, Demo, Logs     |

---

## Project Structure

```
dash_app/
├── app.py              # Main Dash application & all callbacks
├── auth.py             # Authentication & role-based access (FR7)
├── charts.py           # All Plotly figure builders
├── data_engine.py      # Data loading, KPI computation, helpers (FR1, FR6)
├── generate_data.py    # Synthetic IIS CSV generator (run once)
├── requirements.txt
├── README.md
└── data/
    └── iis_logs.csv    # Generated synthetic log data (8,000 rows)
```

---

## Requirements Coverage

| Requirement | Description                                          | Status |
|-------------|------------------------------------------------------|--------|
| FR1         | Python Dash app loading CSV with Pandas              | ✅     |
| FR2         | Geographic KPI distribution charts                   | ✅     |
| FR3         | Dropdown filters – KPI × geographic level × time     | ✅     |
| FR4         | Time-period distribution (daypart/hour/day/month)    | ✅     |
| FR5         | Paginated, filterable log table                      | ✅     |
| FR6         | Summary statistics (avg, std dev, error rate etc.)   | ✅     |
| FR7         | Role-based access control + login authentication     | ✅     |
| NR1         | Responsive, no horizontal scroll                     | ✅     |
| NR2         | Fast load (local Pandas, no network calls)           | ✅     |
| NR3         | Professional dark-theme dashboard design             | ✅     |
| NR4         | Open-source libraries only, well-commented code      | ✅     |
| NR5         | Synthetic data only, local execution                 | ✅     |
| NR6         | Demographic KPI analysis (age group × gender)        | ✅     |

---

## Dashboard Pages

- **Overview** – KPI stat cards, endpoint bar, HTTP status pie, hourly line, daily volume
- **Geographic** – Bar / treemap / pie for KPI by country or continent (FR2/FR3)
- **Time Periods** – KPI distributions by daypart, hour, day of week, or month (FR4)
- **Demographics** – KPI by age group and gender, plus gender × age heatmap (NR6)
- **Log Table** – Filterable, sortable, paginated log entries (FR5)
- **Admin** – Extended stats, user management, dataset info (Admin only – FR7)

---

## Technologies

- **Python 3.x** via Anaconda
- **Plotly Dash** – web framework
- **Pandas / NumPy** – data processing
- **Faker** – synthetic data generation
- **dash-bootstrap-components** – layout utilities
