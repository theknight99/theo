# Bloom Energy (BE) 180C — 2026-03-20 Theoretical (BSM) — Streamlit app
# Shareable Streamlit version
# ---------------------------------------------------------------

from datetime import date
import math
import numpy as np
import plotly.graph_objects as go
import streamlit as st

# ----------------------------- Utilities: Normal PDF/CDF -----------------------------
# (No SciPy needed; avoids extra dependency for easy online deploy.)
SQRT_2PI = math.sqrt(2.0 * math.pi)

def _norm_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / SQRT_2PI

def _norm_cdf(x: float) -> float:
    # Standard normal CDF via erf
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

# ----------------------------- BSM functions (call) + Greeks -----------------------------
def bsm_call_price_greeks(S: float, K: float, T: float, r: float, q: float, sigma: float):
    """
    Returns a dict with: price, delta, gamma, theta_per_day, vega_per_volpt, d1, d2
    Conventions:
      - Theta: per calendar day
      - Vega per vol point: per 1% IV move (0.01)
    """
    if S <= 0 or K <= 0 or sigma <= 0 or T <= 0:
        return {
            "price": float("nan"),
            "delta": float("nan"),
            "gamma": float("nan"),
            "theta_per_day": float("nan"),
            "vega_per_volpt": float("nan"),
            "d1": float("nan"),
            "d2": float("nan"),
        }

    sqrtT = math.sqrt(T)
    d1 = (math.log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / (sigma * sqrtT)
    d2 = d1 - sigma * sqrtT

    Nd1 = _norm_cdf(d1)
    Nd2 = _norm_cdf(d2)
    nd1 = _norm_pdf(d1)

    disc_q = math.exp(-q * T)
    disc_r = math.exp(-r * T)

    # Price
    price = S * disc_q * Nd1 - K * disc_r * Nd2

    # Greeks
    delta = disc_q * Nd1
    gamma = disc_q * nd1 / (S * sigma * sqrtT)
    theta_annual = (
        - (S * disc_q * nd1 * sigma) / (2.0 * sqrtT)
        - r * K * disc_r * Nd2
        + q * S * disc_q * Nd1
    )
    theta_per_day = theta_annual / 365.0

    vega = S * disc_q * nd1 * sqrtT              # per 1.00 (100%) IV move
    vega_per_volpt = vega / 100.0                # per 1 vol point (0.01)

    return {
        "price": float(price),
        "delta": float(delta),
        "gamma": float(gamma),
        "theta_per_day": float(theta_per_day),
        "vega_per_volpt": float(vega_per_volpt),
        "d1": float(d1),
        "d2": float(d2),
    }

# ----------------------------- App config -----------------------------
st.set_page_config(page_title="BE 180C (2026-03-20) Theo", layout="wide")
st.title("Bloom Energy (BE) 180C — 2026-03-20 Theoretical")

# Contract details
K = 180.0
expiry = date(2026, 3, 20)
_today = date.today()
_days_to_expiry = max((expiry - _today).days, 0)
T = max(_days_to_expiry / 365.0, 1e-6)

# ----------------------------- Sidebar controls -----------------------------
st.sidebar.header("Inputs")
S = st.sidebar.slider("Spot (S)", min_value=80.0, max_value=140.0, value=105.0, step=0.5)
iv_pct = st.sidebar.slider("Implied Volatility (IV, %)", min_value=50.0, max_value=150.0, value=115.0, step=1.0)
iv = iv_pct / 100.0

with st.sidebar.expander("Advanced"):
    r_pct = st.slider("Risk-free rate (%, annualized)", min_value=0.0, max_value=10.0, value=4.5, step=0.1)
    q_pct = st.slider("Dividend yield (%, annualized)", min_value=0.0, max_value=5.0, value=0.0, step=0.1)
r = r_pct / 100.0
q = q_pct / 100.0

# ----------------------------- Calculate theo and Greeks -----------------------------
res = bsm_call_price_greeks(S, K, T, r, q, iv)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Theo Price ($)", f"{res['price']:.2f}")
c2.metric("Delta", f"{res['delta']:.3f}")
c3.metric("Gamma", f"{res['gamma']:.6f}")
c4.metric("Theta / day ($)", f"{res['theta_per_day']:.2f}")
c5.metric("Vega / 1 vol pt ($)", f"{res['vega_per_volpt']:.2f}")

st.caption(
    f"Expiry: {expiry.isoformat()} | Days to expiry: {_days_to_expiry} | "
    f"Strike K: {K:.0f} | r: {r_pct:.2f}% | q: {q_pct:.2f}%"
)

# ----------------------------- Price as % of spot and 12.5% threshold -----------------------------
if S > 0 and math.isfinite(res["price"]):
    price_pct_of_spot = res["price"] / S * 100.0
else:
    price_pct_of_spot = float("nan")

st.write(f"Price as % of spot: {price_pct_of_spot:.2f}% | 12.5% of spot: ${0.125 * S:.2f}")

# ----------------------------- Chart 1: Price vs IV (fixed S) -----------------------------
iv_grid = np.linspace(0.80, 1.40, 61)  # 80% to 140%
prices_iv = [bsm_call_price_greeks(S, K, T, r, q, s)["price"] for s in iv_grid]

fig1 = go.Figure()
fig1.add_trace(go.Scatter(
    x=iv_grid * 100.0, y=prices_iv, mode="lines",
    name="Theo vs IV",
    line=dict(color="#2E91E5", width=3)
))
fig1.add_trace(go.Scatter(
    x=[iv_pct], y=[res["price"]],
    mode="markers", name="Current",
    marker=dict(color="#E15F99", size=10, symbol="diamond")
))
fig1.add_hline(
    y=0.125 * S,
    line=dict(color="#9C755F", width=2, dash="dash"),
    annotation_text="12.5% of spot"
)
fig1.update_layout(
    title=f"Theoretical Price vs IV (S={S:.2f})",
    xaxis_title="IV (%)",
    yaxis_title="Theo Price ($)",
    hovermode="x unified",
    template="plotly_dark",
    height=420,
)
st.plotly_chart(fig1, use_container_width=True)

# ----------------------------- Chart 2: Price vs Spot (fixed IV) -----------------------------
spot_grid = np.linspace(80.0, 140.0, 121)
prices_spot = [bsm_call_price_greeks(sv, K, T, r, q, iv)["price"] for sv in spot_grid]
threshold_curve = 0.125 * spot_grid

fig2 = go.Figure()
fig2.add_trace(go.Scatter(
    x=spot_grid, y=prices_spot, mode="lines",
    name="Theo vs Spot",
    line=dict(color="#1CA71C", width=3)
))
fig2.add_trace(go.Scatter(
    x=[S], y=[res["price"]],
    mode="markers", name="Current",
    marker=dict(color="#E15F99", size=10, symbol="diamond")
))
fig2.add_trace(go.Scatter(
    x=spot_grid, y=threshold_curve, mode="lines",
    name="12.5% of Spot",
    line=dict(color="#9C755F", width=2, dash="dash")
))
fig2.update_layout(
    title=f"Theoretical Price vs Spot (IV={iv_pct:.1f}%)",
    xaxis_title="Spot ($)",
    yaxis_title="Theo Price ($)",
    hovermode="x unified",
    template="plotly_dark",
    height=420,
)
st.plotly_chart(fig2, use_container_width=True)

# ----------------------------- Notes -----------------------------
st.markdown(
    "- Purely theoretical (BSM, sticky IV). Actual NBBO may differ.\n"
    "- Vega shown is per 1 vol point (0.01). Theta is per calendar day."
)
