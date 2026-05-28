"""
Painel Interativo de Gestão de Risco
Lucro do segurador no produto de cap de inflação para aluguel de curta duração.

Lucro_λ(π) = V × N_λ × [P_λ × (1 + R/12)^12 − 12 × max(π − λ, 0)]
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from matplotlib import rcParams

# ---------------------------------------------------------------------------
# Style
# ---------------------------------------------------------------------------
rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Inter", "Helvetica Neue", "Arial", "sans-serif"],
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.edgecolor": "#cccccc",
    "axes.linewidth": 0.6,
    "xtick.color": "#555555",
    "ytick.color": "#555555",
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "axes.labelsize": 11,
    "axes.labelcolor": "#333333",
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "figure.facecolor": "#fafafa",
    "axes.facecolor": "#fafafa",
    "grid.color": "#e0e0e0",
    "grid.linewidth": 0.5,
    "grid.linestyle": "--",
})

LAMBDAS = [0.06, 0.07, 0.08]
LAMBDA_COLORS = {"6%": "#5B8DEF", "7%": "#F5A623", "8%": "#4CD964"}
TOTAL_COLOR = "#1A1A2E"
FILL_COLOR = "#1A1A2E"
PI_MIN, PI_MAX, PI_POINTS = 0.03, 0.10, 600

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Gestão de Risco – Cap Inflação", layout="wide")
st.markdown(
    "<h1 style='margin-bottom:0'>Painel de Gestão de Risco</h1>"
    "<p style='color:#888; margin-top:0'>Produto de cap de inflação para aluguel de curta duração</p>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.markdown(
    "<h3 style='margin-bottom:4px'>Parâmetros Gerais</h3>",
    unsafe_allow_html=True,
)

with st.sidebar.container(border=True):
    V = st.number_input(
        "Valor de Aluguel (R$)", min_value=0.0, max_value=100_000.0,
        value=3_000.0, step=100.0, format="%.0f",
        help="Valor mensal do aluguel – multiplica todo o resultado",
    )
    R_annual_pct = st.slider(
        "Taxa livre de risco (a.a.)", 0.0, 15.0, 10.0, 0.25,
        format="%.2f%%",
        help="Taxa anual; capitalizada mensalmente por 12 meses até o vencimento",
    )

R_annual = R_annual_pct / 100
# Compound monthly for 12 months
compound_factor = (1 + R_annual / 12) ** 12

st.sidebar.markdown("")
st.sidebar.markdown(
    "<h3 style='margin-bottom:4px'>Contratos por Teto</h3>",
    unsafe_allow_html=True,
)

params = {}
for lam in LAMBDAS:
    label = f"{lam:.0%}"
    color = LAMBDA_COLORS[label]
    st.sidebar.markdown(
        f"<div style='border-left:3px solid {color}; padding-left:8px; "
        f"margin-bottom:2px; margin-top:12px'>"
        f"<strong style='color:{color}'>Teto (λ) = {label}</strong></div>",
        unsafe_allow_html=True,
    )
    with st.sidebar.container(border=True):
        N = st.slider(
            f"Quantidade de Contratos", 0, 1000, 500, 10,
            key=f"N_{label}",
        )
        P = st.slider(
            f"Preço Venda", 0.0, 0.50, 0.10, 0.005,
            format="%.3f", key=f"P_{label}",
        )
    params[label] = {"N": N, "P": P, "lam": lam}

# ---------------------------------------------------------------------------
# Compute
# ---------------------------------------------------------------------------
pi = np.linspace(PI_MIN, PI_MAX, PI_POINTS)
total_profit = np.zeros_like(pi)

for p in params.values():
    N, P, lam = p["N"], p["P"], p["lam"]
    total_profit += V * N * (P * compound_factor - 12 * np.maximum(pi - lam, 0))

# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(11, 5))

# Shaded region: green above zero, red below
ax.fill_between(pi, total_profit, 0,
                where=(total_profit >= 0),
                color="#4CD964", alpha=0.12, interpolate=True)
ax.fill_between(pi, total_profit, 0,
                where=(total_profit < 0),
                color="#FF3B30", alpha=0.10, interpolate=True)

# Main line
ax.plot(pi, total_profit, color=TOTAL_COLOR, linewidth=2.4, zorder=5,
        label="Lucro Total da Carteira")

# Zero line
ax.axhline(0, color="#999999", linewidth=0.7, linestyle="-", zorder=2)

# Vertical dashed lines at each lambda
for lam in LAMBDAS:
    label = f"{lam:.0%}"
    ax.axvline(lam, color=LAMBDA_COLORS[label], linewidth=1.2, linestyle="--",
               alpha=0.7, zorder=3)
    # Label just above the x-axis
    y_pos = ax.get_ylim()[1] * 0.95
    ax.text(lam + 0.001, y_pos, f"Teto {label}",
            color=LAMBDA_COLORS[label], fontsize=9, fontweight="bold",
            va="top", ha="left", alpha=0.85)

ax.set_xlabel("Inflação Realizada (π)")
ax.set_ylabel("Lucro (R$)")
ax.xaxis.set_major_formatter(mtick.PercentFormatter(1.0, 0))
ax.yaxis.set_major_formatter(
    mtick.FuncFormatter(lambda x, _: f"R$ {x:,.0f}".replace(",", "."))
)
ax.set_xlim(PI_MIN, PI_MAX)
ax.grid(True, axis="y", zorder=0)
ax.set_title("Lucro Total vs. Inflação Realizada")

# Minimal legend
ax.legend(loc="upper right", frameon=True, fancybox=True, framealpha=0.9,
          edgecolor="#dddddd", fontsize=9)

fig.tight_layout()
st.pyplot(fig)
plt.close(fig)

# ---------------------------------------------------------------------------
# Summary table
# ---------------------------------------------------------------------------
st.subheader("Pontos de Equilíbrio (Break-even)")


def breakeven_single(N, P, lam, cf):
    if N == 0:
        return None
    return lam + P * cf / 12


def breakeven_total(params, cf, V, pi):
    total = np.zeros_like(pi)
    for p in params.values():
        N, P, lam = p["N"], p["P"], p["lam"]
        total += V * N * (P * cf - 12 * np.maximum(pi - lam, 0))
    sign_changes = np.where(np.diff(np.sign(total)) < 0)[0]
    if len(sign_changes) == 0:
        return None
    idx = sign_changes[0]
    t = total[idx] / (total[idx] - total[idx + 1])
    return pi[idx] + t * (pi[idx + 1] - pi[idx])


rows = []
for label, p in params.items():
    be = breakeven_single(p["N"], p["P"], p["lam"], compound_factor)
    rows.append({
        "Teto (λ)": label,
        "Qtd Contratos": p["N"],
        "Preço Venda": f"{p['P']:.3f}",
        "Break-even (π)": f"{be:.2%}" if be is not None else "N/A",
    })

be_total = breakeven_total(params, compound_factor, V, pi)
rows.append({
    "Teto (λ)": "Carteira",
    "Qtd Contratos": sum(p["N"] for p in params.values()),
    "Preço Venda": "—",
    "Break-even (π)": f"{be_total:.2%}" if be_total is not None else "N/A",
})

st.table(rows)
