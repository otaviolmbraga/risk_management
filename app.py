"""
Painel Interativo de Gestão de Risco
Lucro da empresa no produto de cap de inflação para aluguel de curta duração.

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
    "figure.dpi": 200,
    "savefig.dpi": 200,
})

LAMBDAS = [0.05, 0.06, 0.07, 0.08]
LAMBDA_COLORS = {"5%": "#E05CFD", "6%": "#5B8DEF", "7%": "#F5A623", "8%": "#4CD964"}
TOTAL_COLOR = "#1A1A2E"
HEDGE_COLOR = "#9B59B6"
COMBINED_COLOR = "#E74C3C"
GREEN_FILL = "#34C759"
RED_FILL = "#FF3B30"
PI_MIN, PI_MAX, PI_POINTS = 0.03, 0.10, 600

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Gestão de Risco – Cap Inflação", layout="wide",
                   initial_sidebar_state="collapsed")
st.markdown(
    "<h1 style='margin-bottom:0'>Painel de Gestão de Risco</h1>"
    "<p style='color:#888; margin-top:0'>Produto de cap de inflação para aluguel de curta duração</p>",
    unsafe_allow_html=True,
)

# Mobile hint — only visible on narrow screens via CSS media query
st.markdown(
    """
    <style>
    .mobile-hint {
        display: none;
        background: linear-gradient(135deg, #f0f4ff 0%, #e8f0fe 100%);
        border: 1px solid #c5d5f0;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 12px;
        font-size: 0.9em;
        color: #444;
        text-align: center;
    }
    .mobile-hint span { font-size: 1.1em; }
    @media (max-width: 768px) {
        .mobile-hint { display: block; }
    }
    </style>
    <div class="mobile-hint">
        <span>☰</span> Toque no menu <b>no canto superior esquerdo</b>
        para ajustar os parâmetros da carteira
        (Valor de Aluguel, Taxa, Contratos por Teto)
    </div>
    """,
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


def _pad_ylim(ax, top_frac=0.15, bot_frac=0.10):
    """Add vertical padding so labels don't sit on top of data."""
    ymin, ymax = ax.get_ylim()
    span = ymax - ymin
    ax.set_ylim(ymin - span * bot_frac, ymax + span * top_frac)


def draw_lambda_markers(ax):
    """Vertical dashed lines + labels at the TOP of the plot."""
    ymin, ymax = ax.get_ylim()
    for lam in LAMBDAS:
        lab = f"{lam:.0%}"
        clr = LAMBDA_COLORS[lab]
        ax.axvline(lam, color=clr, linewidth=0.9, linestyle="--",
                   alpha=0.55, zorder=3)
        ax.text(lam, ymax, f" Teto {lab}",
                color=clr, fontsize=8.5, fontweight="600",
                va="top", ha="left", alpha=0.8,
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
    _pad_ylim(ax)
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
tab_intro, tab_sem, tab_linear, tab_binario, tab_resumo = st.tabs([
    "Introdução", "Sem Hedge", "Hedge Linear", "Hedge Binário", "Resumo",
])

# ---- Tab 0: Introdução ---------------------------------------------------
with tab_intro:
    st.markdown(
        """
        <style>
        .intro-section {
            background: #f8f9fb;
            border-radius: 10px;
            padding: 24px 28px;
            margin-bottom: 16px;
            border: 1px solid #eaedf2;
        }
        .intro-section h3 {
            margin-top: 0;
            margin-bottom: 6px;
            font-size: 1.1em;
            color: #1A1A2E;
        }
        .intro-section p {
            color: #555;
            font-size: 0.95em;
            line-height: 1.6;
            margin-bottom: 0;
        }
        .intro-formula {
            background: #1A1A2E;
            color: #e8e8e8;
            border-radius: 8px;
            padding: 14px 20px;
            font-family: 'Courier New', monospace;
            font-size: 0.95em;
            margin: 12px 0 6px 0;
            text-align: center;
            letter-spacing: 0.3px;
        }
        .intro-cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 14px;
            margin-top: 8px;
        }
        .intro-card {
            background: white;
            border-radius: 10px;
            padding: 20px 22px;
            border: 1px solid #eaedf2;
        }
        .intro-card .card-icon {
            font-size: 1.4em;
            margin-bottom: 6px;
        }
        .intro-card h4 {
            margin: 0 0 6px 0;
            font-size: 1em;
            color: #1A1A2E;
        }
        .intro-card p {
            color: #666;
            font-size: 0.88em;
            line-height: 1.55;
            margin: 0;
        }
        .intro-card code {
            background: #f0f2f6;
            padding: 1px 5px;
            border-radius: 4px;
            font-size: 0.92em;
            color: #1A1A2E;
        }
        </style>

        <div class="intro-section">
            <h3>O Produto</h3>
            <p>
                A empresa vende contratos que protegem locatários contra
                inflação acima de um <b>teto (λ)</b>. Se a inflação realizada
                π superar λ, a empresa paga a diferença — 12 parcelas de
                (π − λ) por contrato, multiplicadas pelo valor do aluguel.
            </p>
            <div class="intro-formula">
                Lucro<sub>λ</sub>(π) = V × N<sub>λ</sub> × [ P<sub>λ</sub> × (1 + R/12)<sup>12</sup> − 12 × max(π − λ, 0) ]
            </div>
            <p style="font-size:0.85em; color:#888; margin-top:4px">
                V = valor do aluguel · N = contratos vendidos · P = preço de venda · R = taxa livre de risco
            </p>
        </div>

        <div class="intro-section">
            <h3>As Abas</h3>
            <div class="intro-cards">
                <div class="intro-card">
                    <div class="card-icon">📊</div>
                    <h4>Sem Hedge</h4>
                    <p>
                        Lucro da carteira sem nenhuma proteção.
                        Mostra como o resultado deteriora à medida que
                        a inflação supera os tetos contratados.
                    </p>
                </div>
                <div class="intro-card">
                    <div class="card-icon">📈</div>
                    <h4>Hedge Linear</h4>
                    <p>
                        Contrato futuro de inflação a uma taxa π̄.
                        Payoff: <code>Notional × (π − π̄)</code>.
                        A <b>razão de hedge</b> define quanto da inclinação
                        negativa da carteira é compensada.
                    </p>
                </div>
                <div class="intro-card">
                    <div class="card-icon">🎯</div>
                    <h4>Hedge Binário</h4>
                    <p>
                        Opção binária que paga <code>(1 − q)</code> se
                        π &gt; π̄, custando <code>q</code> por unidade.
                        A <b>razão de hedge</b> define a cobertura
                        relativa à perda máxima da carteira.
                    </p>
                </div>
                <div class="intro-card">
                    <div class="card-icon">📋</div>
                    <h4>Resumo</h4>
                    <p>
                        Tabela com os pontos de equilíbrio (break-even)
                        para cada teto e para a carteira total.
                    </p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---- Tab 1: Sem Hedge ----------------------------------------------------
with tab_sem:
    fig, ax = make_figure()
    draw_fill(ax, pi, total_profit)
    ax.plot(pi, total_profit, color=TOTAL_COLOR, linewidth=2.6, zorder=5,
            solid_capstyle="round")
    style_ax(ax, "Lucro da Carteira vs. Inflação Realizada")
    draw_breakeven_dot(ax, pi, total_profit)
    st.pyplot(fig, dpi=200)
    plt.close(fig)

# ---- Tab 2: Hedge Linear -------------------------------------------------
# Portfolio worst-case slope (all caps breached): -12 × V × ΣN_λ per unit of π
_total_N = sum(p["N"] for p in params.values())
_portfolio_slope = 12 * V * _total_N          # positive number
_portfolio_loss_at_max = -total_profit[-1] if total_profit[-1] < 0 else 0.0

with tab_linear:
    st.markdown(
        "<h4 style='margin-bottom:0'>Parâmetros do Hedge Linear</h4>"
        "<p style='color:#888; font-size:0.9em; margin-top:0'>"
        "Payoff = Notional × (π − π̄). O <b>Razão de Hedge</b> define "
        "quanto da inclinação negativa da carteira é compensado "
        "(100% = inclinação totalmente neutralizada).</p>",
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
        hedge_ratio_lin = st.slider(
            "Razão de Hedge", 0, 200, 100, 5,
            format="%d%%", key="hr_lin",
            help="100% = hedge compensa toda a inclinação negativa da carteira",
        )

    pi_bar = pi_bar_pct / 100
    notional = (hedge_ratio_lin / 100) * _portfolio_slope
    hedge_payoff = notional * (pi - pi_bar)
    combined = total_profit + hedge_payoff

    st.caption(f"Notional implícito: R$ {notional:,.0f}".replace(",", "."))

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

    # π̄ marker – label at bottom so it doesn't clash with Teto labels
    ax.axvline(pi_bar, color=HEDGE_COLOR, linewidth=0.9, linestyle="--",
               alpha=0.5, zorder=3)
    ymin = ax.get_ylim()[0]
    ax.text(pi_bar, ymin, f" π̄ = {pi_bar:.2%}",
            color=HEDGE_COLOR, fontsize=8.5, fontweight="600",
            va="bottom", ha="left", alpha=0.8,
            path_effects=[pe.withStroke(linewidth=2.5, foreground=BG)])

    draw_breakeven_dot(ax, pi, combined)

    ax.legend(loc="lower left", frameon=True, fancybox=True, framealpha=0.95,
              edgecolor="#eeeeee", fontsize=8.5, borderpad=0.8,
              handlelength=2.2)

    st.pyplot(fig, dpi=200)
    plt.close(fig)

# ---- Tab 3: Hedge Binário ------------------------------------------------
BINARY_COLOR = "#E67E22"

with tab_binario:
    st.markdown(
        "<h4 style='margin-bottom:0'>Parâmetros do Hedge Binário</h4>"
        "<p style='color:#888; font-size:0.9em; margin-top:0'>"
        "Paga q, recebe (1 − q) se π &gt; π̄. O <b>Razão de Hedge</b> "
        "define quanto da perda máxima da carteira (em π = 10%) é coberto "
        "pelo payoff (100% = perda totalmente coberta se gatilho ativado).</p>",
        unsafe_allow_html=True,
    )

    cb1, cb2, cb3 = st.columns(3)
    with cb1:
        pi_bar_bin_pct = st.slider(
            "Inflação gatilho π̄", 3.0, 10.0, 7.0, 0.25,
            format="%.2f%%", key="pi_bar_bin",
            help="Se a inflação realizada superar esse nível, o hedge paga",
        )
    with cb2:
        q = st.slider(
            "Custo do contrato (q)", 0.0, 0.50, 0.20, 0.01,
            format="%.2f", key="q_bin",
            help="Preço pago por unidade; recebe (1 − q) se π > π̄",
        )
    with cb3:
        hedge_ratio_bin = st.slider(
            "Razão de Hedge", 0, 200, 100, 5,
            format="%d%%", key="hr_bin",
            help="100% = payoff cobre toda a perda da carteira em π = 10%",
        )

    pi_bar_bin = pi_bar_bin_pct / 100
    # notional so that (1-q) × notional = hedge_ratio × |loss at pi_max|
    if (1 - q) > 0 and _portfolio_loss_at_max > 0:
        notional_bin = (hedge_ratio_bin / 100) * _portfolio_loss_at_max / (1 - q)
    else:
        notional_bin = 0.0
    # Pay q, receive (1-q) if π > π̄
    bin_payoff = notional_bin * np.where(pi > pi_bar_bin, 1 - q, -q)
    combined_bin = total_profit + bin_payoff

    st.caption(f"Notional implícito: R$ {notional_bin:,.0f}".replace(",", "."))

    fig, ax = make_figure()

    # Unhedged – ghost
    ax.plot(pi, total_profit, color=TOTAL_COLOR, linewidth=1.4, alpha=0.25,
            linestyle="--", zorder=4, label="Sem Hedge",
            solid_capstyle="round")

    # Binary hedge payoff alone
    ax.plot(pi, bin_payoff, color=BINARY_COLOR, linewidth=1.2, alpha=0.4,
            linestyle=":", zorder=4, label="Payoff do Hedge",
            solid_capstyle="round", drawstyle="steps-post")

    # Combined
    draw_fill(ax, pi, combined_bin)
    ax.plot(pi, combined_bin, color=COMBINED_COLOR, linewidth=2.6, zorder=5,
            label="Lucro com Hedge", solid_capstyle="round")

    style_ax(ax, "Lucro com Hedge Binário vs. Inflação Realizada")

    # π̄ marker – label at bottom
    ax.axvline(pi_bar_bin, color=BINARY_COLOR, linewidth=0.9, linestyle="--",
               alpha=0.5, zorder=3)
    ymin = ax.get_ylim()[0]
    ax.text(pi_bar_bin, ymin, f" π̄ = {pi_bar_bin:.2%}",
            color=BINARY_COLOR, fontsize=8.5, fontweight="600",
            va="bottom", ha="left", alpha=0.8,
            path_effects=[pe.withStroke(linewidth=2.5, foreground=BG)])

    draw_breakeven_dot(ax, pi, combined_bin)

    ax.legend(loc="lower left", frameon=True, fancybox=True, framealpha=0.95,
              edgecolor="#eeeeee", fontsize=8.5, borderpad=0.8,
              handlelength=2.2)

    st.pyplot(fig, dpi=200)
    plt.close(fig)

# ---- Tab 4: Resumo -------------------------------------------------------
with tab_resumo:
    st.subheader("Pontos de Equilíbrio (Break-even)")
    summary_table(params, compound_factor, V, pi)
