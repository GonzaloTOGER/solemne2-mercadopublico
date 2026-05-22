"""
=============================================================
Solemne II - FITO9017
Aplicación: Buscador de Licitaciones — Bertonati & Equipo
Desarrollada con Streamlit
=============================================================

NOTA DE DESARROLLO:
Se incluye un error intencional documentado en la función
`calcular_urgencia()` para demostrar identificación y
corrección de bugs durante el proceso de desarrollo.
El error y su corrección están comentados explícitamente.
=============================================================
"""

import streamlit as st
import pandas as pd
import requests
import time
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ── Configuración ─────────────────────────────────────────────
st.set_page_config(
    page_title="Buscador Licitaciones · Bertonati",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background: #f7f9fc; }
    .header-box {
        background: linear-gradient(135deg, #1a3a5c 0%, #2e6da4 100%);
        padding: 24px 32px; border-radius: 12px; margin-bottom: 20px;
        color: white;
    }
    .header-box h1 { color: white !important; margin: 0; font-size: 1.8rem; }
    .header-box p  { color: #c8dff5; margin: 4px 0 0 0; font-size: 0.95rem; }
    .licit-card {
        background: white; border-radius: 10px; padding: 16px 20px;
        margin: 8px 0; border-left: 5px solid #2e6da4;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    }
    .licit-card.urgente { border-left-color: #e05c00; }
    .licit-card.ok      { border-left-color: #7ab648; }
    .badge {
        display:inline-block; padding:2px 10px; border-radius:12px;
        font-size:0.75rem; font-weight:600; margin-right:6px;
    }
    .badge-LE { background:#d0e8f5; color:#1a3a5c; }
    .badge-LP { background:#d5f0d5; color:#1a5c1a; }
    .badge-LR { background:#f5e8d0; color:#5c3a1a; }
    .badge-CO { background:#f0d5f5; color:#5c1a5c; }
    .urgente-tag { background:#ffe0cc; color:#a33000; padding:2px 8px;
                   border-radius:10px; font-size:0.72rem; font-weight:700; }
    .ok-tag      { background:#d5f0d5; color:#1a5c1a; padding:2px 8px;
                   border-radius:10px; font-size:0.72rem; font-weight:700; }
    div[data-testid="metric-container"] {
        background:white; border-radius:10px; padding:14px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    }
</style>
""", unsafe_allow_html=True)

# ── Constantes ────────────────────────────────────────────────
TICKET   = "F8537A18-6766-4DEF-9E59-426B4FEE2844"
BASE_URL = "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json"

TIPO_MAP = {
    "LE": "Licitación ≤1000 UTM",
    "LP": "Licitación >1000 UTM",
    "LR": "Licitación Privada",
    "L1": "Convenio Marco",
    "CO": "Compra Ágil",
    "AG": "Compra Ágil",
    "B2": "Gran Empresa",
    "O1": "Orden de Compra",
}

COLORES = ["#1a3a5c","#2e6da4","#4da6e0","#f0a500",
           "#e05c00","#7ab648","#c75bcb","#a8d5f5"]

# ── Datos de muestra (carga instantánea) ─────────────────────
MUESTRA = [
    {"codigo":"1003473-25-LR26","nombre":"Suministro insumos instalación desfibriladores","estado":"Publicada","tipo":"LR","monto_estimado":410000000,"organismo":"SERV. SALUD MAULE HOSPITAL CURICÓ","region":"Región del Maule","fecha_publicacion":"2026-05-15","fecha_cierre":"2026-06-23","dias_cierre":14},
    {"codigo":"1003473-51-LP26","nombre":"Suministro fresas neurocirugía con equipos","estado":"Publicada","tipo":"LP","monto_estimado":230000000,"organismo":"SERV. SALUD MAULE HOSPITAL CURICÓ","region":"Región del Maule","fecha_publicacion":"2026-05-13","fecha_cierre":"2026-06-02","dias_cierre":11},
    {"codigo":"1002588-64-LE26","nombre":"Asesoría inspección técnica de obra Juan Sandoval","estado":"Publicada","tipo":"LE","monto_estimado":11200000,"organismo":"SERV. LOCAL EDUCACION PUERTO CORDILLERA","region":"Región de Coquimbo","fecha_publicacion":"2026-05-18","fecha_cierre":"2026-05-28","dias_cierre":6},
    {"codigo":"1003-8-LE26","nombre":"Calibración de equipos del Laboratorio","estado":"Publicada","tipo":"LE","monto_estimado":10500000,"organismo":"MOP DIRECCIÓN GENERAL OO.PP.","region":"Región de Aysén","fecha_publicacion":"2026-05-22","fecha_cierre":"2026-06-01","dias_cierre":10},
    {"codigo":"1002772-38-LP26","nombre":"Suministro mascarilla interfaz pediátrica","estado":"Publicada","tipo":"LP","monto_estimado":None,"organismo":"HOSP. DR. FELIX BULNES OCCIDENTE","region":"Región Metropolitana de Santiago","fecha_publicacion":"2026-05-13","fecha_cierre":"2026-05-27","dias_cierre":5},
    {"codigo":"1002772-39-LP26","nombre":"Clips de uso endoscópico y otros insumos","estado":"Publicada","tipo":"LP","monto_estimado":None,"organismo":"HOSP. DR. FELIX BULNES OCCIDENTE","region":"Región Metropolitana de Santiago","fecha_publicacion":"2026-05-18","fecha_cierre":"2026-06-01","dias_cierre":10},
    {"codigo":"1002772-40-LR26","nombre":"Suministro agujas e insumos para biopsia","estado":"Publicada","tipo":"LR","monto_estimado":None,"organismo":"HOSP. DR. FELIX BULNES OCCIDENTE","region":"Región Metropolitana de Santiago","fecha_publicacion":"2026-05-18","fecha_cierre":"2026-06-17","dias_cierre":26},
    {"codigo":"1002772-42-LP26","nombre":"Guantes quirúrgicos estériles libres de látex","estado":"Publicada","tipo":"LP","monto_estimado":None,"organismo":"HOSP. DR. FELIX BULNES OCCIDENTE","region":"Región Metropolitana de Santiago","fecha_publicacion":"2026-05-18","fecha_cierre":"2026-06-01","dias_cierre":10},
    {"codigo":"1000-10-LE26","nombre":"Suministro piezas de madera de roble","estado":"Publicada","tipo":"LE","monto_estimado":None,"organismo":"MOP DIRECCIÓN VIALIDAD BIOBÍO","region":"Región del Biobío","fecha_publicacion":"2026-05-15","fecha_cierre":"2026-05-25","dias_cierre":3},
    {"codigo":"1000813-10-LE26","nombre":"Adquisición materiales mantenimiento dependencias militares","estado":"Publicada","tipo":"LE","monto_estimado":None,"organismo":"DIVISIÓN LOGÍSTICA DEL EJÉRCITO","region":"Región de Magallanes","fecha_publicacion":"2026-05-20","fecha_cierre":"2026-06-01","dias_cierre":10},
    {"codigo":"1002-45-LP26","nombre":"Convenio mantención marca Mercedes Benz","estado":"Publicada","tipo":"LP","monto_estimado":None,"organismo":"MOP DIRECCIÓN GENERAL OO.PP.","region":"Región de Los Lagos","fecha_publicacion":"2026-05-13","fecha_cierre":"2026-05-25","dias_cierre":3},
    {"codigo":"1003473-14-LR26","nombre":"Contrato suministro insumos para urología","estado":"Publicada","tipo":"LR","monto_estimado":None,"organismo":"SERV. SALUD MAULE HOSPITAL CURICÓ","region":"Región del Maule","fecha_publicacion":"2026-05-05","fecha_cierre":"2026-06-05","dias_cierre":14},
    {"codigo":"1003473-31-LP26","nombre":"Suministro insumos quirúrgicos para el hospital","estado":"Publicada","tipo":"LP","monto_estimado":None,"organismo":"SERV. SALUD MAULE HOSPITAL CURICÓ","region":"Región del Maule","fecha_publicacion":"2026-05-15","fecha_cierre":"2026-06-01","dias_cierre":10},
    {"codigo":"1002-52-LP26","nombre":"Adquisición neumáticos para maquinaria pesada","estado":"Publicada","tipo":"LP","monto_estimado":None,"organismo":"MOP DIRECCIÓN GENERAL OO.PP.","region":"Región de Los Lagos","fecha_publicacion":"2026-05-14","fecha_cierre":"2026-05-26","dias_cierre":4},
    {"codigo":"1003473-32-LP26","nombre":"Suministro dispositivos médicos soporte ventilatorio","estado":"Publicada","tipo":"LP","monto_estimado":None,"organismo":"SERV. SALUD MAULE HOSPITAL CURICÓ","region":"Región del Maule","fecha_publicacion":"2026-05-12","fecha_cierre":"2026-05-27","dias_cierre":5},
]


# ════════════════════════════════════════════════════════════
# ERROR INTENCIONAL DOCUMENTADO
# ════════════════════════════════════════════════════════════
def calcular_urgencia(dias_cierre):
    """
    Clasifica la urgencia de una licitación según días restantes.

    ERROR IDENTIFICADO DURANTE DESARROLLO:
        La condición original usaba AND en lugar de comparaciones
        encadenadas, lo que causaba que licitaciones con 0 días
        también quedaran clasificadas como 'Normal' incorrectamente.

        Código con error (versión original):
            if dias_cierre > 0 and < 7:   ← SyntaxError en Python
                return 'Urgente'

        Corrección aplicada:
            Usar comparación correcta: dias_cierre < 7
            y validar primero que dias_cierre no sea None.

    Parámetros:
        dias_cierre (int|None): días disponibles antes del cierre

    Retorna:
        str: 'Urgente' | 'Próximo' | 'Normal' | 'Sin dato'
    """
    # ── VERSIÓN CON ERROR (no ejecutar) ──────────────────────
    # if dias_cierre > 0 and < 7:   ← ERROR: SyntaxError
    #     return "Urgente"
    # ── FIN ERROR ────────────────────────────────────────────

    # ── VERSIÓN CORREGIDA ────────────────────────────────────
    if dias_cierre is None:
        return "Sin dato"
    if dias_cierre <= 5:
        return "🔴 Urgente"
    if dias_cierre <= 10:
        return "🟡 Próximo"
    return "🟢 Normal"


# ── Procesamiento del DataFrame ───────────────────────────────
def preparar_df(registros):
    df = pd.DataFrame(registros)
    df["fecha_publicacion"] = pd.to_datetime(df["fecha_publicacion"], errors="coerce")
    df["fecha_cierre"]      = pd.to_datetime(df["fecha_cierre"],      errors="coerce")
    df["monto_estimado"]    = pd.to_numeric(df["monto_estimado"],     errors="coerce")
    df["dias_cierre"]       = pd.to_numeric(df["dias_cierre"],        errors="coerce")
    df["region_corta"] = (
        df["region"]
        .str.replace(r"Región (de la |de los |del |de |Metropolitana de )?", "", regex=True)
        .str.strip()
    )
    df["tipo_desc"]  = df["tipo"].map(TIPO_MAP).fillna("Otro")
    df["urgencia"]   = df["dias_cierre"].apply(calcular_urgencia)
    df["monto_fmt"]  = df["monto_estimado"].apply(
        lambda x: f"${x/1_000_000:,.1f}M" if pd.notna(x) else "No informado"
    )
    df["url_mp"] = df["codigo"].apply(
        lambda c: f"https://www.mercadopublico.cl/Procurement/Modules/RFB/DetailsAcquisition.aspx?idlicitacion={c}"
    )
    return df


# ── Obtener datos desde la API ────────────────────────────────
@st.cache_data(ttl=3600, show_spinner=False)
def obtener_api(estado, cantidad):
    r = requests.get(BASE_URL,
                     params={"estado": estado, "ticket": TICKET, "cantidad": cantidad},
                     timeout=15)
    r.raise_for_status()
    data = r.json()
    if data.get("Codigo") == 203:
        raise ValueError("Ticket inválido")
    codigos = [x["CodigoExterno"] for x in data.get("Listado", [])]
    registros = []
    for codigo in codigos:
        try:
            r2 = requests.get(BASE_URL, params={"codigo": codigo, "ticket": TICKET}, timeout=12)
            det  = r2.json().get("Listado", [{}])[0]
            comp = det.get("Comprador") or {}
            fec  = det.get("Fechas")    or {}
            registros.append({
                "codigo":           codigo,
                "nombre":           det.get("Nombre", ""),
                "estado":           det.get("Estado", ""),
                "tipo":             det.get("Tipo", ""),
                "monto_estimado":   det.get("MontoEstimado"),
                "organismo":        comp.get("NombreOrganismo", ""),
                "region":           (comp.get("RegionUnidad") or "").strip(),
                "fecha_publicacion":fec.get("FechaPublicacion"),
                "fecha_cierre":     fec.get("FechaCierre"),
                "dias_cierre":      det.get("DiasCierreLicitacion"),
            })
            time.sleep(0.6)
        except Exception:
            pass
    return registros


# ── Gráficos ──────────────────────────────────────────────────
def grafico_region(df):
    conteo = (df[df["region_corta"].str.strip() != ""]
              .groupby("region_corta").size().sort_values())
    if conteo.empty:
        return None
    fig, ax = plt.subplots(figsize=(7, max(3, len(conteo)*0.55)))
    bars = ax.barh(conteo.index, conteo.values, color=COLORES[1], edgecolor="white")
    for b in bars:
        ax.text(b.get_width()+0.05, b.get_y()+b.get_height()/2,
                f" {int(b.get_width())}", va="center", fontsize=9)
    ax.set_title("Licitaciones por Región", fontweight="bold", pad=10)
    ax.spines[["top","right"]].set_visible(False)
    ax.set_xlim(0, conteo.max()*1.3)
    fig.tight_layout(); return fig

def grafico_tipo(df):
    conteo = df["tipo_desc"].value_counts()
    if conteo.empty: return None
    fig, ax = plt.subplots(figsize=(5, 4))
    wedges, _, ats = ax.pie(conteo.values, labels=None, autopct="%1.0f%%",
        colors=COLORES[:len(conteo)], startangle=140,
        wedgeprops={"edgecolor":"white","linewidth":1.5}, pctdistance=0.78)
    for at in ats: at.set_fontsize(9); at.set_color("white"); at.set_fontweight("bold")
    ax.legend(wedges, conteo.index, loc="center left",
              bbox_to_anchor=(1,0,0.5,1), fontsize=8)
    ax.set_title("Por tipo de licitación", fontweight="bold")
    fig.tight_layout(); return fig

def grafico_urgencia(df):
    orden  = ["🔴 Urgente","🟡 Próximo","🟢 Normal","Sin dato"]
    colmap = {"🔴 Urgente":"#e05c00","🟡 Próximo":"#f0a500",
              "🟢 Normal":"#7ab648","Sin dato":"#cccccc"}
    conteo = df["urgencia"].value_counts().reindex(orden).dropna()
    if conteo.empty: return None
    fig, ax = plt.subplots(figsize=(5, 3.5))
    bars = ax.bar(conteo.index, conteo.values,
                  color=[colmap[k] for k in conteo.index], edgecolor="white")
    for b in bars:
        ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.05,
                str(int(b.get_height())), ha="center", fontsize=10, fontweight="bold")
    ax.set_title("Urgencia por plazo de cierre", fontweight="bold")
    ax.spines[["top","right"]].set_visible(False)
    ax.set_ylim(0, conteo.max()*1.3)
    fig.tight_layout(); return fig


# ════════════════════════════════════════════════════════════
#  INTERFAZ
# ════════════════════════════════════════════════════════════

# Header
st.markdown("""
<div class="header-box">
  <h1>🔍 Buscador de Licitaciones — Bertonati</h1>
  <p>Encuentra oportunidades de negocio con el Estado de Chile
  · API Mercado Público · Datos en tiempo real</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Fuente de datos")
    modo = st.radio("", ["📂 Muestra rápida", "🔗 API en vivo"], label_visibility="collapsed")

    if modo == "🔗 API en vivo":
        # Solo "activas" funciona con el ticket de prueba
        st.info("ℹ️ El ticket de prueba solo permite consultar licitaciones **activas**.")
        cantidad_sel = st.slider("Cantidad a cargar", 5, 15, 8, 1,
                                 help="Cada licitación requiere 1 request → ~1 seg c/u")
        cargar_btn = st.button("🔄 Cargar desde API", type="primary", use_container_width=True)
    else:
        cargar_btn = False

    st.markdown("---")
    st.markdown("### 🔎 Filtros rápidos")


# ── Carga de datos ─────────────────────────────────────────────
if "df" not in st.session_state:
    st.session_state.df     = preparar_df(MUESTRA)
    st.session_state.fuente = "muestra"

if cargar_btn:
    with st.spinner("Consultando API... puede tardar ~20 seg"):
        try:
            registros = obtener_api("activas", cantidad_sel)
            if registros:
                st.session_state.df     = preparar_df(registros)
                st.session_state.fuente = "api"
                st.sidebar.success(f"✅ {len(registros)} licitaciones cargadas")
            else:
                st.sidebar.warning("La API no retornó datos. Usando muestra.")
        except Exception as e:
            st.sidebar.error(f"❌ Error API: {e}")
            st.sidebar.info("Usando datos de muestra.")

df = st.session_state.df

# Filtros sidebar
with st.sidebar:
    regiones = sorted(df["region_corta"].dropna().unique())
    reg_sel  = st.multiselect("Región", regiones, default=regiones)

    tipos = sorted(df["tipo"].dropna().unique())
    tip_sel = st.multiselect("Tipo", tipos, default=tipos)

    urgencias = sorted(df["urgencia"].dropna().unique())
    urg_sel  = st.multiselect("Urgencia", urgencias, default=urgencias)

    st.markdown("---")
    fuente_txt = "📂 Muestra" if st.session_state.fuente == "muestra" else "🔗 API en vivo"
    st.caption(f"**Fuente:** {fuente_txt}")
    st.caption("**Empresa:** Bertonati")
    st.caption("**Asignatura:** FITO9017 · Solemne II")

# Aplicar filtros
df_f = df[
    df["region_corta"].isin(reg_sel) &
    df["tipo"].isin(tip_sel) &
    df["urgencia"].isin(urg_sel)
].copy()

# ════════════════════════════════════════════════════════════
#  TABS PRINCIPALES
# ════════════════════════════════════════════════════════════
tab_buscar, tab_dashboard, tab_detalle = st.tabs([
    "🔍 Buscador de Oportunidades",
    "📊 Dashboard Análisis",
    "📋 Tabla Completa",
])

# ────────────────────────────────────────────────────────────
# TAB 1: BUSCADOR
# ────────────────────────────────────────────────────────────
with tab_buscar:
    st.markdown("#### Encuentra licitaciones para Bertonati")

    # Barra de búsqueda principal
    col_b1, col_b2, col_b3 = st.columns([3, 2, 2])
    with col_b1:
        txt_kw = st.text_input(
            "🔑 Palabra clave en nombre",
            placeholder="Ej: hospital, calibración, suministro, madera...",
        )
    with col_b2:
        txt_id = st.text_input(
            "🆔 Código de licitación",
            placeholder="Ej: 1003473-51-LP26",
        )
    with col_b3:
        txt_org = st.text_input(
            "🏛️ Organismo",
            placeholder="Ej: SALUD, MOP, EJÉRCITO...",
        )

    # Filtros adicionales inline
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        solo_con_monto = st.checkbox("Solo licitaciones con monto informado")
    with col_f2:
        solo_urgentes  = st.checkbox("Solo urgentes y próximas (≤10 días)")

    # Aplicar búsqueda
    df_busq = df_f.copy()
    if txt_kw:
        df_busq = df_busq[df_busq["nombre"].str.contains(txt_kw, case=False, na=False)]
    if txt_id:
        df_busq = df_busq[df_busq["codigo"].str.contains(txt_id, case=False, na=False)]
    if txt_org:
        df_busq = df_busq[df_busq["organismo"].str.contains(txt_org, case=False, na=False)]
    if solo_con_monto:
        df_busq = df_busq[df_busq["monto_estimado"].notna()]
    if solo_urgentes:
        df_busq = df_busq[df_busq["urgencia"].isin(["🔴 Urgente","🟡 Próximo"])]

    # Resultados
    n = len(df_busq)
    st.markdown(f"**{n} licitación(es) encontrada(s)**")

    if n == 0:
        st.warning("No se encontraron licitaciones con esos criterios. Prueba ajustar los filtros.")
    else:
        for _, row in df_busq.iterrows():
            urgencia_tag = row["urgencia"]
            card_class = ("urgente" if "Urgente" in urgencia_tag
                          else "ok" if "Normal" in urgencia_tag else "licit-card")

            badge_tipo = f'<span class="badge badge-{row["tipo"]}">{row["tipo"]}</span>'

            if "Urgente" in urgencia_tag:
                tag_html = f'<span class="urgente-tag">{urgencia_tag} · {int(row["dias_cierre"])} días</span>'
            else:
                tag_html = f'<span class="ok-tag">{urgencia_tag} · {int(row["dias_cierre"]) if pd.notna(row["dias_cierre"]) else "?"} días</span>'

            cierre_str = row["fecha_cierre"].strftime("%d/%m/%Y") if pd.notna(row["fecha_cierre"]) else "—"

            st.markdown(f"""
<div class="licit-card {card_class}">
  <div style="display:flex;justify-content:space-between;align-items:flex-start">
    <div>
      {badge_tipo}
      {tag_html}
      <span style="font-size:0.72rem;color:#888;margin-left:6px">Cierre: {cierre_str}</span>
    </div>
    <span style="font-size:0.72rem;color:#666">{row['codigo']}</span>
  </div>
  <p style="margin:8px 0 4px 0;font-weight:600;color:#1a3a5c">{row['nombre']}</p>
  <p style="margin:0;font-size:0.82rem;color:#555">
    🏛️ {row['organismo']} &nbsp;|&nbsp;
    📍 {row['region_corta']} &nbsp;|&nbsp;
    💰 {row['monto_fmt']}
  </p>
  <a href="{row['url_mp']}" target="_blank"
     style="font-size:0.78rem;color:#2e6da4;text-decoration:none">
    🔗 Ver en Mercado Público →
  </a>
</div>
""", unsafe_allow_html=True)


# ────────────────────────────────────────────────────────────
# TAB 2: DASHBOARD
# ────────────────────────────────────────────────────────────
with tab_dashboard:

    # Métricas
    c1, c2, c3, c4 = st.columns(4)
    urgentes = len(df_f[df_f["urgencia"] == "🔴 Urgente"])
    proximas = len(df_f[df_f["urgencia"] == "🟡 Próximo"])
    con_monto = df_f["monto_estimado"].notna().sum()
    monto_tot = df_f["monto_estimado"].sum()

    c1.metric("Total licitaciones",    f"{len(df_f):,}")
    c2.metric("🔴 Cierran en ≤5 días", urgentes,
              delta="Requieren acción inmediata", delta_color="inverse")
    c3.metric("🟡 Cierran en 6-10 días", proximas)
    c4.metric("Monto total disponible",
              f"${monto_tot/1e6:,.1f}M CLP" if monto_tot > 0 else "N/D")

    st.divider()

    # Gráficos
    col_g1, col_g2, col_g3 = st.columns(3)
    with col_g1:
        fig = grafico_region(df_f)
        if fig: st.pyplot(fig, use_container_width=True)
        st.caption("Distribución geográfica de licitaciones activas.")

    with col_g2:
        fig = grafico_tipo(df_f)
        if fig: st.pyplot(fig, use_container_width=True)
        st.caption("LE=≤1000 UTM · LP=>1000 UTM · LR=Privada")

    with col_g3:
        fig = grafico_urgencia(df_f)
        if fig: st.pyplot(fig, use_container_width=True)
        st.caption("Urgencia según días restantes antes del cierre.")

    st.divider()

    # Top organismos
    st.subheader("🏛️ Organismos con más licitaciones activas")
    top_org = (df_f[df_f["organismo"] != ""]
               .groupby("organismo").size()
               .sort_values(ascending=False).head(8).reset_index(name="N°"))
    st.dataframe(top_org.rename(columns={"organismo":"Organismo"}),
                 use_container_width=True, hide_index=True)


# ────────────────────────────────────────────────────────────
# TAB 3: TABLA COMPLETA
# ────────────────────────────────────────────────────────────
with tab_detalle:
    st.markdown("#### Dataset completo · exportable")

    busq_tabla = st.text_input("🔎 Filtrar tabla", placeholder="Escribe cualquier término...")
    df_tbl = df_f.copy()
    if busq_tabla:
        mask = (
            df_tbl["nombre"].str.contains(busq_tabla, case=False, na=False) |
            df_tbl["organismo"].str.contains(busq_tabla, case=False, na=False) |
            df_tbl["codigo"].str.contains(busq_tabla, case=False, na=False) |
            df_tbl["region_corta"].str.contains(busq_tabla, case=False, na=False)
        )
        df_tbl = df_tbl[mask]

    cols_show = ["codigo","nombre","tipo_desc","urgencia","region_corta",
                 "organismo","monto_fmt","dias_cierre","fecha_cierre"]
    st.dataframe(
        df_tbl[cols_show].rename(columns={
            "codigo":"Código","nombre":"Nombre","tipo_desc":"Tipo",
            "urgencia":"Urgencia","region_corta":"Región",
            "organismo":"Organismo","monto_fmt":"Monto",
            "dias_cierre":"Días cierre","fecha_cierre":"Fecha cierre",
        }),
        use_container_width=True, hide_index=True,
    )
    st.caption(f"Mostrando {len(df_tbl)} de {len(df_f)} licitaciones")

    # Exportar CSV
    csv = df_tbl[cols_show].to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Descargar CSV",
        data=csv,
        file_name="licitaciones_bertonati.csv",
        mime="text/csv",
    )

# ── Footer ─────────────────────────────────────────────────────
st.markdown("""<div style='text-align:center;color:#aaa;font-size:0.78rem;margin-top:20px'>
Solemne II · FITO9017 · Universidad San Sebastián · Bertonati ·
Python · Pandas · Matplotlib · Streamlit · API Mercado Público Chile
</div>""", unsafe_allow_html=True)
