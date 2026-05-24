"""
Solemne II - FITO9017
Analizador de Licitaciones Publicas - Chile
Universidad San Sebastian

ERROR INTENCIONAL DOCUMENTADO:
Ver funcion calcular_urgencia() -- error de sintaxis
identificado y corregido durante el desarrollo.
"""

import streamlit as st
import pandas as pd
import requests
import time
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Licitaciones Publicas Chile",
    layout="wide",
)

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


# ============================================================
# ERROR INTENCIONAL DOCUMENTADO
# ============================================================
def calcular_urgencia(dias):
    """
    Clasifica urgencia de una licitacion segun dias restantes al cierre.

    ERROR IDENTIFICADO EN DESARROLLO:
        Comparacion encadenada invalida en Python que genera SyntaxError.

        Codigo con error:
            if dias > 0 and < 7:    <- SyntaxError: invalid syntax
                return "Urgente"

        El operador 'and' requiere dos expresiones booleanas completas.
        La forma 'and < 7' no es valida porque carece de operando izquierdo.

    Correccion aplicada:
        if dias is not None and dias <= 5:
    """
    # -- VERSION CON ERROR (no ejecutar) ----------------------
    # if dias > 0 and < 7:    <- SyntaxError
    #     return "Urgente"
    # -- FIN ERROR --------------------------------------------

    # -- VERSION CORREGIDA ------------------------------------
    if dias is None or pd.isna(dias):
        return "Sin dato"
    dias = int(dias)
    if dias <= 5:
        return "Urgente"
    if dias <= 10:
        return "Proximo"
    return "Normal"


# -- Procesamiento del DataFrame ------------------------------
def listado_a_dataframe(listado):
    """
    Convierte el listado de la API en un DataFrame limpio y tipado.

    Transformaciones:
      - pd.to_datetime : FechaCierre a tipo datetime64
      - pd.to_numeric  : dias_cierre a tipo numerico float64
      - str.replace    : limpieza de prefijos en nombres de region
      - str.strip      : eliminacion de espacios en campos de texto
    """
    registros = []
    for item in listado:
        codigo = item.get("CodigoExterno", "")
        nombre = item.get("Nombre", "").strip()

        partes = codigo.split("-")
        tipo   = partes[-1][:2] if len(partes) >= 2 else ""

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

    df = pd.DataFrame(registros)
    df["dias_cierre"] = pd.to_numeric(df["dias_cierre"], errors="coerce")

    if "region" in df.columns:
        df["region_corta"] = (
            df["region"]
            .str.replace(
                r"Region (de la |de los |del |de |Metropolitana de )?",
                "", regex=True
            )
            .str.strip()
        )

    return df


# -- Carga desde API ------------------------------------------
@st.cache_data(ttl=1800, show_spinner=False)
def cargar_listado_completo():
    """
    Descarga el catalogo completo de licitaciones activas.
    Retorna hasta 4.430 registros. Se cachea por 30 minutos.
    """
    r = requests.get(
        BASE_URL,
        params={"estado": "activas", "ticket": TICKET, "cantidad": 5000},
        timeout=20,
    )
    r.raise_for_status()
    data = r.json()
    if data.get("Codigo") == 203:
        raise ValueError("Ticket no valido")
    return data.get("Listado", [])


@st.cache_data(ttl=3600, show_spinner=False)
def obtener_detalle(codigo):
    """Descarga region, organismo y monto de una licitacion especifica."""
    try:
        r = requests.get(
            BASE_URL,
            params={"codigo": codigo, "ticket": TICKET},
            timeout=12,
        )
        r.raise_for_status()
        listado = r.json().get("Listado", [])
        if not listado:
            return {}
        det  = listado[0]
        comp = det.get("Comprador") or {}
        return {
            "organismo": comp.get("NombreOrganismo", "No informado"),
            "region":    (comp.get("RegionUnidad") or "No informado").strip(),
            "monto":     det.get("MontoEstimado"),
        }
    except Exception:
        return {}


# -- Graficos -------------------------------------------------
def grafico_tipo(df):
    conteo = df["tipo_desc"].value_counts().head(6)
    if conteo.empty:
        return None
    fig, ax = plt.subplots(figsize=(5, 4))
    ax.pie(
        conteo.values,
        labels=conteo.index,
        autopct="%1.0f%%",
        startangle=140,
    )
    ax.set_title("Distribucion por tipo de licitacion")
    fig.tight_layout()
    return fig


def grafico_urgencia(df):
    orden  = ["Urgente", "Proximo", "Normal", "Sin dato"]
    conteo = df["urgencia"].value_counts().reindex(orden).dropna()
    if conteo.empty:
        return None
    fig, ax = plt.subplots(figsize=(5, 3.5))
    ax.bar(conteo.index, conteo.values, color=["#e74c3c","#f39c12","#27ae60","#95a5a6"])
    for i, v in enumerate(conteo.values):
        ax.text(i, v + 0.3, str(int(v)), ha="center", fontsize=10)
    ax.set_title("Licitaciones por urgencia de cierre")
    ax.set_ylabel("Cantidad")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return fig


def grafico_tipos_barra(df):
    conteo = df["tipo"].value_counts().sort_values()
    if conteo.empty:
        return None
    fig, ax = plt.subplots(figsize=(6, max(3, len(conteo) * 0.6)))
    ax.barh(conteo.index, conteo.values)
    for b in ax.patches:
        ax.text(
            b.get_width() + 0.3,
            b.get_y() + b.get_height() / 2,
            str(int(b.get_width())),
            va="center",
            fontsize=9,
        )
    ax.set_title("Licitaciones por codigo de tipo")
    ax.set_xlabel("Cantidad")
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_xlim(0, conteo.max() * 1.2)
    fig.tight_layout()
    return fig


# ============================================================
# INTERFAZ
# ============================================================

st.title("Analizador de Licitaciones Publicas - Chile")
st.caption("Fuente: API Mercado Publico Chile (api.mercadopublico.cl)")

# -- Carga inicial --------------------------------------------
if "df" not in st.session_state:
    with st.spinner("Cargando licitaciones desde la API de Mercado Publico..."):
        try:
            listado = cargar_listado_completo()
            st.session_state.df = listado_a_dataframe(listado)
        except Exception as e:
            st.error(f"No se pudo conectar con la API: {e}")
            st.stop()

# -- Sidebar --------------------------------------------------
with st.sidebar:
    st.header("Opciones")

    if st.button("Actualizar datos", use_container_width=True):
        st.cache_data.clear()
        with st.spinner("Actualizando..."):
            try:
                listado = cargar_listado_completo()
                st.session_state.df = listado_a_dataframe(listado)
                st.success("Datos actualizados correctamente")
            except Exception as e:
                st.error(f"Error: {e}")

    st.divider()
    st.subheader("Filtros")

    df_total = st.session_state.df

    tipos_disp = sorted(df_total["tipo"].dropna().unique().tolist())
    tip_sel    = st.multiselect("Tipo de licitacion", tipos_disp, default=tipos_disp)

    urg_disp = ["Urgente", "Proximo", "Normal", "Sin dato"]
    urg_sel  = st.multiselect("Urgencia", urg_disp, default=urg_disp)

    st.divider()
    st.caption(f"Total en API: {len(df_total):,} licitaciones activas")
    st.caption("FITO9017 - Solemne II")
    st.caption("Universidad San Sebastian")

# Aplicar filtros
df_f = df_total[
    df_total["tipo"].isin(tip_sel) &
    df_total["urgencia"].isin(urg_sel)
].copy()

# -- Tabs -----------------------------------------------------
tab1, tab2, tab3 = st.tabs([
    "Buscador",
    "Dashboard",
    "Tabla de datos",
])


# -- TAB 1: BUSCADOR ------------------------------------------
with tab1:
    st.subheader("Busqueda de licitaciones")

    col1, col2 = st.columns(2)
    with col1:
        txt_kw = st.text_input(
            "Palabra clave",
            placeholder="Ej: hospital, madera, calibracion, pavimento..."
        )
    with col2:
        txt_id = st.text_input(
            "Codigo de licitacion",
            placeholder="Ej: 1003473-51-LP26"
        )

    col3, col4 = st.columns(2)
    with col3:
        solo_urgente = st.checkbox("Solo urgentes y proximas (cierre <= 10 dias)")
    with col4:
        max_res = st.selectbox("Mostrar hasta", [10, 25, 50, 100], index=1)

    # Busqueda sobre los 4.430 registros cargados en memoria
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
        df_busq = df_busq[df_busq["urgencia"].isin(["Urgente", "Proximo"])]

    total_enc = len(df_busq)
    df_busq   = df_busq.head(max_res)

    st.write(
        f"**{total_enc:,} resultado(s) encontrado(s)**"
        + (f" -- mostrando los primeros {max_res}" if total_enc > max_res else "")
    )
    st.divider()

    if total_enc == 0:
        st.warning(
            "No se encontraron licitaciones con los criterios ingresados. "
            "Pruebe con otros terminos o ajuste los filtros del panel lateral."
        )
    else:
        for _, row in df_busq.iterrows():
            urg = row["urgencia"]
            dias_txt = (
                f"{int(row['dias_cierre'])} dias al cierre"
                if pd.notna(row["dias_cierre"]) else "plazo no informado"
            )
            cierre_txt = (
                row["fecha_cierre"].strftime("%d/%m/%Y")
                if pd.notna(row["fecha_cierre"]) else "--"
            )

            with st.container(border=True):
                col_a, col_b = st.columns([6, 2])
                with col_a:
                    st.markdown(f"**{row['nombre']}**")
                    st.caption(
                        f"Tipo: {row['tipo']}  |  "
                        f"Urgencia: {urg}  |  "
                        f"{dias_txt}  |  "
                        f"Cierre: {cierre_txt}"
                    )
                with col_b:
                    st.markdown(
                        f"[Ver en Mercado Publico]({row['url_mp']})",
                    )
                    st.caption(row["codigo"])


# -- TAB 2: DASHBOARD -----------------------------------------
with tab2:
    st.subheader("Resumen estadistico")

    # Metrica general con st.metric
    st.metric(
        label="Total licitaciones activas",
        value=f"{len(df_f):,}",
        help="Segun filtros seleccionados en el panel lateral"
    )

    # Metricas en columnas
    urgentes = len(df_f[df_f["urgencia"] == "Urgente"])
    proximas = len(df_f[df_f["urgencia"] == "Proximo"])
    tipos_u  = df_f["tipo"].nunique()

    c1, c2, c3 = st.columns(3)
    c1.metric("Cierre en <= 5 dias",   f"{urgentes:,}")
    c2.metric("Cierre en 6 a 10 dias", f"{proximas:,}")
    c3.metric("Tipos distintos",        tipos_u)

    st.divider()

    col_g1, col_g2, col_g3 = st.columns(3)

    with col_g1:
        st.write("**Por tipo de licitacion**")
        fig = grafico_tipo(df_f)
        if fig:
            st.pyplot(fig, use_container_width=True)
        st.caption("Proporcion de licitaciones segun tipo y monto en UTM.")

    with col_g2:
        st.write("**Urgencia de cierre**")
        fig = grafico_urgencia(df_f)
        if fig:
            st.pyplot(fig, use_container_width=True)
        st.caption("Dias restantes antes del cierre de ofertas.")

    with col_g3:
        st.write("**Distribucion por codigo**")
        fig = grafico_tipos_barra(df_f)
        if fig:
            st.pyplot(fig, use_container_width=True)
        st.caption("Frecuencia de cada codigo de tipo en el listado activo.")

    st.divider()
    st.write("**Resumen por tipo**")
    resumen = (
        df_f.groupby(["tipo", "tipo_desc"])
        .agg(cantidad=("codigo", "count"))
        .reset_index()
        .sort_values("cantidad", ascending=False)
    )
    resumen["porcentaje"] = (resumen["cantidad"] / len(df_f) * 100).round(1)
    st.dataframe(
        resumen.rename(columns={
            "tipo": "Codigo", "tipo_desc": "Descripcion",
            "cantidad": "Licitaciones", "porcentaje": "% del total",
        }),
        use_container_width=True,
        hide_index=True,
    )


# -- TAB 3: TABLA ---------------------------------------------
with tab3:
    st.subheader("Tabla completa")

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

    cols = ["codigo", "nombre", "tipo_desc", "urgencia",
            "dias_cierre", "fecha_cierre", "estado"]
    st.dataframe(
        df_tbl[cols].rename(columns={
            "codigo":       "Codigo",
            "nombre":       "Nombre",
            "tipo_desc":    "Tipo",
            "urgencia":     "Urgencia",
            "dias_cierre":  "Dias al cierre",
            "fecha_cierre": "Fecha cierre",
            "estado":       "Estado",
        }),
        use_container_width=True,
        hide_index=True,
    )
    st.caption(f"Mostrando {len(df_tbl):,} de {len(df_f):,} registros.")

    csv = df_tbl[cols].to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Descargar CSV",
        data=csv,
        file_name="licitaciones_mercado_publico.csv",
        mime="text/csv",
    )
