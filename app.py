"""
Painel Interativo de Gestão de Risco
Lucro do segurador no produto de cap de inflação para aluguel de curta duração.

Lucro_λ(π) = V × N_λ × [P_λ × (1 + R/12)^12 − 12 × max(π − λ, 0)]
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import matplotlib.patheffects as pe
from matplotlib import rcParams

# ---------------------------------------------------------------------------
# Style
# ---------------------------------------------------------------------------
BG = "#ffffff"
GRID_CLR = "#f0f0f0"

rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Inter", "Helvetica Neue", "Arial", "sans-serif"],
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.spines.left": False,
    "axes.edgecolor": "#dddddd",
    "axes.linewidth": 0.4,
    "xtick.color": "#888888",
    "ytick.color": "#888888",
    "xtick.labelsize": 9.5,
    "ytick.labelsize": 9.5,
    "xtick.major.size": 0,
    "ytick.major.size": 0,
    "xtick.major.pad": 8,
    "ytick.major.pad": 8,
    "axes.labelsize": 10.5,
    "axes.labelcolor": "#555555",
    "axes.titlesize": 14,
    "axes.titleweight": "600",
    "axes.titlepad": 18,
    "figure.facecolor": BG,
    "axes.facecolor": BG,
    "grid.color": GRID_CLR,
    "grid.linewidth": 0.6,
    "grid.linestyle": "-",
})

LAMBDAS = [0.06, 0.07, 0.08]
LAMBDA_COLORS = {"6%": "#5B8DEF", "7%": "#F5A623", "8%": "#4CD964"}
TOTAL_COLOR = "#1A1A2E"
HEDGE_COLOR = "#9B59B6"
COMBINED_COLOR = "#E74C3C"
GREEN_FILL = "#34C759"
RED_FILL = "#FF3B30"
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
    sign_changes = np.where(np.diff(np.sign(curve)) < 0)[0]
    if len(sign_changes) == 0:
        return None
    idx = sign_changes[0]
    t = curve[idx] / (curve[idx] - curve[idx + 1])
    return pi[idx] + t * (pi[idx + 1] - pi[idx])


def _fmt_brl(x, _):
    """Format y-axis as R$ with thousands separator."""
    if abs(x) >= 1_000_000:
        return f"R$ {x/1e6:.1f}M"
    if abs(x) >= 1_000:
        return f"R$ {x/1e3:.0f}k"
    return f"R$ {x:,.0f}"


def make_figure():
    fig, ax = plt.subplots(figsize=(11, 4.8))
    fig.subplots_adjust(left=0.08, right=0.97, top=0.88, bottom=0.13)
    return fig, ax


def draw_fill(ax, pi, profit):
    """Green/red shading around zero."""
    ax.fill_between(pi, profit, 0, where=(profit >= 0),
                    color=GREEN_FILL, alpha=0.08, interpolate=True)
    ax.fill_between(pi, profit, 0, where=(profit < 0),
                    color=RED_FILL, alpha=0.08, interpolate=True)


def draw_lambda_markers(ax):
    """Vertical dashed lines + labels at each teto."""
    ymin, ymax = ax.get_ylim()
    for lam in LAMBDAS:
        lab = f"{lam:.0%}"
        clr = LAMBDA_COLORS[lab]
        ax.axvline(lam, color=clr, linewidth=0.9, linestyle="--",
                   alpha=0.55, zorder=3)
        ax.text(lam, ymax, f" Teto {lab}",
                color=clr, fontsize=8.5, fontweight="600",
                va="bottom", ha="left", alpha=0.8,
                path_effects=[pe.withStroke(linewidth=2.5, foreground=BG)])


def style_ax(ax, title):
    """Common axis decoration."""
    ax.axhline(0, color="#cccccc", linewidth=0.6, zorder=2)
    ax.set_xlabel("Inflação Realizada (π)", labelpad=10)
    ax.set_ylabel("")
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(1.0, 0))
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(_fmt_brl))
    ax.set_xlim(PI_MIN, PI_MAX)
    ax.grid(True, axis="both", zorder=0)
    ax.set_title(title, loc="left")
    draw_lambda_markers(ax)


def draw_breakeven_dot(ax, pi, curve):
    """Place a small dot + annotation at the breakeven crossing."""
    be = breakeven_numerical(curve, pi)
    if be is not None:
        ax.plot(be, 0, "o", color="#FF3B30", markersize=6, zorder=10,
                markeredgecolor="white", markeredgewidth=1.5)
        ax.annotate(f"Break-even\n{be:.2%}",
                    xy=(be, 0), xytext=(be + 0.003, ax.get_ylim()[0] * 0.35),
                    fontsize=8.5, color="#FF3B30", fontweight="600",
                    arrowprops=dict(arrowstyle="-", color="#FF3B30",
                                    lw=0.8, connectionstyle="arc3,rad=0.15"),
                    ha="left", va="center",
                    path_effects=[pe.withStroke(linewidth=2.5, foreground=BG)])


def summary_table(params, compound_factor, V, pi, extra_curve=None):
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
    fig, ax = make_figure()
    draw_fill(ax, pi, total_profit)
    ax.plot(pi, total_profit, color=TOTAL_COLOR, linewidth=2.6, zorder=5,
            solid_capstyle="round")
    style_ax(ax, "Lucro da Carteira vs. Inflação Realizada")
    draw_breakeven_dot(ax, pi, total_profit)
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

    fig, ax = make_figure()

    # Unhedged – thin ghost line
    ax.plot(pi, total_profit, color=TOTAL_COLOR, linewidth=1.4, alpha=0.25,
            linestyle="--", zorder=4, label="Sem Hedge",
            solid_capstyle="round")

    # Hedge payoff – subtle
    ax.plot(pi, hedge_payoff, color=HEDGE_COLOR, linewidth=1.2, alpha=0.4,
            linestyle=":", zorder=4, label="Payoff do Hedge",
            solid_capstyle="round")

    # Combined – primary
    draw_fill(ax, pi, combined)
    ax.plot(pi, combined, color=COMBINED_COLOR, linewidth=2.6, zorder=5,
            label="Lucro com Hedge", solid_capstyle="round")

    style_ax(ax, "Lucro com Hedge Linear vs. Inflação Realizada")

    # π̄ marker
    ax.axvline(pi_bar, color=HEDGE_COLOR, linewidth=0.9, linestyle="--",
               alpha=0.5, zorder=3)
    ymax = ax.get_ylim()[1]
    ax.text(pi_bar, ymax, f" π̄ = {pi_bar:.2%}",
            color=HEDGE_COLOR, fontsize=8.5, fontweight="600",
            va="bottom", ha="left", alpha=0.8,
            path_effects=[pe.withStroke(linewidth=2.5, foreground=BG)])

    draw_breakeven_dot(ax, pi, combined)

    # Legend – small, out of the way
    ax.legend(loc="lower left", frameon=True, fancybox=True, framealpha=0.95,
              edgecolor="#eeeeee", fontsize=8.5, borderpad=0.8,
              handlelength=2.2)

    st.pyplot(fig)
    plt.close(fig)

    st.subheader("Pontos de Equilíbrio (Break-even)")
    summary_table(params, compound_factor, V, pi, extra_curve=combined)

# ---- Tab 3: Hedge Binário (placeholder) ----------------------------------
with tab_binario:
    st.info("Em breve – Hedge Binário será implementado aqui.")
