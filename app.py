"""
Interactive Risk Management Dashboard
Visualizes insurer profit for the short-rental inflation-cap product.

Profit_λ(π) = N_λ × [P_λ × (1+R) − 12 × max(π − λ, 0)]
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
LAMBDAS = [0.06, 0.07, 0.08]
COLORS = {"6%": "#1f77b4", "7%": "#ff7f0e", "8%": "#2ca02c"}
TOTAL_COLOR = "#d62728"
PI_MIN, PI_MAX, PI_POINTS = 0.0, 0.25, 500

st.set_page_config(page_title="Risk Management Dashboard", layout="wide")
st.title("Insurer Profit – Short-Rental Inflation Cap")

# ---------------------------------------------------------------------------
# Sidebar controls
# ---------------------------------------------------------------------------
st.sidebar.header("Parameters")

R = st.sidebar.slider("Risk-free rate R", 0.0, 0.20, 0.10, 0.005, format="%.1f%%",
                       help="Annual risk-free rate applied to premium income")

params = {}
for lam in LAMBDAS:
    label = f"{lam:.0%}"
    st.sidebar.subheader(f"λ = {label}")
    N = st.sidebar.slider(f"N  (contracts) – λ={label}", 0, 1000, 500, 10,
                          key=f"N_{label}")
    P = st.sidebar.slider(f"P  (premium)   – λ={label}", 0.0, 0.50, 0.10, 0.005,
                          format="%.3f", key=f"P_{label}")
    params[label] = {"N": N, "P": P, "lam": lam}

# ---------------------------------------------------------------------------
# Compute profit curves
# ---------------------------------------------------------------------------
pi = np.linspace(PI_MIN, PI_MAX, PI_POINTS)
profits = {}
total_profit = np.zeros_like(pi)

for label, p in params.items():
    N, P, lam = p["N"], p["P"], p["lam"]
    profit = N * (P * (1 + R) - 12 * np.maximum(pi - lam, 0))
    profits[label] = profit
    total_profit += profit

# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 5))

for label, profit in profits.items():
    ax.plot(pi, profit, color=COLORS[label], linewidth=2, label=f"λ = {label}")

ax.plot(pi, total_profit, color=TOTAL_COLOR, linewidth=2.5, linestyle="--",
        label="Total portfolio")
ax.axhline(0, color="grey", linewidth=0.8, linestyle="--")

ax.set_xlabel("Realized inflation π")
ax.set_ylabel("Profit")
ax.xaxis.set_major_formatter(mtick.PercentFormatter(1.0, 0))
ax.legend()
ax.set_xlim(PI_MIN, PI_MAX)
ax.set_title("Profit vs. realized inflation")
fig.tight_layout()

st.pyplot(fig)
plt.close(fig)

# ---------------------------------------------------------------------------
# Summary table – breakeven π for each lambda and total portfolio
# ---------------------------------------------------------------------------
st.subheader("Breakeven inflation")


def breakeven_single(N, P, lam, R):
    """π where profit crosses zero: P(1+R)/(12) + λ, provided N > 0."""
    if N == 0:
        return None
    return lam + P * (1 + R) / 12


def breakeven_total(params, R, pi):
    """Numerical breakeven of the summed profit curve (first zero-crossing)."""
    total = np.zeros_like(pi)
    for p in params.values():
        N, P, lam = p["N"], p["P"], p["lam"]
        total += N * (P * (1 + R) - 12 * np.maximum(pi - lam, 0))
    # Find first sign change from positive to negative
    sign_changes = np.where(np.diff(np.sign(total)) < 0)[0]
    if len(sign_changes) == 0:
        return None
    idx = sign_changes[0]
    # Linear interpolation between idx and idx+1
    t = total[idx] / (total[idx] - total[idx + 1])
    return pi[idx] + t * (pi[idx + 1] - pi[idx])


rows = []
for label, p in params.items():
    be = breakeven_single(p["N"], p["P"], p["lam"], R)
    rows.append({
        "λ": label,
        "N": p["N"],
        "Premium": f"{p['P']:.3f}",
        "Breakeven π": f"{be:.2%}" if be is not None else "N/A",
    })

be_total = breakeven_total(params, R, pi)
rows.append({
    "λ": "Total",
    "N": sum(p["N"] for p in params.values()),
    "Premium": "—",
    "Breakeven π": f"{be_total:.2%}" if be_total is not None else "N/A",
})

st.table(rows)
