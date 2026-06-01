# Risk Management Dashboard – Development Log

## Overview

Interactive Streamlit dashboard for visualizing the profit function of a short-rental inflation-cap product. Deployed on Streamlit Community Cloud.

**Repo**: `risk-dashboard` (standalone repo inside `fintech/risk_management/`)
**Main file**: `app.py`
**Deploy**: Streamlit Community Cloud → points to `app.py` on `main` branch

---

## Core Product Formula

```
Lucro_λ(π) = V × N_λ × [ P_λ × (1 + R/12)^12 − 12 × max(π − λ, 0) ]
```

- **V** – Valor de Aluguel (monthly rent value, master multiplier)
- **N_λ** – Quantidade de Contratos (number of contracts sold at cap λ)
- **P_λ** – Preço Venda (sale price per contract)
- **R** – Taxa livre de risco (annual risk-free rate, compounded monthly over 12 months)
- **λ** – Teto (inflation cap): 5%, 6%, 7%, 8%
- **π** – Inflação realizada (realized inflation)

**Important**: the company is NOT called "seguradora" — we avoid insurance legislation terminology. Always use "empresa".

---

## App Structure

### Tabs

1. **Introdução** – Explains the product, formula, and describes each tab with styled cards
2. **Sem Hedge** – Total portfolio profit vs realized inflation (single line, no legend)
3. **Hedge Linear** – Futures-style hedge: payoff = `Notional × (π − π̄)`
4. **Hedge Binário** – Binary option hedge: pays `(1−q)` if `π > π̄`, costs `q`
5. **Resumo** – Breakeven table for each cap and the total portfolio

### Sidebar Parameters

- **Parâmetros Gerais**: Valor de Aluguel (R$), Taxa livre de risco (a.a.) 0–15%
- **Contratos por Teto**: for each λ (5%, 6%, 7%, 8%) — Quantidade de Contratos (0–1000), Preço Venda (0–0.50)

### Hedge Parameters (inline in each tab)

**Hedge Linear:**
- Inflação contratada π̄ (3–10%)
- Razão de Hedge (0–200%): 100% = hedge slope cancels portfolio's downside slope
- Implied notional = `hedge_ratio × 12 × V × ΣN_λ`

**Hedge Binário:**
- Inflação gatilho π̄ (3–10%)
- Custo do contrato q (0–0.50)
- Razão de Hedge (0–200%): 100% = payout covers max portfolio loss if triggered
- Implied notional = `hedge_ratio × |loss_at_π_max| / (1 − q)`
- Note: changing q adjusts the cost (below π̄) but NOT the triggered payout — this is by design, since the hedge ratio fixes coverage level

---

## Design Decisions

- **Self-contained**: no imports from other folders in the fintech project. Colors, formulas all hardcoded in `app.py` for simple Community Cloud deployment.
- **Matplotlib over Plotly**: consistent with the rest of the codebase.
- **Charts at 200 dpi** for sharp rendering on retina/mobile screens.
- **Portuguese (PT-BR)** throughout — target audience is Brazilian.
- **Mobile-friendly**: sidebar starts collapsed, CSS hint banner appears on narrow screens pointing users to the hamburger menu.
- **No "seguradora"**: use "empresa" to avoid insurance regulation implications.

---

## Visual Style

- White background, left-aligned bold titles
- Left/top/right spines removed, subtle bottom axis
- Grid on both axes, soft solid lines
- Green/red fill between curve and zero line
- Teto labels at top of plot, π̄ labels at bottom (avoid overlap)
- Breakeven dot with annotation arrow
- Y-axis formatted as R$ with compact labels (R$ 500k, R$ 1.2M)
- X-axis: 3% to 10%
- Sidebar: colored left-border accents per teto, bordered containers for parameter groups
- Lambda colors: 5% purple `#E05CFD`, 6% blue `#5B8DEF`, 7% orange `#F5A623`, 8% green `#4CD964`

---

## Deployment Steps

1. GitHub Desktop → **File → Add local repository** → `C:\Users\otavi\Dropbox\fintech\risk_management`
2. Commit changes, then **Push origin**
3. Streamlit Community Cloud auto-redeploys on push

Initial setup was done via CLI `git init` inside `risk_management/` to avoid GitHub Desktop creating nested subfolders. The repo was published as a **public** repo (free tier requirement for Streamlit Cloud).

---

## Session History (May–Jun 2026)

1. **Created initial app** with sidebar sliders for R, N_λ, P_λ across λ = 6%, 7%, 8%. Plot per-lambda lines + total.
2. **Created requirements.txt** (streamlit, numpy, matplotlib) and **.gitignore**.
3. **Standalone repo setup**: moved repo root to `risk_management/` so only this folder is on GitHub, not the whole `fintech/` project.
4. **Git cleanup**: removed multiple accidental nested repos created by GitHub Desktop.
5. **Initialized via CLI**: `git init` + `git add` + `git commit` inside `risk_management/`, then added to GitHub Desktop for publishing.
6. **Published to GitHub** and deployed on Streamlit Community Cloud.
7. **R slider fix**: was displaying 0.15% instead of 15%. Changed to percentage-based input (0–15) with `/100` conversion.
8. **Full Portuguese translation**: all labels, headers, descriptions in PT-BR.
9. **Added Valor de Aluguel**: master parameter multiplying all profits.
10. **Aesthetic overhaul**: removed per-lambda lines, only total portfolio. Vertical dashed lines at tetos. Green/red fills. White background. Compact y-axis. Breakeven dot with annotation.
11. **Sidebar redesign**: bordered containers, colored left-border accents per teto.
12. **Tabs introduced**: Sem Hedge, Hedge Linear, Hedge Binário (placeholder), later Resumo.
13. **Hedge Linear implemented**: π̄ slider + Razão de Hedge (replaces raw notional). Shows ghost unhedged line, hedge payoff, combined.
14. **Hedge Binário implemented**: π̄, q, Razão de Hedge. Step-function payoff. Notional auto-adjusts with q to maintain coverage level.
15. **Label overlap fix**: Teto labels at top, π̄ labels at bottom, vertical padding added.
16. **Removed breakeven tables from chart tabs**, moved to dedicated Resumo tab.
17. **Removed legend from Sem Hedge** (redundant single line).
18. **Mobile UX**: sidebar collapsed by default, CSS banner hint on small screens.
19. **Chart resolution**: bumped to 200 dpi.
20. **Introdução tab added**: explains the product and each tab with styled cards.
21. **Terminology**: replaced "seguradora" with "empresa" everywhere.
22. **Added λ = 5%** cap with purple accent color.
23. **X-axis**: restricted to 3%–10%.
