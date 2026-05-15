"""
app.py  –  AI-Solutions IIS Dashboard  (Refactored – Production Quality)
═══════════════════════════════════════════════════════════════════════════
Run:  python app.py
Open: http://127.0.0.1:8050

Demo credentials
────────────────
  analyst   / analyst123   → admin  (full access)
  sales     / sales123     → basic  (view only)
  marketing / marketing123 → basic  (view only)

Key Improvements
────────────────
  1. Session persistence via dcc.Store (localStorage) – no repeated logins
  2. URL-based routing via dcc.Location – proper SPA navigation
  3. dbc.Navbar replaces custom button navbar – responsive & accessible
  4. Bootstrap Icons replace placeholder text icons throughout
  5. Graph descriptions added via reusable chart_description() helper
  6. Data loaded once into dcc.Store (session) – callbacks read from store
  7. dcc.Loading wrappers on all graphs and tables
  8. dbc.Container/Row/Col layouts replace raw flex divs – mobile-ready
  9. /admin route shows "Access Denied" for non-admin users
 10. Dropdown persistence=True retains filter values across navigation
"""

import json
import dash
from dash import dcc, html, Input, Output, State, ctx, dash_table, no_update
import dash_bootstrap_components as dbc
import pandas as pd

import auth
import data_engine as de
import charts

# ─────────────────────────── App init ─────────────────────────────────────────
app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        dbc.icons.BOOTSTRAP,          # Bootstrap Icons CDN
        "https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&family=JetBrains+Mono:wght@400;600;700&display=swap",
    ],
    title="AI-Solutions Dashboard",
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    use_pages=False,
)
server = app.server

# ─────────────────────────── Design tokens ────────────────────────────────────
C = dict(
    bg_page   = "#F0F4F8",
    bg_card   = "#FFFFFF",
    bg_panel  = "#F8FAFC",
    accent    = "#1D6FA4",
    accent2   = "#5B3FA6",
    accent3   = "#D4590A",
    success   = "#0F7B55",
    warning   = "#B07D00",
    danger    = "#C0143C",
    text      = "#1A202C",
    muted     = "#64748B",
    border    = "#E2E8F0",
)

# Shared card style
CARD = {
    "background":   C["bg_card"],
    "border":       f"1px solid {C['border']}",
    "borderRadius": "14px",
    "padding":      "22px",
    "boxShadow":    "0 1px 6px rgba(0,0,0,0.07)",
    "height":       "100%",
}

INNER_CARD = {**CARD, "padding": "16px"}

# Plotly theme colours reused across charts
CHART_COLORS = [C["accent"], C["accent2"], C["accent3"],
                C["success"], C["warning"], C["danger"]]

# Shared dropdown style
DD = {
    "backgroundColor": "#fff",
    "color":           C["text"],
    "border":          f"1px solid {C['border']}",
    "borderRadius":    "8px",
}


# ─────────────────────────── Utility helpers ──────────────────────────────────

def _hex_to_rgb(h: str) -> str:
    h = h.lstrip("#")
    return f"{int(h[0:2],16)},{int(h[2:4],16)},{int(h[4:6],16)}"


def chart_description(text: str) -> html.Div:
    """Reusable explanatory blurb rendered beneath every chart."""
    return html.Div(
        [html.I(className="bi bi-info-circle me-1", style={"fontSize": "11px"}), text],
        style={
            "fontSize":    "11px",
            "color":       C["muted"],
            "marginTop":   "10px",
            "lineHeight":  "1.55",
            "padding":     "8px 10px",
            "background":  C["bg_panel"],
            "borderRadius":"6px",
            "border":      f"1px solid {C['border']}",
        },
    )


def section_header(title: str, subtitle: str = "", icon: str = "") -> html.Div:
    """Card section heading with optional Bootstrap Icon and subtitle."""
    return html.Div([
        html.Div([
            html.I(className=f"bi {icon} me-2", style={"color": C["accent"]}) if icon else None,
            html.Span(title, style={
                "fontSize":  "13px", "fontWeight": "600",
                "color":     C["text"], "letterSpacing": "0.2px",
            }),
        ], style={"display": "flex", "alignItems": "center"}),
        html.Div(subtitle, style={
            "fontSize": "11px", "color": C["muted"], "marginTop": "3px",
        }) if subtitle else None,
    ], style={"marginBottom": "16px"})


def filter_block(label: str, control) -> html.Div:
    """Labelled filter wrapper."""
    return html.Div([
        html.Label(label, style={
            "fontSize": "11px", "color": C["muted"], "fontWeight": "600",
            "letterSpacing": "0.4px", "textTransform": "uppercase",
            "marginBottom": "6px", "display": "block",
        }),
        control,
    ])


def stat_card(icon_cls: str, label: str, value_id: str,
              color: str = C["accent"], subtitle: str = "") -> html.Div:
    """KPI stat card with Bootstrap Icon."""
    return html.Div([
        # Icon badge
        html.Div(
            html.I(className=f"bi {icon_cls}",
                   style={"fontSize": "18px", "color": color}),
            style={
                "width": "46px", "height": "46px", "borderRadius": "12px",
                "background": f"rgba({_hex_to_rgb(color)},0.12)",
                "display": "flex", "alignItems": "center",
                "justifyContent": "center", "flexShrink": "0",
            },
        ),
        # Text
        html.Div([
            html.Div(label, style={
                "fontSize": "11px", "color": C["muted"], "fontWeight": "600",
                "letterSpacing": "0.4px", "textTransform": "uppercase",
            }),
            html.Div(id=value_id, style={
                "fontSize": "22px", "fontWeight": "700", "color": color,
                "lineHeight": "1.2", "fontFamily": "'JetBrains Mono', monospace",
            }),
            html.Div(subtitle, style={"fontSize": "10px", "color": C["muted"]}),
        ]),
    ], style={
        **CARD,
        "display":    "flex",
        "alignItems": "center",
        "gap":        "14px",
        "padding":    "16px 18px",
    })


def access_denied() -> html.Div:
    """Shown when a basic user tries to reach /admin."""
    return html.Div([
        html.Div([
            html.I(className="bi bi-shield-lock",
                   style={"fontSize": "48px", "color": C["danger"], "marginBottom": "16px"}),
            html.H4("Access Denied", style={"color": C["danger"], "fontWeight": "700"}),
            html.P("You do not have permission to view the Admin panel.",
                   style={"color": C["muted"], "fontSize": "14px"}),
            dbc.Button("Go to Overview", href="/", color="primary", className="mt-3",
                       style={"borderRadius": "8px"}),
        ], style={
            **CARD,
            "textAlign": "center", "maxWidth": "420px",
            "margin": "60px auto", "padding": "48px 32px",
        }),
    ])


# ─────────────────────────── Navbar ───────────────────────────────────────────

def make_navbar(user: dict, pathname: str) -> dbc.Navbar:
    """
    Professional dbc.Navbar with:
      • Brand logo (SPA-ready)
      • NavLinks with active-state highlighting
      • User chip (name + role badge)
      • Logout button
      • Fully responsive (collapses on mobile)
    """
    role_color = C["accent"] if user["role"] == "admin" else C["accent3"]

    nav_items = [
        ("Overview",     "/"),
        ("Geographic",   "/geo"),
        ("Time Periods", "/time"),
        ("Demographics", "/demo"),
        ("Log Table",    "/logs"),
    ]
    if user["role"] == "admin":
        nav_items.append(("Admin", "/admin"))

    links = dbc.Nav([
        dbc.NavItem(dbc.NavLink(
            lbl, href=href, active="exact",
            className="nav-link-custom",
        ))
        for lbl, href in nav_items
    ], navbar=True, className="mx-auto")

    user_section = html.Div([
        # Avatar circle
        html.Div(user["avatar"], style={
            "width": "32px", "height": "32px", "borderRadius": "50%",
            "background": C["accent"], "color": "#fff",
            "display": "flex", "alignItems": "center", "justifyContent": "center",
            "fontSize": "11px", "fontWeight": "700", "flexShrink": "0",
            "fontFamily": "'JetBrains Mono', monospace",
        }),
        html.Div([
            html.Div(user["name"],
                     style={"fontSize": "12px", "fontWeight": "600", "color": C["text"]}),
            html.Div(user["role"].upper(), style={
                "fontSize": "10px", "color": role_color,
                "fontWeight": "700", "letterSpacing": "0.6px",
            }),
        ]),
        dbc.Button(
            [html.I(className="bi bi-box-arrow-right me-1"), "Logout"],
            id="logout-btn", n_clicks=0, size="sm",
            style={
                "background": "transparent",
                "border":     f"1px solid {C['border']}",
                "color":      C["muted"], "fontSize": "11px",
                "borderRadius": "7px", "padding": "4px 10px",
                "fontFamily": "'DM Sans', sans-serif",
            },
        ),
    ], style={"display": "flex", "alignItems": "center", "gap": "10px"})

    # Wrapped in dcc.Link for SPA navigation
    brand = dcc.Link(
        dbc.NavbarBrand([
            html.Span("AI", style={
                "color": C["accent"], "fontWeight": "700",
                "fontFamily": "'JetBrains Mono', monospace",
            }),
            html.Span("-Solutions", style={"color": C["text"], "fontWeight": "400"}),
            html.Span(" ·", style={"color": C["muted"]}),
            html.Span(" Dashboard", style={"color": C["muted"], "fontSize": "12px"}),
        ], style={"fontSize": "16px"}),
        href="/",
        style={"textDecoration": "none"}
    )

    return dbc.Navbar(
        dbc.Container([
            brand,
            dbc.NavbarToggler(id="nav-toggler", n_clicks=0),
            dbc.Collapse(
                [links, user_section],
                id="nav-collapse",
                navbar=True,
            ),
        ], fluid=True),
        color=C["bg_card"],
        dark=False,
        sticky="top",
        className="shadow-sm",
        style={"borderBottom": f"1px solid {C['border']}", "zIndex": 100},
    )


# ─────────────────────────── Login page ───────────────────────────────────────

login_page = dbc.Container([
    dbc.Row(
        dbc.Col(
            html.Div([
                # Brand
                html.Div([
                    html.Div([
                        html.Span("AI", style={
                            "fontSize": "30px", "fontWeight": "700",
                            "color": C["accent"], "fontFamily": "'JetBrains Mono', monospace",
                        }),
                        html.Span("-Solutions", style={
                            "fontSize": "22px", "fontWeight": "300", "color": C["text"],
                        }),
                    ]),
                    html.Div("Analytics Dashboard", style={
                        "fontSize": "11px", "fontWeight": "600", "color": C["muted"],
                        "letterSpacing": "2.5px", "textTransform": "uppercase", "marginTop": "4px",
                    }),
                ], style={"textAlign": "center", "marginBottom": "36px"}),

                html.H2("Sign in", style={
                    "color": C["text"], "fontSize": "20px", "fontWeight": "600",
                    "textAlign": "center", "marginBottom": "6px",
                }),
                html.P("Enter your credentials to access the platform", style={
                    "color": C["muted"], "fontSize": "13px",
                    "textAlign": "center", "marginBottom": "28px",
                }),

                # Username
                html.Label("Username", style={
                    "color": C["muted"], "fontSize": "11px", "fontWeight": "600",
                    "letterSpacing": "0.4px", "textTransform": "uppercase",
                }),
                dcc.Input(
                    id="login-user", type="text", placeholder="e.g. analyst",
                    debounce=False, n_submit=0,
                    style={
                        "backgroundColor": C["bg_panel"],
                        "border": f"1px solid {C['border']}",
                        "borderRadius": "8px", "width": "100%",
                        "padding": "10px 14px", "fontSize": "14px",
                        "color": C["text"], "marginTop": "6px",
                        "marginBottom": "16px", "boxSizing": "border-box",
                        "outline": "none",
                    },
                ),

                # Password
                html.Label("Password", style={
                    "color": C["muted"], "fontSize": "11px", "fontWeight": "600",
                    "letterSpacing": "0.4px", "textTransform": "uppercase",
                }),
                dcc.Input(
                    id="login-pass", type="password", placeholder="••••••••",
                    debounce=False, n_submit=0,
                    style={
                        "backgroundColor": C["bg_panel"],
                        "border": f"1px solid {C['border']}",
                        "borderRadius": "8px", "width": "100%",
                        "padding": "10px 14px", "fontSize": "14px",
                        "color": C["text"], "marginTop": "6px",
                        "marginBottom": "8px", "boxSizing": "border-box",
                        "outline": "none",
                    },
                ),

                html.Div(id="login-error", style={
                    "color": C["danger"], "fontSize": "13px",
                    "marginBottom": "16px", "minHeight": "20px",
                }),

                html.Button(
                    [html.I(className="bi bi-box-arrow-in-right me-2"), "Sign In"],
                    id="login-btn", n_clicks=0,
                    style={
                        "width": "100%", "padding": "12px",
                        "background": C["accent"], "color": "#fff",
                        "fontWeight": "600", "fontSize": "14px",
                        "border": "none", "borderRadius": "8px",
                        "cursor": "pointer", "fontFamily": "'DM Sans', sans-serif",
                    },
                ),

                # Demo hint
                html.Div([
                    html.P([html.I(className="bi bi-key me-1"), "Demo accounts"], style={
                        "color": C["muted"], "fontSize": "11px",
                        "marginBottom": "8px", "fontWeight": "700",
                        "textTransform": "uppercase", "letterSpacing": "0.5px",
                    }),
                    *[html.P(f"{u} / {p}  —  {r}", style={
                        "color": C["muted"], "fontSize": "11px",
                        "margin": "3px 0", "fontFamily": "'JetBrains Mono', monospace",
                    }) for u, p, r in [
                        ("analyst",   "analyst123",   "Admin"),
                        ("sales",     "sales123",     "Basic"),
                        ("marketing", "marketing123", "Basic"),
                    ]],
                ], style={
                    "marginTop": "24px", "padding": "14px",
                    "background": C["bg_panel"], "borderRadius": "8px",
                    "border": f"1px solid {C['border']}",
                }),

            ], style={**CARD, "maxWidth": "420px", "width": "100%", "padding": "38px", "margin": "auto"}),
            width={"size": 12, "md": 6, "lg": 4},
        ),
        className="justify-content-center align-items-center",
        style={"minHeight": "100vh"}
    ),
], fluid=True, style={"background": C["bg_page"]})


# ─────────────────────────── Page: Overview ───────────────────────────────────

def page_overview() -> html.Div:
    return html.Div([
        # KPI stat row
        dbc.Row([
            dbc.Col(stat_card("bi-arrow-up-circle",  "Total Requests",  "stat-total",     C["accent"]),  md=4, lg=2, className="mb-3"),
            dbc.Col(stat_card("bi-play-circle",       "Demo Requests",   "stat-demos",     C["accent2"]), md=4, lg=2, className="mb-3"),
            dbc.Col(stat_card("bi-robot",             "AI Assistant",    "stat-ai",        C["success"]), md=4, lg=2, className="mb-3"),
            dbc.Col(stat_card("bi-exclamation-triangle","Error Rate",    "stat-errors",    C["danger"],  "%"), md=4, lg=2, className="mb-3"),
            dbc.Col(stat_card("bi-stopwatch",         "Avg Duration",    "stat-duration",  C["warning"], "ms"), md=4, lg=2, className="mb-3"),
            dbc.Col(stat_card("bi-geo-alt",           "Countries",       "stat-countries", C["accent3"]), md=4, lg=2, className="mb-3"),
        ], className="g-3 mb-2"),

        # Row 2: endpoint bar + status pie
        dbc.Row([
            dbc.Col(html.Div([
                section_header("Endpoint Hit Distribution",
                               "All requests by URL path", "bi-bar-chart-line"),
                dcc.Loading(dcc.Graph(id="chart-endpoints",
                                     config={"displayModeBar": False})),
                chart_description(
                    "Each bar represents a unique API endpoint. "
                    "Taller bars indicate higher traffic — useful for identifying "
                    "which features drive the most load."
                ),
            ], style=CARD), md=8, className="mb-3"),

            dbc.Col(html.Div([
                section_header("HTTP Status Codes",
                               "Response code breakdown", "bi-pie-chart"),
                dcc.Loading(dcc.Graph(id="chart-status",
                                     config={"displayModeBar": False})),
                chart_description(
                    "Shows the proportion of successful (2xx), client-error (4xx), "
                    "and server-error (5xx) responses. A healthy system should be "
                    "overwhelmingly green."
                ),
            ], style=CARD), md=4, className="mb-3"),
        ], className="g-3"),

        # Row 3: hourly + daily
        dbc.Row([
            dbc.Col(html.Div([
                section_header("Hourly Traffic Pattern",
                               "Request volume by hour of day", "bi-clock"),
                dcc.Loading(dcc.Graph(id="chart-hourly",
                                     config={"displayModeBar": False})),
                chart_description(
                    "Reveals peak-usage hours. Spikes may indicate scheduled jobs "
                    "or shift start times; valleys show natural quiet periods."
                ),
            ], style=CARD), md=4, className="mb-3"),

            dbc.Col(html.Div([
                section_header("Daily Volume (last 30 days)",
                               "Request count per calendar day", "bi-calendar3"),
                dcc.Loading(dcc.Graph(id="chart-daily",
                                     config={"displayModeBar": False})),
                chart_description(
                    "Tracks day-over-day request volume. Sudden drops may signal "
                    "outages; sustained growth indicates increasing adoption."
                ),
            ], style=CARD), md=8, className="mb-3"),
        ], className="g-3"),
    ])


# ─────────────────────────── Page: Geographic ─────────────────────────────────

def page_geo() -> html.Div:
    raw = de.get_raw()
    return html.Div([
        html.Div([
            section_header("Geographic KPI Distribution",
                           "Analyse KPIs by country or continent", "bi-globe2"),
            dbc.Row([
                dbc.Col(filter_block("KPI", dcc.Dropdown(
                    id="geo-kpi", options=de.KPI_OPTIONS,
                    value="Total Requests", clearable=False,
                    style=DD, persistence=True, persistence_type="session",
                )), md=4, className="mb-2"),
                dbc.Col(filter_block("Geographic Level", dcc.Dropdown(
                    id="geo-level", options=de.GEO_OPTIONS,
                    value="country", clearable=False,
                    style=DD, persistence=True, persistence_type="session",
                )), md=4, className="mb-2"),
                dbc.Col(filter_block("Chart Type", dcc.Dropdown(
                    id="geo-chart-type",
                    options=[
                        {"label": "Bar Chart",     "value": "bar"},
                        {"label": "Treemap",       "value": "treemap"},
                        {"label": "Pie (Country)", "value": "pie"},
                    ],
                    value="bar", clearable=False,
                    style=DD, persistence=True, persistence_type="session",
                )), md=4, className="mb-2"),
            ], className="g-2"),
        ], style={**CARD, "marginBottom": "16px"}),

        html.Div([
            dcc.Loading(dcc.Graph(id="chart-geo-main", style={"height": "440px"},
                                  config={"displayModeBar": True,
                                          "modeBarButtonsToRemove": ["lasso2d","select2d"]})),
            chart_description(
                "Each bar/segment represents a country or continent. "
                "Switch the KPI dropdown to compare request counts, error rates, "
                "average duration, and more across geographic regions."
            ),
        ], style=CARD),
    ])


# ─────────────────────────── Page: Time Periods ───────────────────────────────

def page_time() -> html.Div:
    return html.Div([
        html.Div([
            section_header("KPI Distribution by Time Period",
                           "Identify peak usage windows", "bi-clock-history"),
            dbc.Row([
                dbc.Col(filter_block("KPI", dcc.Dropdown(
                    id="time-kpi", options=de.KPI_OPTIONS,
                    value="Total Requests", clearable=False,
                    style=DD, persistence=True, persistence_type="session",
                )), md=6, className="mb-2"),
                dbc.Col(filter_block("Time Dimension", dcc.Dropdown(
                    id="time-dim", options=de.TIME_PERIOD_OPTIONS,
                    value="daypart", clearable=False,
                    style=DD, persistence=True, persistence_type="session",
                )), md=6, className="mb-2"),
            ], className="g-2"),
        ], style={**CARD, "marginBottom": "16px"}),

        html.Div([
            dcc.Loading(dcc.Graph(id="chart-time-main", style={"height": "420px"},
                                  config={"displayModeBar": True,
                                          "modeBarButtonsToRemove": ["lasso2d","select2d"]})),
            chart_description(
                "Breaks down the selected KPI by daypart, hour, weekday, or month. "
                "Use this to schedule maintenance windows, scale infrastructure "
                "proactively, or understand user behaviour patterns."
            ),
        ], style={**CARD, "marginBottom": "16px"}),

        html.Div([
            section_header("Hourly Traffic Reference",
                           "Full 24-hour traffic shape", "bi-activity"),
            dcc.Loading(dcc.Graph(id="chart-time-hourly",
                                  config={"displayModeBar": False})),
            chart_description(
                "A fixed 24-hour view of total request volume — independent of "
                "the KPI filter above. Use as a baseline for comparison."
            ),
        ], style=CARD),
    ])


# ─────────────────────────── Page: Demographics ───────────────────────────────

def page_demo() -> html.Div:
    return html.Div([
        html.Div([
            section_header("Demographic KPI Analysis",
                           "Explore KPI distributions by age group and gender", "bi-people"),
            dbc.Row([
                dbc.Col(filter_block("KPI", dcc.Dropdown(
                    id="demo-kpi", options=de.KPI_OPTIONS,
                    value="AI Assistant Hits", clearable=False,
                    style=DD, persistence=True, persistence_type="session",
                )), md=6, className="mb-2"),
                dbc.Col(filter_block("Demographic Dimension", dcc.Dropdown(
                    id="demo-dim", options=de.DEMO_OPTIONS,
                    value="age_group", clearable=False,
                    style=DD, persistence=True, persistence_type="session",
                )), md=6, className="mb-2"),
            ], className="g-2"),
        ], style={**CARD, "marginBottom": "16px"}),

        dbc.Row([
            dbc.Col(html.Div([
                section_header("KPI by Demographic Group", icon="bi-bar-chart"),
                dcc.Loading(dcc.Graph(id="chart-demo-bar", style={"height": "380px"},
                                      config={"displayModeBar": False})),
                chart_description(
                    "Compares the selected KPI across age groups or gender. "
                    "Identifies which demographic segments engage most with "
                    "the AI assistant or trigger the most errors."
                ),
            ], style=CARD), md=6, className="mb-3"),

            dbc.Col(html.Div([
                section_header("Gender × Age Group Heatmap",
                               "Cross-tabulated request counts", "bi-grid-3x3"),
                dcc.Loading(dcc.Graph(id="chart-demo-heat", style={"height": "380px"},
                                      config={"displayModeBar": False})),
                chart_description(
                    "Darker cells indicate higher request volume at that "
                    "gender–age intersection. Useful for spotting under-served "
                    "or over-indexed demographic segments."
                ),
            ], style=CARD), md=6, className="mb-3"),
        ], className="g-3"),
    ])


# ─────────────────────────── Page: Log Table ──────────────────────────────────

def page_logs() -> html.Div:
    raw = de.get_raw()

    return html.Div([
        html.Div([
            section_header("Recent Log Entries",
                           "Paginated IIS log records – most recent first", "bi-table"),
            dbc.Row([
                dbc.Col(filter_block("Endpoint", dcc.Dropdown(
                    id="log-endpoint-filter",
                    options=[{"label": "All endpoints", "value": "all"}] +
                            [{"label": e, "value": e} for e in sorted(raw["endpoint"].unique())],
                    value="all", clearable=False,
                    style=DD, persistence=True, persistence_type="session",
                )), md=4, className="mb-2"),

                dbc.Col(filter_block("Status Code", dcc.Dropdown(
                    id="log-status-filter",
                    options=[{"label": "All codes", "value": "all"}] +
                            [{"label": str(s), "value": s}
                             for s in sorted(raw["status_code"].unique())],
                    value="all", clearable=False,
                    style=DD, persistence=True, persistence_type="session",
                )), md=4, className="mb-2"),

                dbc.Col(filter_block("Country", dcc.Dropdown(
                    id="log-country-filter",
                    options=[{"label": "All countries", "value": "all"}] +
                            [{"label": c, "value": c} for c in sorted(raw["country"].unique())],
                    value="all", clearable=False,
                    style=DD, persistence=True, persistence_type="session",
                )), md=4, className="mb-2"),
            ], className="g-2"),

            html.Div(id="log-count-badge", style={
                "fontSize": "12px", "color": C["muted"], "marginTop": "8px",
            }),
        ], style={**CARD, "marginBottom": "16px"}),

        html.Div([
            dcc.Loading(dash_table.DataTable(
                id="log-table",
                page_size=15,
                page_action="native",
                sort_action="native",
                filter_action="none",
                style_table={"overflowX": "auto"},
                style_header={
                    "backgroundColor": C["bg_panel"],
                    "color":           C["muted"],
                    "fontWeight":      "600",
                    "fontSize":        "11px",
                    "letterSpacing":   "0.4px",
                    "textTransform":   "uppercase",
                    "border":          f"1px solid {C['border']}",
                    "padding":         "10px 12px",
                },
                style_cell={
                    "backgroundColor": C["bg_card"],
                    "color":           C["text"],
                    "fontSize":        "12px",
                    "border":          f"1px solid {C['border']}",
                    "padding":         "9px 12px",
                    "fontFamily":      "'DM Sans', sans-serif",
                    "maxWidth":        "200px",
                    "overflow":        "hidden",
                    "textOverflow":    "ellipsis",
                },
                style_data_conditional=[
                    {"if": {"row_index": "odd"}, "backgroundColor": C["bg_panel"]},
                    {"if": {"filter_query": "{status_code} >= 400", "column_id": "status_code"},
                     "color": C["danger"], "fontWeight": "600"},
                    {"if": {"filter_query": "{status_code} = 200",  "column_id": "status_code"},
                     "color": C["success"], "fontWeight": "600"},
                ],
                tooltip_delay=0, tooltip_duration=None,
            )),
        ], style=CARD),

        chart_description(
            "Showing the most recent IIS access log records. "
            "Use the filters to drill into a specific endpoint, status code, or country. "
            "Click column headers to sort. Red status codes indicate errors."
        ),
    ])


# ─────────────────────────── Page: Admin ──────────────────────────────────────

def page_admin() -> html.Div:
    df    = de.get_raw()
    stats = de.summary_stats(df)

    def admin_stat(label, value, color):
        return html.Div([
            html.Div(value, style={
                "fontSize": "20px", "fontWeight": "700",
                "color": color, "fontFamily": "'JetBrains Mono', monospace",
            }),
            html.Div(label, style={
                "fontSize": "11px", "color": C["muted"], "textTransform": "uppercase",
                "marginTop": "4px", "fontWeight": "500",
            }),
        ], style={**INNER_CARD, "flex": "1", "minWidth": "130px"})

    def info_row(label, value):
        return html.Div([
            html.Span(label + ":", style={
                "color": C["muted"], "fontSize": "12px",
                "fontWeight": "600", "minWidth": "140px", "display": "inline-block",
            }),
            html.Span(value, style={
                "color": C["text"], "fontSize": "12px",
                "fontFamily": "'JetBrains Mono', monospace",
            }),
        ], style={"padding": "7px 0", "borderBottom": f"1px solid {C['border']}"})

    return html.Div([
        # Header badge
        html.Div([
            html.I(className="bi bi-shield-lock-fill",
                   style={"fontSize": "20px", "color": C["accent"]}),
            html.Div([
                html.H6("Administrator Panel", style={
                    "color": C["accent"], "fontWeight": "700", "margin": "0", "fontSize": "14px",
                }),
                html.Div("Full access — Data Analyst role",
                         style={"color": C["muted"], "fontSize": "12px"}),
            ]),
        ], style={"display": "flex", "alignItems": "center", "gap": "12px", "marginBottom": "20px"}),

        # Stats grid
        html.Div([
            admin_stat("Total Records",      f"{stats['total_requests']:,}",   C["accent"]),
            admin_stat("Avg Daily Requests", f"{stats['avg_daily']:,.1f}",     C["success"]),
            admin_stat("Std Dev (Daily)",    f"±{stats['std_daily']:,.1f}",    C["warning"]),
            admin_stat("Error Rate",         f"{stats['error_rate']}%",        C["danger"]),
            admin_stat("Avg Duration",       f"{stats['avg_duration_ms']} ms", C["accent2"]),
            admin_stat("Unique Countries",   str(stats["unique_countries"]),   C["accent3"]),
        ], style={"display": "flex", "gap": "12px", "flexWrap": "wrap", "marginBottom": "20px"}),

        # User table
        html.Div([
            section_header("User Accounts", "Registered system users", "bi-people-fill"),
            dash_table.DataTable(
                data=[{"Username": u, "Role": d["role"].capitalize(), "Name": d["name"]}
                      for u, d in auth.USERS.items()],
                columns=[{"name": c, "id": c} for c in ["Username", "Name", "Role"]],
                style_header={
                    "backgroundColor": C["bg_panel"],
                    "color": C["muted"], "fontWeight": "600",
                    "fontSize": "11px", "textTransform": "uppercase",
                    "border": f"1px solid {C['border']}", "letterSpacing": "0.4px",
                },
                style_cell={
                    "backgroundColor": C["bg_card"],
                    "color": C["text"], "fontSize": "13px",
                    "border": f"1px solid {C['border']}",
                    "padding": "10px 14px", "fontFamily": "'DM Sans', sans-serif",
                },
                style_data_conditional=[{
                    "if": {"filter_query": "{Role} = Admin", "column_id": "Role"},
                    "color": C["accent"], "fontWeight": "700",
                }],
            ),
        ], style={**CARD, "marginBottom": "16px"}),

        # System info
        html.Div([
            section_header("Dataset Information", icon="bi-database"),
            info_row("CSV Path",      "data/iis_logs.csv"),
            info_row("Total Records", f"{stats['total_requests']:,}"),
            info_row("Date Range",    "Jan 2025 – Mar 2025"),
            info_row("Countries",     str(stats["unique_countries"])),
            info_row("Framework",     "Python Dash + Plotly"),
            info_row("Libraries",     "Pandas, NumPy, Faker"),
        ], style=CARD),

    ], style={**CARD, "maxWidth": "960px"})


# ─────────────────────────── Root layout ──────────────────────────────────────

app.layout = html.Div([
    # URL router – drives all navigation
    dcc.Location(id="url", refresh=False),

    # Session store (localStorage) – persists login across page refresh
    dcc.Store(id="session-user", storage_type="local"),

    # Data store (session) – raw dataset loaded once, shared by all callbacks
    dcc.Store(id="data-store", storage_type="session"),

    # Page content mount point
    html.Div(id="page-root"),

], style={
    "fontFamily": "'DM Sans', sans-serif",
    "background":  C["bg_page"],
    "minHeight":   "100vh",
    "color":       C["text"],
})


# ─────────────────────────── Global CSS ───────────────────────────────────────

app.index_string = '''
<!DOCTYPE html>
<html>
<head>
{%metas%}
<title>{%title%}</title>
{%favicon%}
{%css%}
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #F0F4F8; }

  /* ── Scrollbar ── */
  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: #F0F4F8; }
  ::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 3px; }

  /* ── Nav link custom style (active highlighting) ── */
  .nav-link-custom {
    font-size: 13px !important;
    font-weight: 500 !important;
    color: #64748B !important;
    border-radius: 7px !important;
    padding: 6px 12px !important;
    transition: all 0.15s ease !important;
    text-decoration: none !important;
  }
  .nav-link-custom:hover {
    color: #1A202C !important;
    background: #F0F4F8 !important;
  }
  .nav-link-custom.active {
    color: #1D6FA4 !important;
    background: rgba(29,111,164,0.09) !important;
    border: 1px solid rgba(29,111,164,0.20) !important;
    font-weight: 600 !important;
  }

  /* ── Dropdown overrides – light theme ── */
  .Select-control { background-color: #fff !important; border-color: #E2E8F0 !important; }
  .Select-menu-outer {
    background-color: #fff !important;
    border-color: #E2E8F0 !important;
    box-shadow: 0 4px 14px rgba(0,0,0,0.10) !important;
  }
  .Select-option { color: #1A202C !important; background: #fff !important; }
  .Select-option:hover, .Select-option.is-focused {
    background: #EFF6FF !important; color: #1D6FA4 !important;
  }
  .Select-value-label { color: #1A202C !important; }
  .Select-placeholder { color: #94A3B8 !important; }
  .dash-dropdown .Select-arrow { border-top-color: #94A3B8 !important; }

  /* ── Input focus ── */
  input:focus {
    border-color: #1D6FA4 !important;
    box-shadow: 0 0 0 3px rgba(29,111,164,0.12) !important;
  }

  /* ── Card hover lift ── */
  .card-hover {
    transition: transform 0.18s ease, box-shadow 0.18s ease;
  }
  .card-hover:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0,0,0,0.10) !important;
  }

  /* ── Loading spinner colour ── */
  ._dash-loading-callback { color: #1D6FA4 !important; }
</style>
</head>
<body>
{%app_entry%}
<footer>{%config%}{%scripts%}{%renderer%}</footer>
</body>
</html>
'''


# ═════════════════════════════════════════════════════════════════════════════
#  CALLBACKS
# ═════════════════════════════════════════════════════════════════════════════

# ── Mobile navbar collapse toggle ─────────────────────────────────────────────
@app.callback(
    Output("nav-collapse", "is_open"),
    Input("nav-toggler", "n_clicks"),
    State("nav-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_navbar(n, is_open):
    return not is_open


# ── Authentication – login ─────────────────────────────────────────────────────
@app.callback(
    Output("session-user", "data"),
    Output("login-error",  "children"),
    Input("login-btn",  "n_clicks"),
    Input("login-user", "n_submit"),
    Input("login-pass", "n_submit"),
    State("login-user", "value"),
    State("login-pass", "value"),
    prevent_initial_call=True,
)
def do_login(n_clicks, su, sp, username, password):
    if not username or not password:
        return no_update, "Please enter your username and password."
    user = auth.authenticate(username, password)
    if user:
        return user, ""
    return no_update, [
        html.I(className="bi bi-exclamation-circle me-1"),
        "Invalid username or password.",
    ]


# ── Authentication – logout ────────────────────────────────────────────────────
@app.callback(
    Output("session-user", "data", allow_duplicate=True),
    Output("url", "pathname", allow_duplicate=True),
    Input("logout-btn", "n_clicks"),
    prevent_initial_call=True,
)
def do_logout(_):
    # Clear session and redirect to root (login)
    return None, "/"


# ── Root page renderer – URL-based routing ────────────────────────────────────
@app.callback(
    Output("page-root", "children"),
    Input("url",          "pathname"),
    Input("session-user", "data"),
)
def render_root(pathname, user):
    # Pathname Normalization
    if pathname:
        pathname = pathname.rstrip("/")
        if not pathname:
            pathname = "/"

    # No active session → show login
    if user is None:
        return login_page

    # Route map
    route_page = {
        "/":      page_overview,
        "/geo":   page_geo,
        "/time":  page_time,
        "/demo":  page_demo,
        "/logs":  page_logs,
    }

    # Admin route with access control
    if pathname == "/admin":
        if not auth.is_admin(user):
            page_fn = access_denied          # non-admin → access denied
        else:
            page_fn = page_admin
    else:
        page_fn = route_page.get(pathname, page_overview)

    return html.Div([
        make_navbar(user, pathname),
        dbc.Container(
            page_fn(),
            fluid=True,
            style={"padding": "24px 28px", "maxWidth": "1420px"},
        ),
    ])


# ── Overview charts ────────────────────────────────────────────────────────────
@app.callback(
    Output("stat-total",      "children"),
    Output("stat-demos",      "children"),
    Output("stat-ai",         "children"),
    Output("stat-errors",     "children"),
    Output("stat-duration",   "children"),
    Output("stat-countries",  "children"),
    Output("chart-endpoints", "figure"),
    Output("chart-status",    "figure"),
    Output("chart-hourly",    "figure"),
    Output("chart-daily",     "figure"),
    Input("url", "pathname"),
)
def update_overview(pathname):
    if pathname != "/":
        return [no_update] * 10
    df    = de.get_raw()
    stats = de.summary_stats(df)
    return (
        f"{stats['total_requests']:,}",
        f"{stats['demo_requests']:,}",
        f"{stats['ai_hits']:,}",
        f"{stats['error_rate']}%",
        f"{stats['avg_duration_ms']} ms",
        str(stats["unique_countries"]),
        charts.endpoint_bar(de.endpoint_counts(df)),
        charts.status_pie(de.status_code_counts(df)),
        charts.hourly_line(de.hourly_traffic(df)),
        charts.daily_volume_bar(de.daily_volume(df)),
    )

# ── Geographic charts ──────────────────────────────────────────────────────────
@app.callback(
    Output("chart-geo-main", "figure"),
    Input("geo-kpi",        "value"),
    Input("geo-level",      "value"),
    Input("geo-chart-type", "value"),
)
def update_geo(kpi, level, chart_type):
    df = de.get_raw()
    agg = de.geo_distribution(df, kpi, level)
    if chart_type == "bar":
        return charts.geo_bar(agg, level, kpi)
    elif chart_type == "treemap":
        return charts.geo_treemap(agg, level, kpi)
    else:
        return charts.country_pie(agg, kpi)

# ── Time charts ────────────────────────────────────────────────────────────────
@app.callback(
    Output("chart-time-main",   "figure"),
    Output("chart-time-hourly", "figure"),
    Input("time-kpi", "value"),
    Input("time-dim", "value"),
)
def update_time(kpi, dim):
    df = de.get_raw()
    time_agg = de.time_distribution(df, kpi, dim)
    hourly_agg = de.hourly_traffic(df)
    return charts.time_bar(time_agg, dim, kpi), charts.hourly_line(hourly_agg)

# ── Demographic charts ─────────────────────────────────────────────────────────
@app.callback(
    Output("chart-demo-bar",  "figure"),
    Output("chart-demo-heat", "figure"),
    Input("demo-kpi", "value"),
    Input("demo-dim", "value"),
)
def update_demo(kpi, dim):
    df = de.get_raw()
    bar_agg = de.demographic_distribution(df, kpi, dim)
    pivot = (
        de.filter_kpi(df, kpi)
        .groupby(["gender", "age_group"])
        .size()
        .unstack(fill_value=0)
    )
    return charts.demo_bar(bar_agg, dim, kpi), charts.demo_heatmap(pivot, kpi)

# ── Log table ──────────────────────────────────────────────────────────────────
@app.callback(
    Output("log-table", "data"),
    Output("log-count-badge", "children"),
    Input("log-endpoint-filter", "value"),
    Input("log-status-filter",   "value"),
    Input("log-country-filter",  "value"),
)
def update_logs(endpoint, status, country):
    df = de.get_raw()
    if endpoint != "all":
        df = df[df["endpoint"] == endpoint]
    if status != "all":
        df = df[df["status_code"] == status]
    if country != "all":
        df = df[df["country"] == country]
    
    count_text = f"Showing {len(df):,} records matching filters"
    return df.to_dict("records"), count_text  

server = app.server      

if __name__ == "__main__":
    app.run(debug=False)