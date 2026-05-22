"""
=============================================================
Solemne II - FITO9017
Módulo: Análisis de datos con Pandas
Fuente: API Mercado Público Chile
=============================================================

Este módulo realiza el análisis exploratorio y estadístico
de las licitaciones obtenidas desde la API de Mercado Público.

Análisis incluidos:
  1. Resumen general del dataset
  2. Distribución por tipo de licitación
  3. Distribución por región
  4. Top 10 organismos que más licitan
  5. Análisis de montos estimados
  6. Distribución por días de cierre
  7. Evolución temporal (fecha publicación)
=============================================================
"""

import pandas as pd
import numpy as np

# ── Mapas de referencia ──────────────────────────────────────
TIPO_LICITACION = {
    "LE": "Licitación Pública ≤1000 UTM",
    "LP": "Licitación Pública >1000 UTM",
    "LR": "Licitación Privada",
    "L1": "Convenio Marco",
    "LS": "Licitación de Servicios",
    "CO": "Compra Ágil",
    "AG": "Compra Ágil",
    "B2": "Gran Empresa",
    "E2": "Empresa en el extranjero",
    "I2": "Innovación",
    "O1": "Orden de Compra",
}


def cargar_datos(ruta_csv="licitaciones.csv"):
    """
    Carga el CSV generado por el módulo de API y lo prepara para análisis.
    Aplica limpieza, tipado y enriquecimiento del dataset.

    Parámetros:
        ruta_csv (str): ruta al archivo CSV con los datos

    Retorna:
        pd.DataFrame: DataFrame limpio y enriquecido
    """
    df = pd.read_csv(ruta_csv)

    # Convertir fechas
    for col in ["fecha_publicacion", "fecha_cierre", "fecha_adjudicacion"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    # Convertir numéricos
    df["monto_estimado"] = pd.to_numeric(df["monto_estimado"], errors="coerce")
    df["dias_cierre"]    = pd.to_numeric(df["dias_cierre"],    errors="coerce")
    df["reclamos"]       = pd.to_numeric(df["reclamos"],       errors="coerce").fillna(0)

    # Limpiar región: si viene vacía se marca como "No especificada"
    df["region"] = df["region"].replace("", "No especificada").fillna("No especificada")

    # Acortar nombre de región para gráficos (quitar "Región de/del/de la")
    df["region_corta"] = (
        df["region"]
        .str.replace(r"Región (de la |de los |del |de |Metropolitana de )?", "", regex=True)
        .str.strip()
    )

    # Agregar descripción del tipo de licitación
    df["tipo_descripcion"] = df["tipo"].map(TIPO_LICITACION).fillna("Otro / No especificado")

    # Calcular días desde publicación hasta hoy
    hoy = pd.Timestamp.now()
    df["dias_desde_publicacion"] = (hoy - df["fecha_publicacion"]).dt.days

    print(f"[OK] Datos cargados: {len(df)} licitaciones, {df.shape[1]} columnas")
    return df


def resumen_general(df):
    """
    Genera un resumen estadístico general del dataset.

    Parámetros:
        df (pd.DataFrame): dataset de licitaciones

    Retorna:
        dict: métricas clave del dataset
    """
    resumen = {
        "total_licitaciones":   len(df),
        "regiones_unicas":      df["region"].nunique(),
        "organismos_unicos":    df["organismo"].nunique(),
        "tipos_unicos":         df["tipo"].nunique(),
        "con_monto":            int(df["monto_estimado"].notna().sum()),
        "sin_monto":            int(df["monto_estimado"].isna().sum()),
        "monto_total_CLP":      df["monto_estimado"].sum(),
        "monto_promedio_CLP":   df["monto_estimado"].mean(),
        "monto_mediana_CLP":    df["monto_estimado"].median(),
        "monto_maximo_CLP":     df["monto_estimado"].max(),
        "fecha_mas_antigua":    df["fecha_publicacion"].min(),
        "fecha_mas_reciente":   df["fecha_publicacion"].max(),
        "promedio_dias_cierre": df["dias_cierre"].mean(),
        "total_reclamos":       int(df["reclamos"].sum()),
    }
    return resumen


def analisis_por_tipo(df):
    """
    Analiza la distribución de licitaciones por tipo.

    Retorna:
        pd.DataFrame: conteo y porcentaje por tipo
    """
    resultado = (
        df.groupby(["tipo", "tipo_descripcion"])
        .size()
        .reset_index(name="cantidad")
        .sort_values("cantidad", ascending=False)
    )
    resultado["porcentaje"] = (resultado["cantidad"] / len(df) * 100).round(1)
    return resultado


def analisis_por_region(df):
    """
    Analiza la distribución geográfica de licitaciones.

    Retorna:
        pd.DataFrame: conteo, porcentaje y monto promedio por región
    """
    resultado = df.groupby("region_corta").agg(
        cantidad=("codigo", "count"),
        monto_promedio=("monto_estimado", "mean"),
        total_reclamos=("reclamos", "sum"),
    ).reset_index().sort_values("cantidad", ascending=False)

    resultado["porcentaje"] = (resultado["cantidad"] / len(df) * 100).round(1)
    return resultado


def top_organismos(df, n=10):
    """
    Identifica los organismos que más licitaciones publican.

    Parámetros:
        n (int): número de organismos a mostrar

    Retorna:
        pd.DataFrame: top N organismos por cantidad de licitaciones
    """
    resultado = (
        df[df["organismo"] != ""]
        .groupby("organismo")
        .agg(
            cantidad=("codigo", "count"),
            monto_total=("monto_estimado", "sum"),
        )
        .reset_index()
        .sort_values("cantidad", ascending=False)
        .head(n)
    )
    return resultado


def analisis_montos(df):
    """
    Analiza la distribución de montos estimados de las licitaciones.
    Solo considera las licitaciones que tienen monto informado.

    Retorna:
        dict: estadísticas descriptivas de los montos
    """
    df_con_monto = df[df["monto_estimado"].notna()].copy()

    if df_con_monto.empty:
        return {"mensaje": "No hay licitaciones con monto informado en el dataset actual"}

    stats = {
        "n":        len(df_con_monto),
        "min":      df_con_monto["monto_estimado"].min(),
        "q25":      df_con_monto["monto_estimado"].quantile(0.25),
        "mediana":  df_con_monto["monto_estimado"].median(),
        "media":    df_con_monto["monto_estimado"].mean(),
        "q75":      df_con_monto["monto_estimado"].quantile(0.75),
        "max":      df_con_monto["monto_estimado"].max(),
        "std":      df_con_monto["monto_estimado"].std(),
        "top3":     df_con_monto.nlargest(3, "monto_estimado")[["nombre","monto_estimado"]],
    }
    return stats


def analisis_temporal(df):
    """
    Analiza la evolución temporal de publicaciones por semana.

    Retorna:
        pd.Series: serie temporal con conteo de publicaciones por semana
    """
    df_fechas = df[df["fecha_publicacion"].notna()].copy()
    df_fechas["semana"] = df_fechas["fecha_publicacion"].dt.to_period("W").dt.start_time
    serie = df_fechas.groupby("semana").size()
    serie.name = "cantidad_publicaciones"
    return serie


def analisis_dias_cierre(df):
    """
    Analiza la distribución de días de cierre de licitaciones.
    Permite entender los tiempos de proceso habituales.

    Retorna:
        pd.Series: serie con la distribución de días de cierre
    """
    return df["dias_cierre"].dropna().describe()


# ── Ejecución de prueba ──────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  Solemne II — Análisis de datos con Pandas")
    print("=" * 60)

    # 1. Cargar datos
    df = cargar_datos("licitaciones.csv")

    # 2. Resumen general
    print("\n📊 RESUMEN GENERAL")
    print("-" * 40)
    res = resumen_general(df)
    for k, v in res.items():
        if isinstance(v, float):
            print(f"  {k:<28}: {v:,.0f}")
        else:
            print(f"  {k:<28}: {v}")

    # 3. Por tipo
    print("\n📋 DISTRIBUCIÓN POR TIPO")
    print("-" * 40)
    df_tipo = analisis_por_tipo(df)
    print(df_tipo.to_string(index=False))

    # 4. Por región
    print("\n🗺️  DISTRIBUCIÓN POR REGIÓN")
    print("-" * 40)
    df_region = analisis_por_region(df)
    print(df_region.to_string(index=False))

    # 5. Top organismos
    print("\n🏛️  TOP ORGANISMOS")
    print("-" * 40)
    df_org = top_organismos(df, n=5)
    print(df_org.to_string(index=False))

    # 6. Montos
    print("\n💰 ANÁLISIS DE MONTOS")
    print("-" * 40)
    stats = analisis_montos(df)
    for k, v in stats.items():
        if k != "top3":
            print(f"  {k:<10}: {v:,.0f}" if isinstance(v, float) else f"  {k:<10}: {v}")

    # 7. Días cierre
    print("\n⏱️  DÍAS DE CIERRE")
    print("-" * 40)
    print(analisis_dias_cierre(df))

    print("\n✅ Análisis completado")
