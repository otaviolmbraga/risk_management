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
HEDGE_COLOR = "#9B59B6"
COMBINED_COLOR = "#E74C3C"
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
# Sidebar – general parameters
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
compound_factor = (1 + R_annual / 12) ** 12

# ---------------------------------------------------------------------------
# Sidebar – contracts per cap
# ---------------------------------------------------------------------------
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
# Compute base (unhedged) profit
# ---------------------------------------------------------------------------
pi = np.linspace(PI_MIN, PI_MAX, PI_POINTS)
total_profit = np.zeros_like(pi)

for p in params.values():
    N, P, lam = p["N"], p["P"], p["lam"]
    total_profit += V * N * (P * compound_factor - 12 * np.maximum(pi - lam, 0))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def breakeven_single(N, P, lam, cf):
    if N == 0:
        return None
    return lam + P * cf / 12


def breakeven_numerical(curve, pi):
    """First zero-crossing (positive → negative) via linear interpolation."""
    sign_changes = np.where(np.diff(np.sign(curve)) < 0)[0]
    if len(sign_changes) == 0:
        return None
    idx = sign_changes[0]
    t = curve[idx] / (curve[idx] - curve[idx + 1])
    return pi[idx] + t * (pi[idx + 1] - pi[idx])


def plot_profit(ax, pi, profit, *, label, color, show_fill=True):
    """Draw a profit line with optional green/red shading."""
    if show_fill:
        ax.fill_between(pi, profit, 0, where=(profit >= 0),
                        color="#4CD964", alpha=0.12, interpolate=True)
        ax.fill_between(pi, profit, 0, where=(profit < 0),
                        color="#FF3B30", alpha=0.10, interpolate=True)
    ax.plot(pi, profit, color=color, linewidth=2.4, zorder=5, label=label)


def decorate_ax(ax, pi, title):
    """Common axis formatting."""
    ax.axhline(0, color="#999999", linewidth=0.7, linestyle="-", zorder=2)
    for lam in LAMBDAS:
        lab = f"{lam:.0%}"
        ax.axvline(lam, color=LAMBDA_COLORS[lab], linewidth=1.2,
                   linestyle="--", alpha=0.7, zorder=3)
        y_pos = ax.get_ylim()[1] * 0.95
        ax.text(lam + 0.001, y_pos, f"Teto {lab}",
                color=LAMBDA_COLORS[lab], fontsize=9, fontweight="bold",
                va="top", ha="left", alpha=0.85)
    ax.set_xlabel("Inflação Realizada (π)")
    ax.set_ylabel("Lucro (R$)")
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(1.0, 0))
    ax.yaxis.set_major_formatter(
        mtick.FuncFormatter(lambda x, _: f"R$ {x:,.0f}".replace(",", "."))
    )
    ax.set_xlim(PI_MIN, PI_MAX)
    ax.grid(True, axis="y", zorder=0)
    ax.set_title(title)
    ax.legend(loc="upper right", frameon=True, fancybox=True, framealpha=0.9,
              edgecolor="#dddddd", fontsize=9)


def summary_table(params, compound_factor, V, pi, extra_curve=None):
    """Render the breakeven table. If extra_curve is given, use it for total."""
    curve = extra_curve if extra_curve is not None else total_profit
    rows = []
    for label, p in params.items():
        be = breakeven_single(p["N"], p["P"], p["lam"], compound_factor)
        rows.append({
            "Teto (λ)": label,
            "Qtd Contratos": p["N"],
            "Preço Venda": f"{p['P']:.3f}",
            "Break-even (π)": f"{be:.2%}" if be is not None else "N/A",
        })
    be_total = breakeven_numerical(curve, pi)
    rows.append({
        "Teto (λ)": "Carteira",
        "Qtd Contratos": sum(p["N"] for p in params.values()),
        "Preço Venda": "—",
        "Break-even (π)": f"{be_total:.2%}" if be_total is not None else "N/A",
    })
    st.table(rows)


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_sem, tab_linear, tab_binario = st.tabs([
    "Sem Hedge", "Hedge Linear", "Hedge Binário",
])

# ---- Tab 1: Sem Hedge ----------------------------------------------------
with tab_sem:
    fig, ax = plt.subplots(figsize=(11, 5))
    plot_profit(ax, pi, total_profit, label="Lucro Total da Carteira",
                color=TOTAL_COLOR)
    decorate_ax(ax, pi, "Lucro Total vs. Inflação Realizada")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    st.subheader("Pontos de Equilíbrio (Break-even)")
    summary_table(params, compound_factor, V, pi)

# ---- Tab 2: Hedge Linear -------------------------------------------------
with tab_linear:
    st.markdown(
        "<h4 style='margin-bottom:0'>Parâmetros do Hedge Linear</h4>"
        "<p style='color:#888; font-size:0.9em; margin-top:0'>"
        "Payoff = Notional × (π − π̄) na data de liquidação</p>",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        pi_bar_pct = st.slider(
            "Inflação contratada π̄", 3.0, 10.0, 6.0, 0.25,
            format="%.2f%%", key="pi_bar",
            help="Taxa de inflação negociada no contrato futuro",
        )
    with col2:
        notional = st.number_input(
            "Notional (R$)", min_value=0.0, max_value=50_000_000.0,
            value=500_000.0, step=50_000.0, format="%.0f", key="notional",
            help="Valor nocional do hedge linear",
        )

    pi_bar = pi_bar_pct / 100
    hedge_payoff = notional * (pi - pi_bar)
    combined = total_profit + hedge_payoff

    fig, ax = plt.subplots(figsize=(11, 5))

    # Unhedged – thin, muted
    ax.plot(pi, total_profit, color=TOTAL_COLOR, linewidth=1.2, alpha=0.35,
            linestyle="--", zorder=4, label="Sem Hedge")

    # Hedge payoff alone – thin purple
    ax.plot(pi, hedge_payoff, color=HEDGE_COLOR, linewidth=1.2, alpha=0.5,
            linestyle=":", zorder=4, label="Payoff do Hedge")

    # Combined – bold with fill
    plot_profit(ax, pi, combined, label="Lucro com Hedge",
                color=COMBINED_COLOR)

    # Mark pi_bar
    ax.axvline(pi_bar, color=HEDGE_COLOR, linewidth=1.2, linestyle="--",
               alpha=0.6, zorder=3)
    y_bot = ax.get_ylim()[0] * 0.9 if ax.get_ylim()[0] < 0 else 0
    ax.text(pi_bar + 0.001, ax.get_ylim()[1] * 0.85,
            f"π̄ = {pi_bar:.2%}", color=HEDGE_COLOR, fontsize=9,
            fontweight="bold", va="top", ha="left", alpha=0.85)

    decorate_ax(ax, pi, "Lucro com Hedge Linear vs. Inflação Realizada")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    st.subheader("Pontos de Equilíbrio (Break-even)")
    summary_table(params, compound_factor, V, pi, extra_curve=combined)

# ---- Tab 3: Hedge Binário (placeholder) ----------------------------------
with tab_binario:
    st.info("Em breve – Hedge Binário será implementado aqui.")
