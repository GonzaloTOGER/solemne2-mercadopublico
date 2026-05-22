"""
=============================================================
Solemne II - FITO9017
Aplicación principal: DataViz Mercado Público Chile
Desarrollada con Streamlit
=============================================================

Ejecutar localmente:
    streamlit run app.py

Deploy en Streamlit Community Cloud:
    1. Subir este proyecto a GitHub
    2. Conectar en share.streamlit.io
    3. Seleccionar app.py como archivo principal
=============================================================
"""

import streamlit as st
import pandas as pd
import time

# Importar módulos del proyecto
from api_mercadopublico import construir_dataframe
from analisis import (
    cargar_datos, resumen_general, analisis_por_tipo,
    analisis_por_region, top_organismos, analisis_montos,
    analisis_dias_cierre,
)
from visualizaciones import (
    grafico_por_region, grafico_por_tipo,
    grafico_top_organismos, grafico_dias_cierre,
)

# ── Configuración de la página ───────────────────────────────
st.set_page_config(
    page_title="DataViz Mercado Público Chile",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Estilos CSS personalizados ───────────────────────────────
st.markdown("""
<style>
    .metric-card {
        background: #f0f4fa;
        border-left: 4px solid #1a3a5c;
        border-radius: 6px;
        padding: 12px 16px;
        margin: 4px 0;
    }
    .metric-card h3 { font-size: 1.8rem; color: #1a3a5c; margin: 0; }
    .metric-card p  { font-size: 0.85rem; color: #555; margin: 0; }
    .stAlert { border-radius: 6px; }
    h1 { color: #1a3a5c; }
    h2 { color: #2e6da4; border-bottom: 2px solid #e0eaf5; padding-bottom: 6px; }
</style>
""", unsafe_allow_html=True)


# ── Funciones cacheadas ──────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def obtener_datos(estado, cantidad):
    """
    Obtiene datos desde la API y los cachea por 30 minutos (ttl=1800 seg).
    Evita llamadas repetidas a la API en cada interacción del usuario.
    """
    return construir_dataframe(estado=estado, cantidad=cantidad)


# ── SIDEBAR — Panel de control ───────────────────────────────
with st.sidebar:
    st.image("https://www.chilecompra.cl/wp-content/uploads/2021/04/logo-chilecompra.png",
             width=160)
    st.title("⚙️ Panel de control")
    st.markdown("---")

    st.subheader("Parámetros de consulta")

    estado_sel = st.selectbox(
        "Estado de licitaciones",
        options=["activas", "adjudicadas", "cerradas", "todas"],
        index=0,
        help="Filtra las licitaciones según su estado en Mercado Público"
    )

    cantidad_sel = st.slider(
        "Número de licitaciones a consultar",
        min_value=5,
        max_value=50,
        value=20,
        step=5,
        help="Más licitaciones = más tiempo de carga (1 request por licitación)"
    )

    st.markdown("---")
    cargar_btn = st.button("🔄 Cargar / Actualizar datos", type="primary",
                           use_container_width=True)

    st.markdown("---")
    st.subheader("🔎 Filtros de análisis")

    st.markdown("---")
    st.caption("**Fuente de datos:** API Mercado Público Chile")
    st.caption("api.mercadopublico.cl")
    st.caption("**Asignatura:** FITO9017 — Solemne II")


# ── ESTADO DE SESIÓN ─────────────────────────────────────────
if "df" not in st.session_state:
    st.session_state.df = None

if cargar_btn or st.session_state.df is None:
    with st.spinner("🔗 Consultando API Mercado Público..."):
        try:
            df = obtener_datos(estado_sel, cantidad_sel)
            st.session_state.df = df
            st.sidebar.success(f"✅ {len(df)} licitaciones cargadas")
        except Exception as e:
            st.error(f"❌ Error al conectar con la API: {e}")
            st.stop()

df = st.session_state.df

# ── Filtros dinámicos del sidebar ───────────────────────────
with st.sidebar:
    regiones_disponibles = sorted(
        df["region_corta"].dropna().unique().tolist()
    )
    regiones_sel = st.multiselect(
        "Filtrar por región",
        options=regiones_disponibles,
        default=regiones_disponibles,
        help="Selecciona una o más regiones"
    )

    tipos_disponibles = sorted(df["tipo"].dropna().unique().tolist())
    tipos_sel = st.multiselect(
        "Filtrar por tipo",
        options=tipos_disponibles,
        default=tipos_disponibles,
    )

# Aplicar filtros al DataFrame
df_filtrado = df[
    (df["region_corta"].isin(regiones_sel)) &
    (df["tipo"].isin(tipos_sel))
].copy()

# ── HEADER PRINCIPAL ─────────────────────────────────────────
st.title("🏛️ DataViz — Mercado Público Chile")
st.markdown(
    "Análisis interactivo de licitaciones públicas del Estado de Chile "
    "obtenidas en tiempo real desde la **API oficial de Mercado Público**."
)

# ── SECCIÓN 1: MÉTRICAS CLAVE ────────────────────────────────
st.header("📊 Resumen general")
res = resumen_general(df_filtrado)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Total licitaciones",
        value=f"{res['total_licitaciones']:,}",
        delta=f"de {len(df):,} consultadas",
    )
with col2:
    st.metric(
        label="Regiones representadas",
        value=res["regiones_unicas"],
    )
with col3:
    st.metric(
        label="Organismos únicos",
        value=res["organismos_unicos"],
    )
with col4:
    monto = res.get("monto_total_CLP") or 0
    st.metric(
        label="Monto total estimado",
        value=f"${monto/1_000_000:,.0f}M CLP" if monto else "No disponible",
        help="Solo licitaciones con monto informado"
    )

st.divider()

# ── SECCIÓN 2: VISUALIZACIONES ───────────────────────────────
st.header("📈 Análisis visual")

col_izq, col_der = st.columns(2)

with col_izq:
    st.subheader("🗺️ Licitaciones por región")
    if df_filtrado.empty:
        st.warning("Sin datos para mostrar con los filtros actuales.")
    else:
        fig1 = grafico_por_region(df_filtrado)
        st.pyplot(fig1, use_container_width=True)
        st.caption(
            "Las regiones con más licitaciones activas reflejan mayor actividad "
            "de compra pública en esas zonas del territorio nacional."
        )

with col_der:
    st.subheader("📋 Distribución por tipo")
    if df_filtrado.empty:
        st.warning("Sin datos para mostrar con los filtros actuales.")
    else:
        fig2 = grafico_por_tipo(df_filtrado)
        st.pyplot(fig2, use_container_width=True)
        st.caption(
            "**LE** = Licitación pública ≤1000 UTM | "
            "**LP** = Licitación pública >1000 UTM | "
            "**LR** = Licitación privada"
        )

st.divider()

col_izq2, col_der2 = st.columns(2)

with col_izq2:
    st.subheader("🏛️ Top organismos compradores")
    n_org = st.slider("Mostrar top N organismos", 3, 10, 8, key="slider_org")
    fig3 = grafico_top_organismos(df_filtrado, n=n_org)
    st.pyplot(fig3, use_container_width=True)
    st.caption(
        "Identifica qué servicios o ministerios son los principales "
        "compradores del Estado en el período analizado."
    )

with col_der2:
    st.subheader("⏱️ Plazos de cierre")
    fig4 = grafico_dias_cierre(df_filtrado)
    st.pyplot(fig4, use_container_width=True)
    st.caption(
        "Distribución de los días que los oferentes tienen disponibles "
        "para preparar y enviar sus ofertas antes del cierre."
    )

st.divider()

# ── SECCIÓN 3: ANÁLISIS DETALLADO ───────────────────────────
st.header("🔍 Análisis detallado")

tab1, tab2, tab3 = st.tabs(["Por región", "Por tipo", "Tabla de datos"])

with tab1:
    st.subheader("Desglose por región")
    df_region = analisis_por_region(df_filtrado)
    st.dataframe(
        df_region.rename(columns={
            "region_corta":   "Región",
            "cantidad":       "Licitaciones",
            "monto_promedio": "Monto Prom. (CLP)",
            "total_reclamos": "Total Reclamos",
            "porcentaje":     "% del total",
        }),
        use_container_width=True,
        hide_index=True,
    )

with tab2:
    st.subheader("Desglose por tipo de licitación")
    df_tipo = analisis_por_tipo(df_filtrado)
    st.dataframe(
        df_tipo.rename(columns={
            "tipo":             "Código",
            "tipo_descripcion": "Descripción",
            "cantidad":         "Licitaciones",
            "porcentaje":       "% del total",
        }),
        use_container_width=True,
        hide_index=True,
    )

with tab3:
    st.subheader("Dataset completo")
    # Búsqueda por nombre
    busqueda = st.text_input(
        "🔎 Buscar en nombre de licitación",
        placeholder="Ej: hospital, pavimentación, consultoria...",
    )
    df_mostrar = df_filtrado.copy()
    if busqueda:
        df_mostrar = df_mostrar[
            df_mostrar["nombre"].str.contains(busqueda, case=False, na=False)
        ]
        st.caption(f"Mostrando {len(df_mostrar)} resultado(s) para '{busqueda}'")

    cols_mostrar = ["codigo", "nombre", "tipo", "estado", "region_corta",
                    "organismo", "monto_estimado", "dias_cierre", "fecha_publicacion"]
    st.dataframe(
        df_mostrar[cols_mostrar].rename(columns={
            "codigo":           "Código",
            "nombre":           "Nombre",
            "tipo":             "Tipo",
            "estado":           "Estado",
            "region_corta":     "Región",
            "organismo":        "Organismo",
            "monto_estimado":   "Monto (CLP)",
            "dias_cierre":      "Días cierre",
            "fecha_publicacion":"Fecha publicación",
        }),
        use_container_width=True,
        hide_index=True,
    )
    st.caption(f"Total filas: {len(df_mostrar)}")

st.divider()

# ── FOOTER ───────────────────────────────────────────────────
st.markdown("""
<div style='text-align:center; color:#888; font-size:0.82rem; padding:12px'>
    Solemne II — FITO9017 | Universidad San Sebastián |
    Datos: API Mercado Público Chile (api.mercadopublico.cl) |
    Desarrollado con Python · Pandas · Matplotlib · Streamlit
</div>
""", unsafe_allow_html=True)
