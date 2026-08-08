"""
Sector Rotation (RRG) — separate page, own URL. Independent of the Live
Scanner and FII/DII pages.
"""

import streamlit as st
import plotly.graph_objects as go
from sector_rotation import build_rrg, latest_quadrant_summary

st.set_page_config(page_title="Sector Rotation (RRG)", layout="wide", page_icon="🔄")

st.title("🔄 Sector Rotation — RRG")
st.caption(
    "Relative Rotation Graph: each sector's strength (x-axis) and momentum "
    "(y-axis) vs the Nifty 50, both centered at 100. Sectors classically rotate "
    "clockwise through the four quadrants over time — the tail shows each "
    "sector's last several weeks of movement."
)

with st.sidebar:
    st.header("Settings")
    tail_length = st.slider("Tail length (weeks)", 4, 16, 8)
    ratio_window = st.slider("RS-Ratio smoothing window", 5, 20, 10)
    momentum_window = st.slider("RS-Momentum window", 2, 10, 4)
    st.divider()
    st.caption(
        "Data: Yahoo Finance sector indices vs Nifty 50, weekly closes. "
        "This uses a standard open RS-Ratio/RS-Momentum approximation — "
        "the original JdK RRG formula is proprietary, so exact coordinate "
        "values won't match a licensed StockCharts RRG tick-for-tick, but "
        "the quadrant behavior and rotation pattern are the same idea."
    )

if st.button("🔄 Refresh", type="primary") or "rrg_data" not in st.session_state:
    with st.spinner("Fetching sector index data and computing RRG..."):
        st.session_state["rrg_data"] = build_rrg(
            tail_length=tail_length, ratio_window=ratio_window, momentum_window=momentum_window
        )

rrg_data = st.session_state.get("rrg_data", {})

if not rrg_data:
    st.info("Click **Refresh** to load the chart.")
    st.stop()

# ---------------------------------------------------------------------
# Build the RRG figure
# ---------------------------------------------------------------------
all_x = [v for df in rrg_data.values() for v in df["rs_ratio"]]
all_y = [v for df in rrg_data.values() for v in df["rs_momentum"]]
pad = 2
x_min, x_max = min(all_x + [98]) - pad, max(all_x + [102]) + pad
y_min, y_max = min(all_y + [98]) - pad, max(all_y + [102]) + pad

fig = go.Figure()

# Quadrant backgrounds
fig.add_shape(type="rect", x0=100, x1=x_max, y0=100, y1=y_max,
              fillcolor="rgba(22,163,74,0.10)", line_width=0, layer="below")   # Leading
fig.add_shape(type="rect", x0=100, x1=x_max, y0=y_min, y1=100,
              fillcolor="rgba(234,179,8,0.10)", line_width=0, layer="below")   # Weakening
fig.add_shape(type="rect", x0=x_min, x1=100, y0=y_min, y1=100,
              fillcolor="rgba(185,28,28,0.10)", line_width=0, layer="below")   # Lagging
fig.add_shape(type="rect", x0=x_min, x1=100, y0=100, y1=y_max,
              fillcolor="rgba(37,99,235,0.10)", line_width=0, layer="below")   # Improving

fig.add_hline(y=100, line_color="rgba(150,150,150,0.5)", line_width=1)
fig.add_vline(x=100, line_color="rgba(150,150,150,0.5)", line_width=1)

fig.add_annotation(x=x_max, y=y_max, text="LEADING", showarrow=False, xanchor="right", yanchor="top", font=dict(color="#16a34a", size=12))
fig.add_annotation(x=x_max, y=y_min, text="WEAKENING", showarrow=False, xanchor="right", yanchor="bottom", font=dict(color="#ca8a04", size=12))
fig.add_annotation(x=x_min, y=y_min, text="LAGGING", showarrow=False, xanchor="left", yanchor="bottom", font=dict(color="#b91c1c", size=12))
fig.add_annotation(x=x_min, y=y_max, text="IMPROVING", showarrow=False, xanchor="left", yanchor="top", font=dict(color="#2563eb", size=12))

palette = ["#e11d48", "#f59e0b", "#22c55e", "#06b6d4", "#6366f1", "#ec4899", "#84cc16", "#0ea5e9"]

for i, (sector, df) in enumerate(sorted(rrg_data.items())):
    color = palette[i % len(palette)]
    fig.add_trace(go.Scatter(
        x=df["rs_ratio"], y=df["rs_momentum"],
        mode="lines+markers",
        line=dict(color=color, width=2),
        marker=dict(size=[6] * (len(df) - 1) + [11], color=color,
                    symbol=["circle"] * (len(df) - 1) + ["diamond"]),
        name=sector,
        text=[sector] * len(df),
        hovertemplate="%{text}<br>RS-Ratio: %{x:.2f}<br>RS-Momentum: %{y:.2f}<extra></extra>",
    ))
    last = df.iloc[-1]
    fig.add_annotation(x=last["rs_ratio"], y=last["rs_momentum"], text=f"  {sector}",
                        showarrow=False, xanchor="left", font=dict(color=color, size=11))

fig.update_layout(
    xaxis_title="RS-Ratio (relative strength vs Nifty 50)",
    yaxis_title="RS-Momentum",
    xaxis=dict(range=[x_min, x_max]),
    yaxis=dict(range=[y_min, y_max]),
    height=650,
    template="plotly_dark",
    margin=dict(l=40, r=40, t=20, b=40),
    showlegend=False,
)

st.plotly_chart(fig, use_container_width=True)

st.divider()
st.subheader("Current quadrant per sector")
summary = latest_quadrant_summary(rrg_data)


def _q_color(val):
    return {
        "Leading": "color: #16a34a; font-weight: 600",
        "Weakening": "color: #ca8a04; font-weight: 600",
        "Lagging": "color: #b91c1c; font-weight: 600",
        "Improving": "color: #2563eb; font-weight: 600",
    }.get(val, "")


if not summary.empty:
    styler = summary.style.format(precision=2, subset=["RS-Ratio", "RS-Momentum"])
    style_fn = getattr(styler, "map", None) or styler.applymap
    styler = style_fn(_q_color, subset=["Quadrant"])
    hide_fn = getattr(styler, "hide", None)
    styler = hide_fn(axis="index") if hide_fn else styler.hide_index()
    st.table(styler)
