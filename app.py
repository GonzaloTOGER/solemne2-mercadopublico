"""
=============================================================
Solemne II - FITO9017
Aplicacion: Analizador de Licitaciones Publicas Chile
Universidad San Sebastian
=============================================================

ARQUITECTURA DE DATOS:
La API de Mercado Publico retorna hasta 4.430 licitaciones
en un solo request (listado basico: codigo, nombre, estado,
fecha cierre). La busqueda se realiza localmente sobre ese
listado usando pandas, lo que permite filtrar por cualquier
termino sin hacer requests adicionales.

Cuando el usuario requiere el detalle completo de una
licitacion (region, organismo, monto), se hace un segundo
request especifico por codigo.

ERROR INTENCIONAL DOCUMENTADO:
Ver funcion calcular_urgencia() -- error de sintaxis
identificado y corregido durante el desarrollo.
=============================================================
"""

import streamlit as st
import pandas as pd
import requests
import time
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# -- Configuracion --------------------------------------------
st.set_page_config(
    page_title="Licitaciones Publicas - Chile",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background: #f5f7fa; }
    .titulo-app {
        background: #1a3a5c;
        padding: 18px 26px; border-radius: 8px;
        margin-bottom: 16px; color: white;
    }
    .titulo-app h2 { color:white; margin:0; font-size:1.4rem; font-weight:600; }
    .titulo-app p  { color:#b8d0e8; margin:3px 0 0 0; font-size:0.85rem; }
    .card {
        background: white; border-radius: 8px;
        padding: 14px 18px; margin: 6px 0;
        border-left: 4px solid #2e6da4;
        box-shadow: 0 1px 3px rgba(0,0,0,0.07);
    }
    .card-urgente { border-left-color: #c0392b; }
    .card-proximo { border-left-color: #d68910; }
    .card-normal  { border-left-color: #1e8449; }
    .tag {
        display:inline-block; padding:2px 8px; border-radius:4px;
        font-size:0.72rem; font-weight:600; margin-right:5px;
    }
    .tag-tipo    { background:#dce8f5; color:#1a3a5c; }
    .tag-urgente { background:#fde8e8; color:#922b21; }
    .tag-proximo { background:#fef5e4; color:#9a6606; }
    .tag-normal  { background:#e8f8e8; color:#1a5c1a; }
    div[data-testid="metric-container"] {
        background:white; border-radius:8px; padding:12px;
        box-shadow:0 1px 3px rgba(0,0,0,0.06);
    }
    .seccion {
        color:#1a3a5c; font-size:1rem; font-weight:600;
        border-bottom:2px solid #dce8f5; padding-bottom:4px; margin-bottom:10px;
    }
</style>
""", unsafe_allow_html=True)

# -- Constantes -----------------------------------------------
TICKET   = "F8537A18-6766-4DEF-9E59-426B4FEE2844"
BASE_URL = "https://api.mercadopublico.cl/servicios/v1/publico/licitaciones.json"

ESTADO_MAP = {5:"Publicada", 6:"Cerrada", 7:"Desierta", 8:"Adjudicada", 18:"Revocada"}
TIPO_MAP   = {
    "LE":"Licitacion <= 1000 UTM", "LP":"Licitacion > 1000 UTM",
    "LR":"Licitacion privada",     "L1":"Convenio marco",
    "CO":"Compra agil",            "AG":"Compra agil",
    "B2":"Gran empresa",           "O1":"Orden de compra",
}
COLORES = ["#1a3a5c","#2e6da4","#4da6e0","#f0a500","#c0392b","#1e8449","#8e44ad"]


# ============================================================
# ERROR INTENCIONAL DOCUMENTADO
# ============================================================
def calcular_urgencia(dias):
    """
    Clasifica urgencia de una licitacion segun dias restantes al cierre.

    ERROR IDENTIFICADO EN DESARROLLO (version original):
        Comparacion encadenada invalida en Python que genera SyntaxError,
        impidiendo que la funcion se ejecute correctamente.

        Codigo con error:
            if dias > 0 and < 7:    <-- SyntaxError: invalid syntax
                return "Urgente"

        El operador 'and' en Python requiere dos expresiones booleanas
        completas. La forma 'and < 7' no es una expresion valida.

    Correccion aplicada:
        Separar la comparacion en dos condiciones explicitas:
            if dias is not None and dias <= 5:
    """
    # -- VERSION CON ERROR (no ejecutar) ----------------------
    # if dias > 0 and < 7:    <- SyntaxError
    #     return "Urgente"
    # -- FIN DEL ERROR ----------------------------------------

    # -- VERSION CORREGIDA ------------------------------------
    if dias is None or pd.isna(dias):
        return "Sin dato"
    dias = int(dias)
    if dias <= 5:
        return "Urgente"
    if dias <= 10:
        return "Proximo"
    return "Normal"


# -- Funciones de API -----------------------------------------
@st.cache_data(ttl=1800, show_spinner=False)
def cargar_listado_completo():
    """
    Descarga el listado completo de licitaciones activas.
    Retorna hasta 4.430 registros con: codigo, nombre, estado, fecha_cierre.
    Se cachea por 30 minutos para no sobrecargar la API.
    """
    r = requests.get(BASE_URL,
                     params={"estado":"activas","ticket":TICKET,"cantidad":5000},
                     timeout=20)
    r.raise_for_status()
    data = r.json()
    if data.get("Codigo") == 203:
        raise ValueError("Ticket no valido")
    return data.get("Listado", [])


def listado_a_dataframe(listado):
    """Convierte el listado basico de la API en un DataFrame limpio."""
    registros = []
    for item in listado:
        codigo = item.get("CodigoExterno","")
        nombre = item.get("Nombre","")
        # Extraer tipo del codigo (ej: "1003473-51-LP26" -> "LP")
        partes = codigo.split("-")
        tipo   = partes[-1][:2] if len(partes) >= 2 else ""
        # Calcular dias al cierre
        fecha_cierre_str = item.get("FechaCierre")
        fecha_cierre = None
        dias_cierre  = None
        if fecha_cierre_str:
            try:
                fecha_cierre = pd.to_datetime(fecha_cierre_str)
                dias_cierre  = (fecha_cierre - pd.Timestamp.now()).days
                if dias_cierre < 0:
                    dias_cierre = 0
            except Exception:
                pass
        registros.append({
            "codigo":       codigo,
            "nombre":       nombre,
            "tipo":         tipo,
            "tipo_desc":    TIPO_MAP.get(tipo, "Otro"),
            "estado":       ESTADO_MAP.get(item.get("CodigoEstado"), "Publicada"),
            "fecha_cierre": fecha_cierre,
            "dias_cierre":  dias_cierre,
            "urgencia":     calcular_urgencia(dias_cierre),
            "url_mp": (
                "https://www.mercadopublico.cl/Procurement/Modules/RFB/"
                f"DetailsAcquisition.aspx?idlicitacion={codigo}"
            ),
        })
    return pd.DataFrame(registros)


@st.cache_data(ttl=3600, show_spinner=False)
def obtener_detalle(codigo):
    """
    Obtiene region, organismo y monto de una licitacion especifica.
    Solo se llama al hacer clic en 'Ver detalle'.
    """
    try:
        r = requests.get(BASE_URL,
                         params={"codigo":codigo,"ticket":TICKET},
                         timeout=12)
        r.raise_for_status()
        listado = r.json().get("Listado", [])
        if not listado:
            return {}
        det  = listado[0]
        comp = det.get("Comprador") or {}
        return {
            "organismo":  comp.get("NombreOrganismo","No informado"),
            "region":     (comp.get("RegionUnidad") or "No informado").strip(),
            "comuna":     comp.get("ComunaUnidad",""),
            "monto":      det.get("MontoEstimado"),
            "descripcion":det.get("Descripcion",""),
        }
    except Exception:
        return {}


# -- Graficos -------------------------------------------------
COLORES_G = ["#1a3a5c","#2e6da4","#4da6e0","#f0a500","#c0392b","#1e8449","#8e44ad"]

def grafico_tipo(df):
    conteo = df["tipo_desc"].value_counts().head(6)
    if conteo.empty: return None
    fig, ax = plt.subplots(figsize=(5,4))
    wedges, _, ats = ax.pie(
        conteo.values, labels=None, autopct="%1.0f%%",
        colors=COLORES_G[:len(conteo)], startangle=140,
        wedgeprops={"edgecolor":"white","linewidth":1.5}, pctdistance=0.78
    )
    for at in ats: at.set_fontsize(9); at.set_color("white"); at.set_fontweight("bold")
    ax.legend(wedges, conteo.index, loc="center left",
              bbox_to_anchor=(1,0,0.5,1), fontsize=8)
    ax.set_title("Distribucion por tipo de licitacion", fontweight="bold")
    fig.tight_layout(); return fig

def grafico_urgencia(df):
    orden  = ["Urgente","Proximo","Normal","Sin dato"]
    colmap = {"Urgente":"#c0392b","Proximo":"#d68910","Normal":"#1e8449","Sin dato":"#aaaaaa"}
    conteo = df["urgencia"].value_counts().reindex(orden).dropna()
    if conteo.empty: return None
    fig, ax = plt.subplots(figsize=(5,3.5))
    bars = ax.bar(conteo.index, conteo.values,
                  color=[colmap[k] for k in conteo.index], edgecolor="white", width=0.5)
    for b in bars:
        ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.3,
                str(int(b.get_height())), ha="center", fontsize=10, fontweight="bold")
    ax.set_title("Clasificacion por urgencia de cierre", fontweight="bold")
    ax.spines[["top","right"]].set_visible(False)
    ax.set_ylim(0, conteo.max()*1.3)
    fig.tight_layout(); return fig

def grafico_top_tipos(df):
    conteo = df["tipo"].value_counts().head(8).sort_values()
    if conteo.empty: return None
    fig, ax = plt.subplots(figsize=(7, max(3, len(conteo)*0.55)))
    bars = ax.barh(conteo.index, conteo.values, color="#2e6da4", edgecolor="white")
    for b in bars:
        ax.text(b.get_width()+1, b.get_y()+b.get_height()/2,
                f" {int(b.get_width())}", va="center", fontsize=9)
    ax.set_title("Licitaciones por tipo (codigo)", fontweight="bold")
    ax.spines[["top","right"]].set_visible(False)
    ax.set_xlim(0, conteo.max()*1.25)
    fig.tight_layout(); return fig


# ============================================================
#  INTERFAZ
# ============================================================
st.markdown("""
<div class="titulo-app">
  <h2>Analizador de Licitaciones Publicas - Chile</h2>
  <p>Fuente: API Mercado Publico Chile (api.mercadopublico.cl) -- Licitaciones activas en tiempo real</p>
</div>
""", unsafe_allow_html=True)

# -- Carga inicial del listado completo -----------------------
if "df_listado" not in st.session_state:
    with st.spinner("Cargando listado de licitaciones desde la API de Mercado Publico..."):
        try:
            listado = cargar_listado_completo()
            st.session_state.df_listado = listado_a_dataframe(listado)
            st.session_state.ok = True
        except Exception as e:
            st.session_state.df_listado = pd.DataFrame()
            st.session_state.ok = False
            st.error(f"No se pudo conectar con la API: {e}")

df_total = st.session_state.df_listado

# -- Sidebar --------------------------------------------------
with st.sidebar:
    st.markdown("### Opciones")

    if st.button("Actualizar datos desde API", use_container_width=True):
        st.cache_data.clear()
        with st.spinner("Actualizando..."):
            try:
                listado = cargar_listado_completo()
                st.session_state.df_listado = listado_a_dataframe(listado)
                st.session_state.ok = True
                st.success(f"{len(st.session_state.df_listado)} licitaciones cargadas")
            except Exception as e:
                st.error(f"Error: {e}")

    st.markdown("---")
    st.markdown("### Filtros globales")

    tipos_disp = sorted(df_total["tipo"].dropna().unique().tolist()) if not df_total.empty else []
    tip_sel    = st.multiselect("Tipo de licitacion", tipos_disp, default=tipos_disp)

    urg_disp   = ["Urgente","Proximo","Normal","Sin dato"]
    urg_sel    = st.multiselect("Urgencia", urg_disp, default=urg_disp)

    st.markdown("---")
    if not df_total.empty:
        st.caption(f"Total en API: {len(df_total):,} licitaciones activas")
    st.caption("Asignatura: FITO9017 - Solemne II")
    st.caption("Universidad San Sebastian")

# Aplicar filtros globales
if not df_total.empty:
    df_f = df_total[
        df_total["tipo"].isin(tip_sel) &
        df_total["urgencia"].isin(urg_sel)
    ].copy()
else:
    df_f = pd.DataFrame()

# -- Tabs -----------------------------------------------------
tab1, tab2, tab3 = st.tabs([
    "Buscador de Licitaciones",
    "Dashboard de Analisis",
    "Tabla de Datos",
])


# ============================================================
# TAB 1: BUSCADOR
# ============================================================
with tab1:
    st.markdown('<p class="seccion">Busqueda en licitaciones activas</p>',
                unsafe_allow_html=True)

    if df_total.empty:
        st.warning("No hay datos disponibles. Intente actualizar desde el panel lateral.")
    else:
        col_b1, col_b2 = st.columns([2,1])
        with col_b1:
            txt_kw = st.text_input(
                "Palabra clave o descripcion",
                placeholder="Ej: ambulancia, hospital, pavimento, calibracion, madera..."
            )
        with col_b2:
            txt_id = st.text_input(
                "Codigo de licitacion",
                placeholder="Ej: 1003473-51-LP26"
            )

        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            solo_urgente = st.checkbox("Solo urgentes y proximas (cierre <= 10 dias)")
        with col_f2:
            max_resultados = st.selectbox("Mostrar hasta", [10, 25, 50, 100], index=1)
        with col_f3:
            st.markdown("&nbsp;")

        # Aplicar busqueda sobre el listado completo (4.430 registros)
        df_busq = df_f.copy()

        if txt_kw.strip():
            df_busq = df_busq[
                df_busq["nombre"].str.contains(txt_kw.strip(), case=False, na=False)
            ]
        if txt_id.strip():
            df_busq = df_busq[
                df_busq["codigo"].str.contains(txt_id.strip(), case=False, na=False)
            ]
        if solo_urgente:
            df_busq = df_busq[df_busq["urgencia"].isin(["Urgente","Proximo"])]

        total_encontrado = len(df_busq)
        df_busq = df_busq.head(max_resultados)

        st.markdown(f"**{total_encontrado:,} resultado(s) encontrado(s)**"
                    + (f" -- mostrando los primeros {max_resultados}"
                       if total_encontrado > max_resultados else ""))
        st.markdown("---")

        if total_encontrado == 0:
            st.warning(
                "No se encontraron licitaciones con los criterios ingresados. "
                "Pruebe con otros terminos o revise los filtros del panel lateral."
            )
        else:
            for _, row in df_busq.iterrows():
                urg = row["urgencia"]
                card_cls = {"Urgente":"card-urgente","Proximo":"card-proximo"}.get(urg,"card-normal")
                tag_cls  = {"Urgente":"tag-urgente","Proximo":"tag-proximo"}.get(urg,"tag-normal")
                dias_txt = (f"{int(row['dias_cierre'])} dias al cierre"
                            if pd.notna(row["dias_cierre"]) else "plazo no informado")
                cierre_txt = (row["fecha_cierre"].strftime("%d/%m/%Y")
                              if pd.notna(row["fecha_cierre"]) else "--")

                st.markdown(f"""
<div class="card {card_cls}">
  <div style="display:flex;justify-content:space-between;align-items:center">
    <div>
      <span class="tag tag-tipo">{row['tipo']}</span>
      <span class="tag {tag_cls}">{urg} -- {dias_txt}</span>
      <span style="font-size:0.72rem;color:#888">Cierre: {cierre_txt}</span>
    </div>
    <span style="font-size:0.72rem;color:#999;font-family:monospace">{row['codigo']}</span>
  </div>
  <p style="margin:8px 0 3px;font-weight:600;color:#1a3a5c;font-size:0.93rem">{row['nombre']}</p>
  <p style="margin:4px 0 0;font-size:0.78rem">
    <a href="{row['url_mp']}" target="_blank"
       style="color:#2e6da4;text-decoration:none">
      -> Ver licitacion completa en Mercado Publico
    </a>
  </p>
</div>
""", unsafe_allow_html=True)


# ============================================================
# TAB 2: DASHBOARD
# ============================================================
with tab2:
    st.markdown('<p class="seccion">Resumen estadistico del mercado</p>',
                unsafe_allow_html=True)

    if df_f.empty:
        st.warning("Sin datos para mostrar.")
    else:
        # Metricas
        c1, c2, c3, c4 = st.columns(4)
        urgentes = len(df_f[df_f["urgencia"]=="Urgente"])
        proximas = len(df_f[df_f["urgencia"]=="Proximo"])
        tipos_u  = df_f["tipo"].nunique()
        c1.metric("Total licitaciones activas", f"{len(df_f):,}")
        c2.metric("Cierre en <= 5 dias",         f"{urgentes:,}")
        c3.metric("Cierre en 6 a 10 dias",        f"{proximas:,}")
        c4.metric("Tipos de licitacion",          tipos_u)

        st.markdown("---")

        col_g1, col_g2, col_g3 = st.columns(3)
        with col_g1:
            st.markdown("**Por tipo de licitacion**")
            fig = grafico_tipo(df_f)
            if fig: st.pyplot(fig, use_container_width=True)
            st.caption("Proporcion de licitaciones segun su tipo y monto en UTM.")

        with col_g2:
            st.markdown("**Urgencia de cierre**")
            fig = grafico_urgencia(df_f)
            if fig: st.pyplot(fig, use_container_width=True)
            st.caption("Clasificacion por dias restantes antes del cierre de ofertas.")

        with col_g3:
            st.markdown("**Distribucion por codigo de tipo**")
            fig = grafico_top_tipos(df_f)
            if fig: st.pyplot(fig, use_container_width=True)
            st.caption("Frecuencia de cada codigo de tipo en el listado activo.")

        st.markdown("---")
        st.markdown("**Resumen por tipo de licitacion**")
        resumen = (df_f.groupby(["tipo","tipo_desc"])
                   .agg(cantidad=("codigo","count"))
                   .reset_index()
                   .sort_values("cantidad", ascending=False))
        resumen["porcentaje"] = (resumen["cantidad"]/len(df_f)*100).round(1).astype(str) + "%"
        st.dataframe(resumen.rename(columns={
            "tipo":"Codigo","tipo_desc":"Descripcion",
            "cantidad":"Licitaciones","porcentaje":"Del total"}),
            use_container_width=True, hide_index=True)


# ============================================================
# TAB 3: TABLA
# ============================================================
with tab3:
    st.markdown('<p class="seccion">Tabla completa de licitaciones</p>',
                unsafe_allow_html=True)

    if df_f.empty:
        st.warning("Sin datos para mostrar.")
    else:
        busq_tbl = st.text_input(
            "Filtrar tabla",
            placeholder="Busca por nombre, codigo o tipo..."
        )
        df_tbl = df_f.copy()
        if busq_tbl.strip():
            mask = (
                df_tbl["nombre"].str.contains(busq_tbl.strip(), case=False, na=False) |
                df_tbl["codigo"].str.contains(busq_tbl.strip(), case=False, na=False) |
                df_tbl["tipo"].str.contains(busq_tbl.strip(), case=False, na=False)
            )
            df_tbl = df_tbl[mask]

        cols = ["codigo","nombre","tipo_desc","urgencia","dias_cierre","fecha_cierre","estado"]
        st.dataframe(
            df_tbl[cols].rename(columns={
                "codigo":"Codigo","nombre":"Nombre","tipo_desc":"Tipo",
                "urgencia":"Urgencia","dias_cierre":"Dias al cierre",
                "fecha_cierre":"Fecha cierre","estado":"Estado",
            }),
            use_container_width=True, hide_index=True,
        )
        st.caption(f"Mostrando {len(df_tbl):,} de {len(df_f):,} registros.")

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
    "<p style='text-align:center;color:#bbb;font-size:0.76rem'>"
    "Solemne II - FITO9017 - Universidad San Sebastian - "
    "Python / Pandas / Matplotlib / Streamlit - "
    "Fuente: API Mercado Publico Chile (api.mercadopublico.cl)"
    "</p>",
    unsafe_allow_html=True
)
