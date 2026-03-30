"""
Calculadora de Crédito e Inversión
Matemática Financiera — Streamlit App
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from utils.financial import (
    # Tasas
    tasa_nominal_a_efectiva, tasa_efectiva_a_nominal, tasa_equivalente,
    tasa_efectiva_periodica,
    # Interés Simple
    interes_simple_monto_final, interes_simple_interes,
    interes_simple_capital, interes_simple_tasa, interes_simple_tiempo,
    tabla_interes_simple,
    # Interés Compuesto
    interes_compuesto_monto_final, interes_compuesto_valor_presente,
    interes_compuesto_tasa, interes_compuesto_tiempo,
    tabla_interes_compuesto,
    # Anualidades
    anualidad_cuota_ordinaria, anualidad_vp_ordinaria, anualidad_vf_ordinaria,
    anualidad_cuota_anticipada, anualidad_vp_anticipada, anualidad_vf_anticipada,
    # Gradientes
    gradiente_aritmetico_vp, gradiente_aritmetico_vf,
    gradiente_geometrico_vp, gradiente_geometrico_vf,
    tabla_gradiente,
    # Amortización
    amortizacion_frances, amortizacion_aleman, amortizacion_americano,
    # VPN / TIR
    calcular_vpn, calcular_tir, tabla_vpn_sensibilidad,
    # Plan de Ahorro
    plan_ahorro_tabla, plan_ahorro_vf,
    plan_ahorro_cuota_para_meta, plan_ahorro_meses_para_meta,
    # Formato
    fmt_currency, fmt_percent,
)

# ─────────────────────────────────────────────
# CONFIGURACIÓN GENERAL
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="Calculadora Financiera",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS personalizado
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem 1.5rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 0.5rem;
    }
    .metric-card h3 { margin: 0; font-size: 0.9rem; opacity: 0.85; }
    .metric-card h2 { margin: 0.2rem 0 0; font-size: 1.6rem; font-weight: 700; }
    .result-box {
        background: #f0f4ff;
        border-left: 4px solid #4f46e5;
        padding: 0.8rem 1.2rem;
        border-radius: 0 8px 8px 0;
        margin: 0.5rem 0;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { border-radius: 6px 6px 0 0; }
    h1 { color: #1e1b4b; }
    h2, h3 { color: #312e81; }
</style>
""", unsafe_allow_html=True)


def metric_card(label: str, value: str):
    st.markdown(f"""
    <div class="metric-card">
        <h3>{label}</h3>
        <h2>{value}</h2>
    </div>""", unsafe_allow_html=True)


def result_box(label: str, value: str):
    st.markdown(f"""
    <div class="result-box">
        <strong>{label}:</strong> {value}
    </div>""", unsafe_allow_html=True)


def _fmt_num_col(x) -> str:
    """Formato colombiano: $ 100.000,00"""
    if not (isinstance(x, (int, float)) and not isinstance(x, bool)):
        return x
    s = f"{float(x):,.2f}"        # "100,000.00"
    s = s.replace(",", "X")       # "100X000.00"
    s = s.replace(".", ",")       # "100X000,00"
    s = s.replace("X", ".")       # "100.000,00"
    return f"$ {s}"


def fmt_df(df: pd.DataFrame) -> pd.DataFrame:
    """Formatea columnas numéricas de un dataframe con formato colombiano."""
    df2 = df.copy()
    for col in df2.columns:
        if col == "Período":
            continue
        df2[col] = df2[col].apply(_fmt_num_col)
    return df2


def money_input(label, moneda_sym="$", container=None, **kwargs):
    """number_input monetario con caption en formato colombiano."""
    ctx = container if container is not None else st
    val = ctx.number_input(label, **kwargs)
    ctx.caption(fmt_currency(val, moneda_sym))
    return val


PERIODOS_NOMBRES = {
    "Anual": 1,
    "Semestral": 2,
    "Trimestral": 4,
    "Bimestral": 6,
    "Mensual": 12,
    "Quincenal": 24,
    "Semanal": 52,
    "Diario": 365,
}

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────

with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/money.png", width=70)
    st.title("Calculadora\nFinanciera")
    st.markdown("---")
    modulo = st.radio(
        "Módulo",
        [
            "💰 Plan de Ahorro",
            "🔄 Conversión de Tasas",
            "📈 Interés Simple",
            "📊 Interés Compuesto",
            "💳 Anualidades",
            "📐 Gradientes",
            "🏦 Amortización",
            "📉 VPN / TIR",
        ],
        label_visibility="collapsed",
    )
    st.markdown("---")
    moneda = st.selectbox("Moneda / Prefijo", ["$", "COP", "USD", "EUR", "MXN"])
    st.markdown("<small>© Matemática Financiera</small>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# MÓDULO 0: PLAN DE AHORRO
# ─────────────────────────────────────────────

if modulo == "💰 Plan de Ahorro":
    st.title("💰 Plan de Ahorro — Simulador de Inversión Periódica")

    # ── Configuración de tasa ──────────────────────────────────────────
    st.subheader("1. Configuración de Tasas")
    col_m1, col_m2 = st.columns([1, 2])
    with col_m1:
        metodo = st.selectbox(
            "Método de ingreso",
            ["Tasa Periódica", "Tasa Nominal Anual", "Tasa Efectiva Anual"],
        )

    col_t1, col_t2, col_t3 = st.columns(3)

    if metodo == "Tasa Periódica":
        with col_t1:
            tasa_per_pct = st.number_input(
                "Tasa Periódica (%)", min_value=0.001, value=1.0, step=0.01, format="%.3f"
            )
        tasa_periodica = tasa_per_pct / 100
        per_pago = st.selectbox(
            "Período de pago",
            ["Mensual", "Bimestral", "Trimestral", "Semestral", "Anual"],
            index=0,
        )
        m_map = {"Mensual": 12, "Bimestral": 6, "Trimestral": 4, "Semestral": 2, "Anual": 1}
        m = m_map[per_pago]
        tasa_nominal = tasa_periodica * m
        tasa_efectiva_anual = (1 + tasa_periodica) ** m - 1

    elif metodo == "Tasa Nominal Anual":
        with col_t1:
            tasa_nom_pct = st.number_input(
                "Tasa Nominal Anual (%)", min_value=0.001, value=12.0, step=0.1
            )
        per_pago = st.selectbox(
            "Período de pago / capitalización",
            ["Mensual", "Bimestral", "Trimestral", "Semestral", "Anual"],
            index=0,
        )
        m_map = {"Mensual": 12, "Bimestral": 6, "Trimestral": 4, "Semestral": 2, "Anual": 1}
        m = m_map[per_pago]
        tasa_nominal = tasa_nom_pct / 100
        tasa_periodica = tasa_nominal / m
        tasa_efectiva_anual = (1 + tasa_periodica) ** m - 1

    else:  # Tasa Efectiva Anual
        with col_t1:
            tea_pct = st.number_input(
                "Tasa Efectiva Anual (%)", min_value=0.001, value=12.68, step=0.1
            )
        per_pago = st.selectbox(
            "Período de pago",
            ["Mensual", "Bimestral", "Trimestral", "Semestral", "Anual"],
            index=0,
        )
        m_map = {"Mensual": 12, "Bimestral": 6, "Trimestral": 4, "Semestral": 2, "Anual": 1}
        m = m_map[per_pago]
        tasa_efectiva_anual = tea_pct / 100
        tasa_periodica = (1 + tasa_efectiva_anual) ** (1 / m) - 1
        tasa_nominal = tasa_periodica * m

    # Mostrar resumen de tasas
    with col_t2:
        st.metric("Tasa Periódica", f"{tasa_periodica*100:.4f}%")
        st.metric("Tasa Nominal Anual", f"{tasa_nominal*100:.4f}%")
    with col_t3:
        st.metric("Tasa Efectiva Anual", f"{tasa_efectiva_anual*100:.4f}%")
        st.metric("Períodos por año", m)

    st.divider()

    # ── Parámetros del plan ────────────────────────────────────────────
    st.subheader("2. Parámetros del Plan")
    col_p1, col_p2, col_p3, col_p4 = st.columns(4)
    with col_p1:
        ahorro_inicial = st.number_input(
            "Ahorro Inicial", min_value=0.0, value=0.0, step=100_000.0,
            help="Saldo inicial antes de empezar a ahorrar"
        )
        st.caption(fmt_currency(ahorro_inicial, moneda))
    with col_p2:
        cuota_ahorro = st.number_input(
            "Cuota periódica", min_value=0.0, value=100_000.0, step=10_000.0,
            help="Monto que depositas cada período"
        )
        st.caption(fmt_currency(cuota_ahorro, moneda))
    with col_p3:
        plazo_anios = st.number_input(
            "Plazo (años)", min_value=1, value=18, step=1
        )
    plazo_meses = plazo_anios * m
    col_p4.metric("Total períodos", plazo_meses)
    col_p4.metric("Plazo en meses", plazo_anios * 12)

    # ── Pestañas ──────────────────────────────────────────────────────
    tab_res, tab_tabla, tab_graf, tab_meta = st.tabs(
        ["Resultados", "Tabla de Ahorro", "Gráfica", "Calculadora de Metas"]
    )

    # Generar tabla
    df_ahorro = plan_ahorro_tabla(ahorro_inicial, cuota_ahorro, tasa_periodica, plazo_meses)
    vf_final = df_ahorro.iloc[-1]["Valor Final"]
    total_aportado = ahorro_inicial + cuota_ahorro * plazo_meses
    total_intereses = vf_final - total_aportado

    with tab_res:
        c1, c2, c3 = st.columns(3)
        with c1:
            metric_card("Valor Final Acumulado", fmt_currency(vf_final, moneda))
        with c2:
            metric_card("Total Aportado", fmt_currency(total_aportado, moneda))
        with c3:
            metric_card("Total Intereses Ganados", fmt_currency(total_intereses, moneda))

        st.markdown("")
        col_r1, col_r2, col_r3 = st.columns(3)
        col_r1.metric(
            "Tasa efectiva anual",
            f"{tasa_efectiva_anual*100:.4f}%",
            help="Tasa efectiva anual equivalente a la tasa periódica aplicada"
        )
        col_r2.metric("Tasa periódica aplicada", f"{tasa_periodica*100:.4f}%")
        col_r3.metric("Plazo total", f"{plazo_anios} años / {plazo_meses} períodos")

        # Mini tabla anual
        st.markdown("#### Resumen Anual")
        if m == 12:
            anios_rows = []
            for anio in range(1, plazo_anios + 1):
                idx = anio * 12
                if idx <= len(df_ahorro) - 1:
                    row = df_ahorro.iloc[idx]
                    anios_rows.append({
                        "Año": anio,
                        "Período": int(row["Período"]),
                        "Valor Acumulado": row["Valor Final"],
                        "Intereses Acumulados": df_ahorro.iloc[:idx+1]["Intereses"].sum(),
                        "Total Aportado": ahorro_inicial + cuota_ahorro * idx,
                    })
            df_anual = pd.DataFrame(anios_rows)
            st.dataframe(fmt_df(df_anual), use_container_width=True, hide_index=True)
        else:
            st.info("El resumen anual está disponible para planes mensuales.")

    with tab_tabla:
        st.markdown(f"**Tabla completa — {plazo_meses} períodos**")
        # Mostrar con paginación para tablas largas
        if plazo_meses > 100:
            mostrar_todos = st.checkbox("Mostrar todos los períodos", value=False)
            if mostrar_todos:
                st.dataframe(fmt_df(df_ahorro), use_container_width=True, hide_index=True)
            else:
                periodos_muestra = st.slider("Rango de períodos a mostrar", 0, plazo_meses, (0, min(24, plazo_meses)))
                df_slice = df_ahorro[
                    (df_ahorro["Período"] >= periodos_muestra[0]) &
                    (df_ahorro["Período"] <= periodos_muestra[1])
                ]
                st.dataframe(fmt_df(df_slice), use_container_width=True, hide_index=True)
        else:
            st.dataframe(fmt_df(df_ahorro), use_container_width=True, hide_index=True)

        csv_ahorro = df_ahorro.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Descargar tabla CSV", csv_ahorro, "plan_ahorro.csv", "text/csv")

    with tab_graf:
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            # Evolución del valor acumulado
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(
                x=df_ahorro["Período"], y=df_ahorro["Valor Final"],
                name="Valor Acumulado", fill="tozeroy",
                line=dict(color="#4f46e5"), fillcolor="rgba(79,70,229,0.15)"
            ))
            # Línea de aportes sin interés
            aportes_sin_int = [ahorro_inicial + cuota_ahorro * t for t in range(plazo_meses + 1)]
            fig1.add_trace(go.Scatter(
                x=list(range(plazo_meses + 1)), y=aportes_sin_int,
                name="Solo aportes (sin interés)", line=dict(color="#f59e0b", dash="dash")
            ))
            fig1.update_layout(
                title="Crecimiento del Ahorro",
                xaxis_title="Período",
                yaxis_title="Valor",
                legend=dict(orientation="h", y=-0.2),
            )
            st.plotly_chart(fig1, use_container_width=True)

        with col_g2:
            # Composición final: aportes vs intereses
            fig2 = go.Figure(go.Pie(
                labels=["Aportes", "Intereses Ganados"],
                values=[max(total_aportado, 0), max(total_intereses, 0)],
                hole=0.4,
                marker_colors=["#4f46e5", "#22c55e"],
            ))
            fig2.update_layout(title="Composición del Valor Final")
            st.plotly_chart(fig2, use_container_width=True)

        # Intereses por período
        fig3 = px.bar(
            df_ahorro[df_ahorro["Período"] > 0],
            x="Período", y="Intereses",
            title="Intereses Generados por Período",
            color_discrete_sequence=["#22c55e"],
        )
        st.plotly_chart(fig3, use_container_width=True)

    with tab_meta:
        st.subheader("¿Cuánto necesito ahorrar para llegar a mi meta?")
        tipo_meta = st.radio(
            "Calcular",
            ["Cuota necesaria para una meta", "Tiempo para alcanzar una meta"],
            horizontal=True,
        )

        if tipo_meta == "Cuota necesaria para una meta":
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                meta_val = money_input(
                    "Meta de ahorro", moneda, min_value=1.0, value=100_000_000.0, step=1_000_000.0
                )
            meta_plazo = col_m2.number_input(
                "En cuántos períodos", min_value=1, value=plazo_meses, step=1
            )
            with col_m2:
                meta_inicial = money_input(
                    "Ahorro inicial", moneda, min_value=0.0, value=ahorro_inicial, step=100_000.0, key="meta_ini"
                )
            cuota_necesaria = plan_ahorro_cuota_para_meta(meta_val, meta_inicial, tasa_periodica, meta_plazo)
            metric_card("Cuota periódica necesaria", fmt_currency(cuota_necesaria, moneda))
            result_box("Total a aportar", fmt_currency(cuota_necesaria * meta_plazo + meta_inicial, moneda))
            result_box("Intereses que generará", fmt_currency(meta_val - cuota_necesaria * meta_plazo - meta_inicial, moneda))

        else:
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                meta_val2 = money_input(
                    "Meta de ahorro", moneda, min_value=1.0, value=100_000_000.0, step=1_000_000.0, key="meta_val2"
                )
            with col_m2:
                cuota_meta = money_input(
                    "Cuota periódica que puedes aportar",
                    moneda, min_value=1.0, value=cuota_ahorro, step=10_000.0, key="cuota_meta"
                )
                meta_inicial2 = money_input(
                    "Ahorro inicial", moneda, min_value=0.0, value=ahorro_inicial, step=100_000.0, key="meta_ini2"
                )
            periodos_necesarios = plan_ahorro_meses_para_meta(meta_val2, meta_inicial2, cuota_meta, tasa_periodica)
            if periodos_necesarios:
                anios_nec = periodos_necesarios // m
                per_nec = periodos_necesarios % m
                metric_card("Períodos necesarios", f"{periodos_necesarios}")
                result_box("Equivale a", f"{anios_nec} año(s) y {per_nec} período(s)")
                result_box("Total aportado al llegar a la meta",
                           fmt_currency(meta_inicial2 + cuota_meta * periodos_necesarios, moneda))
            else:
                st.error("No es posible alcanzar esa meta con la cuota indicada en un plazo razonable.")


# ─────────────────────────────────────────────
# MÓDULO 1: CONVERSIÓN DE TASAS
# ─────────────────────────────────────────────

elif modulo == "🔄 Conversión de Tasas":
    st.title("🔄 Conversión de Tasas de Interés")
    tab1, tab2, tab3 = st.tabs(
        ["Nominal ↔ Efectiva", "Tasa Equivalente", "Tabla Comparativa"]
    )

    with tab1:
        st.subheader("Conversión Nominal ↔ Efectiva Anual")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Nominal → Efectiva")
            tasa_nom = st.number_input("Tasa Nominal Anual (%)", min_value=0.0, value=12.0, step=0.1, key="nom1") / 100
            cap_nom = st.selectbox("Capitalización", list(PERIODOS_NOMBRES.keys()), index=4, key="cap1")
            m_nom = PERIODOS_NOMBRES[cap_nom]
            tef = tasa_nominal_a_efectiva(tasa_nom, m_nom)
            metric_card("Tasa Efectiva Anual", f"{tef*100:.4f}%")
            result_box("Tasa periódica", f"{(tasa_nom/m_nom)*100:.4f}%")

        with col2:
            st.markdown("#### Efectiva → Nominal")
            tasa_ef = st.number_input("Tasa Efectiva Anual (%)", min_value=0.0, value=12.68, step=0.1, key="ef1") / 100
            cap_ef = st.selectbox("Capitalización destino", list(PERIODOS_NOMBRES.keys()), index=4, key="cap2")
            m_ef = PERIODOS_NOMBRES[cap_ef]
            tnom_result = tasa_efectiva_a_nominal(tasa_ef, m_ef)
            metric_card("Tasa Nominal Anual", f"{tnom_result*100:.4f}%")
            result_box("Tasa periódica nominal", f"{(tnom_result/m_ef)*100:.4f}%")

    with tab2:
        st.subheader("Tasa Equivalente entre Períodos")
        col1, col2, col3 = st.columns(3)
        with col1:
            tasa_base = st.number_input("Tasa conocida (%)", min_value=0.0, value=12.0, step=0.1) / 100
        with col2:
            per_origen = st.selectbox("Período de la tasa conocida", list(PERIODOS_NOMBRES.keys()), index=0)
        with col3:
            per_destino = st.selectbox("Período destino", list(PERIODOS_NOMBRES.keys()), index=4)

        n_origen = PERIODOS_NOMBRES[per_origen]
        n_destino = PERIODOS_NOMBRES[per_destino]
        # Convertir a tasa por subperíodo base y luego al destino
        tasa_equiv = tasa_equivalente(tasa_base, n_destino, n_origen)
        st.markdown("")
        metric_card(f"Tasa equivalente {per_destino.lower()}", f"{tasa_equiv*100:.6f}%")
        result_box("Comprobación anual", f"{((1+tasa_equiv)**n_destino - 1)*100:.4f}%")

    with tab3:
        st.subheader("Tabla Comparativa de Tasas Equivalentes")
        tasa_anual_comp = st.number_input("Tasa Efectiva Anual (%)", min_value=0.01, value=20.0, step=0.5) / 100
        rows = []
        for nombre, m in PERIODOS_NOMBRES.items():
            te = tasa_equivalente(tasa_anual_comp, 1, m)  # de anual a subperíodo
            tn = tasa_efectiva_a_nominal(tasa_anual_comp, m)
            rows.append({
                "Período": nombre,
                "Períodos/año": m,
                "Tasa Efectiva Periódica (%)": f"{te*100:.6f}%",
                "Tasa Nominal Anual (%)": f"{tn*100:.4f}%",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────
# MÓDULO 2: INTERÉS SIMPLE
# ─────────────────────────────────────────────

elif modulo == "📈 Interés Simple":
    st.title("📈 Interés Simple")
    tab1, tab2 = st.tabs(["Calculadora", "Tabla de Capitalización"])

    with tab1:
        st.subheader("Calcular variable desconocida")
        incognita = st.selectbox(
            "Variable a calcular",
            ["Monto Final (VF)", "Capital Inicial (VP)", "Tasa de Interés (i)", "Tiempo (t)"],
        )
        col1, col2 = st.columns(2)

        if incognita == "Monto Final (VF)":
            with col1:
                c = money_input("Capital Inicial (VP)", moneda, min_value=0.0, value=10_000.0, step=100.0)
                i = st.number_input("Tasa de interés por período (%)", min_value=0.0, value=2.0, step=0.1) / 100
                t = st.number_input("Tiempo (períodos)", min_value=0.0, value=12.0, step=1.0)
            with col2:
                vf = interes_simple_monto_final(c, i, t)
                interes = interes_simple_interes(c, i, t)
                metric_card("Monto Final (VF)", fmt_currency(vf, moneda))
                result_box("Interés total generado", fmt_currency(interes, moneda))
                result_box("Capital inicial", fmt_currency(c, moneda))

        elif incognita == "Capital Inicial (VP)":
            with col1:
                vf = money_input("Monto Final (VF)", moneda, min_value=0.0, value=12_400.0, step=100.0)
                i = st.number_input("Tasa de interés por período (%)", min_value=0.0, value=2.0, step=0.1) / 100
                t = st.number_input("Tiempo (períodos)", min_value=0.0, value=12.0, step=1.0)
            with col2:
                c = interes_simple_capital(vf, i, t)
                metric_card("Capital Inicial (VP)", fmt_currency(c, moneda))
                result_box("Interés total", fmt_currency(vf - c, moneda))

        elif incognita == "Tasa de Interés (i)":
            with col1:
                c = money_input("Capital Inicial (VP)", moneda, min_value=0.01, value=10_000.0, step=100.0)
                vf = money_input("Monto Final (VF)", moneda, min_value=0.01, value=12_400.0, step=100.0)
                t = st.number_input("Tiempo (períodos)", min_value=0.01, value=12.0, step=1.0)
            with col2:
                i = interes_simple_tasa(c, vf, t)
                metric_card("Tasa por período", f"{i*100:.4f}%")
                result_box("Tasa anual (×12)", f"{i*12*100:.4f}%")

        else:  # Tiempo
            with col1:
                c = money_input("Capital Inicial (VP)", moneda, min_value=0.01, value=10_000.0, step=100.0)
                vf = money_input("Monto Final (VF)", moneda, min_value=0.01, value=12_400.0, step=100.0)
                i = st.number_input("Tasa de interés por período (%)", min_value=0.0001, value=2.0, step=0.1) / 100
            with col2:
                t = interes_simple_tiempo(c, vf, i)
                metric_card("Tiempo (períodos)", f"{t:.4f}")

    with tab2:
        st.subheader("Tabla de Capitalización Simple")
        col1, col2, col3 = st.columns(3)
        with col1:
            c_t = money_input("Capital (VP)", moneda, min_value=0.0, value=10_000.0, step=100.0, key="is_c")
        i_t = col2.number_input("Tasa por período (%)", min_value=0.0, value=2.0, step=0.1, key="is_i") / 100
        n_t = col3.number_input("Número de períodos", min_value=1, value=12, step=1, key="is_n")

        df = tabla_interes_simple(c_t, i_t, n_t)
        st.dataframe(fmt_df(df), use_container_width=True, hide_index=True)

        fig = px.line(df, x="Período", y="Saldo Final", title="Crecimiento del Capital (Interés Simple)",
                      markers=True, color_discrete_sequence=["#4f46e5"])
        fig.update_layout(yaxis_title="Saldo Final", xaxis_title="Período")
        st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────
# MÓDULO 3: INTERÉS COMPUESTO
# ─────────────────────────────────────────────

elif modulo == "📊 Interés Compuesto":
    st.title("📊 Interés Compuesto")
    tab1, tab2 = st.tabs(["Calculadora", "Tabla y Gráfica"])

    with tab1:
        st.subheader("Calcular variable desconocida")
        incognita = st.selectbox(
            "Variable a calcular",
            ["Valor Futuro (VF)", "Valor Presente (VP)", "Tasa de Interés (i)", "Tiempo (n)"],
        )
        col1, col2 = st.columns(2)

        if incognita == "Valor Futuro (VF)":
            with col1:
                vp = money_input("Valor Presente (VP)", moneda, min_value=0.0, value=10_000.0, step=100.0)
                i = st.number_input("Tasa efectiva por período (%)", min_value=0.0, value=2.0, step=0.1) / 100
                n = st.number_input("Número de períodos (n)", min_value=0.0, value=12.0, step=1.0)
            with col2:
                vf = interes_compuesto_monto_final(vp, i, n)
                metric_card("Valor Futuro (VF)", fmt_currency(vf, moneda))
                result_box("Interés total generado", fmt_currency(vf - vp, moneda))
                result_box("Factor (1+i)^n", f"{(1+i)**n:.6f}")

        elif incognita == "Valor Presente (VP)":
            with col1:
                vf = money_input("Valor Futuro (VF)", moneda, min_value=0.0, value=12_682.0, step=100.0)
                i = st.number_input("Tasa efectiva por período (%)", min_value=0.0, value=2.0, step=0.1) / 100
                n = st.number_input("Número de períodos (n)", min_value=0.0, value=12.0, step=1.0)
            with col2:
                vp = interes_compuesto_valor_presente(vf, i, n)
                metric_card("Valor Presente (VP)", fmt_currency(vp, moneda))
                result_box("Descuento total", fmt_currency(vf - vp, moneda))

        elif incognita == "Tasa de Interés (i)":
            with col1:
                vp = money_input("Valor Presente (VP)", moneda, min_value=0.01, value=10_000.0, step=100.0)
                vf = money_input("Valor Futuro (VF)", moneda, min_value=0.01, value=12_682.0, step=100.0)
                n = st.number_input("Número de períodos (n)", min_value=0.01, value=12.0, step=1.0)
            with col2:
                i = interes_compuesto_tasa(vp, vf, n)
                metric_card("Tasa por período", f"{i*100:.4f}%")

        else:
            with col1:
                vp = money_input("Valor Presente (VP)", moneda, min_value=0.01, value=10_000.0, step=100.0)
                vf = money_input("Valor Futuro (VF)", moneda, min_value=0.01, value=12_682.0, step=100.0)
                i = st.number_input("Tasa efectiva por período (%)", min_value=0.0001, value=2.0, step=0.1) / 100
            with col2:
                n = interes_compuesto_tiempo(vp, vf, i)
                metric_card("Número de períodos", f"{n:.4f}")

    with tab2:
        st.subheader("Tabla de Capitalización Compuesta")
        col1, col2, col3 = st.columns(3)
        with col1:
            c_t = money_input("Capital (VP)", moneda, min_value=0.0, value=10_000.0, step=100.0, key="ic_c")
        i_t = col2.number_input("Tasa por período (%)", min_value=0.0, value=2.0, step=0.1, key="ic_i") / 100
        n_t = col3.number_input("Número de períodos", min_value=1, value=12, step=1, key="ic_n")

        df = tabla_interes_compuesto(c_t, i_t, n_t)
        st.dataframe(fmt_df(df), use_container_width=True, hide_index=True)

        # Comparativa simple vs compuesto
        saldos_simple = [c_t * (1 + i_t * t) for t in range(n_t + 1)]
        saldos_comp = [c_t * (1 + i_t) ** t for t in range(n_t + 1)]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=list(range(n_t + 1)), y=saldos_simple, name="Interés Simple",
                                  mode="lines+markers", line=dict(color="#f59e0b", dash="dash")))
        fig.add_trace(go.Scatter(x=list(range(n_t + 1)), y=saldos_comp, name="Interés Compuesto",
                                  mode="lines+markers", line=dict(color="#4f46e5")))
        fig.update_layout(title="Simple vs Compuesto", xaxis_title="Período", yaxis_title="Saldo")
        st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────
# MÓDULO 4: ANUALIDADES
# ─────────────────────────────────────────────

elif modulo == "💳 Anualidades":
    st.title("💳 Anualidades")
    tipo_anualidad = st.radio("Tipo de anualidad", ["Vencida (Ordinaria)", "Anticipada"], horizontal=True)
    tab1, tab2, tab3 = st.tabs(["Valor Presente", "Valor Futuro", "Cuota"])

    col_cfg1, col_cfg2 = st.columns(2)

    if tipo_anualidad == "Vencida (Ordinaria)":
        with tab1:
            st.subheader("Valor Presente de Anualidad Vencida")
            c1, c2 = st.columns(2)
            with c1:
                cuota = money_input("Cuota periódica", moneda, min_value=0.0, value=500.0, step=50.0, key="av_vp_c")
                tasa = st.number_input("Tasa efectiva por período (%)", min_value=0.0, value=1.5, step=0.1, key="av_vp_i") / 100
                n = st.number_input("Número de períodos", min_value=1, value=24, step=1, key="av_vp_n")
            with c2:
                vp = anualidad_vp_ordinaria(cuota, tasa, n)
                metric_card("Valor Presente", fmt_currency(vp, moneda))
                result_box("Total pagado", fmt_currency(cuota * n, moneda))
                result_box("Total intereses", fmt_currency(cuota * n - vp, moneda))

        with tab2:
            st.subheader("Valor Futuro de Anualidad Vencida")
            c1, c2 = st.columns(2)
            with c1:
                cuota = money_input("Cuota periódica", moneda, min_value=0.0, value=500.0, step=50.0, key="av_vf_c")
                tasa = st.number_input("Tasa efectiva por período (%)", min_value=0.0, value=1.5, step=0.1, key="av_vf_i") / 100
                n = st.number_input("Número de períodos", min_value=1, value=24, step=1, key="av_vf_n")
            with c2:
                vf = anualidad_vf_ordinaria(cuota, tasa, n)
                metric_card("Valor Futuro", fmt_currency(vf, moneda))
                result_box("Total aportado", fmt_currency(cuota * n, moneda))
                result_box("Rendimiento total", fmt_currency(vf - cuota * n, moneda))

        with tab3:
            st.subheader("Cuota de Anualidad Vencida")
            c1, c2 = st.columns(2)
            with c1:
                base = st.radio("Calcular cuota desde", ["Valor Presente (VP)", "Valor Futuro (VF)"], key="av_cuota_base")
                val = money_input("Valor", moneda, min_value=0.0, value=10_000.0, step=100.0, key="av_cuota_val")
                tasa = st.number_input("Tasa efectiva por período (%)", min_value=0.0, value=1.5, step=0.1, key="av_cuota_i") / 100
                n = st.number_input("Número de períodos", min_value=1, value=24, step=1, key="av_cuota_n")
            with c2:
                if base == "Valor Presente (VP)":
                    cuota = anualidad_cuota_ordinaria(val, tasa, n)
                    metric_card("Cuota periódica", fmt_currency(cuota, moneda))
                    result_box("Total a pagar", fmt_currency(cuota * n, moneda))
                    result_box("Total intereses", fmt_currency(cuota * n - val, moneda))
                else:
                    vp_eq = anualidad_vp_ordinaria(1, tasa, n)
                    vf_eq = anualidad_vf_ordinaria(1, tasa, n)
                    cuota = val / vf_eq if vf_eq != 0 else 0
                    metric_card("Cuota periódica", fmt_currency(cuota, moneda))
                    result_box("Total aportado", fmt_currency(cuota * n, moneda))

    else:  # Anticipada
        with tab1:
            st.subheader("Valor Presente de Anualidad Anticipada")
            c1, c2 = st.columns(2)
            with c1:
                cuota = money_input("Cuota periódica", moneda, min_value=0.0, value=500.0, step=50.0, key="aa_vp_c")
                tasa = st.number_input("Tasa efectiva por período (%)", min_value=0.0, value=1.5, step=0.1, key="aa_vp_i") / 100
                n = st.number_input("Número de períodos", min_value=1, value=24, step=1, key="aa_vp_n")
            with c2:
                vp = anualidad_vp_anticipada(cuota, tasa, n)
                metric_card("Valor Presente", fmt_currency(vp, moneda))
                result_box("Total pagado", fmt_currency(cuota * n, moneda))
                result_box("Total intereses", fmt_currency(cuota * n - vp, moneda))

        with tab2:
            st.subheader("Valor Futuro de Anualidad Anticipada")
            c1, c2 = st.columns(2)
            with c1:
                cuota = money_input("Cuota periódica", moneda, min_value=0.0, value=500.0, step=50.0, key="aa_vf_c")
                tasa = st.number_input("Tasa efectiva por período (%)", min_value=0.0, value=1.5, step=0.1, key="aa_vf_i") / 100
                n = st.number_input("Número de períodos", min_value=1, value=24, step=1, key="aa_vf_n")
            with c2:
                vf = anualidad_vf_anticipada(cuota, tasa, n)
                metric_card("Valor Futuro", fmt_currency(vf, moneda))
                result_box("Total aportado", fmt_currency(cuota * n, moneda))
                result_box("Rendimiento", fmt_currency(vf - cuota * n, moneda))

        with tab3:
            st.subheader("Cuota de Anualidad Anticipada")
            c1, c2 = st.columns(2)
            with c1:
                vp = money_input("Valor Presente (VP)", moneda, min_value=0.0, value=10_000.0, step=100.0, key="aa_cuota_vp")
                tasa = st.number_input("Tasa efectiva por período (%)", min_value=0.0, value=1.5, step=0.1, key="aa_cuota_i") / 100
                n = st.number_input("Número de períodos", min_value=1, value=24, step=1, key="aa_cuota_n")
            with c2:
                cuota = anualidad_cuota_anticipada(vp, tasa, n)
                metric_card("Cuota periódica", fmt_currency(cuota, moneda))
                result_box("Total a pagar", fmt_currency(cuota * n, moneda))
                result_box("Total intereses", fmt_currency(cuota * n - vp, moneda))


# ─────────────────────────────────────────────
# MÓDULO 5: GRADIENTES
# ─────────────────────────────────────────────

elif modulo == "📐 Gradientes":
    st.title("📐 Gradientes")
    tipo_grad = st.radio("Tipo de gradiente", ["Aritmético", "Geométrico"], horizontal=True)

    col1, col2 = st.columns(2)

    if tipo_grad == "Aritmético":
        st.subheader("Gradiente Aritmético")
        st.markdown("Las cuotas aumentan (o disminuyen) en un valor constante **G** cada período.")

        with col1:
            cuota1 = money_input("Primera cuota (A₁)", moneda, min_value=0.0, value=1_000.0, step=100.0, key="ga_c1")
            g = money_input("Gradiente (G)", moneda, value=100.0, step=50.0, key="ga_g")
            tasa = st.number_input("Tasa efectiva por período (%)", min_value=0.0, value=2.0, step=0.1, key="ga_i") / 100
            n = st.number_input("Número de períodos", min_value=1, value=12, step=1, key="ga_n")

        with col2:
            vp = gradiente_aritmetico_vp(cuota1, g, tasa, n)
            vf = gradiente_aritmetico_vf(cuota1, g, tasa, n)
            metric_card("Valor Presente (VP)", fmt_currency(vp, moneda))
            metric_card("Valor Futuro (VF)", fmt_currency(vf, moneda))
            result_box("Cuota equivalente uniforme", fmt_currency(anualidad_cuota_ordinaria(vp, tasa, n), moneda))

        df = tabla_gradiente(cuota1, g, n, "aritmetico")
        st.subheader("Flujo de Cuotas")
        col_a, col_b = st.columns([2, 3])
        with col_a:
            st.dataframe(fmt_df(df), use_container_width=True, hide_index=True)
        with col_b:
            fig = px.bar(df, x="Período", y="Cuota", title="Gradiente Aritmético",
                         color_discrete_sequence=["#4f46e5"])
            st.plotly_chart(fig, use_container_width=True)

    else:  # Geométrico
        st.subheader("Gradiente Geométrico")
        st.markdown("Las cuotas crecen en una tasa porcentual constante **g** cada período.")

        with col1:
            cuota1 = money_input("Primera cuota (A₁)", moneda, min_value=0.0, value=1_000.0, step=100.0, key="gg_c1")
            g = st.number_input("Tasa de crecimiento del gradiente (%)", value=3.0, step=0.5, key="gg_g") / 100
            tasa = st.number_input("Tasa efectiva por período (%)", min_value=0.0, value=2.0, step=0.1, key="gg_i") / 100
            n = st.number_input("Número de períodos", min_value=1, value=12, step=1, key="gg_n")

        with col2:
            vp = gradiente_geometrico_vp(cuota1, g, tasa, n)
            vf = gradiente_geometrico_vf(cuota1, g, tasa, n)
            metric_card("Valor Presente (VP)", fmt_currency(vp, moneda))
            metric_card("Valor Futuro (VF)", fmt_currency(vf, moneda))

        df = tabla_gradiente(cuota1, g, n, "geometrico")
        st.subheader("Flujo de Cuotas")
        col_a, col_b = st.columns([2, 3])
        with col_a:
            st.dataframe(fmt_df(df), use_container_width=True, hide_index=True)
        with col_b:
            fig = px.bar(df, x="Período", y="Cuota", title="Gradiente Geométrico",
                         color_discrete_sequence=["#059669"])
            st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────
# MÓDULO 6: AMORTIZACIÓN
# ─────────────────────────────────────────────

elif modulo == "🏦 Amortización":
    st.title("🏦 Tabla de Amortización")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        capital = money_input("Capital del crédito", moneda, min_value=100.0, value=50_000_000.0, step=1_000_000.0)
    tasa_pct = col2.number_input("Tasa efectiva por período (%)", min_value=0.001, value=1.5, step=0.1)
    n_periodos = col3.number_input("Número de cuotas", min_value=1, value=36, step=1)
    sistema = col4.selectbox("Sistema", ["Francés (Cuota constante)", "Alemán (Capital constante)", "Americano (Bullet)"])

    tasa = tasa_pct / 100

    tab_tabla, tab_grafica, tab_resumen = st.tabs(["Tabla", "Gráfica", "Resumen"])

    if sistema == "Francés (Cuota constante)":
        df, cuota = amortizacion_frances(capital, tasa, n_periodos)
        cuota_display = cuota
    elif sistema == "Alemán (Capital constante)":
        df = amortizacion_aleman(capital, tasa, n_periodos)
        cuota_display = None
    else:
        df = amortizacion_americano(capital, tasa, n_periodos)
        cuota_display = None

    with tab_tabla:
        if cuota_display:
            st.info(f"**Cuota fija:** {fmt_currency(cuota_display, moneda)}")
        st.dataframe(fmt_df(df), use_container_width=True, hide_index=True)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Descargar CSV", csv, "amortizacion.csv", "text/csv")

    with tab_grafica:
        df_num = df[df["Período"] != "TOTAL"].copy()
        for col in ["Intereses", "Abono Capital", "Saldo Final", "Cuota Total"]:
            df_num[col] = pd.to_numeric(df_num[col], errors="coerce")
        df_num["Período"] = pd.to_numeric(df_num["Período"], errors="coerce")

        fig1 = go.Figure()
        fig1.add_trace(go.Bar(x=df_num["Período"], y=df_num["Abono Capital"],
                               name="Abono Capital", marker_color="#4f46e5"))
        fig1.add_trace(go.Bar(x=df_num["Período"], y=df_num["Intereses"],
                               name="Intereses", marker_color="#f59e0b"))
        fig1.update_layout(barmode="stack", title="Composición de la Cuota por Período",
                            xaxis_title="Período", yaxis_title="Valor")
        st.plotly_chart(fig1, use_container_width=True)

        fig2 = px.area(df_num, x="Período", y="Saldo Final",
                       title="Evolución del Saldo de la Deuda",
                       color_discrete_sequence=["#ef4444"])
        st.plotly_chart(fig2, use_container_width=True)

    with tab_resumen:
        total_row = df[df["Período"] == "TOTAL"].iloc[0]
        total_pagado = pd.to_numeric(total_row["Cuota Total"], errors="coerce")
        total_intereses = pd.to_numeric(total_row["Intereses"], errors="coerce")

        col_r1, col_r2, col_r3 = st.columns(3)
        with col_r1:
            metric_card("Capital Financiado", fmt_currency(capital, moneda))
        with col_r2:
            metric_card("Total Intereses", fmt_currency(total_intereses, moneda))
        with col_r3:
            metric_card("Total Pagado", fmt_currency(total_pagado, moneda))

        costo = (total_intereses / capital) * 100
        result_box("Costo del crédito sobre el capital", f"{costo:.2f}%")
        result_box("Tasa efectiva por período", f"{tasa*100:.4f}%")
        result_box("Número de cuotas", str(n_periodos))


# ─────────────────────────────────────────────
# MÓDULO 7: VPN / TIR
# ─────────────────────────────────────────────

elif modulo == "📉 VPN / TIR":
    st.title("📉 VPN / TIR — Evaluación de Proyectos")

    st.subheader("Ingresa los Flujos de Caja")
    col1, col2 = st.columns([1, 2])

    with col1:
        inversion = money_input("Inversión inicial (período 0)", moneda, min_value=0.0, value=10_000_000.0, step=100_000.0)
        n_flujos = st.number_input("Número de períodos de flujo", min_value=1, value=5, step=1, max_value=30)
        tasa_desc = st.number_input("Tasa de descuento (%)", min_value=0.0, value=10.0, step=0.5) / 100

        st.markdown("#### Flujos de Caja (períodos 1 a n)")
        flujos_entrada = []
        for i in range(1, n_flujos + 1):
            f = money_input(f"Flujo período {i}", moneda, value=3_000_000.0, step=100_000.0, key=f"flujo_{i}")
            flujos_entrada.append(f)

    flujos_completos = [-inversion] + flujos_entrada

    with col2:
        vpn = calcular_vpn(tasa_desc, flujos_completos)
        tir = calcular_tir(flujos_completos)

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            metric_card("VPN", fmt_currency(vpn, moneda))
        with col_m2:
            if tir is not None:
                metric_card("TIR", f"{tir*100:.4f}%")
            else:
                metric_card("TIR", "No encontrada")

        if vpn > 0:
            st.success("✅ El proyecto es **viable** (VPN > 0)")
        elif vpn == 0:
            st.warning("⚠️ El proyecto es **indiferente** (VPN = 0)")
        else:
            st.error("❌ El proyecto **no es viable** (VPN < 0)")

        if tir is not None:
            if tir > tasa_desc:
                st.success(f"✅ TIR ({tir*100:.2f}%) > Tasa de descuento ({tasa_desc*100:.2f}%) → Viable")
            else:
                st.error(f"❌ TIR ({tir*100:.2f}%) < Tasa de descuento ({tasa_desc*100:.2f}%) → No viable")

        # Tabla de flujos
        st.markdown("#### Flujos descontados")
        rows = []
        for t, f in enumerate(flujos_completos):
            fd = f / (1 + tasa_desc) ** t
            rows.append({"Período": t, "Flujo de Caja": f, "Flujo Descontado": fd})
        df_flujos = pd.DataFrame(rows)
        st.dataframe(fmt_df(df_flujos), use_container_width=True, hide_index=True)

        # Gráfica de flujos
        fig = go.Figure()
        colores = ["#ef4444" if f < 0 else "#22c55e" for f in flujos_completos]
        fig.add_trace(go.Bar(
            x=list(range(len(flujos_completos))),
            y=flujos_completos,
            marker_color=colores,
            name="Flujo de Caja",
        ))
        fig.update_layout(title="Diagrama de Flujo de Caja", xaxis_title="Período", yaxis_title="Flujo")
        st.plotly_chart(fig, use_container_width=True)

    # Análisis de sensibilidad VPN
    st.markdown("---")
    st.subheader("Análisis de Sensibilidad del VPN")
    col_s1, col_s2 = st.columns(2)
    tmin = col_s1.number_input("Tasa mínima (%)", min_value=0.0, value=0.0, step=1.0) / 100
    tmax = col_s2.number_input("Tasa máxima (%)", min_value=0.1, value=50.0, step=1.0) / 100

    df_sens = tabla_vpn_sensibilidad(flujos_completos, tmin, tmax, pasos=40)
    fig_sens = px.line(df_sens, x="Tasa (%)", y="VPN",
                       title="VPN en función de la Tasa de Descuento",
                       color_discrete_sequence=["#4f46e5"])
    fig_sens.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="VPN = 0")
    if tir is not None:
        fig_sens.add_vline(x=tir * 100, line_dash="dot", line_color="green",
                           annotation_text=f"TIR = {tir*100:.2f}%")
    st.plotly_chart(fig_sens, use_container_width=True)
