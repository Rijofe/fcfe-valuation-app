import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

st.set_page_config(page_title="CMIN3 FCFE Valuation", layout="wide")

# ── Dados históricos ──────────────────────────────────────────
anos = [2021, 2022, 2023, 2024, 2025]

dados = {
    'Lucro Líquido':        [6.371,  2.950,  3.569,  4.528,  1.649],
    'EBITDA Ajustado':      [10.381, 6.033,  7.861,  5.799,  6.309],
    'Receita Líquida':      [12.500, 13.800, 17.000, 13.009, 15.333],
    'D&A':                  [0.648,  1.050,  1.054,  1.176,  1.303],
    'CapEx':                [1.406,  1.242,  1.633,  1.852,  2.397],
    'Resultado Financeiro': [0.500, -0.772, -1.172,  0.782, -2.508],
}

# ── Constantes ────────────────────────────────────────────────
DR      = 0.20
pct_cg  = 0.05
IR      = 0.34
n_acoes = 5485        # milhões
preco_atual = 4.90

rf_medio = np.mean([-0.772, -1.172, 0.782])   # real 2022-2024
da_2025  = 1.303
capex_2025 = 2.397
rec_2024   = 13.009
vol_base   = 45.8     # Mt
c1_base    = 21.5     # USD/t

# ── Funções ───────────────────────────────────────────────────
def calcular_ke(Rf, ERP, CRP, beta, lam, inf_br, inf_us):
    Ke_usd = Rf + CRP * lam + beta * ERP
    return (1 + Ke_usd) * (1 + inf_br) / (1 + inf_us) - 1

def calcular_fcfe_macro(fe, fx, Ke):
    receita  = vol_base * (fe - 10) * fx / 1000
    ebitda_m = receita - vol_base * c1_base * fx / 1000
    lucro_n  = (ebitda_m - da_2025) * (1 - IR) + rf_medio * (1 - IR)
    dcg      = pct_cg * (receita - rec_2024)
    return lucro_n - (capex_2025 - da_2025) * (1 - DR) - dcg * (1 - DR)

def calcular_dcf(fcfe_base, g1, g2, g_perp, Ke):
    fcfe_b, fcfes, anos_p = fcfe_base, [], []
    for i in range(1, 4):
        fcfe_b *= (1 + g1); fcfes.append(fcfe_b); anos_p.append(2025 + i)
    for i in range(1, 4):
        fcfe_b *= (1 + g2); fcfes.append(fcfe_b); anos_p.append(2028 + i)
    arr  = np.array(fcfes)
    t    = np.arange(1, len(arr) + 1)
    vp_f = (arr / (1 + Ke) ** t).sum()
    vt   = arr[-1] * (1 + g_perp) / (Ke - g_perp)
    vp_t = vt / (1 + Ke) ** len(arr)
    equity = vp_f + vp_t
    return equity * 1000 / n_acoes, equity, arr, anos_p, vp_f, vp_t

# ── Layout ────────────────────────────────────────────────────
st.title("📊 CMIN3 — Valuation FCFE")
st.caption("Dados reais: releases CSN 2022-25 | DRE imagens 2022-23 | Guia de Modelagem CSN")

# Sidebar — parâmetros
with st.sidebar:
    st.header("⚙️ Parâmetros")

    st.subheader("Macro")
    fe  = st.slider("Fe62% (USD/t)",  min_value=60,   max_value=150,  value=100, step=5)
    fx  = st.slider("Câmbio BRL/USD", min_value=4.50, max_value=8.00, value=5.80, step=0.10)

    st.subheader("Custo do Equity")
    Rf     = st.slider("Rf (%)",         2.0, 8.0, 5.0, 0.5, format="%.1f%%") / 100
    ERP    = st.slider("ERP (%)",        4.0, 8.0, 5.5, 0.5, format="%.1f%%") / 100
    CRP    = st.slider("CRP (%)",        1.0, 5.0, 2.5, 0.5, format="%.1f%%") / 100
    beta   = st.slider("Beta",           0.70, 1.50, 1.07, 0.05)
    lam    = st.slider("Lambda (λ)",     0.10, 1.00, 0.35, 0.05,
                       help="Fração do CRP aplicada. CMIN3 exportadora = 0,35")
    inf_br = st.slider("IPCA (%)",       3.0, 8.0, 4.5, 0.5, format="%.1f%%") / 100
    inf_us = st.slider("Inflação US (%)", 1.0, 4.0, 2.5, 0.5, format="%.1f%%") / 100

    st.subheader("Crescimento")
    g1     = st.slider("g Fase 1 (2026-28)", 0, 25, 10, 1, format="%d%%") / 100
    g2     = st.slider("g Fase 2 (2029-31)", 0, 15,  6, 1, format="%d%%") / 100
    g_perp = st.slider("g Perpetuidade",     2.0, 6.0, 4.0, 0.5, format="%.1f%%") / 100

# Cálculos principais
Ke       = calcular_ke(Rf, ERP, CRP, beta, lam, inf_br, inf_us)
fcfe_base = calcular_fcfe_macro(fe, fx, Ke)
pj, equity, fcfes, anos_p, vp_f, vp_t = calcular_dcf(fcfe_base, g1, g2, g_perp, Ke)
upside = (pj / preco_atual - 1) * 100

# ── Métricas no topo ──────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Preço Justo", f"R$ {pj:.2f}", f"{upside:+.1f}%")
col2.metric("Preço Atual", f"R$ {preco_atual:.2f}")
col3.metric("Ke (BRL)", f"{Ke:.1%}")
col4.metric("FCFE Base", f"R$ {fcfe_base:.2f}B")
col5.metric("Equity Value", f"R$ {equity:.1f}B")

if upside > 15:
    st.success(f"✅ DESCONTADA — upside de {upside:.1f}% no cenário atual")
elif upside < -15:
    st.error(f"❌ CARA — downside de {abs(upside):.1f}% no cenário atual")
else:
    st.warning(f"⚖️ PRÓXIMA DO JUSTO — {upside:+.1f}% no cenário atual")

st.divider()

# ── Gráficos principais ───────────────────────────────────────
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("FCFE Projetado (R$ B)")
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(anos_p, fcfes, 'o-', color='#1565C0', lw=2.5, ms=8)
    for a, v in zip(anos_p, fcfes):
        ax.annotate(f'{v:.2f}', (a, v), textcoords='offset points',
                   xytext=(0, 10), ha='center', fontsize=9, color='#1565C0', fontweight='bold')
    ax.axhline(fcfe_base, color='grey', ls=':', lw=1.5, label=f'Base R${fcfe_base:.2f}B')
    ax.set_ylabel('R$ Bilhões'); ax.legend(fontsize=9)
    ax.set_xticks(anos_p)
    ax.set_ylim(bottom=0)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(alpha=0.3)
    st.pyplot(fig); plt.close()

with col_b:
    st.subheader("Decomposição do Valor")
    fig, ax = plt.subplots(figsize=(7, 4))
    categorias = ['VP FCFEs\n2026-31', 'VP Terminal', 'Equity\nTotal']
    valores    = [vp_f, vp_t, equity]
    cores_bar  = ['#42A5F5', '#1565C0', '#0D47A1']
    bars = ax.bar(categorias, valores, color=cores_bar, alpha=0.85, width=0.5)
    for bar, v in zip(bars, valores):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.3,
               f'R$ {v:.1f}B', ha='center', fontsize=10, fontweight='bold')
    ax.set_ylabel('R$ Bilhões')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(alpha=0.3, axis='y')
    st.pyplot(fig); plt.close()

st.divider()

# ── Heatmap Fe x Câmbio ───────────────────────────────────────
st.subheader("Heatmap: Preço Justo por Fe62% × Câmbio")

fe_range  = [80, 90, 100, 110, 120, 130]
fx_range  = [5.00, 5.40, 5.80, 6.20, 6.60, 7.00]

tabela = {}
for fe_h in fe_range:
    row = {}
    for fx_h in fx_range:
        fb_h = calcular_fcfe_macro(fe_h, fx_h, Ke)
        pj_h, *_ = calcular_dcf(fb_h, g1, g2, g_perp, Ke)
        row[f'BRL {fx_h:.2f}'] = round(pj_h, 2)
    tabela[f'Fe {fe_h}$/t'] = row

df_heat = pd.DataFrame(tabela).T.astype(float)

fig, ax = plt.subplots(figsize=(12, 5))
im = ax.imshow(df_heat.values, cmap='RdYlGn', aspect='auto',
               vmin=preco_atual * 0.3, vmax=preco_atual * 2.5)

ax.set_xticks(range(len(df_heat.columns)))
ax.set_xticklabels(df_heat.columns, fontsize=10)
ax.set_yticks(range(len(df_heat.index)))
ax.set_yticklabels(df_heat.index, fontsize=10)

for i in range(len(df_heat.index)):
    for j in range(len(df_heat.columns)):
        val = df_heat.iloc[i, j]
        u   = (val / preco_atual - 1) * 100
        sym = '▲' if u > 0 else '▼'
        cor = 'white' if abs(u) > 40 else 'black'
        ax.text(j, i, f'R$ {val:.2f}\n{sym}{abs(u):.0f}%',
               ha='center', va='center', fontsize=9, fontweight='bold', color=cor)

# Marca posição atual dos sliders
try:
    fi = fe_range.index(fe)
    fxi = fx_range.index(round(fx, 2))
    ax.add_patch(plt.Rectangle((fxi-0.5, fi-0.5), 1, 1,
                               fill=False, edgecolor='blue', lw=3))
except ValueError:
    pass

ax.set_xlabel('Câmbio USD/BRL', fontsize=12)
ax.set_ylabel('Preço Fe62% (USD/t)', fontsize=12)
ax.set_title(f'Cenário Base | Ke={Ke:.1%} | g1={g1:.0%} | g∞={g_perp:.1%} | □ = posição atual',
            fontsize=11, fontweight='bold')
plt.colorbar(im, ax=ax, label='Preço Justo (R$)', fraction=0.02, pad=0.02)
plt.tight_layout()
st.pyplot(fig); plt.close()

st.divider()

# ── Dados históricos ──────────────────────────────────────────
with st.expander("📋 Dados Históricos e Fontes"):
    df_hist = pd.DataFrame(dados, index=anos).round(3)
    st.dataframe(df_hist)
    st.markdown("""
    **Fontes:**
    - D&A 2022: R\\$ 1,050B — CPV R\\$0,990B (DRE imagem 4T22) + ~R\\$0,060B SG&A
    - D&A 2023: R\\$ 1,054B — proporção 31,2% sobre CSN consolidada (planilha)
    - D&A 2024: R\\$ 1,176B — tabela segmento Mineração (release 4T25) ✅
    - D&A 2025: R\\$ 1,303B — soma 4 trimestres (releases 2025) ✅
    - RF 2022: R\\$-0,772B — calculado da DRE (imagem 4T22) ✅
    - RF 2023: R\\$-1,172B — calculado da DRE (imagem 4T23) ✅
    - RF 2024: R\\$+0,782B — release 4T24 ✅
    - CapEx 2024: R\\$ 1,852B — release 4T25 ✅
    - CapEx 2025: R\\$ 2,397B — soma 4 trimestres (releases 2025) ✅
    """)

with st.expander("🔢 Parâmetros do Modelo"):
    col1, col2, col3 = st.columns(3)
    col1.metric("Ke (BRL)", f"{Ke:.2%}")
    col1.metric("RF médio 22-24", f"R$ {rf_medio:.3f}B")
    col2.metric("FCFE base 2025", f"R$ {fcfe_base:.3f}B")
    col2.metric("g perpetuidade", f"{g_perp:.1%}")
    col3.metric("VP FCFEs", f"R$ {vp_f:.1f}B")
    col3.metric("VP Terminal", f"R$ {vp_t:.1f}B")
