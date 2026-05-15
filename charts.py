"""
charts.py
─────────
All Plotly figure-building functions.
Every function returns a go.Figure ready to drop into a dcc.Graph.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# ── Design tokens ──────────────────────────────────────────────────────────────
PALETTE = [
    "#00D4FF", "#7B2FBE", "#FF6B35", "#00C49A",
    "#FFB800", "#FF3366", "#4ECDC4", "#A78BFA",
]
BG          = "rgba(0,0,0,0)"      # transparent → inherits card bg
GRID_COLOR  = "rgba(255,255,255,0.07)"
TEXT_COLOR  = "#E2E8F0"
FONT_FAMILY = "DM Sans, sans-serif"
AXIS_FONT   = dict(color="#94A3B8", family=FONT_FAMILY, size=11)
TITLE_FONT  = dict(color=TEXT_COLOR, family=FONT_FAMILY, size=14)

BASE_LAYOUT = dict(
    paper_bgcolor = BG,
    plot_bgcolor  = BG,
    font          = dict(color=TEXT_COLOR, family=FONT_FAMILY),
    margin        = dict(l=10, r=10, t=40, b=10),
    legend        = dict(
        bgcolor     = "rgba(15,23,42,0.6)",
        bordercolor = "rgba(255,255,255,0.1)",
        borderwidth = 1,
        font        = dict(size=11),
    ),
    xaxis = dict(
        gridcolor    = GRID_COLOR,
        zerolinecolor= GRID_COLOR,
        tickfont     = AXIS_FONT,
        title_font   = AXIS_FONT,
    ),
    yaxis = dict(
        gridcolor    = GRID_COLOR,
        zerolinecolor= GRID_COLOR,
        tickfont     = AXIS_FONT,
        title_font   = AXIS_FONT,
    ),
)

def _apply_base(fig: go.Figure, title: str = "") -> go.Figure:
    fig.update_layout(**BASE_LAYOUT, title=dict(text=title, font=TITLE_FONT, x=0.01))
    return fig


# ── FR2 / FR3 – Geographic distribution ───────────────────────────────────────

def geo_bar(df: pd.DataFrame, geo_col: str, kpi: str) -> go.Figure:
    fig = go.Figure(go.Bar(
        x            = df[geo_col],
        y            = df["count"],
        marker_color = PALETTE[0],
        marker_line  = dict(color="rgba(0,0,0,0.2)", width=1),
        hovertemplate= f"<b>%{{x}}</b><br>{kpi}: %{{y:,}}<extra></extra>",
    ))
    _apply_base(fig, f"{kpi} by {geo_col.capitalize()}")
    fig.update_traces(marker=dict(
        color=df["count"],
        colorscale=[[0,"#1E3A5F"],[0.5,"#00A8CC"],[1,"#00D4FF"]],
        showscale=False,
    ))
    return fig


def geo_treemap(df: pd.DataFrame, geo_col: str, kpi: str) -> go.Figure:
    fig = px.treemap(
        df, path=[geo_col], values="count",
        color="count",
        color_continuous_scale=["#0F2027","#203A43","#00D4FF"],
    )
    fig.update_traces(
        hovertemplate="<b>%{label}</b><br>Count: %{value:,}<extra></extra>",
        textfont=dict(color="white", size=12),
    )
    fig.update_coloraxes(showscale=False)
    _apply_base(fig, f"{kpi} – {geo_col.capitalize()} Treemap")
    return fig


def country_pie(df: pd.DataFrame, kpi: str) -> go.Figure:
    fig = go.Figure(go.Pie(
        labels           = df["country"],
        values           = df["count"],
        hole             = 0.5,
        marker_colors    = PALETTE,
        textfont_size    = 11,
        hovertemplate    = "<b>%{label}</b><br>%{value:,} requests (%{percent})<extra></extra>",
    ))
    _apply_base(fig, f"{kpi} by Country")
    fig.update_layout(showlegend=True)
    return fig


# ── FR4 – Time-period distribution ────────────────────────────────────────────

def time_bar(df: pd.DataFrame, time_col: str, kpi: str) -> go.Figure:
    labels = df[time_col].astype(str)
    fig = go.Figure(go.Bar(
        x            = labels,
        y            = df["count"],
        marker_color = PALETTE[2],
        hovertemplate= f"<b>%{{x}}</b><br>{kpi}: %{{y:,}}<extra></extra>",
    ))
    fig.update_traces(marker=dict(
        color=df["count"],
        colorscale=[[0,"#2D1B69"],[0.5,"#7B2FBE"],[1,"#C084FC"]],
        showscale=False,
    ))
    _apply_base(fig, f"{kpi} by {time_col.replace('_',' ').title()}")
    return fig


def hourly_line(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Scatter(
        x    = df["hour"],
        y    = df["count"],
        mode = "lines+markers",
        line = dict(color=PALETTE[0], width=2.5),
        marker= dict(color=PALETTE[0], size=6),
        fill = "tozeroy",
        fillcolor="rgba(0,212,255,0.08)",
        hovertemplate="Hour %{x}:00 → %{y:,} requests<extra></extra>",
    ))
    _apply_base(fig, "Hourly Traffic Pattern")
    fig.update_xaxes(tickmode="linear", dtick=2, ticksuffix=":00")
    return fig


def daily_volume_bar(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Bar(
        x            = df["date"],
        y            = df["count"],
        marker_color = PALETTE[3],
        hovertemplate= "%{x|%d %b}<br>%{y:,} requests<extra></extra>",
    ))
    _apply_base(fig, "Daily Request Volume (Last 30 Days)")
    return fig


# ── Endpoint & status overview ─────────────────────────────────────────────────

def endpoint_bar(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure(go.Bar(
        x            = df["count"],
        y            = df["endpoint"],
        orientation  = "h",
        marker_color = PALETTE,
        hovertemplate= "<b>%{y}</b><br>%{x:,} hits<extra></extra>",
    ))
    _apply_base(fig, "Endpoint Hit Distribution")
    fig.update_layout(yaxis=dict(autorange="reversed"))
    return fig


def status_pie(df: pd.DataFrame) -> go.Figure:
    STATUS_COLORS = {
        "200": "#00C49A", "301": "#FFB800", "302": "#4ECDC4",
        "404": "#FF3366", "500": "#FF6B35", "403": "#A78BFA",
    }
    colors = [STATUS_COLORS.get(s, PALETTE[0]) for s in df["status_str"]]
    fig = go.Figure(go.Pie(
        labels        = df["status_str"],
        values        = df["count"],
        hole          = 0.5,
        marker_colors = colors,
        hovertemplate = "<b>HTTP %{label}</b><br>%{value:,} (%{percent})<extra></extra>",
        textfont_size = 12,
    ))
    _apply_base(fig, "HTTP Status Code Distribution")
    return fig


# ── FR6 / NR6 – Demographics ──────────────────────────────────────────────────

def demo_bar(df: pd.DataFrame, demo_col: str, kpi: str) -> go.Figure:
    fig = go.Figure(go.Bar(
        x            = df[demo_col],
        y            = df["count"],
        marker_color = PALETTE[6],
        hovertemplate= f"<b>%{{x}}</b><br>{kpi}: %{{y:,}}<extra></extra>",
    ))
    fig.update_traces(marker=dict(
        color=df["count"],
        colorscale=[[0,"#134E4A"],[0.5,"#0D9488"],[1,"#4ECDC4"]],
        showscale=False,
    ))
    _apply_base(fig, f"{kpi} by {demo_col.replace('_',' ').title()}")
    return fig


def demo_heatmap(df_pivot: pd.DataFrame, kpi: str) -> go.Figure:
    """Cross-tab of gender vs age_group."""
    fig = go.Figure(go.Heatmap(
        z            = df_pivot.values,
        x            = list(df_pivot.columns),
        y            = list(df_pivot.index),
        colorscale   = [[0,"#0F2027"],[0.5,"#203A43"],[1,"#00D4FF"]],
        hovertemplate= "Gender: %{y}<br>Age: %{x}<br>Count: %{z:,}<extra></extra>",
        showscale    = True,
        colorbar     = dict(tickfont=dict(color=TEXT_COLOR, size=10)),
    ))
    _apply_base(fig, f"{kpi} – Gender × Age Group Heatmap")
    return fig


# ── Admin – summary sparkline ──────────────────────────────────────────────────

def daily_sparkline(df: pd.DataFrame) -> go.Figure:
    daily = df.groupby("date").size().reset_index(name="count")
    fig = go.Figure(go.Scatter(
        x    = daily["date"],
        y    = daily["count"],
        mode = "lines",
        line = dict(color=PALETTE[0], width=1.5),
        fill = "tozeroy",
        fillcolor="rgba(0,212,255,0.06)",
    ))
    fig.update_layout(
        **BASE_LAYOUT,
        margin = dict(l=0,r=0,t=0,b=0),
        xaxis  = dict(visible=False),
        yaxis  = dict(visible=False),
        height = 60,
    )
    return fig
