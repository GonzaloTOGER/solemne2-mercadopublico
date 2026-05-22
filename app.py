"""
=============================================================
Solemne II - FITO9017
Aplicacion: Analizador de Licitaciones Publicas Chile
Universidad San Sebastian
=============================================================

NOTA DE DESARROLLO:
Se incluye un error intencional documentado en la funcion
calcular_urgencia() para demostrar identificacion y
correccion de bugs durante el proceso de desarrollo.
=============================================================
"""

import streamlit as st
import pandas as pd
import requests
import time
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# -- Configuracion de pagina ----------------------------------
st.set_page_config(
    page_title="Licitaciones Publicas Chile",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    body { font-family: 'Segoe UI', sans-serif; }
    [data-testid="stAppViewContainer"] { background: #f5f7fa; }
    .titulo-app {
        background: #1a3a5c;
        padding: 20px 28px;
        border-radius: 8px;
        margin-bottom: 18px;
        color: white;
    }
    .titulo-app h2 { color: white; margin: 0; font-size: 1.5rem; font-weight: 600; }
    .titulo-app p  { color: #b8d0e8; margin: 4px 0 0 0; font-size: 0.88rem; }
    .card-licit {
        background: white;
        border-radius: 8px;
        padding: 14px 18px;
        margin: 6px 0;
        border-left: 4px solid #2e6da4;
        box-shadow: 0 1px 3px rgba(0,0,0,0.07);
    }
    .card-urgente { border-left-color: #c0392b; }
    .card-proximo { border-left-color: #d68910; }
    .card-normal  { border-left-color: #1e8449; }
    .tag {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.72rem;
        font-weight: 600;
        margin-right: 5px;
        letter-spacing: 0.3px;
    }
    .tag-tipo    { background: #dce8f5; color: #1a3a5c; }
    .tag-urgente { background: #fde8e8; color: #922b21; }
    .tag-proximo { background: #fef5e4; color: #9a6606; }
    .tag-normal  { background: #e8f8e8; color: #1a5c1a; }
    div[data-testid="metric-container"] {
        background: white;
        border-radius: 8px;
        padding: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    .seccion { color: #1a3a5c; font-size: 1.05rem; font-weight: 600;
               border-bottom: 2px solid #dce8f5; padding-bottom: 4px; margin-bottom: 12px; }
</style>
""", unsafe_allow_html=True)

# -- Constantes -----------------------------------------------
TICKET   = "F8537A18-6766-4DEF-9E59-426B4FEE2844"
BASE_URL = "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json"

TIPO_MAP = {
    "LE": "Licitacion publica <= 1000 UTM",
    "LP": "Licitacion publica > 1000 UTM",
    "LR": "Licitacion privada",
    "L1": "Convenio marco",
    "CO": "Compra agil",
    "AG": "Compra agil",
    "B2": "Gran empresa",
    "O1": "Orden de compra",
}

COLORES = ["#1a3a5c","#2e6da4","#4da6e0","#f0a500",
           "#c0392b","#1e8449","#8e44ad","#a8d5f5"]

MUESTRA = [
    {"codigo":"1003473-25-LR26","nombre":"Suministro insumos instalacion desfibriladores","estado":"Publicada","tipo":"LR","monto_estimado":410000000,"organismo":"Servicio de Salud del Maule - Hospital de Curico","region":"Region del Maule","fecha_publicacion":"2026-05-15","fecha_cierre":"2026-06-23","dias_cierre":14},
    {"codigo":"1003473-51-LP26","nombre":"Suministro fresas neurocirugía con equipos","estado":"Publicada","tipo":"LP","monto_estimado":230000000,"organismo":"Servicio de Salud del Maule - Hospital de Curico","region":"Region del Maule","fecha_publicacion":"2026-05-13","fecha_cierre":"2026-06-02","dias_cierre":11},
    {"codigo":"1002588-64-LE26","nombre":"Asesoria inspeccion tecnica de obra Juan Sandoval","estado":"Publicada","tipo":"LE","monto_estimado":11200000,"organismo":"Servicio Local de Educacion Puerto Cordillera","region":"Region de Coquimbo","fecha_publicacion":"2026-05-18","fecha_cierre":"2026-05-28","dias_cierre":6},
    {"codigo":"1003-8-LE26","nombre":"Calibracion de equipos del Laboratorio","estado":"Publicada","tipo":"LE","monto_estimado":10500000,"organismo":"MOP Direccion General de Obras Publicas","region":"Region de Aysen","fecha_publicacion":"2026-05-22","fecha_cierre":"2026-06-01","dias_cierre":10},
    {"codigo":"1002772-38-LP26","nombre":"Suministro mascarilla interfaz pediatrica","estado":"Publicada","tipo":"LP","monto_estimado":None,"organismo":"Hospital Dr. Felix Bulnes Occidente","region":"Region Metropolitana de Santiago","fecha_publicacion":"2026-05-13","fecha_cierre":"2026-05-27","dias_cierre":5},
    {"codigo":"1002772-39-LP26","nombre":"Clips de uso endoscopico y otros insumos","estado":"Publicada","tipo":"LP","monto_estimado":None,"organismo":"Hospital Dr. Felix Bulnes Occidente","region":"Region Metropolitana de Santiago","fecha_publicacion":"2026-05-18","fecha_cierre":"2026-06-01","dias_cierre":10},
    {"codigo":"1002772-40-LR26","nombre":"Suministro agujas e insumos para biopsia","estado":"Publicada","tipo":"LR","monto_estimado":None,"organismo":"Hospital Dr. Felix Bulnes Occidente","region":"Region Metropolitana de Santiago","fecha_publicacion":"2026-05-18","fecha_cierre":"2026-06-17","dias_cierre":26},
    {"codigo":"1002772-42-LP26","nombre":"Guantes quirurgicos esteriles libres de latex","estado":"Publicada","tipo":"LP","monto_estimado":None,"organismo":"Hospital Dr. Felix Bulnes Occidente","region":"Region Metropolitana de Santiago","fecha_publicacion":"2026-05-18","fecha_cierre":"2026-06-01","dias_cierre":10},
    {"codigo":"1000-10-LE26","nombre":"Suministro piezas de madera de roble","estado":"Publicada","tipo":"LE","monto_estimado":None,"organismo":"MOP Direccion de Vialidad Region del Biobio","region":"Region del Biobio","fecha_publicacion":"2026-05-15","fecha_cierre":"2026-05-25","dias_cierre":3},
    {"codigo":"1000813-10-LE26","nombre":"Adquisicion materiales mantenimiento dependencias","estado":"Publicada","tipo":"LE","monto_estimado":None,"organismo":"Division Logistica del Ejercito","region":"Region de Magallanes","fecha_publicacion":"2026-05-20","fecha_cierre":"2026-06-01","dias_cierre":10},
    {"codigo":"1002-45-LP26","nombre":"Convenio mantencion marca Mercedes Benz","estado":"Publicada","tipo":"LP","monto_estimado":None,"organismo":"MOP Direccion General de Obras Publicas","region":"Region de Los Lagos","fecha_publicacion":"2026-05-13","fecha_cierre":"2026-05-25","dias_cierre":3},
    {"codigo":"1003473-14-LR26","nombre":"Contrato suministro insumos para urologia","estado":"Publicada","tipo":"LR","monto_estimado":None,"organismo":"Servicio de Salud del Maule - Hospital de Curico","region":"Region del Maule","fecha_publicacion":"2026-05-05","fecha_cierre":"2026-06-05","dias_cierre":14},
    {"codigo":"1003473-31-LP26","nombre":"Suministro insumos quirurgicos para el hospital","estado":"Publicada","tipo":"LP","monto_estimado":None,"organismo":"Servicio de Salud del Maule - Hospital de Curico","region":"Region del Maule","fecha_publicacion":"2026-05-15","fecha_cierre":"2026-06-01","dias_cierre":10},
    {"codigo":"1002-52-LP26","nombre":"Adquisicion neumaticos para maquinaria pesada","estado":"Publicada","tipo":"LP","monto_estimado":None,"organismo":"MOP Direccion General de Obras Publicas","region":"Region de Los Lagos","fecha_publicacion":"2026-05-14","fecha_cierre":"2026-05-26","dias_cierre":4},
    {"codigo":"1003473-32-LP26","nombre":"Suministro dispositivos medicos soporte ventilatorio","estado":"Publicada","tipo":"LP","monto_estimado":None,"organismo":"Servicio de Salud del Maule - Hospital de Curico","region":"Region del Maule","fecha_publicacion":"2026-05-12","fecha_cierre":"2026-05-27","dias_cierre":5},
]


# ============================================================
# ERROR INTENCIONAL DOCUMENTADO
# ============================================================
def calcular_urgencia(dias):
    """
    Clasifica urgencia de una licitacion segun dias restantes al cierre.

    ERROR IDENTIFICADO EN DESARROLLO (version original):
        La condicion usaba una comparacion encadenada invalida en Python,
        lo que generaba SyntaxError y la funcion no podia ejecutarse.

        Codigo con error:
            if dias > 0 and < 7:   <- SyntaxError: invalid syntax
                return "Urgente"

        Correccion aplicada:
            Separar correctamente las comparaciones con operadores booleanos
            y validar primero si el valor es None.
    """
    # -- VERSION CON ERROR (no ejecutar) ----------------------
    # if dias > 0 and < 7:    <- SyntaxError
    #     return "Urgente"
    # -- FIN ERROR --------------------------------------------

    # -- VERSION CORREGIDA ------------------------------------
    if dias is None:
        return "Sin dato"
    if dias <= 5:
        return "Urgente"
    if dias <= 10:
        return "Proximo"
    return "Normal"


# -- Procesamiento del DataFrame ------------------------------
def preparar_df(registros):
    df = pd.DataFrame(registros)
    df["fecha_publicacion"] = pd.to_datetime(df["fecha_publicacion"], errors="coerce")
    df["fecha_cierre"]      = pd.to_datetime(df["fecha_cierre"],      errors="coerce")
    df["monto_estimado"]    = pd.to_numeric(df["monto_estimado"],     errors="coerce")
    df["dias_cierre"]       = pd.to_numeric(df["dias_cierre"],        errors="coerce")
    df["region_corta"] = (
        df["region"]
        .str.replace(r"Regi.n (de la |de los |del |de |Metropolitana de )?",
                     "", regex=True)
        .str.strip()
    )
    df["tipo_desc"] = df["tipo"].map(TIPO_MAP).fillna("Otro")
    df["urgencia"]  = df["dias_cierre"].apply(calcular_urgencia)
    df["monto_fmt"] = df["monto_estimado"].apply(
        lambda x: f"${x/1_000_000:,.1f}M CLP" if pd.notna(x) else "No informado"
    )
    df["url_mp"] = df["codigo"].apply(
        lambda c: f"https://www.mercadopublico.cl/Procurement/Modules/RFB/"
                  f"DetailsAcquisition.aspx?idlicitacion={c}"
    )
    return df


# -- API ------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def obtener_api(cantidad):
    r = requests.get(BASE_URL,
                     params={"estado":"activas","ticket":TICKET,"cantidad":cantidad},
                     timeout=15)
    r.raise_for_status()
    data = r.json()
    if data.get("Codigo") == 203:
        raise ValueError("Ticket invalido")
    codigos   = [x["CodigoExterno"] for x in data.get("Listado", [])]
    registros = []
    for codigo in codigos:
        try:
            r2  = requests.get(BASE_URL,
                               params={"codigo":codigo,"ticket":TICKET},
                               timeout=12)
            det  = r2.json().get("Listado", [{}])[0]
            comp = det.get("Comprador") or {}
            fec  = det.get("Fechas")    or {}
            registros.append({
                "codigo":            codigo,
                "nombre":            det.get("Nombre",""),
                "estado":            det.get("Estado",""),
                "tipo":              det.get("Tipo",""),
                "monto_estimado":    det.get("MontoEstimado"),
                "organismo":         comp.get("NombreOrganismo",""),
                "region":            (comp.get("RegionUnidad") or "").strip(),
                "fecha_publicacion": fec.get("FechaPublicacion"),
                "fecha_cierre":      fec.get("FechaCierre"),
                "dias_cierre":       det.get("DiasCierreLicitacion"),
            })
            time.sleep(0.6)
        except Exception:
            pass
    return registros


# -- Graficos -------------------------------------------------
def grafico_region(df):
    conteo = (df[df["region_corta"].str.strip() != ""]
              .groupby("region_corta").size().sort_values())
    if conteo.empty:
        return None
    fig, ax = plt.subplots(figsize=(7, max(3, len(conteo)*0.6)))
    bars = ax.barh(conteo.index, conteo.values, color="#2e6da4", edgecolor="white")
    for b in bars:
        ax.text(b.get_width()+0.05, b.get_y()+b.get_height()/2,
                f" {int(b.get_width())}", va="center", fontsize=9)
    ax.set_title("Licitaciones por region", fontweight="bold", pad=10)
    ax.spines[["top","right"]].set_visible(False)
    ax.set_xlim(0, conteo.max()*1.3)
    fig.tight_layout()
    return fig

def grafico_tipo(df):
    conteo = df["tipo_desc"].value_counts()
    if conteo.empty:
        return None
    fig, ax = plt.subplots(figsize=(5, 4))
    wedges, _, ats = ax.pie(
        conteo.values, labels=None, autopct="%1.0f%%",
        colors=COLORES[:len(conteo)], startangle=140,
        wedgeprops={"edgecolor":"white","linewidth":1.5}, pctdistance=0.78
    )
    for at in ats:
        at.set_fontsize(9); at.set_color("white"); at.set_fontweight("bold")
    ax.legend(wedges, conteo.index, loc="center left",
              bbox_to_anchor=(1,0,0.5,1), fontsize=8)
    ax.set_title("Distribucion por tipo", fontweight="bold")
    fig.tight_layout()
    return fig

def grafico_urgencia(df):
    orden  = ["Urgente","Proximo","Normal","Sin dato"]
    colmap = {"Urgente":"#c0392b","Proximo":"#d68910","Normal":"#1e8449","Sin dato":"#cccccc"}
    conteo = df["urgencia"].value_counts().reindex(orden).dropna()
    if conteo.empty:
        return None
    fig, ax = plt.subplots(figsize=(5, 3.5))
    bars = ax.bar(conteo.index, conteo.values,
                  color=[colmap[k] for k in conteo.index], edgecolor="white")
    for b in bars:
        ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.05,
                str(int(b.get_height())), ha="center", fontsize=10, fontweight="bold")
    ax.set_title("Urgencia por plazo de cierre", fontweight="bold")
    ax.spines[["top","right"]].set_visible(False)
    ax.set_ylim(0, conteo.max()*1.3)
    fig.tight_layout()
    return fig


# ============================================================
#  INTERFAZ
# ============================================================

st.markdown("""
<div class="titulo-app">
  <h2>Analizador de Licitaciones Publicas - Chile</h2>
  <p>Fuente de datos: API Mercado Publico Chile (api.mercadopublico.cl) - Datos en tiempo real</p>
</div>
""", unsafe_allow_html=True)

# -- Sidebar --------------------------------------------------
with st.sidebar:
    st.markdown("### Fuente de datos")
    modo = st.radio(
        "",
        ["Datos de muestra (carga inmediata)", "Consultar API en vivo"],
        label_visibility="collapsed"
    )

    if modo == "Consultar API en vivo":
        st.info("El ticket de prueba permite solo licitaciones activas.")
        cantidad_sel = st.slider("Cantidad a cargar", 5, 15, 8, 1)
        cargar_btn = st.button("Cargar desde API", type="primary", use_container_width=True)
    else:
        cargar_btn = False

    st.markdown("---")
    st.markdown("### Filtros")


# -- Carga de datos -------------------------------------------
if "df" not in st.session_state:
    st.session_state.df     = preparar_df(MUESTRA)
    st.session_state.fuente = "muestra"

if cargar_btn:
    with st.spinner("Consultando API Mercado Publico..."):
        try:
            registros = obtener_api(cantidad_sel)
            if registros:
                st.session_state.df     = preparar_df(registros)
                st.session_state.fuente = "api"
                st.sidebar.success(f"{len(registros)} licitaciones cargadas desde la API")
            else:
                st.sidebar.warning("La API no retorno datos. Se mantienen datos de muestra.")
        except Exception as e:
            st.sidebar.error(f"Error de conexion: {e}")

df = st.session_state.df

with st.sidebar:
    regiones = sorted(df["region_corta"].dropna().unique())
    reg_sel  = st.multiselect("Region", regiones, default=regiones)

    tipos = sorted(df["tipo"].dropna().unique())
    tip_sel = st.multiselect("Tipo de licitacion", tipos, default=tipos)

    urgencias = ["Urgente","Proximo","Normal","Sin dato"]
    urg_disp  = [u for u in urgencias if u in df["urgencia"].values]
    urg_sel   = st.multiselect("Urgencia", urg_disp, default=urg_disp)

    st.markdown("---")
    fuente_txt = "Muestra" if st.session_state.fuente == "muestra" else "API en vivo"
    st.caption(f"Fuente activa: {fuente_txt}")
    st.caption("Asignatura: FITO9017 - Solemne II")
    st.caption("Universidad San Sebastian")

df_f = df[
    df["region_corta"].isin(reg_sel) &
    df["tipo"].isin(tip_sel) &
    df["urgencia"].isin(urg_sel)
].copy()

if st.session_state.fuente == "muestra":
    st.info("Mostrando datos de muestra. Para obtener datos en tiempo real, "
            "seleccione 'Consultar API en vivo' en el panel lateral.")

# -- Tabs -----------------------------------------------------
tab1, tab2, tab3 = st.tabs([
    "Buscador de Licitaciones",
    "Dashboard de Analisis",
    "Tabla de Datos",
])


# -- TAB 1: BUSCADOR ------------------------------------------
with tab1:
    st.markdown('<p class="seccion">Busqueda de licitaciones</p>', unsafe_allow_html=True)

    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        txt_kw  = st.text_input("Palabra clave", placeholder="Ej: hospital, madera, calibracion")
    with col_b2:
        txt_id  = st.text_input("Codigo de licitacion", placeholder="Ej: 1003473-51-LP26")
    with col_b3:
        txt_org = st.text_input("Organismo", placeholder="Ej: Salud, MOP, Ejercito")

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        solo_monto   = st.checkbox("Solo licitaciones con monto informado")
    with col_f2:
        solo_urgente = st.checkbox("Solo con plazo de cierre <= 10 dias")

    # Aplicar busqueda
    df_busq = df_f.copy()

    if txt_kw.strip():
        df_busq = df_busq[
            df_busq["nombre"].str.contains(txt_kw.strip(), case=False, na=False)
        ]
    if txt_id.strip():
        df_busq = df_busq[
            df_busq["codigo"].str.contains(txt_id.strip(), case=False, na=False)
        ]
    if txt_org.strip():
        df_busq = df_busq[
            df_busq["organismo"].str.contains(txt_org.strip(), case=False, na=False)
        ]
    if solo_monto:
        df_busq = df_busq[df_busq["monto_estimado"].notna()]
    if solo_urgente:
        df_busq = df_busq[df_busq["urgencia"].isin(["Urgente","Proximo"])]

    st.markdown(f"**{len(df_busq)} resultado(s) encontrado(s)**")
    st.markdown("---")

    if len(df_busq) == 0:
        st.warning("No se encontraron licitaciones con los criterios ingresados. "
                   "Verifique los terminos de busqueda o ajuste los filtros del panel lateral.")
    else:
        for _, row in df_busq.iterrows():
            urg = row["urgencia"]
            card_cls = {"Urgente":"card-urgente","Proximo":"card-proximo"}.get(urg,"card-normal")
            tag_cls  = {"Urgente":"tag-urgente", "Proximo":"tag-proximo"}.get(urg,"tag-normal")

            dias_txt = (f"{int(row['dias_cierre'])} dias al cierre"
                        if pd.notna(row["dias_cierre"]) else "plazo no informado")
            cierre_txt = (row["fecha_cierre"].strftime("%d/%m/%Y")
                          if pd.notna(row["fecha_cierre"]) else "--")

            st.markdown(f"""
<div class="card-licit {card_cls}">
  <div style="display:flex;justify-content:space-between;align-items:center">
    <div>
      <span class="tag tag-tipo">{row['tipo']}</span>
      <span class="tag {tag_cls}">{urg} - {dias_txt}</span>
      <span style="font-size:0.72rem;color:#888">Cierre: {cierre_txt}</span>
    </div>
    <span style="font-size:0.72rem;color:#999;font-family:monospace">{row['codigo']}</span>
  </div>
  <p style="margin:8px 0 3px 0;font-weight:600;color:#1a3a5c;font-size:0.95rem">{row['nombre']}</p>
  <p style="margin:0;font-size:0.82rem;color:#555">
    - Organismo: {row['organismo']}<br>
    - Region: {row['region_corta']} &nbsp;|&nbsp; Monto estimado: {row['monto_fmt']}
  </p>
  <p style="margin:6px 0 0 0;font-size:0.78rem">
    <a href="{row['url_mp']}" target="_blank"
       style="color:#2e6da4;text-decoration:none">
      -> Ver licitacion en Mercado Publico
    </a>
  </p>
</div>
""", unsafe_allow_html=True)


# -- TAB 2: DASHBOARD -----------------------------------------
with tab2:
    st.markdown('<p class="seccion">Resumen estadistico</p>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    urgentes  = len(df_f[df_f["urgencia"] == "Urgente"])
    proximas  = len(df_f[df_f["urgencia"] == "Proximo"])
    monto_tot = df_f["monto_estimado"].sum()

    c1.metric("Total licitaciones",         f"{len(df_f):,}")
    c2.metric("Cierre en <= 5 dias",        urgentes)
    c3.metric("Cierre en 6 a 10 dias",      proximas)
    c4.metric("Monto total estimado",
              f"${monto_tot/1e6:,.1f}M CLP" if monto_tot > 0 else "No disponible")

    st.markdown("---")

    col_g1, col_g2, col_g3 = st.columns(3)
    with col_g1:
        st.markdown("**Distribucion por region**")
        fig = grafico_region(df_f)
        if fig:
            st.pyplot(fig, use_container_width=True)
            st.caption("Numero de licitaciones activas segun region geografica.")

    with col_g2:
        st.markdown("**Distribucion por tipo**")
        fig = grafico_tipo(df_f)
        if fig:
            st.pyplot(fig, use_container_width=True)
            st.caption("LE = <= 1000 UTM | LP = > 1000 UTM | LR = Privada")

    with col_g3:
        st.markdown("**Urgencia de cierre**")
        fig = grafico_urgencia(df_f)
        if fig:
            st.pyplot(fig, use_container_width=True)
            st.caption("Clasificacion segun dias restantes antes del cierre de ofertas.")

    st.markdown("---")
    st.markdown("**Organismos con mayor actividad licitatoria**")
    top_org = (df_f[df_f["organismo"] != ""]
               .groupby("organismo").size()
               .sort_values(ascending=False)
               .head(8).reset_index(name="Licitaciones"))
    st.dataframe(
        top_org.rename(columns={"organismo":"Organismo"}),
        use_container_width=True, hide_index=True
    )


# -- TAB 3: TABLA ---------------------------------------------
with tab3:
    st.markdown('<p class="seccion">Tabla de datos completa</p>', unsafe_allow_html=True)

    busq_tbl = st.text_input(
        "Filtrar tabla (busca en nombre, organismo, codigo y region)",
        placeholder="Ingrese cualquier termino de busqueda..."
    )
    df_tbl = df_f.copy()
    if busq_tbl.strip():
        mask = (
            df_tbl["nombre"].str.contains(busq_tbl.strip(), case=False, na=False) |
            df_tbl["organismo"].str.contains(busq_tbl.strip(), case=False, na=False) |
            df_tbl["codigo"].str.contains(busq_tbl.strip(), case=False, na=False) |
            df_tbl["region_corta"].str.contains(busq_tbl.strip(), case=False, na=False)
        )
        df_tbl = df_tbl[mask]

    cols = ["codigo","nombre","tipo_desc","urgencia","region_corta",
            "organismo","monto_fmt","dias_cierre","fecha_cierre"]
    st.dataframe(
        df_tbl[cols].rename(columns={
            "codigo":"Codigo","nombre":"Nombre","tipo_desc":"Tipo",
            "urgencia":"Urgencia","region_corta":"Region",
            "organismo":"Organismo","monto_fmt":"Monto estimado",
            "dias_cierre":"Dias al cierre","fecha_cierre":"Fecha cierre",
        }),
        use_container_width=True, hide_index=True,
    )
    st.caption(f"Mostrando {len(df_tbl)} de {len(df_f)} registros.")

    csv = df_tbl[cols].to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Descargar datos en CSV",
        data=csv,
        file_name="licitaciones_mercado_publico.csv",
        mime="text/csv",
    )

# -- Pie de pagina --------------------------------------------
st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#aaa;font-size:0.78rem'>"
    "Solemne II - FITO9017 - Universidad San Sebastian - "
    "Python / Pandas / Matplotlib / Streamlit - "
    "Fuente: API Mercado Publico Chile"
    "</p>",
    unsafe_allow_html=True
)
